import streamlit as st
import requests
import time
import pandas as pd

# -------------------------------------------------------------
# 1. UI/UX Psychology & Gulf Bank CSS Injection
# -------------------------------------------------------------
st.set_page_config(page_title="Sococo | PLIE Showcase", layout="wide")

st.markdown("""
    <style>
        /* Base Architecture: Stark White & Deep Charcoal */
        .stApp {
            background-color: #FAFAFA;
            color: #121212;
            font-family: 'Inter', sans-serif;
        }
        
        /* Typography constraints */
        h1, h2, h3 {
            color: #121212 !important;
            font-weight: 700 !important;
            letter-spacing: -0.5px;
        }

        /* Primary Action Buttons (Gulf Bank Crimson) */
        .stButton>button {
            background-color: #A30000 !important;
            color: #FFFFFF !important;
            border: 1px solid #A30000 !important;
            border-radius: 4px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease;
            width: 100%;
        }
        
        /* Secondary hover state (Champagne Gold) */
        .stButton>button:hover {
            background-color: #121212 !important;
            border: 1px solid #C5A059 !important;
            color: #C5A059 !important;
        }

        /* Clean up the file uploader */
        .stFileUploader {
            border: 1px dashed #C5A059;
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 4px;
        }
        
        /* Dataframes / Tables */
        .stDataFrame {
            border: 1px solid #E0E0E0;
            border-radius: 4px;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 2. Application Logic & Configuration
# -------------------------------------------------------------
API_BASE_URL = "http://127.0.0.1:8000/api"
TENANT_ID = 1

# --- Replace the old st.title and st.markdown with this centered HTML ---
st.markdown("<h1 style='text-align: center; color: #121212;'>Enterprise Activation Engine</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555555; margin-bottom: 40px;'>Upload raw domain targets. The engine will autonomously enrich, score, and draft tailored copy.</p>", unsafe_allow_html=True)

# Split the layout to draw focus
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # --- PHASE 1: INGESTION ---
    uploaded_file = st.file_uploader("Upload CSV List", type=["csv"])
    
    if uploaded_file is not None:
        if st.button("Initialize Pipeline"):
            with st.spinner("Ingesting targets..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                res = requests.post(f"{API_BASE_URL}/upload-csv/{TENANT_ID}", files=files)
                
                if res.status_code == 200:
                    st.success("Ingestion successful. Ready for enrichment.")
                    st.session_state['ready_to_process'] = True
                else:
                    st.error(f"Ingestion failed: {res.text}")

    # --- PHASE 2: ORCHESTRATION & QUEUE POLLING ---
    if st.session_state.get('ready_to_process', False):
        if st.button("Execute Enrichment & AI Synthesis"):
            trigger_res = requests.post(f"{API_BASE_URL}/generate-batch/{TENANT_ID}?batch_size=10")
            
            if trigger_res.status_code == 200:
                job_id = trigger_res.json()["job_id"]
                my_bar = st.progress(0, text="Establishing connections to data providers...")
                
                is_complete = False
                while not is_complete:
                    time.sleep(0.5)
                    status_res = requests.get(f"{API_BASE_URL}/job-status/{job_id}").json()
                    status = status_res['status']
                    total = status_res['total']
                    completed = status_res['completed']
                    
                    if total > 0:
                        progress_pct = int((completed / total) * 100)
                        my_bar.progress(progress_pct, text=f"Enriching targets... {completed}/{total} completed")
                    
                    if status == "complete":
                        is_complete = True
                        my_bar.progress(100, text="Synthesis Complete.")
                        st.session_state['job_complete'] = True
            else:
                st.error("Failed to trigger processing.")

# --- PHASE 3: PRESENTATION (Progressive Disclosure with Tabs) ---
if st.session_state.get('job_complete', False):
    st.markdown("---")
    st.subheader("Enriched Leads & Drafts")
    
    results_res = requests.get(f"{API_BASE_URL}/results/{TENANT_ID}")
    
    if results_res.status_code == 200:
        leads = results_res.json()
        
        for lead in leads:
            with st.expander(f"⭐ Score: {lead['plie_score']} | {lead['company_name']} ({lead['domain']})"):
                st.markdown(f"**Firmographics:** {lead['headcount_current']} Employees | {lead['funding_stage']} Funding")
                st.markdown(f"**Intent Signal:** {lead['intent_score']}/100")
                st.markdown("---")
                
                # Create 3 sleek tabs for the drafts
                tab1, tab2, tab3 = st.tabs(["Variant A: The 'Why Now'", "Variant B: Pattern Interrupt", "Variant C: Blunt Force"])
                
                with tab1:
                    st.info(lead.get('message_draft_a', 'Draft pending...'))
                with tab2:
                    st.info(lead.get('message_draft_b', 'Draft pending...'))
                with tab3:
                    st.info(lead.get('message_draft_c', 'Draft pending...'))