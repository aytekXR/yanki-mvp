# One image runs both the api and the worker (different commands via compose).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir uv

# Install runtime dependencies first for better layer caching. psycopg[binary]
# bundles libpq, so no apt packages are needed.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8141

# api command; the worker service overrides this with `python -m app.worker`.
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8141"]
