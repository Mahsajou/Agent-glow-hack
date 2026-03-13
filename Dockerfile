# Persona Temporal Worker
FROM python:3.12-slim

WORKDIR /app

# Install dependencies (copy first for layer caching)
COPY agent/requirements.txt agent/requirements.txt
RUN pip install --no-cache-dir -r agent/requirements.txt

# Copy agent code (agent/output excluded via .dockerignore)
COPY agent/ agent/

# Output directory for generated artifacts (mount a volume in production for persistence)
RUN mkdir -p /app/agent/output

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Required at runtime: GMI_API_KEY, EXA_API_KEY
# Optional: TEMPORAL_HOST (default localhost:7233), TEMPORAL_NAMESPACE, TEMPORAL_TASK_QUEUE
CMD ["python", "agent/run.py", "worker"]
