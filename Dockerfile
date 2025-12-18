# Multi-stage build for production deployment
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Create non-root user for security
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app && \
    mkdir -p /app/logs && \
    chown -R botuser:botuser /app/logs

USER botuser

# Update PATH
ENV PATH=/root/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run database migrations and start bot
CMD ["sh", "-c", "alembic upgrade head && python -m src.main"]
