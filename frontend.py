import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Use Case Discovery Agent",
    layout="wide",
    page_icon="🔍",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .hero-title {
        font-size: 2.6rem; font-weight: 700;
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .hero-sub {
        font-size: 1.05rem; color: #94a3b8; margin-bottom: 2rem;
    }
    .use-case-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 24px rgba(99,102,241,0.08);
        transition: box-shadow 0.2s;
    }
    .use-case-card:hover { box-shadow: 0 8px 32px rgba(139,92,246,0.18); }
    .card-id {
        display: inline-block;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white; font-weight: 700; font-size: 0.9rem;
        padding: 0.2rem 0.75rem; border-radius: 999px; margin-bottom: 0.6rem;
    }
    .card-title { font-size: 1.3rem; font-weight: 700; color: #e2e8f0; margin-bottom: 0.4rem; }
    .card-desc { color: #94a3b8; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem; }
    .tag-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.8rem; }
    .tag {
        background: #1e293b; border: 1px solid #475569;
        color: #a5b4fc; font-size: 0.78rem; padding: 0.2rem 0.6rem; border-radius: 6px;
    }
    .section-label {
        color: #6366f1; font-size: 0.78rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.3rem;
    }
    .data-flow-box {
        background: #0f172a; border: 1px solid #1e293b;
        border-radius: 8px; padding: 0.7rem 1rem;
        color: #a5b4fc; font-family: monospace; font-size: 0.85rem;
        white-space: pre-wrap; line-height: 1.7;
    }
    .process-step {
        display: flex; align-items: flex-start; gap: 0.6rem;
        color: #cbd5e1; font-size: 0.9rem; margin-bottom: 0.3rem;
    }
    .step-num {
        background: #6366f1; color: white; font-size: 0.72rem; font-weight: 700;
        min-width: 1.4rem; height: 1.4rem; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; margin-top: 0.1rem;
    }
    .finalize-card {
        background: linear-gradient(135deg, #0f172a, #1e1b4b);
        border: 2px solid #6366f1; border-radius: 16px;
        padding: 2rem; margin-top: 1.5rem;
    }
    .kpi-item {
        background: #1e293b; border-left: 3px solid #6366f1;
        padding: 0.5rem 0.9rem; border-radius: 4px;
        color: #e2e8f0; font-size: 0.92rem; margin-bottom: 0.5rem;
    }
    .action-step {
        background: #0f172a; border: 1px solid #334155;
        padding: 0.6rem 1rem; border-radius: 8px;
        color: #cbd5e1; font-size: 0.92rem; margin-bottom: 0.5rem;
    }
    .confirm-banner {
        background: linear-gradient(90deg, #059669, #10b981);
        color: white; font-weight: 600; font-size: 1rem;
        padding: 0.9rem 1.4rem; border-radius: 10px; margin-bottom: 1.5rem;
        text-align: center;
    }
    .domain-chip {
        display: inline-block;
        background: #1e293b; border: 1px solid #6366f1;
        color: #a5b4fc; padding: 0.3rem 0.9rem; border-radius: 999px;
        font-size: 0.85rem; margin-right: 0.4rem; margin-bottom: 0.4rem; cursor: pointer;
    }
    stButton > button {
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
        color: white; border: none; border-radius: 8px;
        font-weight: 600; padding: 0.5rem 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Session State Init
# ─────────────────────────────────────────────
if "step" not in st.session_state:
    st.session_state.step = "discover"   # discover | results | finalized | case_study
if "domain" not in st.session_state:
    st.session_state.domain = ""
if "use_cases" not in st.session_state:
    st.session_state.use_cases = []
if "finalized" not in st.session_state:
    st.session_state.finalized = None
if "case_study" not in st.session_state:
    st.session_state.case_study = None

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Use Case Discovery Agent")
    st.caption("Powered by Antigravity + FastAPI")
    st.markdown("---")

    try:
        status = requests.get(f"{API_URL}/status", timeout=3).json()
        st.markdown(f"**🟢 Backend:** Online")
        st.markdown(f"**📂 Domains explored:** {len(status.get('cached_domains', []))}")
        st.markdown(f"**📦 Cache size:** {status.get('cache_size', 0)} items")
        domains = status.get("cached_domains", [])
        if domains:
            st.markdown("**Recent domains:**")
            for d in domains:
                st.markdown(f"- {d.title()}")
    except Exception:
        st.markdown("**🔴 Backend:** Offline — restart FastAPI on port 8000")

    st.markdown("---")

    if st.button("🔄 Start Over", use_container_width=True):
        st.session_state.step = "discover"
        st.session_state.domain = ""
        st.session_state.use_cases = []
        st.session_state.finalized = None
        st.rerun()

    st.markdown("---")
    st.markdown("""
**Architecture**
- Frontend: Streamlit
- Backend: FastAPI
- Cache: In-memory + APScheduler
- LLM: Ollama `llama3.2` → HF `Mistral-7B`
    """)

# ─────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="hero-title">🔍 Use Case Discovery Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Find, compare, and lock in a real-world ML use case — calm, structured, step by step.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# STEP 1: DISCOVER
# ─────────────────────────────────────────────
if st.session_state.step == "discover":
    st.markdown("### Which domain would you like to explore?")
    st.markdown("Enter a business domain below and I'll surface 5–8 relevant, realistic use cases for you.")

    # Quick domain chips
    st.markdown("**Popular domains:**")
    quick_domains = ["Finance", "Healthcare", "Retail", "Manufacturing", "Logistics", "Cybersecurity", "HR", "Real Estate"]
    cols = st.columns(4)
    for i, qd in enumerate(quick_domains):
        if cols[i % 4].button(qd, key=f"chip_{qd}"):
            st.session_state.domain = qd.lower()
            st.rerun()

    st.markdown("---")

    with st.form("domain_form"):
        domain_input = st.text_input(
            "Domain keyword",
            value=st.session_state.domain,
            placeholder="e.g., finance, healthcare, supply chain, retail…",
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("🔍 Discover Use Cases", use_container_width=True)

    if submitted and domain_input.strip():
        st.session_state.domain = domain_input.strip().lower()
        with st.spinner(f"Discovering use cases for **{st.session_state.domain}**…"):
            try:
                res = requests.get(f"{API_URL}/discover", params={"domain": st.session_state.domain}, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.use_cases = data["use_cases"]
                    st.session_state.step = "results"
                    st.rerun()
                else:
                    st.error("Unexpected error from backend. Please try again.")
            except requests.exceptions.ConnectionError:
                st.error("🔴 Cannot reach backend. Make sure FastAPI is running on port 8000.")
            except Exception as e:
                st.error(f"Error: {e}")

# ─────────────────────────────────────────────
# STEP 2: RESULTS — show all use case cards
# ─────────────────────────────────────────────
elif st.session_state.step == "results":
    domain_title = st.session_state.domain.title()
    st.markdown(f"### ✅ Found {len(st.session_state.use_cases)} use cases for **{domain_title}**")
    st.caption("Review the cards below, then select one to finalise.")
    st.markdown("---")

    for uc in st.session_state.use_cases:
        # Tech stack tags
        tech_tags = "".join(
            f'<span class="tag">{t.strip()}</span>'
            for t in uc["tech_stack"].split(",")
        )
        # Business process steps
        process_html = "".join(
            f'<div class="process-step"><span class="step-num">{i+1}</span><span>{step}</span></div>'
            for i, step in enumerate(uc["business_process"])
        )

        st.markdown(f"""
<div class="use-case-card">
    <span class="card-id">#{uc['id']}</span>
    <div class="card-title">{uc['title']}</div>
    <div class="card-desc">{uc['description']}</div>
    <div class="section-label">🏷 Domain</div>
    <div style="color:#cbd5e1; margin-bottom:0.8rem;">{uc['domain']} → {uc['subdomain']}</div>
    <div class="section-label">⚙️ Tech Stack</div>
    <div class="tag-row">{tech_tags}</div>
    <div class="section-label">📋 Business Process</div>
    {process_html}
    <div class="section-label" style="margin-top:0.8rem;">🔀 Architecture Diagram</div>
    <div class="data-flow-box">{uc.get('architecture_diagram', uc['data_flow'])}</div>
    <div style="margin-top:0.8rem; color:#10b981; font-size:0.88rem;">💰 {uc['value']}</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎯 Which use case would you like to finalise?")
    st.caption("Select the ID number of your chosen use case.")

    uc_options = {f"#{uc['id']} — {uc['title']}": uc['id'] for uc in st.session_state.use_cases}

    col_sel, col_btn, col_cs = st.columns([3, 1, 1])
    with col_sel:
        selected_label = st.selectbox("Choose a use case", list(uc_options.keys()), label_visibility="collapsed")
    with col_btn:
        if st.button("✅ Finalise", use_container_width=True):
            selected_id = uc_options[selected_label]
            with st.spinner("Locking in your use case…"):
                try:
                    res = requests.post(
                        f"{API_URL}/finalize",
                        json={"domain": st.session_state.domain, "use_case_id": selected_id},
                        timeout=15
                    )
                    if res.status_code == 200:
                        st.session_state.finalized = res.json()
                        st.session_state.step = "finalized"
                        st.rerun()
                    else:
                        st.error(f"Error: {res.json().get('detail', 'Could not finalise.')}")
                except Exception as e:
                    st.error(f"Backend error: {e}")
    with col_cs:
        if st.button("📄 Case Study", use_container_width=True):
            selected_id = uc_options[selected_label]
            with st.spinner("Generating full case study…"):
                try:
                    res = requests.post(
                        f"{API_URL}/case-study",
                        json={"domain": st.session_state.domain, "use_case_id": selected_id},
                        timeout=15
                    )
                    if res.status_code == 200:
                        st.session_state.case_study = res.json()
                        st.session_state.step = "case_study"
                        st.rerun()
                    else:
                        st.error(f"Error: {res.json().get('detail', 'Could not generate case study.')}")
                except Exception as e:
                    st.error(f"Backend error: {e}")

# ─────────────────────────────────────────────
# STEP 3: FINALIZED
# ─────────────────────────────────────────────
elif st.session_state.step == "finalized":
    f = st.session_state.finalized
    uc = f["use_case"]

    st.markdown(f'<div class="confirm-banner">{f["confirmation_message"]}</div>', unsafe_allow_html=True)

    st.markdown(f"## 🎉 {uc['title']}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Domain", uc["domain"])
    col2.metric("Subdomain", uc["subdomain"])
    col3.metric("ML Technique", uc["ml_technique"])

    st.markdown('<div class="finalize-card">', unsafe_allow_html=True)

    st.markdown("### 📝 Use Case Summary")
    st.info(uc["description"])

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**⚙️ Tech Stack**")
        for t in uc["tech_stack"].split(","):
            st.markdown(f"- `{t.strip()}`")
    with col_b:
        st.markdown("**📥 Input Data**")
        st.write(uc["input_data"])

    st.markdown("---")
    st.markdown("### 📊 Key Performance Indicators (KPIs)")
    for kpi in f["kpis"]:
        st.markdown(f'<div class="kpi-item">📌 {kpi}</div>', unsafe_allow_html=True)

    st.markdown("### 🗺️ Action Plan")
    for step in f["action_plan"]:
        st.markdown(f'<div class="action-step">▶️ {step}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🚀 Futuristic View (Next 2-5 Years)")
    st.success(uc["futuristic_view"])

    st.markdown("### 💼 Client-Ready Implementation")
    st.warning(uc["client_ready_details"])

    st.markdown("### 📊 Architecture Diagram")
    st.code(uc.get("architecture_diagram", uc["data_flow"]), language="text")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Phase 4: Copy-ready text + Claude prompt ─────────────────
    st.markdown("---")
    st.markdown("## 📋 Phase 4 — Copy-Ready Output")
    st.info("This use case has been finalized. Below you'll find the complete copy‑ready text and a prompt you can use with Claude Sonnet to generate an improved version.")

    tab1, tab2 = st.tabs(["📄 Copy-Ready Case Study", "🤖 Claude Regeneration Prompt"])

    with tab1:
        st.caption("Click the copy icon (top-right of the block) to copy the full case study to clipboard.")
        copy_text = f.get("copy_ready_text", "")
        if copy_text:
            st.code(copy_text, language="text")
        else:
            st.warning("Copy-ready text not available. Please re-finalize.")

    with tab2:
        st.caption("Paste this prompt into Claude Sonnet to generate a deeply enriched version of this use case.")
        claude_text = f.get("claude_prompt", "")
        if claude_text:
            st.code(claude_text, language="text")
        else:
            st.warning("Claude prompt not available. Please re-finalize.")


    st.markdown("---")
    col_x, col_y, col_z = st.columns(3)
    with col_x:
        if st.button("🔁 Explore Another Domain", use_container_width=True):
            st.session_state.step = "discover"
            st.session_state.domain = ""
            st.session_state.use_cases = []
            st.session_state.finalized = None
            st.rerun()
    with col_y:
        if st.button("⬅️ Back to Use Case List", use_container_width=True):
            st.session_state.step = "results"
            st.session_state.finalized = None
            st.rerun()
    with col_z:
        uc_id = st.session_state.finalized["use_case"]["id"] if st.session_state.finalized else None
        if uc_id and st.button("📄 View Full Case Study", use_container_width=True):
            with st.spinner("Generating case study…"):
                try:
                    res = requests.post(
                        f"{API_URL}/case-study",
                        json={"domain": st.session_state.domain, "use_case_id": uc_id},
                        timeout=15
                    )
                    if res.status_code == 200:
                        st.session_state.case_study = res.json()
                        st.session_state.step = "case_study"
                        st.rerun()
                    else:
                        st.error(f"Error: {res.json().get('detail', 'Could not generate.')}")
                except Exception as e:
                    st.error(f"Backend error: {e}")

# ─────────────────────────────────────────────
# STEP 4: CASE STUDY (Phase 2)
# ─────────────────────────────────────────────
elif st.session_state.step == "case_study":
    cs = st.session_state.case_study
    uc = cs["use_case"]

    st.markdown(f'<div class="hero-title">📄 Case Study</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-sub">{uc["domain"]} → {uc["subdomain"]}</div>', unsafe_allow_html=True)
    st.markdown(f"# {uc['title']}")
    st.markdown("---")

    # Problem Statement
    st.markdown("## 🚨 Problem Statement")
    st.info(cs["problem_statement"])

    # Objective
    st.markdown("## 🎯 Objective / Goal")
    st.success(cs["objective"])

    # Target Audience
    st.markdown("## 👥 Target Audience / Users")
    cols = st.columns(len(cs["target_audience"]))
    for i, persona in enumerate(cs["target_audience"]):
        cols[i].markdown(f'<div class="kpi-item">👤 {persona}</div>', unsafe_allow_html=True)

    # Solution Overview
    st.markdown("## 💡 Solution Overview")
    st.markdown(cs["solution_overview"])
    st.markdown("---")

    # Key Features
    st.markdown("## ⭐ Key Features & Functionalities")
    feat_cols = st.columns(2)
    for i, feat in enumerate(cs["key_features"]):
        with feat_cols[i % 2]:
            st.markdown(f'<div class="action-step"><strong>✅ {feat["title"]}</strong><br>{feat["description"]}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Tech Stack
    st.markdown("## ⚙️ Tech Stack")
    tech_tags = "".join(
        f'<span class="tag">{t.strip()}</span>' for t in cs["tech_stack_expanded"].split(",")
    )
    st.markdown(f'<div class="tag-row">{tech_tags}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Architecture
    st.markdown("## 🏗️ Architecture / Flow")
    arch_col1, arch_col2 = st.columns([2, 1])
    with arch_col1:
        for i, step in enumerate(cs["architecture_steps"]):
            st.markdown(f'<div class="process-step"><span class="step-num">{i+1}</span><span>{step}</span></div>', unsafe_allow_html=True)
    with arch_col2:
        st.code(cs["architecture_diagram"], language="text")

    st.markdown("---")

    # Dataset Requirements
    st.markdown("## 📦 Dataset Requirements")
    for req in cs["dataset_requirements"]:
        st.markdown(f"- {req}")

    # Model Details
    st.markdown("## 🤖 Model Details")
    md = cs["model_details"]
    m1, m2, m3 = st.columns(3)
    m1.markdown(f"**Algorithm**\n\n`{md['algorithm']}`")
    m2.markdown(f"**Training Strategy**\n\n{md['training']}")
    m3.markdown(f"**Evaluation Metrics**\n\n{md['evaluation_metrics']}")

    st.markdown("---")

    # Integration Points
    st.markdown("## 🔗 Integration Points")
    for pt in cs["integration_points"]:
        st.markdown(f"- {pt}")

    # Risks & Mitigations
    st.markdown("## ⚠️ Risks & Mitigations")
    for rm in cs["risks_and_mitigations"]:
        with st.expander(f"🔴 Risk: {rm['risk']}"):
            st.success(f"✅ Mitigation: {rm['mitigation']}")

    st.markdown("---")

    # Success Metrics
    st.markdown("## 📊 Success Metrics (KPIs)")
    for sm in cs["success_metrics"]:
        st.markdown(f'<div class="kpi-item">📌 {sm}</div>', unsafe_allow_html=True)

    # Timeline
    st.markdown("## 🗓️ Implementation Timeline")
    tl_cols = st.columns(len(cs["timeline_estimate"]))
    for i, phase in enumerate(cs["timeline_estimate"]):
        with tl_cols[i]:
            st.markdown(f"""<div class="action-step" style="text-align:center">
<strong>{phase['phase']}</strong><br>
<span style="color:#6366f1;font-size:1.1rem;font-weight:700">{phase['duration']}</span><br>
<span style="font-size:0.8rem;color:#94a3b8">{phase['deliverable']}</span>
</div>""", unsafe_allow_html=True)

    # ROI
    st.markdown("## 💰 ROI Estimate")
    st.warning(cs["roi_estimate"])

    st.markdown("---")
    nav1, nav2, nav3 = st.columns(3)
    with nav1:
        if st.button("⬅️ Back to List", use_container_width=True):
            st.session_state.step = "results"
            st.session_state.case_study = None
            st.rerun()
    with nav2:
        if st.button("✅ Finalise This Use Case", use_container_width=True):
            with st.spinner("Locking in…"):
                try:
                    res = requests.post(
                        f"{API_URL}/finalize",
                        json={"domain": st.session_state.domain, "use_case_id": uc["id"]},
                        timeout=15
                    )
                    if res.status_code == 200:
                        st.session_state.finalized = res.json()
                        st.session_state.step = "finalized"
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    with nav3:
        if st.button("🔁 New Domain", use_container_width=True):
            st.session_state.step = "discover"
            st.session_state.domain = ""
            st.session_state.use_cases = []
            st.session_state.case_study = None
            st.rerun()
