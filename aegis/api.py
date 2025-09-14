from __future__ import annotations

from typing import Dict, List, Optional
import time

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import Response as FastAPIResponse
from pydantic import BaseModel, Field

from .privacy_engine import DPConfig, DifferentialPrivacyEngine
from .federated_coordinator import FederatedCoordinator
from .security.rbac import Role, allow, parse_role
from .security.audit import AuditLogger
from .compliance.report import generate_markdown, generate_pdf
from .data_validation import (
    validate_dataset_size,
    detect_imbalance,
    check_missing_values,
    check_high_dimensionality,
    validate_schema,
)
import os
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    _HAVE_METRICS = True
except Exception:  # pragma: no cover - optional
    Counter = Histogram = generate_latest = CONTENT_TYPE_LATEST = None
    _HAVE_METRICS = False

# Optional Redis for rate limiting
try:
    import redis as _redis  # type: ignore
    _REDIS_URL = os.environ.get("REDIS_URL")
    _RATE_BACKEND = os.environ.get("AEGIS_RATE_LIMIT_BACKEND", "memory").lower()
    _REDIS = _redis.Redis.from_url(_REDIS_URL) if (_REDIS_URL and _RATE_BACKEND == "redis") else None
except Exception:  # pragma: no cover
    _REDIS = None

app = FastAPI(title="Aegis API", version="0.1.0")
def _mtls_sim_check(x_client_cert: Optional[str]) -> None:
    require = os.environ.get("AEGIS_REQUIRE_MTLS_SIM", "0") == "1"
    if require and not x_client_cert:
        raise HTTPException(status_code=403, detail="Client certificate required (simulated)")
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# Prometheus metrics (optional)
if _HAVE_METRICS:
    REQ_COUNT = Counter("aegis_requests_total", "Total API requests", ["endpoint", "method", "status"])
    REQ_LATENCY = Histogram("aegis_request_latency_seconds", "Request latency", ["endpoint", "method"])
else:  # lightweight stubs
    class _Null:
        def labels(self, *args, **kwargs):
            return self
        def inc(self, *_a, **_k):
            return None
        def observe(self, *_a, **_k):
            return None
    REQ_COUNT = _Null()
    REQ_LATENCY = _Null()

@app.get("/metrics")
async def metrics():
    if not _HAVE_METRICS:
        return {"status": "metrics_disabled"}
    return FastAPIResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


audit = AuditLogger()


class Participant(BaseModel):
    client_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    key_hex: str = Field(..., min_length=2)


class DPConfigModel(BaseModel):
    clipping_norm: float = Field(1.0, gt=0)
    noise_multiplier: float = Field(1.0, ge=0)
    sample_rate: float = Field(0.01, gt=0, le=1)
    delta: float = Field(1e-5, gt=0, lt=1)
    accountant: str = Field("rdp")


class StrategyModel(BaseModel):
    strategy: str = Field(..., pattern=r"^(trimmed_mean|krum)$")


class TrainingStartModel(BaseModel):
    session_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    rounds: int = Field(..., ge=1, le=10000)


class DatasetRegistration(BaseModel):
    client_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    num_samples: int = Field(..., ge=1)
    num_features: int = Field(..., ge=1)
    missing_fraction: float = Field(0.0, ge=0, le=1)
    class_counts: Dict[str, int] = Field(default_factory=dict)
    feature_schema: List[str] = Field(default_factory=list, alias="schema")

    model_config = {
        "populate_by_name": True,
        "alias_generator": None,
    }


# In-memory stores for Stage 4
participants: Dict[str, bytes] = {}
engine = DifferentialPrivacyEngine(DPConfig())
coordinator = FederatedCoordinator(aggregator="trimmed_mean", auth_keys={})
sessions: Dict[str, Dict[str, object]] = {}
datasets: Dict[str, Dict[str, object]] = {}


def require_permission(permission: str):
    async def _dep(x_role: Optional[str] = Header(default=None, alias="X-Role")) -> Role:
        role = parse_role(x_role)
        if not allow(role, permission):
            raise HTTPException(status_code=403, detail="forbidden")
        return role
    return _dep


# Simple in-memory rate limiter (Stage 4): limit key per action within window
_RATE_BUCKET: Dict[str, List[float]] = {}

def rate_limiter(key_name: str, limit: int = 10, window_s: float = 60.0):
    async def _dep(request: Request) -> None:
        # Allow disabling in certain environments
        if os.environ.get("AEGIS_DISABLE_RATE_LIMIT", "0") == "1":
            return
        now = time.time()
        # Scope bucket by server port to avoid cross-test/process interference
        port = request.url.port or 0
        instance_key = f"{key_name}:{port}"
        # Redis backend (sorted set with timestamps)
        if _REDIS is not None:
            zkey = f"aegis:rl:{instance_key}"
            cutoff = now - window_s
            try:
                _REDIS.zremrangebyscore(zkey, 0, cutoff)
                count = _REDIS.zcard(zkey)
                if count >= limit:
                    raise HTTPException(status_code=429, detail="rate limit exceeded")
                _REDIS.zadd(zkey, {str(now): now})
                _REDIS.expire(zkey, int(window_s))
                return
            except Exception:
                # Fallback to memory on Redis errors
                pass
        bucket = _RATE_BUCKET.setdefault(instance_key, [])
        # trim old
        cutoff = now - window_s
        while bucket and bucket[0] < cutoff:
            bucket.pop(0)
        if len(bucket) >= limit:
            raise HTTPException(status_code=429, detail="rate limit exceeded")
        bucket.append(now)
    return _dep


@app.post("/participants")
async def register_participant(p: Participant, role: Role = Depends(require_permission("participant:register")), _: None = Depends(rate_limiter("participant:register", limit=20, window_s=60))):
    key = bytes.fromhex(p.key_hex)
    participants[p.client_id] = key
    coordinator.auth_keys[p.client_id] = key
    evt = audit.emit(actor=role.value, action="participant:register", params=p.model_dump(), outcome="ok")
    return {"status": "ok", "audit": evt.to_json()}


@app.post("/dataset/register")
async def register_dataset(d: DatasetRegistration, role: Role = Depends(require_permission("dataset:register"))):
    warnings: List[str] = []
    warnings += validate_dataset_size(d.num_samples)
    warnings += detect_imbalance(d.class_counts)
    warnings += check_missing_values(d.missing_fraction)
    warnings += check_high_dimensionality(d.num_features)
    # Cross-participant schema check against first available reference
    if d.feature_schema and datasets:
        ref_schema: Optional[List[str]] = None
        for meta in datasets.values():
            if isinstance(meta, dict) and meta.get("schema"):
                ref_schema = list(meta.get("schema", []))  # type: ignore[arg-type]
                break
        if ref_schema:
            _ok, schema_w = validate_schema({"existing": ref_schema, d.client_id: d.feature_schema})
            warnings += schema_w
    datasets[d.client_id] = d.model_dump(by_alias=True)
    evt = audit.emit(actor=role.value, action="dataset:register", params=d.model_dump(), outcome="ok")
    return {"status": "ok", "warnings": warnings, "audit": evt.to_json()}


@app.post("/dp/config")
async def set_dp_config(cfg: DPConfigModel, role: Role = Depends(require_permission("dp:configure")), _: None = Depends(rate_limiter("dp:configure", limit=30, window_s=60))):
    engine.config = DPConfig.from_dict(cfg.model_dump())
    evt = audit.emit(actor=role.value, action="dp:configure", params=cfg.model_dump(), outcome="ok")
    return {"status": "ok", "audit": evt.to_json()}


@app.get("/dp/assess")
async def dp_assess(steps: int = 1000, role: Role = Depends(require_permission("dp:assess"))):
    res = engine.assess_parameters(steps=steps)
    return res


@app.post("/dp/budget/consume")
async def dp_budget_consume(steps: int, role: Role = Depends(require_permission("dp:budget"))):
    spent = engine.consume_budget(steps=steps)
    return {"spent_epsilon": spent, "delta": engine.config.delta}


@app.post("/dp/budget/reset")
async def dp_budget_reset(role: Role = Depends(require_permission("dp:budget"))):
    engine.reset_budget()
    return {"status": "ok"}


@app.post("/strategy")
async def set_strategy(s: StrategyModel, role: Role = Depends(require_permission("strategy:select")), _: None = Depends(rate_limiter("strategy:select", limit=60, window_s=60))):
    coordinator.aggregator = s.strategy
    evt = audit.emit(actor=role.value, action="strategy:select", params=s.model_dump(), outcome="ok")
    return {"status": "ok", "audit": evt.to_json()}


@app.post("/training/start")
async def start_training(body: TrainingStartModel, role: Role = Depends(require_permission("training:start")), _: None = Depends(rate_limiter("training:start", limit=60, window_s=60))):
    import time as _t
    _t0 = _t.perf_counter()
    sessions[body.session_id] = {
        "status": "running",
        "total_rounds": int(body.rounds),
        "current_round": 0,
        "started_at": _t.time(),
        "round_duration_s": float(os.environ.get("AEGIS_ROUND_DURATION_S", "3.0")),
    }
    evt = audit.emit(actor=role.value, action="training:start", params=body.model_dump(), outcome="ok")
    REQ_COUNT.labels("/training/start", "POST", "200").inc()
    REQ_LATENCY.labels("/training/start", "POST").observe(_t.perf_counter() - _t0)
    return {"status": "started", "audit": evt.to_json()}


@app.post("/training/stop")
async def stop_training(session_id: str, role: Role = Depends(require_permission("training:stop")), _: None = Depends(rate_limiter("training:stop", limit=120, window_s=60))):
    if session_id in sessions:
        sessions[session_id]["status"] = "stopped"
    evt = audit.emit(actor=role.value, action="training:stop", params={"session_id": session_id}, outcome="ok")
    return {"status": sessions.get(session_id, {}).get("status", "unknown"), "audit": evt.to_json()}


@app.get("/training/status")
async def training_status(session_id: str, role: Role = Depends(require_permission("training:status"))):
    import time as _t
    meta = sessions.get(session_id)
    if not meta:
        return {"session_id": session_id, "status": "unknown", "current_round": 0, "total_rounds": 0, "eta_seconds": 0.0}
    total_rounds = int(meta.get("total_rounds", int(meta.get("rounds", 0))))
    started_at = float(meta.get("started_at", _t.time()))
    round_duration_s = float(meta.get("round_duration_s", 3.0))
    elapsed = max(0.0, _t.time() - started_at)
    current_round = min(total_rounds, int(elapsed // max(round_duration_s, 0.1))) if total_rounds > 0 else 0
    status_val = str(meta.get("status", "running"))
    if current_round >= total_rounds and total_rounds > 0:
        status_val = "completed"
        meta["status"] = status_val
        meta["current_round"] = total_rounds
    else:
        meta["current_round"] = current_round
    eta = max(0.0, total_rounds * round_duration_s - elapsed)
    try:
        steps = max(1, current_round)
        assess = engine.assess_parameters(steps=steps)
        eps_est = float(assess.get("epsilon", 0.0))
    except Exception:
        eps_est = None
    # Keep backward compatibility: include old 'status' only response keys as well
    response = {
        "session_id": session_id,
        "status": status_val,
        "current_round": int(meta.get("current_round", current_round)),
        "total_rounds": total_rounds,
        "eta_seconds": eta,
    }
    if eps_est is not None:
        response["epsilon_estimate"] = eps_est
    return response


@app.get("/openapi.json")
async def openapi():
    return app.openapi()


@app.get("/compliance/report")
async def compliance_report(format: str = "markdown", steps: Optional[int] = None, x_client_cert: Optional[str] = Header(default=None, alias="X-Client-Cert"), role: Role = Depends(require_permission("report:generate")), _: None = Depends(rate_limiter("report:generate", limit=30, window_s=60))):
    import time as _t
    _t0 = _t.perf_counter()
    _mtls_sim_check(x_client_cert)
    # Estimate epsilon using DP engine for report context
    try:
        # choose steps from the active session with the largest configured rounds, fallback to 1000
        derived_steps = max((int(meta.get("total_rounds", int(meta.get("rounds", 0)))) for meta in sessions.values()), default=1000)
    except Exception:
        derived_steps = 1000
    steps_used = int(steps) if steps is not None and int(steps) > 0 else derived_steps
    assess = engine.assess_parameters(steps=steps_used)
    # Collect versions if available
    versions: Dict[str, str] = {"aegis_api": app.version}
    try:
        import fastapi as _fastapi  # type: ignore
        versions["fastapi"] = getattr(_fastapi, "__version__", "unknown")
    except Exception:
        pass
    try:
        import pydantic as _pyd  # type: ignore
        versions["pydantic"] = getattr(_pyd, "__version__", "unknown")
    except Exception:
        pass
    # Best-effort optional libs
    try:
        import flwr as _flwr  # type: ignore
        versions["flwr"] = getattr(_flwr, "__version__", "unknown")
    except Exception:
        pass
    try:
        import opacus as _opacus  # type: ignore
        versions["opacus"] = getattr(_opacus, "__version__", "unknown")
    except Exception:
        pass
    try:
        import torch as _torch  # type: ignore
        versions["torch"] = getattr(_torch, "__version__", "unknown")
    except Exception:
        pass
    md = generate_markdown(
        dp_config=engine.config,
        participants=participants,
        sessions=sessions,
        strategy=coordinator.aggregator,
        epsilon=float(assess.get("epsilon", 0.0)),
        epsilon_steps=steps_used,
        notes=str(assess.get("notes", "")),
        versions=versions,
    )
    evt = audit.emit(actor=role.value, action="report:generate", params={"participants": len(participants)}, outcome="ok")
    if format.lower() == "pdf":
        try:
            pdf_bytes = generate_pdf(md)
        except RuntimeError as e:
            REQ_COUNT.labels("/compliance/report", "GET", "500").inc()
            REQ_LATENCY.labels("/compliance/report", "GET").observe(_t.perf_counter() - _t0)
            raise HTTPException(status_code=500, detail=str(e))
        REQ_COUNT.labels("/compliance/report", "GET", "200").inc()
        REQ_LATENCY.labels("/compliance/report", "GET").observe(_t.perf_counter() - _t0)
        return FastAPIResponse(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "inline; filename=report.pdf"})
    REQ_COUNT.labels("/compliance/report", "GET", "200").inc()
    REQ_LATENCY.labels("/compliance/report", "GET").observe(_t.perf_counter() - _t0)
    return {"markdown": md, "audit": evt.to_json()}


# Phase 5: Compliance & Audit endpoints
class GDPRRequest(BaseModel):
    action: str = Field(..., pattern=r"^(export|delete)$")
    subject_id: str = Field(..., min_length=1, max_length=128)


@app.post("/compliance/gdpr")
async def compliance_gdpr(req: GDPRRequest, role: Role = Depends(require_permission("compliance:gdpr"))):
    # No PII is stored server-side in this demo; simulate success with audit trail
    evt = audit.emit(actor=role.value, action=f"gdpr:{req.action}", params={"subject_id": req.subject_id}, outcome="ok")
    return {"status": "ok", "audit": evt.to_json()}


@app.get("/compliance/hipaa")
async def compliance_hipaa(role: Role = Depends(require_permission("compliance:hipaa"))):
    # Return a minimal HIPAA capability summary for testing
    evt = audit.emit(actor=role.value, action="hipaa:summary", params={}, outcome="ok")
    return {"phi_at_rest": False, "phi_in_transit_protected": True, "audit": evt.to_json()}


@app.get("/audit/logs")
async def audit_logs(role: Role = Depends(require_permission("audit:read"))):
    events = [e.to_json() for e in audit.events()]
    return {"events": events, "valid_chain": audit.verify_chain()}


@app.get("/audit/checksum")
async def audit_checksum(role: Role = Depends(require_permission("audit:read"))):
    return {"checksum": audit.checksum(), "count": len(audit.events())}
