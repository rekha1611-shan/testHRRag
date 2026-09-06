# HR Support Chatbot — Gemini RAG

## Overview

This project implements a Retrieval-Augmented Generation (RAG) HR support chatbot that answers employee questions using the HR policy PDFs in `documents/`.

The application now uses **Google Gemini instead of OpenAI** for both generation and embeddings.

## Core stack

- Python
- Streamlit
- LangChain
- Google Gemini via `langchain-google-genai`
- Gemini chat model: `gemini-2.5-flash`
- Gemini embedding model: `gemini-embedding-001`
- FAISS vector database
- PyPDF
- Google Secret Manager for GCP secrets
- Docker
- Google App Engine Flexible

## Architecture

```text
Employee question
      |
      v
Gemini query embedding
      |
      v
FAISS similarity search
      |
      v
Relevant HR policy chunks
      |
      v
Prompt + chat history
      |
      v
Gemini 2.5 Flash
      |
      v
Grounded HR response
```

## Project structure

```text
15_HR_rag_chatbot_memory_UI/
├── documents/                 # HR policy PDFs
├── app.py                     # Streamlit app
├── app_with_memory.py         # Streamlit app with chat history
├── chatbot.py                 # CLI chatbot
├── ingest.py                  # Builds Gemini FAISS index
├── rag_store.py               # Shared indexing/loading logic
├── gcp_secrets.py             # Local/GCP Gemini secret loader
├── Dockerfile
├── app.yaml
├── requirements.txt
├── .env.example
└── DEPLOY_GCP.md
```

## Local setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate it and install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure the Gemini API key

Copy `.env.example` to `.env` and set your real Gemini API key:

```env
GEMINI_API_KEY=your_real_gemini_api_key
GEMINI_CHAT_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001
AUTO_BUILD_FAISS_INDEX=true
```

Never commit the real `.env` file.

### 3. Build the FAISS index

Recommended before running or deploying:

```bash
python ingest.py
```

This recreates `hr_faiss_index/` using Gemini embeddings.

The previous OpenAI FAISS index is intentionally not included because vectors created by different embedding models are not interchangeable.

### 4. Run the application

Memory-enabled UI:

```bash
streamlit run app_with_memory.py
```

Basic UI:

```bash
streamlit run app.py
```

CLI:

```bash
python chatbot.py
```

## Automatic index rebuild

If `AUTO_BUILD_FAISS_INDEX=true` and a compatible Gemini index is missing, the application builds one from the PDFs at startup.

For deployment, pre-building with `python ingest.py` is preferable because it avoids repeated embedding calls if a new App Engine instance starts without a persisted local index.

## GCP deployment

See `DEPLOY_GCP.md` for the complete App Engine Flexible + Docker deployment sequence.

## Grounding behavior

The assistant is instructed to answer only from retrieved HR policy context. If the policy context does not contain the answer, it responds:

> I’m not sure based on current HR policies.

## Limitations

- FAISS is local to the application container; it is not a distributed vector database.
- Streamlit session memory is not durable across instance restarts/deployments.
- No role-based authorization is implemented.
- Retrieved source citations are not displayed in the UI.

## Disclaimer

This chatbot is intended for informational and educational use. Official HR decisions should follow company policy and HR approval processes.
