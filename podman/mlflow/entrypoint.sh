#!/bin/bash

# Script de entrypoint para MLflow
set -e

echo "Iniciando MLflow Server..."

# Aguardar PostgreSQL estar disponível
echo "Aguardando PostgreSQL..."
until pg_isready -h postgres -p 5432 -U bigbrother; do
    echo "PostgreSQL não está pronto - aguardando..."
    sleep 2
done

# Aguardar MinIO estar disponível
echo "Aguardando MinIO..."
until curl -f http://minio:9000/minio/health/live > /dev/null 2>&1; do
    echo "MinIO não está pronto - aguardando..."
    sleep 2
done

# Criar bucket para modelos no MinIO se não existir
echo "Verificando bucket de modelos..."
python3 -c "
import boto3
from botocore.exceptions import ClientError
import os

s3 = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='bigbrother',
    aws_secret_access_key='bigbrother'
)

try:
    s3.head_bucket(Bucket='models')
    print('Bucket models já existe')
except ClientError:
    s3.create_bucket(Bucket='models')
    print('Bucket models criado')
"

# Inicializar banco de dados do MLflow
echo "Inicializando banco de dados..."
mlflow db upgrade "${MLFLOW_BACKEND_STORE_URI}"

# Iniciar servidor MLflow
echo "Iniciando servidor MLflow..."
exec mlflow server \
    --host 0.0.0.0 \
    --port 5000 \
    --backend-store-uri "${MLFLOW_BACKEND_STORE_URI}" \
    --default-artifact-root "${MLFLOW_DEFAULT_ARTIFACT_ROOT}" \
    --serve-artifacts \
    --workers 4 