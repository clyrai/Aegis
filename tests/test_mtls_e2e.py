from __future__ import annotations

import os
import tempfile
import threading
import time
import subprocess

import httpx


def _run(cmd: list[str], cwd: str):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


def test_mtls_end_to_end():
    # Skip if openssl not present
    try:
        subprocess.run(["openssl", "version"], check=True, capture_output=True)
    except Exception:
        return

    from aegis.server import main as server_main
    from aegis.api import app  # noqa: F401 used via import side-effects

    with tempfile.TemporaryDirectory() as tmp:
        # Generate CA
        ca_conf = os.path.join(tmp, "ca.conf")
        with open(ca_conf, "w") as f:
            f.write(
                """
[req]
distinguished_name = req
[req_distinguished_name]
[v3_ca]
basicConstraints=critical,CA:true
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always,issuer
"""
            )
        _run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-subj", "/CN=TestCA", "-keyout", "ca.key", "-out", "ca.crt",
            "-days", "1", "-config", "ca.conf", "-extensions", "v3_ca",
        ], tmp)

        # Server cert
        _run(["openssl", "req", "-newkey", "rsa:2048", "-nodes", "-subj", "/CN=localhost", "-keyout", "server.key", "-out", "server.csr"], tmp)
        server_ext = os.path.join(tmp, "server.ext")
        with open(server_ext, "w") as f:
            f.write(
                """
[v3_ext]
basicConstraints=CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:localhost,IP:127.0.0.1
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
"""
            )
        _run([
            "openssl", "x509", "-req", "-in", "server.csr", "-CA", "ca.crt",
            "-CAkey", "ca.key", "-CAcreateserial", "-out", "server.crt",
            "-days", "1", "-extfile", "server.ext", "-extensions", "v3_ext",
        ], tmp)

        # Client cert
        _run(["openssl", "req", "-newkey", "rsa:2048", "-nodes", "-subj", "/CN=client", "-keyout", "client.key", "-out", "client.csr"], tmp)
        client_ext = os.path.join(tmp, "client.ext")
        with open(client_ext, "w") as f:
            f.write(
                """
[v3_ext]
basicConstraints=CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=clientAuth
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
"""
            )
        _run([
            "openssl", "x509", "-req", "-in", "client.csr", "-CA", "ca.crt",
            "-CAkey", "ca.key", "-CAcreateserial", "-out", "client.crt", "-days", "1",
            "-extfile", "client.ext", "-extensions", "v3_ext",
        ], tmp)

        # Start server with mTLS required
        os.environ.update({
            "AEGIS_TLS_CERT": os.path.join(tmp, "server.crt"),
            "AEGIS_TLS_KEY": os.path.join(tmp, "server.key"),
            "AEGIS_TLS_CLIENT_CA": os.path.join(tmp, "ca.crt"),
            "AEGIS_MTLS_REQUIRE": "1",
            "AEGIS_HOST": "127.0.0.1",
            "AEGIS_PORT": "8443",
        })

        class Srv(threading.Thread):
            def run(self) -> None:
                server_main()

        t = Srv(daemon=True)
        t.start()
        time.sleep(1.5)

        # Without client cert: should fail TLS handshake
        import ssl as _ssl
        ca_path = os.path.join(tmp, "ca.crt")
        verify_ctx = _ssl.create_default_context(cafile=ca_path)
        with httpx.Client(verify=verify_ctx) as client:
            failed = False
            try:
                client.get("https://127.0.0.1:8443/healthz", timeout=3)
            except Exception:
                failed = True
            assert failed

        # With client cert: should succeed
        client_ctx = _ssl.create_default_context(cafile=ca_path)
        client_ctx.load_cert_chain(
            certfile=os.path.join(tmp, "client.crt"), keyfile=os.path.join(tmp, "client.key")
        )
        with httpx.Client(verify=client_ctx) as client:
            r = client.get("https://127.0.0.1:8443/healthz", timeout=5)
            assert r.status_code == 200
