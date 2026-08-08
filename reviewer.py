import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_ai import Agent

# 1. Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: API Key missing in .env file!")
    exit(1)

MODEL_NAME = 'google:gemini-2.5-flash'

# 2. Define the agent
reviewer_agent = Agent(
    MODEL_NAME,
    system_prompt=(
        "You are an expert Security Engineer and Tech Lead. "
        "Perform a comprehensive audit of the code across 3 dimensions:\n"
        "1. SECURITY: OWASP vulnerabilities, hardcoded secrets, injection risks.\n"
        "2. PERFORMANCE: Time/space complexity (e.g., O(N^2) loops), memory leaks.\n"
        "3. CODE QUALITY: Naming, exception handling, and clean code standards.\n\n"
        "Assign an overall code health score (0-100) and provide a formatted Markdown PR review comment with fixes."
    )
)

async def main():
    bad_code_sample = """
import sqlite3

API_KEY = "AIzaSySecretApiKey1234567890"

def fetch_user(user_id):
    conn = sqlite3.connect("database.db")
    # Vulnerable to SQL Injection
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return conn.execute(query).fetchall()

def find_duplicates(numbers):
    # Inefficient O(N^2) complexity
    dups = []
    for i in range(len(numbers)):
        for j in range(len(numbers)):
            if i != j and numbers[i] == numbers[j]:
                dups.append(numbers[i])
    return dups
"""

    print("⚡ Running Code Audit via Pydantic AI...")
    prompt = f"Audit this code:\n\n```python\n{bad_code_sample}\n```"
    
    result = await reviewer_agent.run(prompt)
    
    print("\n" + "="*50)
    print(" FINAL CODE REVIEW REPORT")
    print("="*50 + "\n")
    
    # Safe attribute extraction across pydantic-ai versions
    output_text = getattr(result, "output", None) or getattr(result, "content", None) or getattr(result, "data", str(result))
    print(output_text)

if __name__ == "__main__":
    asyncio.run(main())