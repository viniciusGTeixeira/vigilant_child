FROM python:3.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    cmake \
    build-essential \
    gfortran \
    git \
    wget \
    python3-distutils \
    python3-dev \
    libatlas-base-dev \
    libavcodec-dev \
    libavformat-dev \
    libgtk-3-dev \
    libswscale-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*
    # Install system dependencies


# Copy requirements first for better caching
COPY requirements/base.txt requirements/base.txt
COPY requirements/fastapi.txt requirements/fastapi.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements/fastapi.txt

# Copy application code
COPY fastapi/app /app

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 