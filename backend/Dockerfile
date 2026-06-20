FROM python:3.12-slim

WORKDIR /app

ARG ANALYZER_TYPE=mock

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# CLIP is optional — skip the heavy PyTorch stack on small Railway instances.
RUN if [ "$ANALYZER_TYPE" = "clip" ]; then \
      pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
      && pip install --no-cache-dir git+https://github.com/openai/CLIP.git; \
    fi

COPY app ./app

ENV PYTHONUNBUFFERED=1
ENV ANALYZER_TYPE=${ANALYZER_TYPE}
ENV CLIP_MODEL=ViT-B/32
ENV ENVIRONMENT=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/ping')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
