import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pydantic_ai import Agent
from schemas import PRReviewPayload

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: API Key missing in .env file!")
    sys.exit(1)

MODEL_NAME = 'google:gemini-2.5-flash'

annotation_agent = Agent(
    MODEL_NAME,
    system_prompt=(
        "You are an expert Security Engineer and Tech Lead reviewing pull request code diffs.\n"
        "Inspect the provided diff and identify line-specific security flaws, performance bottlenecks, or clean code issues.\n"
        "For each issue, specify the exact file path, target line number, and a clear comment proposing a fix.\n"
        "Crucially, provide the COMPLETE, FULLY REFACTORED and secure Python source code in the 'refactored_code' field."
    )
)

async def main():
    diff_file = Path("pr_diff.txt")
    if diff_file.exists() and diff_file.stat().st_size > 0:
        code_diff = diff_file.read_text(encoding="utf-8")
    else:
        code_diff = """
diff --git a/vulnerable_sample.py b/vulnerable_sample.py
new file mode 100644
--- /dev/null
+++ b/vulnerable_sample.py
@@ -0,0 +1,7 @@
+import sqlite3
+
+def get_user_data(user_id):
+    conn = sqlite3.connect("database.db")
+    query = f"SELECT * FROM users WHERE id = '{user_id}'"
+    return conn.execute(query).fetchall()
"""

    prompt = f"Perform a line-by-line review on this git diff and provide the complete refactored code fix:\n\n```diff\n{code_diff}\n```"
    
    try:
        result = await annotation_agent.run(prompt, result_type=PRReviewPayload)
    except TypeError:
        result = await annotation_agent.run(prompt)

    output_data = getattr(result, "data", None) or getattr(result, "output", None)
    
    # Save the refactored code to disk if present
    if hasattr(output_data, "refactored_code") and output_data.refactored_code:
        Path("refactored_patch.py").write_text(output_data.refactored_code, encoding="utf-8")

    if hasattr(output_data, "model_dump"):
        print(json.dumps(output_data.model_dump(), indent=2))
    elif isinstance(output_data, dict):
        print(json.dumps(output_data, indent=2))
    else:
        mock_payload = PRReviewPayload(
            overall_score=75,
            summary=str(output_data or result),
            annotations=[]
        )
        print(json.dumps(mock_payload.model_dump(), indent=2))

if __name__ == "__main__":
    asyncio.run(main())