---
applyTo: '**'
---
ROLE
You are an expert Python software architect and cryptography/ML engineer.
You will specify, generate, and document the complete codebase for Aegis—a production-ready, privacy-preserving ML orchestration platform for Clyrai that automates differential privacy (DP) and federated learning (FL) for real enterprise deployments.

GLOBAL CONSTRAINTS
- Delivery target: production-feasible in 6–12 weeks for a solo founder with AI tooling.
- Libraries: Favor open-source, non-proprietary Python libraries (Opacus for DP-SGD; Flower for FL; FastAPI for API; Streamlit or Click for UI; scikit-learn/PyTorch/TensorFlow for model examples).
- Quality: Production-grade code, modular, typed where practical, with tests, docs, CI scaffolding, and deploy artifacts.
- Security & Compliance: mTLS for transport, RBAC, audit logs, input validation, and automated compliance reports (Markdown/PDF), with DP as a first-class control.

FOUNDATIONS (TECH ANCHORS)
- Differential Privacy: Implement DP-SGD via Opacus with Gaussian/Rényi/moments accounting, support epsilon-targeting (auto-calibration) and step-wise accounting; expose noise multiplier, clipping norm, sample rate as first-class parameters.
- Federated Orchestration: Use Flower as the coordination substrate; implement a custom server strategy providing Krum and coordinate-wise Trimmed Mean aggregators; handle participant auth, stragglers, retries, and basic health signaling.
- API & Security: Build a FastAPI service with mTLS, RBAC (role-based permissions on admin/run/report endpoints), structured audit logs, input validation, and OpenAPI schema.

DELIVERABLES (STAGE-BASED WITH ACCEPTANCE CRITERIA)

Stage 1 — Architecture Summary
- Deliver: README section with architecture diagram (ASCII or mermaid), component responsibilities, data flow, security boundaries, and dependency choices.
- Accept when: A new engineer can explain data flow, trust boundaries, and module interactions in <10 minutes.

Stage 2 — DifferentialPrivacyEngine
- Deliver: Python module `aegis/privacy_engine.py` implementing DP-SGD via Opacus (Gaussian/RDP accounting), APIs for:
  - epsilon_targeting(accuracy_goal, delta) → calibrated (epsilon, noise_multiplier)
  - stepwise_accounting() → running epsilon/delta given training steps
  - configuration for clipping, noise multiplier, sample rate
- Tests: Unit tests validate accountant values on toy datasets; verify that stricter (lower) epsilon decreases utility as expected; serialization of DP config.
- Accept when: `pytest tests/test_dp_engine.py` passes; epsilon tracking matches expected ranges for provided toy configs; docs show how to tune DP.

Stage 3 — FederatedCoordinator (Flower Strategy)
- Deliver: `aegis/federated_coordinator.py` with Flower server strategy implementing:
  - Selectable aggregators: Krum and Trimmed Mean
  - Participant authentication handshake; signed/validated update envelopes
  - Straggler policy and retry/backoff; minimal health pings
- Tests: Simulation with 3–5 clients; correctness tests on aggregation outputs; adversarial unit tests simulating a small number of Byzantine clients.
- Accept when: `python -m examples.flower_sim.run_demo` trains a small model successfully with both aggregators; tests pass.

Stage 4 — API Layer (FastAPI)
- Deliver: `aegis/api.py` exposing endpoints for:
  - Dataset/participant registration and lifecycle
  - Training session start/stop/status
  - DP configuration (epsilon target, clipping, noise multiplier)
  - Federated strategy selection (Krum/Trimmed Mean)
  - Compliance report generation (Markdown/PDF)
- Security: mTLS enforced in server configuration, RBAC middleware, Pydantic validation, structured audit logs.
- Accept when: OpenAPI schema renders; RBAC prevents low-privilege access; invalid inputs rejected; audit logs persist key events.

Stage 5 — CLI or Dashboard
- Deliver: Choose either:
  - CLI via Click `aegis/cli.py` mirroring API flows; or
  - Streamlit dashboard `aegis/dashboard.py` with real-time charts (accuracy, loss, epsilon consumption), privacy sliders, and run controls.
- Accept when: End-to-end run starts, tracks metrics, and completes; UI/CLI options match API features; demo script runs without manual code edits.

Stage 6 — Compliance Reporting
- Deliver: `aegis/compliance/report.py` producing Markdown (and PDF export) containing:
  - DP configuration (epsilon, delta, accountant method, clipping, noise, sample rate)
  - Training audit summary (participants, timestamps, strategy, versions)
  - Mappings to GDPR/HIPAA/EU AI Act narratives, including DPIA-style risk notes
- Accept when: A generated report includes all required sections and can be reviewed by non-technical stakeholders.

Stage 7 — Security & Audit Tests
- Deliver: Tests for membership inference and model inversion on at least one dataset/model combo; measure attack success across multiple epsilon settings; API auth/mTLS tests; RBAC unit tests; input validation tests.
- Accept when: Security test suite runs in CI, producing CSV/Markdown reports; mTLS/RBAC tests pass; attacks show expected degradation with stronger privacy (lower epsilon).

Stage 8 — Containerization & Deploy
- Deliver: Dockerfile(s), docker-compose, Kubernetes manifests (Deployments, Services, ConfigMaps, Secrets for certs/keys), runbook for certificate issuance/rotation and client onboarding.
- Accept when: `docker compose up` launches API + coordinator + UI locally; Kubernetes manifests deploy and pass health checks; secrets are mounted; mTLS enforced.

Stage 9 — Integration Examples
- Deliver: `examples/` containing:
  - scikit-learn example (non-DP baseline through FL)
  - PyTorch + Opacus example (DP training via FL)
  - TensorFlow example (non-DP or minimal DP note if TF-DP is deferred)
  - 2–3 simulated clients + server runner scripts
- Accept when: Examples run end-to-end without editing core modules; results saved and plotted.

Stage 10 — Documentation
- Deliver: README (quickstart, architecture, security model, config matrix), API reference (OpenAPI link), developer guide (contrib, tests, style), ops guide (deploy, certs, rotation, backups), and FAQ.
- Accept when: A fresh engineer can build, run demos, and deploy in <60 minutes.

Stage 11 — Performance & Benchmarking
- Deliver: `benchmarks/` scripts for:
  - Federated training speed (per round, per aggregator)
  - Privacy-utility tradeoff across epsilon values
  - Compliance report runtime
- Accept when: Scripts emit CSV/Markdown summaries and optional plots; baseline thresholds documented in README.

SECURITY & OPERATIONS (SPECIFICS)
- mTLS: Configure Uvicorn/gunicorn + FastAPI to require client certs; document CA chain, cert issuance/rotation, and error handling; in Kubernetes, store keys/certs in Secrets and mount as volumes.
- RBAC: Define roles (admin, operator, viewer) and guard sensitive endpoints (e.g., training start/stop, DP config changes, report generation).
- Audit Logs: JSON-structured events with timestamps, actor, action, parameters hash, and outcome; rotate and persist logs; include hash chaining or signatures if trivial to add.
- Inputs: Strict validation with Pydantic; reject out-of-range epsilon, noise multipliers, and clipping norms; enforce rate limits on sensitive endpoints.

OUTPUT STRUCTURE (FILES & FOLDERS)
- aegis/
  - privacy_engine.py
  - federated_coordinator.py
  - api.py
  - cli.py OR dashboard.py
  - compliance/report.py
  - security/ (rbac.py, mtls.md, audit.py)
  - __init__.py
- examples/
  - sklearn_demo.py
  - pytorch_opacus_demo.py
  - tensorflow_demo.py
  - flower_sim/ (server.py, client.py, dataset.py)
- tests/
  - test_dp_engine.py
  - test_federated_coordinator.py
  - test_api_security.py
  - test_attack_membership_inference.py
  - test_attack_model_inversion.py
- benchmarks/
  - benchmark_training_speed.py
  - benchmark_dp_tradeoff.py
  - benchmark_report_runtime.py
- deploy/
  - Dockerfile
  - docker-compose.yml
  - k8s/ (deployment.yaml, service.yaml, configmap.yaml, secrets.yaml)
- docs/
  - README.md
  - ARCHITECTURE.md (diagram)
  - OPERATIONS.md (mTLS, certs, rotation, runbook)
  - API.md (OpenAPI link and examples)
  - COMPLIANCE.md
  - CHANGELOG.md

DEMO & COMMANDS
- Provide a “happy path” demo script:
  1) start API/coordinator (local docker-compose),
  2) register 2–3 simulated participants,
  3) set epsilon target and select aggregator,
  4) run a training session,
  5) watch real-time metrics (CLI or Streamlit),
  6) generate a compliance report.
- Provide curl/HTTPie examples, CLI commands, and Streamlit usage instructions.
- Ensure demos run without modifying core code.

CI & QUALITY
- Add a simple GitHub Actions workflow: lint (ruff/flake8), type-check (mypy optional), tests (pytest), security tests, and artifact upload for benchmark and compliance reports.
- Include seed control and reproducibility notes.

START HERE
1) Produce the architecture diagram and a brief design summary first, with a dependency matrix and security boundary notes.
2) Then implement Stage 2 (DP Engine) with tests and docs.
3) Proceed stage-by-stage; after each stage, print acceptance checks and how to run them.
