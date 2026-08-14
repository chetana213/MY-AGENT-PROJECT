# 🛡️ SecureCode AI — AI-Powered Code Security & Refactoring Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/Model-Gemini%202.5%20Flash-orange.svg)](https://deepmind.google/technologies/gemini/)
[![LangChain RAG](https://img.shields.io/badge/RAG-ChromaDB-green.svg)](https://www.langchain.com/)

**SecureCode AI** is an enterprise-grade developer security and automated code refactoring platform. It leverages **Google Gemini 2.5 Flash**, **LangChain Chroma RAG**, and **Pydantic AI** to perform automated static application security testing (SAST), enforce internal corporate coding policies, validate AST syntax, and auto-remediate vulnerabilities.

---

## ✨ Key Features

- **⚡ Multi-Agent Security Pipeline:** End-to-end analysis encompassing static scanning, semantic policy compliance, targeted refactoring, and post-fix re-scan verification.
- **📚 Policy Intelligence via RAG:** Matches user-submitted code against internal security policies (`company_rules.md`) stored in a local Chroma vector database.
- **🔄 Dedicated Auto-Refactoring:** Generates clean, minimal, runnable Python remediations that fix security flaws while strictly preserving original business logic.
- **🔍 AST Syntax & Re-scan Validation:** Validates generated refactorings using Python `ast.parse` and re-scans the fix to confirm verified vulnerability resolution.
- **⚖️ Side-by-Side Visual Diff:** Clean before-and-after comparison highlighting security remediations.
- **💬 Interactive AI Security Lead:** Context-aware assistant that answers follow-up architectural and vulnerability questions based on real scan data.
- **📊 Real-time Session Telemetry:** Dynamic dashboard tracking audits executed, vulnerabilities blocked, and health scores across runs.
- **📥 One-Click Markdown Reports:** Export detailed compliance and audit reports with a single click.

---

## 🏗️ Architecture & Pipeline Flow

[ User Python Code ]
│
▼
[ AST Syntax Validation ]
│
▼
[ RAG Policy Retrieval (ChromaDB) ] ──▶ [ company_rules.md ]
│
▼
[ SAST Security Analysis Agent (Gemini 2.5 Flash) ]
│
├─▶ [ Structured FindingItems (Severity, Line, Policy) ]
└─▶ [ Deterministic Score Calculation ]
│
▼
[ Clean Refactoring Agent ]
│
▼
[ AST Syntax Verification (ast.parse) ]
│
▼
[ Security Re-scan Verification Agent ] ──▶ [ Verified Fixes Count ]
│
├─▶ [ Side-by-Side Unified Diff ]
├─▶ [ Interactive AI Security Lead Context ]
└─▶ [ Exportable Markdown Audit Report ]


---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- A Google Gemini API Key ([Get an API Key](https://aistudio.google.com/))

### 2. Clone the Repository
```bash
git clone [https://github.com/](https://github.com/)<your-username>/<your-repo-name>.git
cd <your-repo-name>
3. Set Up Virtual Environment
Bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
4. Install Dependencies
Bash
pip install -r requirements.txt
5. Configure Environment Variables
Create a .env file in the project root:

Code snippet
GOOGLE_API_KEY=your_gemini_api_key_here
6. Run the Application
Bash
streamlit run app.py
📂 Project Structure
.
├── app.py              # Streamlit UI & Dashboard Interface
├── services.py         # Multi-Agent Security Engine & Pipeline Logic
├── schemas.py          # Pydantic Data Models (Findings, Payloads)
├── rag_engine.py       # LangChain + ChromaDB RAG Policy Retriever
├── company_rules.md    # Internal Corporate Security & Engineering Guidelines
├── requirements.txt    # Project Dependencies
└── README.md           # Project Documentation
