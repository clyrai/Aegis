# Aegis in 5 minutes (Quick tour)

What you’ll see
- A running privacy-preserving ML stack
- One federated training run
- Live dashboards and a compliance report

1) Start Aegis
- Make sure Docker is running
- Start services: `docker compose -f deploy/docker-compose.yml up -d`
- Open API docs: http://localhost:8000/docs

2) Register two participants
- `http POST :8000/participants X-Role:admin client_id=c1 key_hex=aa`
- `http POST :8000/participants X-Role:admin client_id=c2 key_hex=bb`

3) Set a balanced privacy level
- `http POST :8000/dp/config X-Role:operator clipping_norm:=1.0 noise_multiplier:=1.0 sample_rate:=0.01 delta:=1e-5 accountant=rdp`

4) Choose a federated strategy
- `http POST :8000/strategy X-Role:operator strategy=trimmed_mean`

5) Start training (3 rounds)
- `http POST :8000/training/start X-Role:operator session_id=tour rounds:=3`

6) See it live
- Grafana: http://localhost:3000 (default dashboard is provisioned)

7) Create a report
- `http GET :8000/compliance/report X-Role:viewer > tour_report.md`

Next: basics/privacy_explainer.md for an approachable overview of DP and FL.
