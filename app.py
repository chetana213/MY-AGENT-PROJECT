import streamlit as st
import asyncio
import os
from dotenv import load_dotenv

from services import (
    get_api_key,
    run_security_audit,
    ask_security_lead,
    generate_side_by_side_diff,
    generate_markdown_report
)

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="SecureCode AI — Developer Security Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()
api_key = get_api_key(st.secrets)
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key

# ----------------- CLEAN SAAS THEME (PRESERVED) -----------------
st.markdown("""
<style>
    @import url('[https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap](https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap)');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, sans-serif !important;
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] div.block-container {
        padding: 1.25rem 0.85rem !important;
    }
    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 12px;
        margin-bottom: 12px;
        border-bottom: 1px solid #e2e8f0;
    }
    .brand-title {
        font-size: 19px;
        font-weight: 700;
        color: #0f172a;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .brand-subtitle {
        font-size: 12.5px;
        color: #64748b;
    }
    .system-ready-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 6px;
        padding: 3px 9px;
        font-size: 11.5px;
        font-weight: 600;
        color: #16a34a;
    }
    .section-label-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .section-label {
        font-size: 13.5px;
        font-weight: 700;
        color: #0f172a;
    }
    .config-strip {
        display: flex;
        gap: 6px;
        margin-bottom: 8px;
    }
    .config-pill {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 5px;
        padding: 3px 8px;
        font-size: 11.5px;
        color: #475569;
    }
    .stTextArea textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 12.5px !important;
        line-height: 1.55 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
    }
    div.stButton > button:first-child {
        background-color: #2563eb !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        padding: 9px 18px !important;
        border-radius: 6px !important;
        border: 1px solid #1d4ed8 !important;
    }
    .score-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 10px 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .score-num {
        font-size: 22px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    .score-green { color: #16a34a; }
    .score-amber { color: #d97706; }
    .score-red { color: #dc2626; }
    .metric-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-bottom: 10px;
    }
    .metric-chip {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 10px;
        text-align: center;
    }
    .metric-val {
        font-size: 17px;
        font-weight: 700;
        color: #0f172a;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-lbl {
        font-size: 10.5px;
        color: #64748b;
    }
    .finding-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 10px 12px;
        margin-bottom: 8px;
    }
    .finding-crit { border-left: 4px solid #dc2626; }
    .finding-high { border-left: 4px solid #ea580c; }
    .finding-med { border-left: 4px solid #d97706; }
    .finding-low { border-left: 4px solid #2563eb; }
    .empty-container {
        background: #ffffff;
        border: 1px dashed #cbd5e1;
        border-radius: 8px;
        padding: 24px 14px;
        text-align: center;
    }
    .pipeline-bar {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .code-container-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12.5px;
        line-height: 1.5;
        overflow-x: auto;
        white-space: pre;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE METRICS -----------------
if "analytics" not in st.session_state:
    st.session_state["analytics"] = {
        "audits_count": 0,
        "vulns_found": 0,
        "vulns_fixed": 0,
        "scores": []
    }
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

# ----------------- 1. SIDEBAR -----------------
with st.sidebar:
    st.markdown("""
    <div style="padding-bottom: 10px; border-bottom: 1px solid #e2e8f0; margin-bottom: 12px;">
        <div style="font-size: 16px; font-weight: 700; color: #0f172a; display: flex; align-items: center; gap: 6px;">
            🛡️ SecureCode AI
        </div>
        <div style="font-size: 11.5px; color: #64748b;">AI-Powered Code Security</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size: 10.5px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 6px;">System Status</div>
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 10px; margin-bottom: 14px; font-size: 11.5px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: #475569;">Security Engine</span>
            <span style="color: #16a34a; font-weight: 600;">● Online</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: #475569;">Gemini Model</span>
            <span style="color: #16a34a; font-weight: 600;">● Connected</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="color: #475569;">Policy Knowledge</span>
            <span style="color: #16a34a; font-weight: 600;">● Active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size: 10.5px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 6px;">Workspace Modules</div>
    <div style="font-size: 12px; color: #334155; display: flex; flex-direction: column; gap: 4px;">
        <div style="background: #eff6ff; border-left: 3px solid #2563eb; padding: 5px 8px; color: #1d4ed8; font-weight: 600;">⚡ Code Auditor</div>
        <div style="padding: 4px 8px; color: #475569;">🔍 Security Findings</div>
        <div style="padding: 4px 8px; color: #475569;">🔄 AI Refactoring</div>
        <div style="padding: 4px 8px; color: #475569;">📊 Security Analytics</div>
        <div style="padding: 4px 8px; color: #475569;">💬 AI Security Lead</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size: 10.5px; color: #94a3b8; text-align: center;">
        Powered by Gemini 2.5 • LangChain RAG • Pydantic AI
    </div>
    """, unsafe_allow_html=True)

# ----------------- 2. HEADER -----------------
st.markdown("""
<div class="top-header">
    <div>
        <div class="brand-title">🛡️ SecureCode AI</div>
        <div class="brand-subtitle">Analyze vulnerabilities, enforce internal security policies, and automatically refactor insecure code.</div>
    </div>
    <div style="text-align: right;">
        <span class="system-ready-badge">● System Ready</span>
        <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">Gemini 2.5 Flash • RAG Enabled • SAST Ready</div>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["⚡ Security Scan Workspace", "📊 Security Analytics"])

# ----------------- TAB 1: CODE AUDITOR -----------------
with tab1:
    col1, col2 = st.columns([1.05, 1], gap="medium")

    with col1:
        st.markdown("""
        <div class="section-label-bar">
            <span class="section-label">📝 Source Code</span>
            <span style="font-size: 11.5px; color: #64748b;">Python 3.x Supported</span>
        </div>
        <div class="config-strip">
            <span class="config-pill">Language: <strong>Python</strong></span>
            <span class="config-pill">Scan: <strong>SAST + RAG</strong></span>
            <span class="config-pill">Model: <strong>Gemini 2.5 Flash</strong></span>
        </div>
        """, unsafe_allow_html=True)

        sample_code = """import sqlite3

def get_user_data(user_id):
    conn = sqlite3.connect("database.db")
    # Vulnerable SQL query
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    return conn.execute(query).fetchall()
"""
        code_input = st.text_area("Source Code", value=sample_code, height=270, label_visibility="collapsed")
        run_button = st.button("🚀 Run Security Audit", type="primary", use_container_width=True)

    with col2:
        st.markdown("""
        <div class="section-label-bar">
            <span class="section-label">🔍 Security Analysis</span>
            <span style="font-size: 11.5px; color: #64748b;">Multi-Agent Pipeline</span>
        </div>
        """, unsafe_allow_html=True)

        if run_button:
            if not os.getenv("GOOGLE_API_KEY"):
                st.error("API Key not found. Please verify your environment variables or Streamlit secrets.")
            else:
                progress_placeholder = st.empty()
                progress_placeholder.info("🔎 1/4 Performing SAST inspection and RAG policy lookup...")
                
                try:
                    data, policy = asyncio.run(run_security_audit(code_input))
                    progress_placeholder.info("🤖 2/4 Extracting clean refactored source & validating AST...")
                    
                    st.session_state["review_data"] = data
                    st.session_state["original_code"] = code_input
                    st.session_state["retrieved_policy"] = policy
                    st.session_state["chat_messages"] = []

                    # Session Analytics Tracking
                    st.session_state["analytics"]["audits_count"] += 1
                    st.session_state["analytics"]["vulns_found"] += len(data.get("findings", []))
                    st.session_state["analytics"]["vulns_fixed"] += data.get("fixed_count", 0)
                    st.session_state["analytics"]["scores"].append(data.get("overall_score", 100))

                    progress_placeholder.empty()
                except Exception as e:
                    progress_placeholder.empty()
                    st.error(f"Audit failed: {str(e)}")

        if "review_data" in st.session_state:
            data = st.session_state["review_data"]
            score = data.get("overall_score", 100)
            findings = data.get("findings", [])
            lines_count = len(st.session_state["original_code"].splitlines())

            score_color = "score-green" if score >= 80 else ("score-amber" if score >= 50 else "score-red")
            posture_text = "🟢 Good Security Posture" if score >= 80 else ("🟠 Needs Attention" if score >= 50 else "🔴 Critical Issues Found")

            # Score Banner
            st.markdown(f"""
            <div class="score-card">
                <div>
                    <div style="font-size: 10.5px; font-weight: 700; color: #64748b; text-transform: uppercase;">Security Posture</div>
                    <div style="font-size: 12.5px; color: #1e293b; font-weight: 600; margin-top: 1px;">{posture_text}</div>
                </div>
                <div class="score-num {score_color}">{score} <span style="font-size: 13px; color: #94a3b8;">/ 100</span></div>
            </div>
            """, unsafe_allow_html=True)

            # Metric Chips
            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-chip">
                    <div class="metric-val">{len(findings)}</div>
                    <div class="metric-lbl">Findings</div>
                </div>
                <div class="metric-chip">
                    <div class="metric-val">{lines_count}</div>
                    <div class="metric-lbl">Lines Scanned</div>
                </div>
                <div class="metric-chip">
                    <div class="metric-val">{data.get('fixed_count', 0)}</div>
                    <div class="metric-lbl">Verified Fixes</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Summary Box
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 12px; margin-bottom: 8px; font-size: 12.5px; color: #334155;">
                <strong>Summary:</strong> {data.get('summary', 'Audit executed.')}
            </div>
            """, unsafe_allow_html=True)

            # Findings
            if findings:
                for f in findings:
                    sev = (f.get("severity") if isinstance(f, dict) else getattr(f, "severity", "MED")).upper()
                    title = f.get("title") if isinstance(f, dict) else getattr(f, "title", "Security Issue")
                    line = f.get("line") if isinstance(f, dict) else getattr(f, "line", "N/A")
                    exp = f.get("explanation") if isinstance(f, dict) else getattr(f, "explanation", "")
                    rec = f.get("recommendation") if isinstance(f, dict) else getattr(f, "recommendation", "")
                    pol = f.get("related_policy") if isinstance(f, dict) else getattr(f, "related_policy", None)

                    border_class = "finding-crit" if sev == "CRITICAL" else ("finding-high" if sev == "HIGH" else "finding-med")
                    policy_info = f"<div style='margin-top: 4px; font-size: 11.5px; color: #0284c7;'><b>Policy:</b> {pol}</div>" if pol else ""

                    st.markdown(f"""
                    <div class="finding-card {border_class}">
                        <div style="display: flex; justify-content: space-between; font-weight: 600; font-size: 12.5px;">
                            <span>{title} (Line {line})</span>
                            <span style="font-size: 10px; padding: 1px 4px; border-radius: 3px; background: #f1f5f9;">{sev}</span>
                        </div>
                        <div style="font-size: 12px; color: #475569; margin-top: 3px;">{exp}</div>
                        <div style="font-size: 11.5px; color: #16a34a; margin-top: 3px;"><b>Fix:</b> {rec}</div>
                        {policy_info}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("✅ No security vulnerabilities detected in the submitted code.")

            # Policy Context
            with st.expander("📚 Matched Internal Policies (RAG Context)"):
                st.markdown(st.session_state.get("retrieved_policy", "No specific policy retrieved."))

            # Download Report
            report_md = generate_markdown_report(data, st.session_state["original_code"], st.session_state.get("retrieved_policy", ""))
            st.download_button("📥 Export Security Audit Report (.md)", data=report_md, file_name="security_audit_report.md", mime="text/markdown", use_container_width=True)

        else:
            st.markdown("""
            <div class="empty-container">
                <div style="font-size: 24px; margin-bottom: 4px;">🛡️</div>
                <div style="font-size: 14px; font-weight: 600; color: #0f172a;">Ready for Analysis</div>
                <div style="font-size: 12px; color: #64748b; margin-top: 4px;">Paste Python code on the left and run the audit to trigger the Multi-Agent pipeline.</div>
            </div>
            """, unsafe_allow_html=True)

    # ----------------- PIPELINE VISUALIZATION -----------------
    st.markdown("""
    <div class="pipeline-bar">
        <span style="font-size: 11.5px; font-weight: 700; color: #0f172a;">🤖 AI Pipeline:</span>
        <span style="font-size: 11.5px; color: #475569;">1. Code Parser</span>
        <span style="color: #cbd5e1;">→</span>
        <span style="font-size: 11.5px; color: #475569;">2. SAST Security Agent</span>
        <span style="color: #cbd5e1;">→</span>
        <span style="font-size: 11.5px; color: #475569;">3. RAG Policy Agent</span>
        <span style="color: #cbd5e1;">→</span>
        <span style="font-size: 11.5px; color: #475569;">4. Dedicated Clean Refactor</span>
        <span style="color: #cbd5e1;">→</span>
        <span style="font-size: 11.5px; color: #475569;">5. AST Validation & Re-scan</span>
    </div>
    """, unsafe_allow_html=True)

    # ----------------- REFACTORING & DIFF -----------------
    if "review_data" in st.session_state and st.session_state["review_data"].get("refactored_code"):
        st.markdown("---")
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <div>
                <div style="font-size: 15px; font-weight: 700; color: #0f172a;">🔄 AI Secure Refactoring & Verification</div>
                <div style="font-size: 12px; color: #64748b;">Compare original vulnerable code against validated, clean Python source.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        syntax_msg = st.session_state["review_data"].get("syntax_message", "")
        if st.session_state["review_data"].get("syntax_valid", False):
            st.success(f"✓ Syntax Valid (AST Verified) | Verified Fixes: {st.session_state['review_data'].get('fixed_count', 0)} | Post-Fix Score: {st.session_state['review_data'].get('refactored_score', 100)}/100")
        else:
            st.error(f"✗ Syntax Error: {syntax_msg}")

        # Code Action Bar
        col_down, col_space = st.columns([1, 3])
        with col_down:
            st.download_button(
                label="📥 Download Refactored Code (.py)",
                data=st.session_state["review_data"]["refactored_code"],
                file_name="refactored_code.py",
                mime="text/x-python",
                use_container_width=True
            )

        diff_html = generate_side_by_side_diff(
            st.session_state["original_code"],
            st.session_state["review_data"]["refactored_code"]
        )
        st.components.v1.html(diff_html, height=340, scrolling=True)

        # ----------------- AI SECURITY LEAD CHAT -----------------
        st.markdown("---")
        st.markdown("""
        <div style="font-size: 15px; font-weight: 700; color: #0f172a;">💬 AI Security Lead</div>
        <div style="font-size: 12px; color: #64748b; margin-bottom: 8px;">Ask follow-up questions regarding vulnerabilities, architecture tradeoffs, or ORM alternatives.</div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Why is this code vulnerable?", use_container_width=True):
                st.session_state["chat_input_val"] = "Why is this code vulnerable to SQL injection?"
        with c2:
            if st.button("How to use SQLAlchemy ORM?", use_container_width=True):
                st.session_state["chat_input_val"] = "How would I write this using SQLAlchemy ORM instead?"
        with c3:
            if st.button("Explain context manager fix", use_container_width=True):
                st.session_state["chat_input_val"] = "Explain why context managers are required here."

        for msg in st.session_state["chat_messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        prompt_val = st.session_state.pop("chat_input_val", None)
        user_prompt = st.chat_input("Ask AI Security Lead a question...") or prompt_val

        if user_prompt:
            st.session_state["chat_messages"].append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.markdown(user_prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing with full audit context..."):
                    try:
                        bot_reply = asyncio.run(ask_security_lead(
                            user_prompt=user_prompt,
                            original_code=st.session_state["original_code"],
                            refactored_code=st.session_state["review_data"].get("refactored_code", ""),
                            policy=st.session_state.get("retrieved_policy", ""),
                            audit_data=st.session_state["review_data"]
                        ))
                        st.markdown(bot_reply)
                        st.session_state["chat_messages"].append({"role": "assistant", "content": bot_reply})
                    except Exception as e:
                        st.error(f"Chat error: {str(e)}")

# ----------------- TAB 2: ANALYTICS -----------------
with tab2:
    st.markdown("""
    <div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 2px;">📊 Session Security Analytics</div>
    <div style="font-size: 12px; color: #64748b; margin-bottom: 14px;">Real-time metrics computed directly from session audits.</div>
    """, unsafe_allow_html=True)

    an = st.session_state["analytics"]
    audits_count = an["audits_count"]
    vulns_found = an["vulns_found"]
    vulns_fixed = an["vulns_fixed"]
    avg_score = round(sum(an["scores"]) / len(an["scores"]), 1) if an["scores"] else 100.0

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="Audits Executed (Session)", value=str(audits_count))
    with m2:
        st.metric(label="Vulnerabilities Detected", value=str(vulns_found))
    with m3:
        st.metric(label="Average Session Score", value=f"{avg_score}/100")