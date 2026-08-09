import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

DB_DIR = "./chroma_db"
RULES_FILE = "company_rules.md"

def build_or_load_vectorstore():
    """Indexes company_rules.md into ChromaDB using Gemini embeddings."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    # Initialize Google Gemini Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=api_key
    )

    if os.path.exists(DB_DIR):
        # Load existing vector index from disk
        vectorstore = Chroma(
            persist_directory=DB_DIR,
            embedding_function=embeddings
        )
    else:
        # Load rulebook document
        loader = TextLoader(RULES_FILE, encoding="utf-8")
        documents = loader.load()

        # Split text into manageable chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        chunks = text_splitter.split_documents(documents)

        # Build and persist vector index
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
    # Test query
    sample_code = "query = f'SELECT * FROM users WHERE id = {user_id}'"
    rules = retrieve_relevant_rules(sample_code)
    print("🔍 Retrieved Context:\n", rules)