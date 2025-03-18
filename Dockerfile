FROM python:3.11-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.6.7 /uv /uvx /bin/

COPY . /code
WORKDIR /code

RUN uv sync --frozen --no-cache
CMD ["/code/.venv/bin/fastapi", "run", "src/app.py", "--port", "8000", "--host", "0.0.0.0"]
