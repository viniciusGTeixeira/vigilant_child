FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar MLflow e dependências
RUN pip install --no-cache-dir \
    mlflow==2.8.1 \
    psycopg2-binary \
    boto3 \
    prometheus-client \
    gunicorn

# Criar usuário não-root
RUN useradd -m -u 1000 mlflow && \
    mkdir -p /var/log/mlflow && \
    chown -R mlflow:mlflow /var/log/mlflow

# Copiar arquivos de configuração
COPY config.yaml /etc/mlflow/config.yaml
COPY users.txt /etc/mlflow/users.txt
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# Tornar script executável
RUN chmod +x /usr/local/bin/entrypoint.sh

# Variáveis de ambiente
ENV MLFLOW_S3_ENDPOINT_URL=http://minio:9000
ENV AWS_ACCESS_KEY_ID=bigbrother
ENV AWS_SECRET_ACCESS_KEY=bigbrother
ENV MLFLOW_BACKEND_STORE_URI=postgresql://bigbrother:bigbrother@postgres:5432/bigbrother
ENV MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://models/

# Expor porta
EXPOSE 5000

# Mudar para usuário não-root
USER mlflow

# Comando de inicialização
CMD ["/usr/local/bin/entrypoint.sh"] 