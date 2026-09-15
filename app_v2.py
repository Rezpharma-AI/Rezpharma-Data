import os
import streamlit as st
import requests

# --- Configuration ---
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="RezpharmaCDSS | Clinical Dashboard",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- UI Header ---
st.title("RezpharmaCDSS Clinical Dashboard")
st.markdown("**Statistically Sound Polypharmacy Decision Support** | *Fusing 2.85M DDIs, Kinetic GFR, and Bayesian PK/PD*")
st.caption(f"Connected to Backend: `{API_URL}`")

# --- Sidebar Inputs ---
st.sidebar.header("1. Patient Regimen")
drug_input = st.sidebar.text_area(
    "Current Medications (comma-separated):",
    value="Warfarin, Aspirin, Amiodarone, Simvastatin, Clarithromycin",
    height=100
)

st.sidebar.header("2. Live Lab Covariate (M3)")
potassium = st.sidebar.select_slider(
    "Serum Potassium (K⁺) mEq/L:",
    options=[3.0, 3.3, 3.5, 4.0, 4.2, 4.5, 5.0],
    value=3.3,
    help="Hypokalemia potentiates QT-prolongation risk (M1 conditional reasoning)."
)

run_btn = st.sidebar.button("Run Decision Support", type="primary", use_container_width=True)

# --- Main Execution ---
if run_btn:
    drugs = [d.strip().title() for d in drug_input.split(',') if d.strip()]
    
    if not drugs:
        st.warning("Please enter at least one medication.")
        st.stop()

    st.markdown("---")
    
    # Step 1: Call M1/DDI Backend
    with st.spinner("Screening against 2,855,310 interactions..."):
        try:
            payload = {"patient_id": "DEMO_PT_001", "drugs": drugs}
            r1 = requests.post(f"{API_URL}/api/v1/m1/analyze", json=payload, timeout=15)
            r1.raise_for_status()
            m1_data = r1.json()
        except requests.exceptions.ConnectionError:
            st.error(f"❌ Cannot connect to API at `{API_URL}`. Is the FastAPI backend running?")
            st.stop()
        except Exception as e:
            st.error(f"API Error: {e}")
            st.stop()

    st.success(f"✅ Screened {len(drugs)} drugs. Found **{m1_data.get('interactions_found', 0)}** raw interactions.")

    # Step 2: Call Advisor Backend
    with st.spinner("Running Expected Utility & Knapsack Alert Budget..."):
        try:
            r2 = requests.get(f"{API_URL}/api/v1/advisor/recommendations", timeout=15)
            r2.raise_for_status()
            adv_data = r2.json()
        except Exception as e:
            st.error(f"Advisor API Error: {e}")
            st.stop()

    # Step 3: Display Results
    st.markdown("---")
    st.subheader("🚨 Prioritized Alerts (Knapsack Budget ≤ 3)")
    
    alerts = adv_data.get('alerts_selected', [])
    suppressed = adv_data.get('alerts_suppressed', [])

    if not alerts:
        st.info("No actionable alerts. Regimen is safe based on current physiology.")
    else:
        cols = st.columns(len(alerts))
        for i, alert in enumerate(alerts):
            with cols[i]:
                harm = alert.get('harm', 'Unknown').replace('_', ' ').title()
                action = alert.get('action', 'Monitor').replace('_', ' ').title()
                p_harm = alert.get('p_harm', 0)
                
                st.error(f"**{harm}**")
                st.metric("P(Harm)", f"{p_harm:.1%}")
                st.markdown(f"**Action:** {action}")

    if suppressed:
        with st.expander(f"🔇 {len(suppressed)} Alerts Suppressed (Alert Fatigue Control)"):
            for alert in suppressed:
                harm = alert.get('harm', 'Unknown').replace('_', ' ').title()
                p_harm = alert.get('p_harm', 0)
                st.caption(f"• {harm} (P={p_harm:.1%}) - Suppressed to protect cognitive load.")

    # Step 4: Show Raw Interactions (Optional)
    with st.expander("🔍 View Raw M1 Interaction Data"):
        interactions = m1_data.get('interactions', [])
        if interactions:
            for hit in interactions[:10]:
                sev = hit.get('severity', 'unknown').upper()
                perp = hit.get('perpetrator', '?')
                vict = hit.get('victim', '?')
                mech = hit.get('mechanism', 'No mechanism provided')
                st.markdown(f"- **[{sev}]** {perp} + {vict}: *{mech[:100]}...*")