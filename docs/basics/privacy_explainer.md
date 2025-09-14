# Privacy, simply explained

Differential Privacy (DP)
- Think of adding a drop of water to a lake: you can’t tell if any one drop was added. DP adds tiny, carefully chosen noise during training so an attacker can’t say whether a specific person’s data was used.
- Privacy budget (epsilon): a dial that controls how much noise is added. Lower epsilon = stronger privacy.

Federated Learning (FL)
- Instead of moving raw data to a central server, each site trains locally and only shares model updates (not records).
- This reduces data movement and keeps sensitive data where it belongs.

Why both matter
- DP protects individuals even if models are shared.
- FL limits exposure by design, ideal for collaborations (hospitals, banks, agencies).

How Aegis helps
- Friendly controls to set epsilon and track privacy usage.
- Federation that handles slow/unreliable sites so training keeps going.
- Reports you can hand to risk and legal teams.
