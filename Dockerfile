# TeamAI - Department Intelligence System
# Multi-stage Dockerfile for production deployment

# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 teamai && \
    mkdir -p /app/data /app/data/chroma && \
    chown -R teamai:teamai /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/teamai/.local
ENV PATH=/home/teamai/.local/bin:$PATH

# Copy application code
COPY --chown=teamai:teamai backend/ /app/backend/
COPY --chown=teamai:teamai frontend/ /app/frontend/

# Switch to non-root user
USER teamai

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8001

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/openclaw/status || exit 1

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
