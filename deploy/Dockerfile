# Cloud Run container: FastAPI web layer + the ONE agent + the bundled stdio MCP server.
# The agent spawns mcp_server/ as a local subprocess (no separate service to stand up).
# Secrets (DEEPSEEK_API_KEY) are injected at deploy time via Cloud Run — NEVER baked in.
FROM python:3.12-slim

# Faster, quieter Python in a container.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install deps first so the layer caches across code changes. litellm (in requirements.txt)
# is required because the deployed model is DeepSeek (ADK_MODEL=deepseek/deepseek-chat).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app. .dockerignore keeps .env, .venv, .git, caches, and node_modules OUT.
COPY . .

# Cloud Run sends traffic to $PORT (8080 by default). Bind uvicorn to it on all interfaces.
# Shell form so $PORT expands at runtime. The MCP server is launched by the agent over stdio,
# inside this same container — it is NOT a separate process to start here.
ENV PORT=8080
CMD exec uvicorn web.app:app --host 0.0.0.0 --port ${PORT}
