# FAQ (for non‑experts)

What problem does Aegis solve?
- It lets you train useful models without exposing raw data, even across organizations.

Is this only for large enterprises?
- No. A single team can start on one machine, then scale to multiple sites when needed.

What if I don’t know DP/FL?
- You don’t need to. Aegis has sensible defaults and guardrails. You can tune later.

Will my models be worse with DP?
- With strong privacy (low epsilon), some accuracy drops are expected. Aegis helps you find a good balance.

Can I bring my own models?
- Yes. Use our examples for PyTorch, TensorFlow, and scikit‑learn as a starting point.

How do I see progress?
- Grafana dashboards show training metrics and privacy budget consumption.

Is my data safe in transit?
- Yes, we support mTLS between services and participants.
