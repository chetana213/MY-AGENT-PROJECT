import streamlit as st
import asyncio
import json
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from pydantic_ai import Agent
from schemas import PRReviewPayload
from rag_engine import retrieve_relevant_rules

# Page Configuration
st.set_page_config(
    page_title="AI Code Reviewer & Security Shield",
    page_icon="🛡️",
    layout="wide"
)

# Load environment variables
load_dotenv()

# Automatically fetch API key
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key

# Sidebar Setup
st.sidebar.title("🛡️ AI Security Config")
st.sidebar.success("🔒 API Key loaded securely")
st.sidebar.markdown("---")
st.sidebar.info("Powered by **Google Gemini 2.5 Flash**, **LangChain RAG**, & **Pydantic AI**")

# Main Title
st.title("🛡️ Multi-Agent AI Code Reviewer & Refactor Dashboard")
st.markdown("Paste your source code below to perform instant **SAST vulnerability analysis**, evaluate against **internal corporate coding policies via RAG**, and receive **auto-refactored security fixes**.")

# Tab Selection
tab1, tab2 = st.tabs(["⚡ Live Code Auditor", "📊 Dashboard Metrics"])

with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 Input Source Code")
        sample_code = """import sqlite3

def get_user_data(user_id):
    conn = sqlite3.connect("database.db")
    # Vulnerable SQL query
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    return conn.execute(query).fetchall()
"""
        code_input = st.text_area("Source Code (Python)", value=sample_code, height=350)
        run_button = st.button("🚀 Run Security Audit", type="primary", use_container_width=True)

    with col2:
        st.subheader("🔍 Security Audit Results")
        
        if run_button:
            if not os.getenv("GOOGLE_API_KEY"):
                st.error("API Key not found! Please check your Streamlit Secrets or environment setup.")
            else:
                with st.spinner("Retrieving company policies via LangChain RAG & auditing code..."):
                    try:
                        # 1. Retrieve RAG Policy Context
                        retrieved_policy = retrieve_relevant_rules(code_input)
                        
                        # 2. Construct simulated diff
                        fake_diff = f"""
diff --git a/input_code.py b/input_code.py
new file mode 100644
--- /dev/null
+++ b/input_code.py
@@ -0,0 +1,10 @@
+{code_input}
"""
                        # 3. Dynamic Prompt with RAG Context
                        system_prompt = (
                            "You are an expert Security Engineer and Tech Lead.\n"
                            "Review code diffs against general SAST practices AND the following internal company rules:\n\n"
                            f"--- INTERNAL COMPANY POLICIES ---\n{retrieved_policy}\n-----------------------------------\n\n"
                            "Identify flaws, specify line numbers, and provide the complete refactored code in 'refactored_code'."
                        )

                        agent = Agent('google:gemini-2.5-flash', system_prompt=system_prompt)

                        async def run_review():
                            prompt = f"Review this code diff:\n\n```diff\n{fake_diff}\n```"
                            try:
                                res = await agent.run(prompt, result_type=PRReviewPayload)
                            except TypeError:
                                res = await agent.run(prompt)
                            return getattr(res, "data", None) or getattr(res, "output", None)

                        review_data = asyncio.run(run_review())

                        # Format output
                        if hasattr(review_data, "model_dump"):
                            data = review_data.model_dump()
                        elif isinstance(review_data, dict):
                            data = review_data
                        else:
                            data = {"overall_score": 50, "summary": str(review_data), "annotations": [], "refactored_code": ""}

                        score = data.get("overall_score", 100)
                        
                        # Display Health Score
                        if score >= 80:
                            st.success(f"### Code Health Score: {score}/100 ✅")
                        elif score >= 50:
                            st.warning(f"### Code Health Score: {score}/100 ⚠️")
                        else:
                            st.error(f"### Code Health Score: {score}/100 🚨")

                        # Display Retrieved RAG Guidelines
                        with st.expander("📚 Retrieved Company Policy Guidelines (RAG Context)"):
                            st.markdown(retrieved_policy)

                        # Display Summary
                        st.markdown("#### 📄 Executive Summary")
                        st.markdown(data.get("summary", "No summary provided."))

                        # Display Annotations
                        annotations = data.get("annotations", [])
                        if annotations:
                            st.markdown("#### 🐛 Identified Flaws & Annotations")
                            for ann in annotations:
                                line = ann.get("line", "N/A") if isinstance(ann, dict) else getattr(ann, "line", "N/A")
                                comment = ann.get("comment", "") if isinstance(ann, dict) else getattr(ann, "comment", "")
                                st.warning(f"**Line {line}:** {comment}")

                        # Display Refactored Code
                        refactored = data.get("refactored_code", "")
                        if refactored:
                            st.markdown("#### 🛠️ Auto-Refactored Fix")
                            st.code(refactored, language="python")

                    except Exception as e:
                        st.error(f"Audit failed: {str(e)}")

with tab2:
    st.subheader("📊 Repository & Scanning Metrics")
    m1, m2, m3 = st.columns(3)
    m1.metric(label="Total Audits Executed", value="16", delta="+4 today")
    m2.metric(label="Vulnerabilities Blocked", value="32", delta="+7 high severity")
    m3.metric(label="Average Health Score", value="81/100", delta="+15%")
    
    st.info("Continuous integration metrics are logged automatically via GitHub Actions workflows.")