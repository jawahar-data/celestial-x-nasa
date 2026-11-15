# ==============================================================================
# CELESTIAL X 2.0 — Production Dockerfile
# Optimized for Google Cloud Run, AWS App Runner, & Docker Engine
# NASA Space Apps Challenge 2026
# ==============================================================================

FROM python:3.11-slim as base

# Set environment flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080 \
    STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Install minimal OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r celestial && useradd -r -g celestial -d /app -s /sbin/nologin celestial

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Set permissions for non-root user and SQLite database
RUN chown -R celestial:celestial /app

USER celestial

# Healthcheck for Cloud Run / Docker Compose
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl --fail http://localhost:${PORT}/_stcore/health || exit 1

EXPOSE 8080

# Launch CELESTIAL X multi-page application
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0"]

