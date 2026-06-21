# Railway entrypoint when the service root is the repository root (not backend/).
FROM python:3.12-slim

WORKDIR /app

ARG ANALYZER_TYPE=mock

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements-docker.txt ./requirements-docker.txt
RUN pip install --no-cache-dir -r requirements-docker.txt

RUN if [ "$ANALYZER_TYPE" = "clip" ]; then \
      pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
      && pip install --no-cache-dir git+https://github.com/openai/CLIP.git; \
    fi

COPY backend/app ./app

ENV PYTHONUNBUFFERED=1
ENV ANALYZER_TYPE=${ANALYZER_TYPE}
ENV CLIP_MODEL=ViT-B/32
ENV ENVIRONMENT=production

# Do not EXPOSE a fixed port — Railway injects $PORT (usually 8080). A wrong
# EXPOSE value makes the public domain target port mismatch and returns 502.

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
