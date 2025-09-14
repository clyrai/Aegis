from __future__ import annotations

import os
import ssl
from typing import Optional

import uvicorn

from aegis.api import app


def build_ssl_context(
    certfile: Optional[str] = None,
    keyfile: Optional[str] = None,
    cafile: Optional[str] = None,
    require_client_cert: bool = False,
) -> Optional[ssl.SSLContext]:
    if not certfile or not keyfile:
        return None
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
    if cafile:
        ctx.load_verify_locations(cafile=cafile)
        ctx.verify_mode = ssl.CERT_REQUIRED if require_client_cert else ssl.CERT_OPTIONAL
    else:
        ctx.verify_mode = ssl.CERT_NONE
    # Stronger defaults
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def main():
    host = os.environ.get("AEGIS_HOST", "0.0.0.0")
    port = int(os.environ.get("AEGIS_PORT", "8000"))
    cert = os.environ.get("AEGIS_TLS_CERT")
    key = os.environ.get("AEGIS_TLS_KEY")
    ca = os.environ.get("AEGIS_TLS_CLIENT_CA")
    require_client = os.environ.get("AEGIS_MTLS_REQUIRE", "0") == "1"
    log_level = os.environ.get("AEGIS_LOG_LEVEL", "info")

    ctx = None
    if cert and key:
        try:
            ctx = build_ssl_context(certfile=cert, keyfile=key, cafile=ca, require_client_cert=require_client)
        except Exception:
            ctx = None

    if ctx is not None:
        try:
            uvicorn.run(app, host=host, port=port, log_level=log_level, ssl=ctx)
            return
        except TypeError:
            # Older uvicorn versions may not support the 'ssl' kwarg
            pass

    # Fallback to file-based parameters
    ssl_params = {}
    if cert and key:
        ssl_params.update({
            "ssl_certfile": cert,
            "ssl_keyfile": key,
        })
    if ca:
        ssl_params.update({
            "ssl_ca_certs": ca,
            "ssl_cert_reqs": ssl.CERT_REQUIRED if require_client else ssl.CERT_OPTIONAL,
        })
    uvicorn.run(app, host=host, port=port, log_level=log_level, **ssl_params)


if __name__ == "__main__":
    main()
