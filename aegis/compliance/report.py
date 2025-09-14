from __future__ import annotations

from dataclasses import asdict
from typing import Dict
from typing import Optional

from aegis.privacy_engine import DPConfig
try:  # optional PDF dependency
    from fpdf import FPDF
except Exception:  # pragma: no cover - optional
    FPDF = None


def generate_markdown(
    *,
    dp_config: DPConfig,
    participants: Dict[str, bytes],
    sessions: Dict[str, Dict[str, str]],
    strategy: str,
    epsilon: Optional[float] = None,
    epsilon_steps: Optional[int] = None,
    notes: Optional[str] = None,
    versions: Optional[Dict[str, str]] = None,
) -> str:
    cfg = asdict(dp_config)
    parts = [
        "# Aegis Compliance Report\n",
        "## Differential Privacy Configuration\n",
        f"- Accountant: {cfg['accountant']}\n",
        f"- Clipping Norm: {cfg['clipping_norm']}\n",
        f"- Noise Multiplier (sigma): {cfg['noise_multiplier']}\n",
        f"- Sample Rate: {cfg['sample_rate']}\n",
        f"- Delta: {cfg['delta']}\n",
        "\n## Training Audit Summary\n",
        f"- Participants registered: {len(participants)}\n",
        f"- Strategy: {strategy}\n",
        "- Sessions:\n",
    ]
    for sid, meta in sessions.items():
        parts.append(f"  - {sid}: status={meta.get('status','unknown')}, rounds={meta.get('rounds','?')}\n")

    if epsilon is not None:
        if epsilon_steps is not None:
            parts.append(f"- Epsilon (approx., {epsilon_steps} steps): {epsilon:.4f}\n")
        else:
            parts.append(f"- Epsilon (approx.): {epsilon:.4f}\n")
    if notes:
        parts.append(f"- Notes: {notes}\n")
    parts.extend(
        [
            "\n## Regulatory Mapping\n",
            "### GDPR\n",
            "- Data minimization: No raw data leaves client; only model updates are shared in federated rounds.\n",
            "- Privacy by design: DP-SGD adds calibrated noise and clipping to bound individual impact.\n",
            "- Data subject rights: Export/delete workflows are available via compliance endpoints.\n",
            "### HIPAA\n",
            "- PHI handled at source; DP reduces re-identification risk in model updates.\n",
            "- Transport security: mTLS (or TLS) recommended for all inter-site communications.\n",
            "### EU AI Act\n",
            "- Risk management: DP and robust aggregation (e.g., Trimmed Mean, Krum) reduce attack surface.\n",
            "\n## DPIA-style Risk Notes\n",
            "- Utility vs privacy: Lower epsilon provides stronger privacy but may reduce model accuracy.\n",
            "- Data representativeness: Imbalanced or tiny datasets can reduce utility with DP; consider mitigation.\n",
            "- Adversarial resilience: Robust aggregation mitigates some Byzantine behaviors but is not a panacea.\n",
            "\n## Notes\n",
            "- This report is designed for non-technical stakeholders; see API docs for full configuration details.\n",
        ]
    )
    if versions:
        parts.append("\n## Versions\n")
        for k, v in versions.items():
            parts.append(f"- {k}: {v}\n")
        parts.append("\n")
    return "".join(parts)


def generate_pdf(markdown: str) -> bytes:
    """Generate a simple PDF from Markdown text (headings treated as bold).

    Uses fpdf2 if available; otherwise raises RuntimeError.
    """
    if FPDF is None:  # pragma: no cover - optional dep
        raise RuntimeError("PDF generation requires 'fpdf2'. Install via: pip install fpdf2")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    page_width = pdf.w - 2 * pdf.l_margin
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("### "):
            pdf.set_font("Helvetica", style="B", size=12)
            pdf.multi_cell(page_width, 8, text=line[4:])
            pdf.set_font("Helvetica", size=12)
        elif line.startswith("## "):
            pdf.set_font("Helvetica", style="B", size=14)
            pdf.multi_cell(page_width, 8, text=line[3:])
            pdf.set_font("Helvetica", size=12)
        elif line.startswith("# "):
            pdf.set_font("Helvetica", style="B", size=16)
            pdf.multi_cell(page_width, 8, text=line[2:])
            pdf.set_font("Helvetica", size=12)
        else:
            pdf.multi_cell(page_width, 6, text=line)
    # Output as bytes (fpdf2 >= 2.5 returns bytes or bytearray)
    out = pdf.output()
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    # Fallback for older versions returning str
    assert isinstance(out, str)
    return out.encode("latin1")


__all__ = ["generate_markdown", "generate_pdf"]


if __name__ == "__main__":  # lightweight CLI for report generation
    import argparse
    from aegis.privacy_engine import DPConfig

    ap = argparse.ArgumentParser()
    ap.add_argument("--format", choices=["markdown", "pdf"], default="markdown")
    ap.add_argument("--output", type=str, default="compliance_report.md")
    args = ap.parse_args()

    cfg = DPConfig()
    participants = {"demo": b"k"}
    sessions = {"demo": {"status": "stopped", "rounds": "3"}}
    md = generate_markdown(dp_config=cfg, participants=participants, sessions=sessions, strategy="trimmed_mean")
    if args.format == "markdown":
        with open(args.output, "w", encoding="utf-8") as f_text:
            f_text.write(md)
        print(f"Wrote {args.output}")
    else:
        data = generate_pdf(md)
        out = args.output if args.output.lower().endswith(".pdf") else args.output + ".pdf"
        with open(out, "wb") as f_bin:
            f_bin.write(data)
        print(f"Wrote {out}")
