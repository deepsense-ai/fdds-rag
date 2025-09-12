# Multi-stage build for efficiency
FROM python:3.11-slim AS builder

# Install uv for dependency management
COPY --from=ghcr.io/astral-sh/uv:0.6.7 /uv /uvx /bin/

# Set working directory
WORKDIR /code

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies in virtual environment
RUN uv sync --frozen --no-dev

# Base runtime stage
FROM python:3.11-slim AS base-runtime

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -m -g appuser appuser

# Set working directory
WORKDIR /code

# Copy virtual environment from builder stage
COPY --chown=appuser:appuser --from=builder /code /code

# Copy application source code
COPY --chown=appuser:appuser src/ ./src/
CMD mkdir /home/appuser
# Switch to non-root user
USER appuser

ENV PYTHONPATH="/code/src:$PYTHONPATH"
ENV PATH="/code/.venv/bin:$PATH"

FROM base-runtime AS api

HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/config', timeout=2)" || exit 1

CMD ["ragbits", "api", "run", "src.chat:MyChat", "--host", "0.0.0.0", "--port", "8000"]

# Ingestion service stage
FROM base-runtime AS ingestion

RUN docling-tools models download
ENV DOCLING_ARTIFACTS_PATH /home/appuser/.cache/docling/models
CMD ["python", "src/manage_pdfs.py", "--ingest", "data/pdfs.txt"]
