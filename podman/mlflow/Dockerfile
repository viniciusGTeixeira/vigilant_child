FROM python:3.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install MLflow
RUN pip install mlflow psycopg2-binary boto3

# Expose MLflow UI port
EXPOSE 5000

# Environment variables for MLflow
ENV MLFLOW_S3_ENDPOINT_URL=http://minio:9000
ENV AWS_ACCESS_KEY_ID=minioadmin
ENV AWS_SECRET_ACCESS_KEY=minioadmin

# Start MLflow server
CMD ["mlflow", "server", \
    "--host", "0.0.0.0", \
    "--port", "5000", \
    "--backend-store-uri", "postgresql://bigbrother:bigbrother@postgres/bigbrother", \
    "--default-artifact-root", "s3://mlflow/"] 