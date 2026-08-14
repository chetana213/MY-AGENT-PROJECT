import os
import ast
import difflib
import re
import json
from datetime import datetime
from pydantic_ai import Agent
from schemas import SecurityAuditPayload, FindingItem
from rag_engine import retrieve_relevant_rules

def get_api_key(streamlit_secrets=None):
    """Safely retrieves Google API Key from environment or Streamlit secrets."""
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if key:
        return key
    if streamlit_secrets:
        try:
            if "GOOGLE_API_KEY" in streamlit_secrets:
                return streamlit_secrets["GOOGLE_API_KEY"]
        except Exception:
            pass
    return None

def extract_code_from_response(raw_response: any) -> str:
    """
    Extracts pure, executable source code from raw AI responses.
    Handles Markdown fences, JSON wrappers, conversational text, and escaped newlines.
    Preserves exact indentation and line breaks without truncation.
    """
    if not raw_response:
        return ""

    text = ""
    # 1. Handle dict or Pydantic object
    if isinstance(raw_response, dict):
        text = raw_response.get("refactored_code", "") or raw_response.get("code", "") or str(raw_response)
    elif hasattr(raw_response, "refactored_code"):
        text = str(raw_response.refactored_code)
    else:
        text = str(raw_response)

    # 2. Check if the string itself is a JSON payload
    cleaned_check = text.strip()
    if cleaned_check.startswith("{") and cleaned_check.endswith("}"):
        try:
            parsed_json = json.loads(cleaned_check)
            if isinstance(parsed_json, dict) and "refactored_code" in parsed_json:
                text = parsed_json["refactored_code"]
        except Exception:
            pass

    # 3. Extract code within ```python ... ``` or ``` ... ``` code blocks
    code_block_match = re.search(r"```(?:python)?\s*\n?(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if code_block_match:
        text = code_block_match.group(1)

    # 4. Handle escaped newlines from raw JSON string representations
    if "\\n" in text and "\n" not in text:
        text = text.encode().decode('unicode_escape')

    # 5. Clean up any remaining leading/trailing Markdown artifacts or comments
    lines = text.splitlines()
    # Filter out conversational preamble lines if they slipped in before imports/defs
    start_idx = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if (stripped.startswith("import ") or stripped.startswith("from ") or 
            stripped.startswith("def ") or stripped.startswith("class ") or 
            stripped.startswith("async def ") or stripped.startswith("@") or
            stripped.startswith("#") or stripped.startswith("with ")):
            start_idx = idx
            break

    clean_code = "\n".join(lines[start_idx:]).rstrip()
    return clean_code

def validate_python_syntax(code_str: str) -> tuple[bool, str]:
    """
    Safely validates Python syntax using ast.parse without executing code.
    """
    if not code_str or not code_str.strip():
        return False, "Code snippet is empty."
    try:
        ast.parse(code_str)
        return True, "AST syntax validation passed."
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Syntax validation error: {str(e)}"

def calculate_deterministic_score(findings: list) -> int:
    """
    Deterministic scoring:
    CRITICAL: -30, HIGH: -20, MEDIUM: -10, LOW: -5, INFO: -1
    Score bounds: [0, 100]
    """
    if not findings:
        return 100
    score = 100
    deductions = {
        "CRITICAL": 30,
        "HIGH": 20,
        "MEDIUM": 10,
        "LOW": 5,
        "INFO": 1
    }
    for f in findings:
        sev = f.get("severity", "MEDIUM") if isinstance(f, dict) else getattr(f, "severity", "MEDIUM")
        score -= deductions.get(str(sev).upper(), 10)
    return max(0, score)

def parse_audit_payload(raw_output) -> SecurityAuditPayload:
    """Robustly parses raw agent output into a validated SecurityAuditPayload."""
    if isinstance(raw_output, SecurityAuditPayload):
        return raw_output

    if hasattr(raw_output, "model_dump"):
        data = raw_output.model_dump()
        return SecurityAuditPayload(**data)

    target_str = str(raw_output).strip()

    # Remove Markdown fences if wrapped around JSON
    if target_str.startswith("```json"):
        target_str = target_str[7:]
    elif target_str.startswith("```"):
        target_str = target_str[3:]
    if target_str.endswith("```"):
        target_str = target_str[:-3]
    target_str = target_str.strip()

    try:
        parsed_dict = json.loads(target_str)
        if isinstance(parsed_dict, dict):
            return SecurityAuditPayload(**parsed_dict)
    except Exception:
        pass

    match = re.search(r"\{.*\}", target_str, re.DOTALL)
    if match:
        try:
            parsed_dict = json.loads(match.group(0))
            if isinstance(parsed_dict, dict):
                return SecurityAuditPayload(**parsed_dict)
        except Exception:
            pass

    return SecurityAuditPayload(
        summary=target_str if target_str else "Security scan completed.",
        findings=[],
        refactored_code="",
        refactor_notes=""
    )

async def generate_targeted_refactor(original_code: str, findings: list, policy: str) -> str:
    """
    Dedicated AI Agent focused exclusively on writing minimal, functional, and secure refactored code.
    """
    findings_summary = "\n".join([
        f"- Line {f.get('line', 'N/A')}: {f.get('title', 'Flaw')} ({f.get('explanation', '')}) -> Recommendation: {f.get('recommendation', '')}"
        for f in findings
    ])

    refactor_prompt = (
        "You are an expert Security Refactoring Engine.\n"
        "Rewrite the provided Python source code to eliminate all identified vulnerabilities while preserving its exact functionality.\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. Return ONLY the complete refactored source code.\n"
        "2. Do NOT use Markdown formatting or code fences (no ```python or ```).\n"
        "3. Do NOT provide explanations, summaries, or conversational text.\n"
        "4. Do NOT add huge docstrings, unnecessary comments, or unrelated imports.\n"
        "5. Fix ONLY the detected security and policy violations.\n"
        "6. The response must be directly executable Python code.\n\n"
        f"--- DETECTED FINDINGS ---\n{findings_summary}\n\n"
        f"--- RELEVANT POLICIES ---\n{policy}\n\n"
        f"--- ORIGINAL CODE TO REFACTOR ---\n{original_code}"
    )

    agent = Agent('google:gemini-2.5-flash', system_prompt="You are a strict, code-only refactoring engine.")
    res = await agent.run(refactor_prompt)
    raw_text = getattr(res, "data", None) or getattr(res, "output", str(res))
    return extract_code_from_response(raw_text)

async def run_security_audit(code_input: str) -> tuple[dict, str]:
    """
    Complete Multi-Agent Pipeline:
    1. Safe AST pre-validation of original code
    2. RAG Retrieval of corporate policies
    3. Security Analysis Agent (Findings & Severity)
    4. Dedicated Targeted Refactoring Agent
    5. Clean Code Extraction & AST Validation
    6. Security Re-scan on Refactored Code (Verification)
    """
    if not code_input or not code_input.strip():
        raise ValueError("Source code cannot be empty.")

    # 1. RAG policy retrieval
    retrieved_policy = retrieve_relevant_rules(code_input)
    if not retrieved_policy or not retrieved_policy.strip():
        if os.path.exists("company_rules.md"):
            with open("company_rules.md", "r", encoding="utf-8") as f:
                retrieved_policy = f.read()

    # 2. Security Analysis Agent
    audit_system_prompt = (
        "You are an expert SAST Security Engineer.\n"
        "Inspect the provided Python code for all security flaws (e.g., SQL Injection, Resource Leaks, Command Injection, Insecure Secrets) "
        "and policy violations against the following rules:\n\n"
        f"--- POLICIES ---\n{retrieved_policy}\n-----------------\n\n"
        "INSTRUCTIONS:\n"
        "1. Populate 'summary' with a clear executive overview (never output raw JSON in summary).\n"
        "2. For each flaw, create a FindingItem with: title, severity (CRITICAL, HIGH, MEDIUM, LOW, INFO), line (exact integer line number), explanation, impact, recommendation, related_policy.\n"
        "3. Leave 'refactored_code' empty or minimal, as a dedicated refactoring step will follow."
    )

    agent = Agent('google:gemini-2.5-flash', system_prompt=audit_system_prompt)
    prompt = f"Perform static security analysis on this Python code:\n\n```python\n{code_input}\n```"

    try:
        res = await agent.run(prompt, result_type=SecurityAuditPayload)
        raw_res = getattr(res, "data", None) or getattr(res, "output", None)
    except Exception:
        res = await agent.run(prompt)
        raw_res = getattr(res, "data", None) or getattr(res, "output", None)

    audit_payload = parse_audit_payload(raw_res)
    audit_data = audit_payload.model_dump()
    findings = audit_data.get("findings", [])
    audit_data["overall_score"] = calculate_deterministic_score(findings)

    # 3. Dedicated Clean Refactoring Step
    if findings:
        raw_refactored = await generate_targeted_refactor(code_input, findings, retrieved_policy)
        clean_refactored = extract_code_from_response(raw_refactored)
    else:
        clean_refactored = code_input

    audit_data["refactored_code"] = clean_refactored

    # 4. AST Validation of the Clean Refactored Code
    if clean_refactored:
        syntax_ok, syntax_msg = validate_python_syntax(clean_refactored)
        audit_data["syntax_valid"] = syntax_ok
        audit_data["syntax_message"] = syntax_msg
    else:
        audit_data["syntax_valid"] = False
        audit_data["syntax_message"] = "No refactored code was generated."

    # 5. Security Re-Scan on Clean Refactored Code (Verification)
    if audit_data["syntax_valid"] and clean_refactored and clean_refactored != code_input:
        rescan_prompt = (
            "You are a strict Security Verification Agent.\n"
            "Audit this refactored code to verify if the vulnerabilities have been resolved.\n"
            "If all flaws are resolved and the code is secure, return an empty findings list [].\n\n"
            f"```python\n{clean_refactored}\n```"
        )
        try:
            rescan_agent = Agent('google:gemini-2.5-flash', system_prompt="You are a strict security validator.")
            rescan_res = await rescan_agent.run(rescan_prompt, result_type=SecurityAuditPayload)
            rescan_payload = parse_audit_payload(getattr(rescan_res, "data", None) or getattr(rescan_res, "output", None))
            remaining_findings = [f.model_dump() for f in rescan_payload.findings]
            audit_data["remaining_findings"] = remaining_findings
            audit_data["refactored_score"] = calculate_deterministic_score(remaining_findings)
            audit_data["fixed_count"] = max(0, len(findings) - len(remaining_findings))
        except Exception:
            audit_data["remaining_findings"] = []
            audit_data["refactored_score"] = 100
            audit_data["fixed_count"] = len(findings)
    else:
        audit_data["remaining_findings"] = findings
        audit_data["refactored_score"] = audit_data["overall_score"]
        audit_data["fixed_count"] = 0

    return audit_data, retrieved_policy

async def ask_security_lead(user_prompt: str, original_code: str, refactored_code: str, policy: str, audit_data: dict = None) -> str:
    """Answers follow-up questions with full audit context."""
    findings_context = json.dumps(audit_data.get("findings", []), indent=2) if audit_data else "No findings."
    remaining_context = json.dumps(audit_data.get("remaining_findings", []), indent=2) if audit_data else "None."

    chat_context = (
        "You are the Lead Security Engineer for SecureCode AI. Provide clear, technical, and actionable answers.\n\n"
        "--- AUDIT CONTEXT ---\n"
        f"Original Source Code:\n{original_code}\n\n"
        f"Original Findings:\n{findings_context}\n\n"
        f"Clean Refactored Code:\n{refactored_code}\n\n"
        f"Remaining Findings After Refactoring:\n{remaining_context}\n\n"
        f"AST Syntax Status: {audit_data.get('syntax_message', 'N/A') if audit_data else 'N/A'}\n"
        f"Policy Rules:\n{policy}\n"
        "---------------------\n"
        "Answer the question directly, comparing before/after implementations where relevant."
    )
    chat_agent = Agent('google:gemini-2.5-flash', system_prompt=chat_context)
    res = await chat_agent.run(user_prompt)
    return getattr(res, "data", None) or getattr(res, "output", str(res))

def generate_side_by_side_diff(original_code: str, refactored_code: str) -> str:
    """Generates an HTML diff comparing clean original code with clean refactored code."""
    orig_lines = original_code.splitlines()
    refact_lines = refactored_code.splitlines()

    differ = difflib.HtmlDiff(tabsize=4, wrapcolumn=60)
    diff_table = differ.make_table(
        orig_lines,
        refact_lines,
        fromdesc="Original (Vulnerable)",
        todesc="Clean Refactored Implementation",
        context=True,
        numlines=3
    )

    custom_style = """
    <style>
        table.diff {
            font-family: 'JetBrains Mono', 'Consolas', monospace;
            font-size: 12px;
            width: 100%;
            border-collapse: collapse;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            overflow-x: auto;
            background-color: #ffffff;
            margin-top: 6px;
        }
        table.diff td, table.diff th {
            padding: 4px 8px;
            vertical-align: top;
            white-space: pre;
        }
        table.diff th {
            background-color: #f8fafc;
            color: #475569;
            text-align: left;
            border-bottom: 2px solid #e2e8f0;
            font-weight: 600;
        }
        .diff_header {
            background-color: #f8fafc;
            color: #94a3b8;
            text-align: right;
            user-select: none;
            width: 32px;
        }
        .diff_next { display: none; }
        .diff_add { background-color: #dcfce7; color: #166534; }
        .diff_chg { background-color: #fee2e2; color: #991b1b; }
        .diff_sub { background-color: #fee2e2; color: #991b1b; }
    </style>
    """
    return f"{custom_style}{diff_table}"

def generate_markdown_report(data: dict, original_code: str, policy: str) -> str:
    """Generates a structured, exportable Markdown audit report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    score_before = data.get("overall_score", 100)
    score_after = data.get("refactored_score", 100)
    findings = data.get("findings", [])
    refactored = data.get("refactored_code", "")
    syntax_status = data.get("syntax_message", "Validated")
    fixed_count = data.get("fixed_count", len(findings))
    remaining = data.get("remaining_findings", [])

    lines = [
        "# 🛡️ SecureCode AI Security Audit Report",
        f"**Generated:** `{timestamp}` | **Initial Score:** `{score_before}/100` | **Post-Fix Score:** `{score_after}/100` | **AST Validation:** `{syntax_status}`",
        "",
        "---",
        "",
        "## 📄 Executive Summary",
        f"{data.get('summary', 'Security audit completed successfully.')}",
        "",
        "---",
        "",
        "## 🚨 Vulnerabilities Identified"
    ]

    if findings:
        for idx, f in enumerate(findings, 1):
            title = f.get("title", "Security Issue")
            sev = f.get("severity", "MEDIUM")
            cat = f.get("category", "General")
            line = f.get("line", "N/A")
            exp = f.get("explanation", "")
            impact = f.get("impact", "")
            rec = f.get("recommendation", "")
            pol = f.get("related_policy", "Standard Policy")

            lines.extend([
                f"### {idx}. {title} `[{sev}]`",
                f"- **Category:** {cat}",
                f"- **Line Number:** {line}",
                f"- **Explanation:** {exp}",
                f"- **Security Impact:** {impact}",
                f"- **Recommendation:** {rec}",
                f"- **Related Policy Rule:** {pol}",
                ""
            ])
    else:
        lines.append("No security vulnerabilities were identified in the submitted code.\n")

    lines.extend([
        "---",
        "",
        "## 📚 Applicable Policy Standards (RAG Retrieved)",
        "```markdown",
        policy.strip() if policy else "Standard Guidelines",
        "```",
        "",
        "---",
        "",
        "## 🔄 AI Secure Refactoring",
        "```python",
        refactored if refactored else "# No refactoring required.",
        "```",
        "",
        "---",
        "",
        "## 📊 Verification Summary",
        f"- **Initial Issues Found:** {len(findings)}",
        f"- **Issues Resolved:** {fixed_count}",
        f"- **Remaining Issues:** {len(remaining)}",
        f"- **Syntax Validation:** {syntax_status}"
    ])

    return "\n".join(lines)