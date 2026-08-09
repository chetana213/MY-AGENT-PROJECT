import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pydantic_ai import Agent

from schemas import PRReviewPayload
from rag_engine import retrieve_relevant_rules

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: API Key missing in .env file!")
    sys.exit(1)

MODEL_NAME = 'google:gemini-2.5-flash'

async def main():
    diff_file = Path("pr_diff.txt")
    if diff_file.exists() and diff_file.stat().st_size > 0:
        code_diff = diff_file.read_text(encoding="utf-8")
    else:
        code_diff = """import sqlite3
def get_user_data(user_id):
    conn = sqlite3.connect("database.db")
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    return conn.execute(query).fetchall()
"""

    # Retrieve relevant internal security policies via LangChain RAG
    policy_context = retrieve_relevant_rules(code_diff)

    # Inject policy context into the dynamic system prompt
    dynamic_system_prompt = (
        "You are an expert Security Engineer and Tech Lead.\n"
        "Review code diffs against general SAST practices AND the following internal company rules:\n\n"
        f"--- INTERNAL COMPANY POLICIES ---\n{policy_context}\n-----------------------------------\n\n"
        "Identify flaws, target line numbers, and provide the fully refactored code in 'refactored_code'."
    )

    agent = Agent(MODEL_NAME, system_prompt=dynamic_system_prompt)
    prompt = f"Review this code diff:\n\n```python\n{code_diff}\n```"

    try:
        result = await agent.run(prompt, result_type=PRReviewPayload)
    except TypeError:
        result = await agent.run(prompt)

    output_data = getattr(result, "data", None) or getattr(result, "output", None)
    
    if hasattr(output_data, "refactored_code") and output_data.refactored_code:
        Path("refactored_patch.py").write_text(output_data.refactored_code, encoding="utf-8")

    if hasattr(output_data, "model_dump"):
        print(json.dumps(output_data.model_dump(), indent=2))

if __name__ == "__main__":
    asyncio.run(main())