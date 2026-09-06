"""Runtime secret loading helpers for local and Google Cloud deployments."""

import os


def ensure_gemini_api_key() -> None:
    """Ensure GEMINI_API_KEY is available.

    Local development can provide GEMINI_API_KEY through .env or the shell.
    On Google Cloud, set GEMINI_SECRET_NAME to a Secret Manager secret name.
    """
    if os.getenv("GEMINI_API_KEY"):
        return

    secret_name = os.getenv("GEMINI_SECRET_NAME")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    if not secret_name:
        raise RuntimeError(
            "GEMINI_API_KEY is not set and GEMINI_SECRET_NAME is not configured."
        )
    if not project_id:
        raise RuntimeError(
            "GOOGLE_CLOUD_PROJECT is not available; cannot read Secret Manager."
        )

    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
    resource_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": resource_name})
    os.environ["GEMINI_API_KEY"] = response.payload.data.decode("utf-8").strip()
