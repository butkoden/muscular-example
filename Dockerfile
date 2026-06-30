ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/muscles/src:/app/muscles-wsgi/src:/app/muscles-asgi/src:/app/muscles-cli/src:/app/muscular-example

WORKDIR /app

COPY muscles ./muscles
COPY muscles-wsgi ./muscles-wsgi
COPY muscles-asgi ./muscles-asgi
COPY muscles-cli ./muscles-cli
COPY muscular-example ./muscular-example

WORKDIR /app/muscular-example

RUN python -m pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python", "-m", "example_4.server"]
