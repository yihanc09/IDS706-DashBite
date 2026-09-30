FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y make \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md Makefile ./
COPY pipeline ./pipeline
COPY dashboard ./dashboard
COPY tests ./tests

RUN python -m pip install --no-cache-dir .[test]

RUN mkdir -p /app/data/raw /app/data/features /app/data/models \
    /app/data/predictions /app/data/quality

EXPOSE 8501

HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=12 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=2)"

CMD ["make", "container-run"]