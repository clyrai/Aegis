from __future__ import annotations

import os
import time
import httpx
import streamlit as st


BASE_URL = os.environ.get("AEGIS_API_URL", "http://127.0.0.1:8000")


def headers(role: str):
    return {"X-Role": role}


st.set_page_config(page_title="Aegis Dashboard", layout="wide")
st.title("Aegis — Privacy-Preserving ML Orchestration")

with st.sidebar:
    st.header("Connection")
    base_url = st.text_input("API URL", value=BASE_URL)
    role = st.selectbox("Role", options=["viewer", "operator", "admin"], index=1)
    st.divider()
    st.header("DP Config")
    clip = st.number_input("Clipping norm", min_value=0.0, value=1.0)
    noise = st.number_input("Noise multiplier", min_value=0.0, value=1.0)
    sample = st.number_input("Sample rate", min_value=0.0001, max_value=1.0, value=0.01)
    delta = st.number_input("Delta", min_value=1e-9, max_value=1e-3, value=1e-5, format="%.9f")
    if st.button("Apply DP Config"):
        r = httpx.post(f"{base_url}/dp/config", headers=headers("operator"), json={
            "clipping_norm": clip,
            "noise_multiplier": noise,
            "sample_rate": sample,
            "delta": delta,
            "accountant": "rdp",
        })
        st.toast(f"DP config: {r.status_code}")
    st.divider()
    st.header("Strategy")
    strat = st.selectbox("Aggregator", ["trimmed_mean", "krum"])
    if st.button("Set Strategy"):
        r = httpx.post(f"{base_url}/strategy", headers=headers("operator"), json={"strategy": strat})
        st.toast(f"Strategy: {r.status_code}")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Run Controls")
    session_id = st.text_input("Session ID", value="demo")
    rounds = st.number_input("Rounds", min_value=1, value=3)
    if st.button("Start Training"):
        httpx.post(f"{base_url}/training/start", headers=headers("operator"), json={"session_id": session_id, "rounds": int(rounds)})
    if st.button("Stop Training"):
        httpx.post(f"{base_url}/training/stop", headers=headers("operator"), params={"session_id": session_id})

with col2:
    st.subheader("Metrics")
    placeholder = st.empty()
    chart_data = []
    for _ in range(10):
        try:
            r = httpx.get(f"{base_url}/training/status", headers=headers("viewer"), params={"session_id": session_id}, timeout=2)
            status = r.json().get("status", "?") if r.status_code == 200 else "error"
            chart_data.append({"t": time.time(), "status": 1.0 if status == "running" else 0.0})
            placeholder.line_chart(chart_data, x="t", y="status")
            time.sleep(1)
        except Exception:
            time.sleep(1)

st.divider()
if st.button("Generate Compliance Report (PDF)"):
    r = httpx.get(f"{base_url}/compliance/report", headers=headers("viewer"), params={"format": "pdf"})
    st.write(f"Status: {r.status_code}, size: {len(r.content) if r.status_code==200 else 0} bytes")
