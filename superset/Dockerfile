FROM apache/superset:latest

USER root

RUN uv pip install \
    --python /app/.venv/bin/python \
    --no-cache-dir \
    trino

USER superset