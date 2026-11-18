FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VKS_HOST=0.0.0.0 \
    VKS_PORT=7870

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN python -m pip install --no-cache-dir .

EXPOSE 7870
VOLUME ["/app/data"]
HEALTHCHECK --interval=20s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7870/login.html', timeout=3)" || exit 1
CMD ["python", "-m", "vks", "--host", "0.0.0.0", "--port", "7870"]
