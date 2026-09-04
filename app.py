import streamlit as st
import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.title("Rezpharma CDSS — Frontend")
st.write("Backend URL:", BACKEND_URL)

st.markdown("This frontend reads the BACKEND_URL environment variable. For local testing, set BACKEND_URL to http://127.0.0.1:8000 or run the backend locally with uvicorn.")

if st.button("Check backend /health"):
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
        resp.raise_for_status()
        st.success(f"OK: {resp.status_code} — {resp.text}")
    except Exception as e:
        st.error(f"Failed to reach backend: {e}")

st.write("Use the Streamlit UI to interact with your API. In production, set BACKEND_URL in Railway to your API service domain.")
