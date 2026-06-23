# Skeleton — verify against current ADK deploy guidance.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# The agent spawns the MCP server as a local stdio subprocess (bundled in this image).
CMD ["python", "-m", "agent.agent"]
