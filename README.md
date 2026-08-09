# Multi-Agent AI Code Reviewer & SAST Shield

An automated, multi-agent AI code review platform powered by **Google Gemini** and **Pydantic AI**. It performs continuous security audits, static analysis synthesis (Bandit), line-by-line pull request annotations via GitHub Actions, and local pre-commit guard checks.

---

## Features

- **Hybrid SAST Analysis:** Integrates **Bandit** static analysis with **Gemini 2.5 Flash** to eliminate false positives and provide actionable code fixes.
- **Inline PR Annotations:** Automatically posts line-specific comments on GitHub Pull Requests via Octokit and GitHub Actions.
- **Local Git Pre-Commit Hook:** Intercepts `git commit` commands locally and blocks code with security health scores below 50/100.
- **Structured Pydantic Output:** Ensures standardized JSON audit payloads for reports and CI/CD pipelines.

---

## Tech Stack

- **AI Framework:** Pydantic AI
- **LLM Engine:** Google Gemini (`gemini-2.5-flash`)
- **Static Analysis:** Bandit
- **CI/CD:** GitHub Actions & GitHub Octokit API
- **Language:** Python 3.11+

---

## Quickstart & Local Setup

### 1. Clone & Setup Virtual Environment
```bash
git clone [https://github.com/chetana213/MY-AGENT-PROJECT.git](https://github.com/chetana213/MY-AGENT-PROJECT.git)
cd MY-AGENT-PROJECT

python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
