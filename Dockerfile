FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/dan-jun/video-knowledge-studio"
LABEL org.opencontainers.image.description="Local-first AI learning workspace with synchronized notes and video production"
LABEL org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VKS_HOST=0.0.0.0 \
    VKS_PORT=7870

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       ffmpeg \
       fonts-noto-cjk \
       libcairo2-dev \
       libgl1 \
       libpango1.0-dev \
       pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
ARG VKS_INSTALL_PRODUCTION=1
RUN if [ "$VKS_INSTALL_PRODUCTION" = "1" ]; then \
      python -m pip install --no-cache-dir ".[production]"; \
    else \
      python -m pip install --no-cache-dir .; \
    fi

EXPOSE 7870
VOLUME ["/app/data"]
HEALTHCHECK --interval=20s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7870/login.html', timeout=3)" || exit 1
CMD ["python", "-m", "vks", "--host", "0.0.0.0", "--port", "7870"]
