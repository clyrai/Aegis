from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional


class Role(str, Enum):
    admin = "admin"
    operator = "operator"
    viewer = "viewer"


# Simple in-memory RBAC map for Stage 4
ROLE_PERMS: Dict[Role, List[str]] = {
    Role.admin: [
        "participant:register",
    "dataset:register",
        "training:start",
        "training:stop",
        "training:status",
        "dp:configure",
    "dp:assess",
    "dp:budget",
        "strategy:select",
        "report:generate",
    "compliance:gdpr",
    "compliance:hipaa",
    "audit:read",
    ],
    Role.operator: [
        "participant:register",
    "dataset:register",
        "training:start",
        "training:stop",
        "training:status",
        "dp:configure",
    "dp:assess",
        "strategy:select",
    "compliance:gdpr",
    "compliance:hipaa",
    ],
    Role.viewer: [
        "training:status",
        "report:generate",
    "audit:read",
    ],
}


def allow(role: Role, permission: str) -> bool:
    return permission in ROLE_PERMS.get(role, [])


def parse_role(header_value: Optional[str]) -> Role:
    # Expect header like: X-Role: admin|operator|viewer
    if header_value in {r.value for r in Role} and header_value is not None:
        return Role(header_value)
    return Role.viewer
