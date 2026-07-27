ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/muscles/src:/app/muscles-wsgi/src:/app/muscles-asgi/src:/app/muscles-cli/src:/app/muscles-sql/src:/app/muscles-ai/src:/app/muscles-documents/src:/app/muscles-jsonrpc/src:/app/muscles-sse/src:/app/muscles-otel/src:/app/muscles-mcp/src:/app/muscles-data/src:/app/muscles-data-elasticsearch/src:/app/muscles-data-opensearch/src:/app/muscles-data-qdrant/src:/app/muscles-data-redis/src:/app/muscles-data-mongodb/src:/app/muscles-data-s3/src:/app/muscles-data-sqlalchemy/src:/app/muscular-example

WORKDIR /app

COPY muscles ./muscles
COPY muscles-wsgi ./muscles-wsgi
COPY muscles-asgi ./muscles-asgi
COPY muscles-cli ./muscles-cli
COPY muscles-sql ./muscles-sql
COPY muscles-ai ./muscles-ai
COPY muscles-documents ./muscles-documents
COPY muscles-jsonrpc ./muscles-jsonrpc
COPY muscles-sse ./muscles-sse
COPY muscles-otel ./muscles-otel
COPY muscles-mcp ./muscles-mcp
COPY muscles-data ./muscles-data
COPY muscles-data-elasticsearch ./muscles-data-elasticsearch
COPY muscles-data-opensearch ./muscles-data-opensearch
COPY muscles-data-qdrant ./muscles-data-qdrant
COPY muscles-data-redis ./muscles-data-redis
COPY muscles-data-mongodb ./muscles-data-mongodb
COPY muscles-data-s3 ./muscles-data-s3
COPY muscles-data-sqlalchemy ./muscles-data-sqlalchemy
COPY muscular-example ./muscular-example

WORKDIR /app/muscular-example

RUN python -m pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["gunicorn", "example_4.web:app", "--bind", "0.0.0.0:8080"]
