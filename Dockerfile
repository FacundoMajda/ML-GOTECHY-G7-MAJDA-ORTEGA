# syntax=docker/dockerfile:1.7

# ML-GOTECHY — multi-stage + uv + CPU-only torch + opencv-headless
# Imagen ~510MB (vs ~2.4GB con CUDA). Cache mount hace rebuilds incrementales ~10s.

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# gcc + libgl solo en builder. libgl lo dejan las wheels de opencv en link-time.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Layer deps: cacheado mientras pyproject.toml + uv.lock no cambien.
# --extra-index-url para torch CPU-only desde PyTorch.
# --index-strategy unsafe-best-match: PyTorch CPU index tiene versiones viejas
# de paquetes comunes (certifi, urllib3); first-index rompe el lock.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev \
        --index-strategy unsafe-best-match \
        --extra-index-url https://download.pytorch.org/whl/cpu

COPY src/ src/
COPY schema.sql .

# Layer proyecto: --no-editable para venv self-contained (no necesita source en runtime).
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-editable \
        --index-strategy unsafe-best-match \
        --extra-index-url https://download.pytorch.org/whl/cpu


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Solo runtime libs. libgl por seguridad (cv2 import en algunos modulos).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY src/ src/
COPY schema.sql .

RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["python", "-m", "src.app"]