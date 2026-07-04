ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/muscles/src:/app/muscles-wsgi/src:/app/muscles-asgi/src:/app/muscles-cli/src:/app/muscles-sql/src:/app/muscles-ai/src:/app/muscles-documents/src:/app/muscles-jsonrpc/src:/app/muscles-sse/src:/app/muscles-otel/src:/app/muscles-mcp/src:/app/muscular-example

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
COPY muscular-example ./muscular-example

WORKDIR /app/muscular-example

RUN python -m pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python", "-m", "example_4.server"]
