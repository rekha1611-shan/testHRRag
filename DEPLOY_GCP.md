# Deploy the Gemini HR RAG Chatbot to Google Cloud App Engine Flexible

The project uses a custom App Engine Flexible runtime so the `Dockerfile` controls the Python, Streamlit, LangChain, Gemini, and FAISS environment.

## 1. Prerequisites

Install the Google Cloud CLI and authenticate:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

Enable required Google Cloud services:

```bash
gcloud services enable \
  appengine.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

You also need a Gemini API key created for the Gemini Developer API.

## 2. Create the App Engine application

This is required only once per GCP project.

Choose the region carefully because the App Engine application region cannot be changed later.

```bash
gcloud app create --region=YOUR_REGION
```

## 3. Store the Gemini API key in Secret Manager

Create the secret the first time:

```bash
printf '%s' 'YOUR_GEMINI_API_KEY' | \
  gcloud secrets create gemini-api-key \
  --data-file=- \
  --replication-policy=automatic
```

To rotate an existing key:

```bash
printf '%s' 'YOUR_NEW_GEMINI_API_KEY' | \
  gcloud secrets versions add gemini-api-key --data-file=-
```

Grant the App Engine default service account access to the secret:

```bash
PROJECT_ID="$(gcloud config get-value project)"

gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

If the App Engine service uses a custom service account, grant the role to that account instead.

## 4. Recommended: build the Gemini FAISS index before deployment

Create a local `.env` file from `.env.example` and set your Gemini API key.

Then run:

```bash
python ingest.py
```

This creates:

```text
hr_faiss_index/
├── index.faiss
├── index.pkl
└── embedding_model.txt
```

The marker file ensures the application does not accidentally load an index generated with another embedding model.

If you skip this step, `AUTO_BUILD_FAISS_INDEX=true` allows the deployed application to build the index during startup. That is convenient for a demo, but pre-building is preferable because App Engine instance-local storage is not durable and a new instance may need to generate embeddings again.

## 5. Test locally with Docker

Build the container:

```bash
docker build -t hr-rag-chatbot-gemini .
```

Run it with your local `.env` file:

```bash
docker run --rm \
  -p 8080:8080 \
  --env-file .env \
  hr-rag-chatbot-gemini
```

Open:

```text
http://localhost:8080
```

Health endpoint:

```text
http://localhost:8080/_stcore/health
```

## 6. Deploy to App Engine

Run from the directory containing `app.yaml` and `Dockerfile`:

```bash
gcloud app deploy app.yaml
```

Open the deployed application:

```bash
gcloud app browse
```

## 7. View logs

```bash
gcloud app logs tail -s default
```

## Runtime configuration

`app.yaml` supplies non-secret configuration:

```yaml
GEMINI_SECRET_NAME: "gemini-api-key"
GEMINI_CHAT_MODEL: "gemini-2.5-flash"
GEMINI_EMBEDDING_MODEL: "models/gemini-embedding-001"
AUTO_BUILD_FAISS_INDEX: "true"
```

The actual Gemini key is not stored in `app.yaml`, the Dockerfile, or the repository. `gcp_secrets.py` reads it from Secret Manager at runtime and exposes it to the application as `GEMINI_API_KEY`.

## Important notes

- The application uses the Gemini Developer API with an API key, not Vertex AI authentication.
- Streamlit binds to `0.0.0.0:8080`, which is required by this App Engine Flexible container configuration.
- The real `.env` file is excluded from Docker and Cloud deployment.
- App Engine Flexible keeps at least one instance running, so it does not scale to zero.
- Streamlit chat history is session/process state and can be lost after reconnects, restarts, or deployments.
- Local FAISS storage is suitable for this demo. For a larger production system, consider a managed/persistent vector store.
