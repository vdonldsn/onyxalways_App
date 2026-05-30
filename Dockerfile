# Multi-purpose Dockerfile for OnyxAlways Orders
# Works on Railway, Fly.io, Render, your own VPS, etc.

FROM python:3.12-slim

WORKDIR /app

# Install build deps for psycopg2 only if needed (binary wheel usually fine)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Cache pip layer separately so dependency changes don't rebuild everything
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway/Render/Fly all inject $PORT; default to 8000 for local docker run
ENV PORT=8000
EXPOSE 8000

# Use shell form so $PORT expands correctly
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
