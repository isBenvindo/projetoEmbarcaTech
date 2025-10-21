# back-end/Dockerfile
# syntax=docker/dockerfile:1

FROM python:3.11-slim

# configs úteis p/ containers Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências nativas para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements.txt (na raiz)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copia o código do backend
COPY back-end/ /app/

# Usuário não root (opção 1 - adduser)
RUN adduser --disabled-password --gecos "" app && chown -R app:app /app
USER app

# Defaults (podem ser sobrescritos pelo compose)
ENV HOST=0.0.0.0 PORT=8000

EXPOSE 8000

# Sobe a API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]