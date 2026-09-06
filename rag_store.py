"""FAISS indexing and loading utilities for the Gemini-backed HR RAG app."""

import os
import shutil
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

DATA_FOLDER = Path(os.getenv("DATA_FOLDER", "documents"))
VECTOR_DB_PATH = Path(os.getenv("VECTOR_DB_PATH", "hr_faiss_index"))
EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
MODEL_MARKER = VECTOR_DB_PATH / "embedding_model.txt"


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Create the Gemini embeddings client used for both indexing and retrieval."""
    api_key = os.environ["GEMINI_API_KEY"]
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=api_key,
        vertexai=False,
    )


def _index_is_compatible() -> bool:
    index_file = VECTOR_DB_PATH / "index.faiss"
    metadata_file = VECTOR_DB_PATH / "index.pkl"
    if not index_file.exists() or not metadata_file.exists() or not MODEL_MARKER.exists():
        return False
    return MODEL_MARKER.read_text(encoding="utf-8").strip() == EMBEDDING_MODEL


def build_vectorstore() -> FAISS:
    """Rebuild the FAISS index from all PDFs using Gemini embeddings."""
    if not DATA_FOLDER.exists():
        raise FileNotFoundError(f"Document folder not found: {DATA_FOLDER}")

    documents = []
    pdf_files = sorted(DATA_FOLDER.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {DATA_FOLDER}")

    for pdf_path in pdf_files:
        documents.extend(PyPDFLoader(str(pdf_path)).load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    chunks = splitter.split_documents(documents)
    if not chunks:
        raise RuntimeError("No text chunks were created from the HR documents.")

    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)

    if VECTOR_DB_PATH.exists():
        shutil.rmtree(VECTOR_DB_PATH)
    VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(VECTOR_DB_PATH))
    MODEL_MARKER.write_text(EMBEDDING_MODEL, encoding="utf-8")

    print(
        f"Built Gemini FAISS index from {len(pdf_files)} PDFs, "
        f"{len(documents)} pages, and {len(chunks)} chunks."
    )
    return vectorstore


def load_or_build_vectorstore() -> FAISS:
    """Load a compatible FAISS index, or rebuild it when configured to do so."""
    embeddings = get_embeddings()

    if _index_is_compatible():
        return FAISS.load_local(
            str(VECTOR_DB_PATH),
            embeddings,
            allow_dangerous_deserialization=True,
        )

    auto_build = os.getenv("AUTO_BUILD_FAISS_INDEX", "true").lower() in {
        "1", "true", "yes", "on"
    }
    if not auto_build:
        raise RuntimeError(
            "A compatible Gemini FAISS index was not found. Run `python ingest.py` "
            "before starting the app, or set AUTO_BUILD_FAISS_INDEX=true."
        )

    print(
        "Compatible Gemini FAISS index not found. Rebuilding from documents..."
    )
    return build_vectorstore()
