import streamlit as st
import asyncio
import os
import difflib
import re
import json
from datetime import datetime
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

# Helper: Robust API Key Retrieval
def get_api_key():
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if key:
        return key
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass
    return None

api_key = get_api_key()
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key

# Sidebar Setup
st.sidebar.title("🛡️ AI Security Config")
if api_key:
    st.sidebar.success("🔒 API Key loaded securely")
else:
    st.sidebar.error("⚠️ API Key not detected")
st.sidebar.markdown("---")
st.sidebar.info("Powered by **Google Gemini 2.5 Flash**, **LangChain RAG**, & **Pydantic AI**")

# Main Header
st.title("🛡️ Multi-Agent AI Code Reviewer & Refactor Dashboard")
st.markdown("Paste your source code below to perform instant **SAST vulnerability analysis**, evaluate against **internal corporate policies via RAG**, view **visual diffs**, and chat directly with your AI Security Lead.")

# Helper: Robust Normalization of Review Data
def parse_review_output(raw_output) -> dict:
    """Extracts structured fields even if the model outputs JSON embedded in summary."""
    data = {
        "overall_score": 50,
        "summary": "",
        "annotations": [],
        "refactored_code": ""
    }

    if hasattr(raw_output, "model_dump"):
        data.update(raw_output.model_dump())
    elif isinstance(raw_output, dict):
        data.update(raw_output)
    elif isinstance(raw_output, str):
        data["summary"] = raw_output

    # Check if summary contains an embedded JSON object
    summary_text = str(data.get("summary", "")).strip()
    json_match = re.search(r"\{.*\}", summary_text, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            if isinstance(parsed, dict):
                if "summary" in parsed:
                    data["summary"] = parsed["summary"]
                if "annotations" in parsed and (not data["annotations"] or len(data["annotations"]) == 0):
                    data["annotations"] = parsed["annotations"]
                if "refactored_code" in parsed and not data["refactored_code"]:
                    data["refactored_code"] = parsed["refactored_code"]
                if "overall_score" in parsed:
                    data["overall_score"] = parsed["overall_score"]
        except Exception:
            pass

    # Extract python code if refactored_code is still empty
    if not data["refactored_code"] or not data["refactored_code"].strip():
        code_match = re.search(r"```python\s*(.*?)\s*```", str(data.get("summary", "")), re.DOTALL)
        if code_match:
            data["refactored_code"] = code_match.group(1).strip()

    return data

# Helper: Generate Side-by-Side Diff HTML
def generate_side_by_side_diff(original_code: str, refactored_code: str) -> str:
    orig_lines = original_code.splitlines()
    refact_lines = refactored_code.splitlines()

    differ = difflib.HtmlDiff(tabsize=4, wrapcolumn=60)
    diff_table = differ.make_table(
        orig_lines,
        refact_lines,
        fromdesc="Original Vulnerable Code",
        todesc="AI Auto-Refactored Fix",
        context=True,
        numlines=3
    )

    custom_style = """
    <style>
        table.diff {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            width: 100%;
            border-collapse: collapse;
            border: 1px solid #30363d;
            border-radius: 8px;
            overflow: hidden;
            margin-top: 10px;
        }
        table.diff td, table.diff th {
            padding: 4px 8px;
            vertical-align: top;
        }
        table.diff th {
            background-color: #161b22;
            color: #c9d1d9;
            text-align: left;
            border-bottom: 2px solid #30363d;
        }
        .diff_header {
            background-color: #21262d;
            color: #8b949e;
            text-align: right;
            user-select: none;
            width: 35px;
        }
        .diff_next {
            background-color: #21262d;
            display: none;
        }
        .diff_add {
            background-color: rgba(46, 160, 67, 0.25);
            color: #3fb950;
        }
        .diff_chg {
            background-color: rgba(218, 54, 51, 0.25);
            color: #f85149;
        }
        .diff_sub {
            background-color: rgba(218, 54, 51, 0.25);
            color: #f85149;
        }
    </style>
    """
    return f"{custom_style}{diff_table}"

# Helper: Generate Exportable Markdown Report
def generate_markdown_report(data: dict, original_code: str, policy: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_refactor = data.get("refactored_code", "").strip()
    safe_policy = policy.strip() if policy and policy.strip() else "Standard Corporate Coding Guidelines Applied."

    report_lines = [
        "# 🛡️ Security Audit & Code Review Report",
        f"**Generated on:** `{timestamp}`  ",
        f"**Code Health Score:** `{data.get('overall_score', 'N/A')}/100`",
        "",
        "---",
        "",
        "## 📄 Executive Summary",
        f"{data.get('summary', 'No summary provided.')}",
        "",
        "---",
        "",
        "## 📚 Applicable Policy Standards (RAG Retrieved)",
        "```markdown",
        safe_policy,
        "```",
        "",
        "---",
        "",
        "## 🐛 Identified Flaws & Annotations"
    ]

    annotations = data.get("annotations", [])
    if annotations:
        for ann in annotations:
            line = "N/A"
            comment = ""
            if isinstance(ann, dict):
                line = ann.get("line", "N/A")
                comment = ann.get("flaw") or ann.get("comment", "")
            else:
                line = getattr(ann, "line", "N/A")
                comment = getattr(ann, "flaw", None) or getattr(ann, "comment", "")
            report_lines.append(f"- **Line {line}:** {comment}")
    else:
        report_lines.append("- No specific line annotations reported.")

    report_lines.extend([
        "",
        "---",
        "",
        "## 📝 Original Source Code",
        "```python",
        original_code,
        "```",
        "",
        "---",
        "",
        "## 🚀 Recommended Refactored Fix",
        "```python",
        clean_refactor if clean_refactor else "# No refactoring required.",
        "```"
    ])

    return "\n".join(report_lines)

# Initialize Chat History in Session State
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

# Tabs
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
        code_input = st.text_area("Source Code (Python)", value=sample_code, height=320)
        run_button = st.button("🚀 Run Security Audit", type="primary", use_container_width=True)

    with col2:
        st.subheader("🔍 Security Audit Results")

        if run_button:
            if not os.getenv("GOOGLE_API_KEY"):
                st.error("API Key not found! Please check your environment variables or Streamlit secrets.")
            else:
                with st.spinner("Retrieving RAG policies & running AI code audit..."):
                    try:
                        # 1. Retrieve RAG Policy Context
                        retrieved_policy = retrieve_relevant_rules(code_input)
                        if not retrieved_policy or not retrieved_policy.strip():
                            if os.path.exists("company_rules.md"):
                                with open("company_rules.md", "r", encoding="utf-8") as f:
                                    retrieved_policy = f.read()

                        # 2. Simulated Diff
                        fake_diff = f"""
diff --git a/input_code.py b/input_code.py
new file mode 100644
--- /dev/null
+++ b/input_code.py
@@ -0,0 +1,10 @@
+{code_input}
"""
                        # 3. Prompt with RAG
                        system_prompt = (
                            "You are an expert Security Engineer and Tech Lead.\n"
                            "Review code diffs against general SAST practices AND the following internal company rules:\n\n"
                            f"--- INTERNAL COMPANY POLICIES ---\n{retrieved_policy}\n-----------------------------------\n\n"
                            "Return clean structured output with health score, summary explanation, line-by-line annotations, and refactored_code."
                        )

                        agent = Agent('google:gemini-2.5-flash', system_prompt=system_prompt)

                        async def run_review():
                            prompt = f"Review this code diff:\n\n```diff\n{fake_diff}\n```"
                            try:
                                res = await agent.run(prompt, result_type=PRReviewPayload)
                            except TypeError:
                                res = await agent.run(prompt)
                            return getattr(res, "data", None) or getattr(res, "output", None)

                        raw_review_data = asyncio.run(run_review())
                        data = parse_review_output(raw_review_data)

                        # Save to Session State
                        st.session_state["review_data"] = data
                        st.session_state["original_code"] = code_input
                        st.session_state["retrieved_policy"] = retrieved_policy
                        st.session_state["chat_messages"] = []

                    except Exception as e:
                        st.error(f"Audit failed: {str(e)}")

        # Render Review Results from Session State
        if "review_data" in st.session_state:
            data = st.session_state["review_data"]
            score = data.get("overall_score", 100)

            if score >= 80:
                st.success(f"### Code Health Score: {score}/100 ✅")
            elif score >= 50:
                st.warning(f"### Code Health Score: {score}/100 ⚠️")
            else:
                st.error(f"### Code Health Score: {score}/100 🚨")

            with st.expander("📚 Retrieved Company Policy Guidelines (RAG Context)"):
                st.markdown(st.session_state.get("retrieved_policy", ""))

            st.markdown("#### 📄 Executive Summary")
            st.markdown(data.get("summary", "No summary provided."))

            annotations = data.get("annotations", [])
            if annotations:
                st.markdown("#### 🐛 Identified Flaws & Annotations")
                for ann in annotations:
                    line = "N/A"
                    comment = ""
                    if isinstance(ann, dict):
                        line = ann.get("line", "N/A")
                        comment = ann.get("flaw") or ann.get("comment", "")
                    else:
                        line = getattr(ann, "line", "N/A")
                        comment = getattr(ann, "flaw", None) or getattr(ann, "comment", "")
                    st.warning(f"**Line {line}:** {comment}")

            # Download Report Button
            report_md = generate_markdown_report(data, st.session_state["original_code"], st.session_state.get("retrieved_policy", ""))
            st.download_button(
                label="📥 Download Security Audit Report (.md)",
                data=report_md,
                file_name="security_audit_report.md",
                mime="text/markdown",
                use_container_width=True
            )

    # Full-Width Side-by-Side Diff Section
    if "review_data" in st.session_state and st.session_state["review_data"].get("refactored_code"):
        st.markdown("---")
        st.subheader("🔍 Side-by-Side Visual Diff (Before vs. After)")
        diff_html = generate_side_by_side_diff(
            st.session_state["original_code"],
            st.session_state["review_data"]["refactored_code"]
        )
        st.components.v1.html(diff_html, height=350, scrolling=True)

        # Interactive Follow-Up Chat Section
        st.markdown("---")
        st.subheader("💬 Ask AI Security Lead (Follow-Up Questions)")
        st.caption("Ask questions about this vulnerability, alternatives, or implementation details.")

        for msg in st.session_state["chat_messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if user_prompt := st.chat_input("e.g., How would I write this using SQLAlchemy ORM instead?"):
            st.session_state["chat_messages"].append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.markdown(user_prompt)

            chat_context = (
                f"You are a helpful Security Engineer assisting a developer with code they just submitted.\n"
                f"Original Code:\n{st.session_state['original_code']}\n\n"
                f"AI Refactored Fix:\n{st.session_state['review_data'].get('refactored_code', '')}\n\n"
                f"Retrieved Company Policies:\n{st.session_state.get('retrieved_policy', '')}\n\n"
                f"Answer the developer's question accurately, concisely, and with secure code examples if requested."
            )

            chat_agent = Agent('google:gemini-2.5-flash', system_prompt=chat_context)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    async def get_chat_response():
                        res = await chat_agent.run(user_prompt)
                        return getattr(res, "data", None) or getattr(res, "output", str(res))

                    bot_reply = asyncio.run(get_chat_response())
                    st.markdown(bot_reply)
                    st.session_state["chat_messages"].append({"role": "assistant", "content": bot_reply})

with tab2:
    st.subheader("📊 Repository & Scanning Metrics")
    m1, m2, m3 = st.columns(3)
    m1.metric(label="Total Audits Executed", value="18", delta="+2 recent")
    m2.metric(label="Vulnerabilities Blocked", value="34", delta="+2 critical")
    m3.metric(label="Average Health Score", value="84/100", delta="+3%")