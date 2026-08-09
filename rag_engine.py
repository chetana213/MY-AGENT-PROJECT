import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

DB_DIR = "./chroma_db"
RULES_FILE = "company_rules.md"

def get_embeddings_model():
    """Initializes Google Gemini Embeddings using active model gemini-embedding-001."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        google_api_key=api_key
    )

def build_or_load_vectorstore():
    """Indexes company_rules.md into ChromaDB using Gemini embeddings."""
    embeddings = get_embeddings_model()

    if os.path.exists(DB_DIR) and os.path.exists(os.path.join(DB_DIR, "chroma.sqlite3")):
        vectorstore = Chroma(
            persist_directory=DB_DIR,
            embedding_function=embeddings
        )
    else:
        # Clear out any incomplete or corrupted DB folder
        if os.path.exists(DB_DIR):
            shutil.rmtree(DB_DIR, ignore_errors=True)

        rule_path = Path(RULES_FILE)
        if not rule_path.exists():
            raise FileNotFoundError(f"{RULES_FILE} not found in root directory!")
        
        content = rule_path.read_text(encoding="utf-8")
        documents = [Document(page_content=content, metadata={"source": RULES_FILE})]

        # Chunk text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=40
        )
        chunks = text_splitter.split_documents(documents)

        # Build and persist Chroma index
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=DB_DIR
        )

    return vectorstore

def retrieve_relevant_rules(code_query: str, k: int = 2) -> str:
    """Retrieves top-k relevant company rules for a code snippet."""
    try:
        vectorstore = build_or_load_vectorstore()
        docs = vectorstore.similarity_search(code_query, k=k)
        retrieved_rules = "\n\n".join([doc.page_content for doc in docs])
        return retrieved_rules
    except Exception as e:
        print(f"Warning: RAG retrieval skipped ({e})")
        return "No specific company policies retrieved."

if __name__ == "__main__":
    print("⚡ Testing RAG retrieval with Gemini embeddings...")
    sample_code = "query = f'SELECT * FROM users WHERE id = {user_id}'"
    rules = retrieve_relevant_rules(sample_code)
    print("\n🔍 Retrieved Context:\n")
    print(rules)