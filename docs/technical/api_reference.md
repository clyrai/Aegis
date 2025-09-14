# Aegis API reference (overview)

Base URL
- Default local: `http://localhost:8000`
- Production: behind TLS and mTLS as configured
- Roles: `admin`, `operator`, `viewer` (use header `X-Role` in examples)

Participants
- Register: `POST /participants`
	```bash
	http POST :8000/participants X-Role:admin client_id=c1 key_hex=aa
	```

Datasets
- Register: `POST /datasets`
	```bash
	http POST :8000/datasets X-Role:admin name=demo format=csv
	```

Privacy configuration
- Set DP config: `POST /dp/config`
	```bash
	http POST :8000/dp/config X-Role:operator clipping_norm:=1.0 noise_multiplier:=1.0 sample_rate:=0.01 delta:=1e-5 accountant=rdp
	```

Federated strategy
- Select aggregator: `POST /strategy`
	```bash
	http POST :8000/strategy X-Role:operator strategy=trimmed_mean
	```

Training sessions
- Start: `POST /training/start`
	```bash
	http POST :8000/training/start X-Role:operator session_id=run1 rounds:=5
	```
- Status: `GET /training/status?session_id=run1`
	```bash
	http GET :8000/training/status X-Role:viewer session_id==run1
	```
- Stop: `POST /training/stop`
	```bash
	http POST :8000/training/stop X-Role:operator session_id=run1
	```

Compliance report
- Generate: `GET /compliance/report`
	```bash
	http GET :8000/compliance/report X-Role:viewer > report.md
	```

See OpenAPI at `/docs` or `/openapi.json` for full schemas and error responses.
