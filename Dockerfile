# Cloud Run container: FastAPI web layer + the ONE agent + the bundled stdio MCP server.
# The agent spawns mcp_server/ as a local subprocess (no separate service to stand up).
#
# This Dockerfile lives at the REPO ROOT on purpose: `gcloud run deploy --source .` only
# auto-detects a Dockerfile here, not in subdirectories. See deploy/README.md for the steps.
#
# Credentials are injected at DEPLOY time, never baked in:
#   - Gemini via Vertex (default): the Cloud Run service account provides ADC — no API key at all.
#   - DeepSeek (alternate):        DEEPSEEK_API_KEY from Secret Manager.
# .dockerignore keeps .env out of the image.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install deps first so the layer caches across code changes. litellm (in requirements.txt) is
# only exercised for the non-Gemini DeepSeek backend; harmless to keep installed otherwise.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app. .dockerignore keeps .env, .venv, .git, caches, and node_modules OUT.
COPY . .

# Cloud Run sends traffic to $PORT (8080 by default). Bind uvicorn to it on all interfaces.
# Shell form so $PORT expands at runtime. The MCP server is launched by the agent over stdio
# inside this same container — it is NOT a separate process to start here.
ENV PORT=8080
CMD exec uvicorn web.app:app --host 0.0.0.0 --port ${PORT}
