ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/muscles/src:/app/muscles-wsgi/src:/app/muscles-cli/src:/app/butko-info-site

WORKDIR /app

COPY muscles ./muscles
COPY muscles-wsgi ./muscles-wsgi
COPY muscles-cli ./muscles-cli
COPY butko-info-site ./butko-info-site

WORKDIR /app/butko-info-site

RUN python -m pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python", "-m", "butko_info.server"]
