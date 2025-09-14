# Aegis Compliance Report
## Differential Privacy Configuration
- Accountant: rdp
- Clipping Norm: 1.0
- Noise Multiplier (sigma): 1.0
- Sample Rate: 0.01
- Delta: 1e-05

## Training Audit Summary
- Participants registered: 2
- Strategy: trimmed_mean
- Sessions:
  - rich3: status=running, rounds=?
  - run1: status=completed, rounds=?
- Epsilon (approx., 5 steps): 0.0003
- Notes: ultra-low-epsilon: severe utility loss likely; consider fewer steps or lower noise.

## Regulatory Mapping
### GDPR
- Data minimization: No raw data leaves client; only model updates are shared in federated rounds.
- Privacy by design: DP-SGD adds calibrated noise and clipping to bound individual impact.
- Data subject rights: Export/delete workflows are available via compliance endpoints.
### HIPAA
- PHI handled at source; DP reduces re-identification risk in model updates.
- Transport security: mTLS (or TLS) recommended for all inter-site communications.
### EU AI Act
- Risk management: DP and robust aggregation (e.g., Trimmed Mean, Krum) reduce attack surface.

## DPIA-style Risk Notes
- Utility vs privacy: Lower epsilon provides stronger privacy but may reduce model accuracy.
- Data representativeness: Imbalanced or tiny datasets can reduce utility with DP; consider mitigation.
- Adversarial resilience: Robust aggregation mitigates some Byzantine behaviors but is not a panacea.

## Notes
- This report is designed for non-technical stakeholders; see API docs for full configuration details.

## Versions
- aegis_api: 0.1.0
- fastapi: 0.116.1
- pydantic: 2.11.7


