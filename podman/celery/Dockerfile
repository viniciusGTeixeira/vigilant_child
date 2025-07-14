FROM python:3.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and code
COPY requirements.txt .
COPY ./app .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start Celery worker
CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"] 