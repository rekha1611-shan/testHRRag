"""Build the HR FAISS knowledge base using Gemini embeddings."""

from dotenv import load_dotenv

from gcp_secrets import ensure_gemini_api_key
from rag_store import build_vectorstore

load_dotenv()
ensure_gemini_api_key()
build_vectorstore()
print("HR knowledge base successfully indexed with Gemini embeddings.")
