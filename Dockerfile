FROM python:3.11-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.6.7 /uv /uvx /bin/

COPY . /code
WORKDIR /code
RUN uv sync

CMD ["/code/.venv/bin/ragbits", "api", "run", "src.chat:MyChat", "--config-path", "config.yaml", "--host", "0.0.0.0", "--ui-build-dir", "src/ui-build"]
