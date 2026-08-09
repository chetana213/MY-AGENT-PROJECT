import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

DB_DIR = "./chroma_db"
RULES_FILE = "company_rules.md"

def retrieve_relevant_rules(code_query: str, k: int = 2) -> str:
    """
    Retrieves top-k relevant company rules for a code snippet.
    Uses ChromaDB vector store when available, with graceful fallback to raw rules text.
    """
    rule_path = Path(RULES_FILE)
    if not rule_path.exists():
        return "No specific company policies retrieved."

    rule_content = rule_path.read_text(encoding="utf-8")

    try:
        from langchain_chroma import Chroma
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=api_key
        )

        if os.path.exists(DB_DIR) and os.path.exists(os.path.join(DB_DIR, "chroma.sqlite3")):
            vectorstore = Chroma(
                persist_directory=DB_DIR,
                embedding_function=embeddings
            )
        else:
            if os.path.exists(DB_DIR):
                shutil.rmtree(DB_DIR, ignore_errors=True)

            documents = [Document(page_content=rule_content, metadata={"source": RULES_FILE})]
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=40)
            chunks = text_splitter.split_documents(documents)

            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=DB_DIR
            )

        docs = vectorstore.similarity_search(code_query, k=k)
        return "\n\n".join([doc.page_content for doc in docs])

    except Exception:
        return rule_content

if __name__ == "__main__":
    sample_code = "query = f'SELECT * FROM users WHERE id = {user_id}'"
    print("🔍 Retrieved Context:\n")
    print(retrieve_relevant_rules(sample_code))
