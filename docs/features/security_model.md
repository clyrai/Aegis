# Security model

Trust boundaries
- Participants authenticate to the coordinator
- All traffic is protected with mTLS (client and server certs)
- RBAC limits who can change configs or start runs

Auditability
- Every sensitive action is recorded with timestamps and actor identity
- Logs are tamper-evident via hashing/signing

Input validation
- All incoming requests are validated and out-of-range values are rejected

Operational hygiene
- Secrets stored as files/Secrets, rotated regularly
- Minimal privileges for services and users
