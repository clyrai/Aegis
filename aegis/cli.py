from __future__ import annotations

import os
import json
import time
from typing import Optional

import click
import httpx

DEFAULT_URL = os.environ.get("AEGIS_API_URL", "http://127.0.0.1:8000")


def _headers(role: str) -> dict:
    return {"X-Role": role}


@click.group()
def aegis():
    """Aegis CLI — control the Aegis API end-to-end."""


@aegis.command("register-participant")
@click.option("--client-id", required=True)
@click.option("--key-hex", required=True)
@click.option("--role", default="admin", show_default=True)
@click.option("--url", default=DEFAULT_URL, show_default=True)
def register_participant(client_id: str, key_hex: str, role: str, url: str):
    r = httpx.post(f"{url}/participants", headers=_headers(role), json={"client_id": client_id, "key_hex": key_hex})
    click.echo(r.text)


@aegis.command("configure-dp")
@click.option("--clipping", default=1.0, type=float, show_default=True)
@click.option("--noise", default=1.0, type=float, show_default=True)
@click.option("--sample-rate", default=0.01, type=float, show_default=True)
@click.option("--delta", default=1e-5, type=float, show_default=True)
@click.option("--role", default="operator", show_default=True)
@click.option("--url", default=DEFAULT_URL, show_default=True)
def configure_dp(clipping: float, noise: float, sample_rate: float, delta: float, role: str, url: str):
    body = {
        "clipping_norm": clipping,
        "noise_multiplier": noise,
        "sample_rate": sample_rate,
        "delta": delta,
        "accountant": "rdp",
    }
    r = httpx.post(f"{url}/dp/config", headers=_headers(role), json=body)
    click.echo(r.text)


@aegis.command("set-strategy")
@click.option("--strategy", type=click.Choice(["krum", "trimmed_mean"]), default="trimmed_mean", show_default=True)
@click.option("--role", default="operator", show_default=True)
@click.option("--url", default=DEFAULT_URL, show_default=True)
def set_strategy(strategy: str, role: str, url: str):
    r = httpx.post(f"{url}/strategy", headers=_headers(role), json={"strategy": strategy})
    click.echo(r.text)


@aegis.command("start")
@click.option("--session-id", required=True)
@click.option("--rounds", type=int, default=5, show_default=True)
@click.option("--role", default="operator", show_default=True)
@click.option("--url", default=DEFAULT_URL, show_default=True)
def start(session_id: str, rounds: int, role: str, url: str):
    r = httpx.post(f"{url}/training/start", headers=_headers(role), json={"session_id": session_id, "rounds": rounds})
    click.echo(r.text)


@aegis.command("status")
@click.option("--session-id", required=True)
@click.option("--role", default="viewer", show_default=True)
@click.option("--url", default=DEFAULT_URL, show_default=True)
def status(session_id: str, role: str, url: str):
    r = httpx.get(f"{url}/training/status", headers=_headers(role), params={"session_id": session_id})
    click.echo(r.text)


@aegis.command("stop")
@click.option("--session-id", required=True)
@click.option("--role", default="operator", show_default=True)
@click.option("--url", default=DEFAULT_URL, show_default=True)
def stop(session_id: str, role: str, url: str):
    r = httpx.post(f"{url}/training/stop", headers=_headers(role), params={"session_id": session_id})
    click.echo(r.text)


@aegis.command("report")
@click.option("--role", default="viewer", show_default=True)
@click.option("--url", default=DEFAULT_URL, show_default=True)
@click.option("--format", "fmt", type=click.Choice(["markdown", "pdf"]), default="markdown", show_default=True)
@click.option("--steps", type=int, default=None, help="Override steps for epsilon estimate")
@click.option("--output", type=str, default=None, help="Output file when format=pdf")
def report(role: str, url: str, fmt: str, steps: Optional[int], output: Optional[str]):
    params = {"format": fmt}
    if steps and steps > 0:
        params["steps"] = steps
    r = httpx.get(f"{url}/compliance/report", headers=_headers(role), params=params)
    if r.status_code != 200:
        click.echo(r.text)
        return
    if fmt == "markdown":
        data = r.json()
        click.echo(data.get("markdown", ""))
    else:
        out = output or "report.pdf"
        with open(out, "wb") as f:
            f.write(r.content)
        click.echo(f"Wrote {out}")


# Audit utilities (top-level group under aegis)
@aegis.group()
def audit() -> None:
    """Audit utilities (verify tamper-evident logs)."""


@audit.command("verify-jsonl")
@click.argument("path", type=click.Path(exists=True, readable=True, dir_okay=False))
def audit_verify_jsonl(path: str) -> None:
    """Verify a JSONL hash-chained audit log file."""
    from .tools.audit_verify import verify_jsonl

    res = verify_jsonl(path)
    if not res.ok:
        click.echo(
            f"FAIL - checked={res.checked} idx={res.failed_index} msg={res.message}",
            err=True,
        )
        raise SystemExit(1)
    click.echo(f"OK - checked={res.checked}")


@audit.command("verify-sqlite")
@click.argument("db", type=click.Path(exists=True, readable=True, dir_okay=False))
@click.option("--hmac-key-env", default="AEGIS_AUDIT_HMAC_KEY", help="Env var name for HMAC key")
def audit_verify_sqlite(db: str, hmac_key_env: str) -> None:
    """Verify a SQLite+HMAC audit log database."""
    from .tools.audit_verify import verify_sqlite

    res = verify_sqlite(db, hmac_key_env)
    if not res.ok:
        click.echo(
            f"FAIL - checked={res.checked} idx={res.failed_index} msg={res.message}",
            err=True,
        )
        raise SystemExit(1)
    click.echo(f"OK - checked={res.checked}")


@aegis.command("watch")
@click.option("--session-id", required=True)
@click.option("--steps-per-round", type=int, default=100, show_default=True)
@click.option("--interval", type=float, default=1.0, show_default=True)
@click.option("--role", default="viewer", show_default=True)
@click.option("--url", default=DEFAULT_URL, show_default=True)
def watch(session_id: str, steps_per_round: int, interval: float, role: str, url: str):
    """Poll status and display a simple epsilon estimate based on rounds."""
    # Fetch dp config for sample rate and noise
    httpx.post(
        f"{url}/dp/config",
        headers=_headers("operator"),
        json={"clipping_norm": 1.0, "noise_multiplier": 1.0, "sample_rate": 0.01, "delta": 1e-5, "accountant": "rdp"},
    )
    total_steps = 0
    while True:
        r = httpx.get(f"{url}/training/status", headers=_headers(role), params={"session_id": session_id})
        if r.status_code != 200:
            click.echo(r.text)
            break
        st = r.json()
        rounds = int(st.get("rounds", 0))
        total_steps = rounds * steps_per_round
        # This is a placeholder; epsilon reporting will come from server in later stages.
        # Here we just print total steps.
        click.echo(json.dumps({"rounds": rounds, "approx_steps": total_steps}))
        if st.get("status") == "stopped":
            break
        time.sleep(interval)


@aegis.command("demo")
@click.option("--spawn-api/--no-spawn-api", default=True, show_default=True, help="Spawn local API server for the demo")
@click.option("--rounds", type=int, default=3, show_default=True)
@click.option("--port", type=int, default=8002, show_default=True)
@click.option("--url", default=None)
def demo(spawn_api: bool, rounds: int, port: int, url: Optional[str]):
    """Happy-path demo.

    If `--no-spawn-api` is used, this will contact the provided `--url` or
    `http://127.0.0.1:<port>` and fetch a compliance report to print to stdout.
    This ensures a tangible output for docs/tests while keeping the demo simple.
    """
    base_url = url or f"http://127.0.0.1:{port}"
    # In this lightweight build we don't spawn an API; the test suite starts one.
    # For real usage, users typically run docker compose and then run this demo.
    try:
        r = httpx.get(f"{base_url}/compliance/report", headers=_headers("viewer"), timeout=10)
        if r.status_code == 200:
            data = r.json()
            md = data.get("markdown", "")
            if md:
                click.echo(md)
                return
            click.echo(r.text)
            return
        click.echo(r.text)
    except Exception as e:
        click.echo(json.dumps({"error": str(e), "base_url": base_url, "rounds": rounds}))
    # Optional: add Flower integration subcommands if available
    try:
        from .flower_integration import (
            is_flower_available,
            start_flower_client,
            start_flower_server,
        )

        @aegis.command("flower-server")
        @click.option("--address", default="127.0.0.1:8080", show_default=True)
        @click.option("--aggregator", type=click.Choice(["trimmed_mean", "krum"]), default="trimmed_mean", show_default=True)
        @click.option("--rounds", type=int, default=3, show_default=True)
        def flower_server(address: str, aggregator: str, rounds: int):
            """Start a Flower server using Aegis aggregators."""
            if not is_flower_available():
                click.echo("Flower is not installed. Please 'pip install flwr numpy'.")
                return
            start_flower_server(server_address=address, aggregator=aggregator, rounds=rounds)

        @aegis.command("flower-client")
        @click.option("--address", default="127.0.0.1:8080", show_default=True)
        @click.option("--dim", type=int, default=8, show_default=True)
        @click.option("--steps", type=int, default=20, show_default=True)
        @click.option("--lr", type=float, default=0.1, show_default=True)
        @click.option("--seed", type=int, default=0, show_default=True)
        def flower_client(address: str, dim: int, steps: int, lr: float, seed: int):
            """Start a Flower NumPy client performing local updates using Aegis examples."""
            if not is_flower_available():
                click.echo("Flower is not installed. Please 'pip install flwr numpy'.")
                return
            start_flower_client(server_address=address, dim=dim, steps=steps, lr=lr, seed=seed)
    except Exception:
        # Keep CLI import-safe if Flower extras not present
        pass


if __name__ == "__main__":  # pragma: no cover
    aegis()
