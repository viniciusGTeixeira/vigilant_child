FROM python:3.12-slim

WORKDIR /app

# Configurar pip para retry e timeout
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=5

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip primeiro
RUN pip install --no-cache-dir --upgrade pip

# Instalar PyTorch CPU-only (versão mais leve)
RUN pip install --no-cache-dir \
    torch==2.1.0+cpu \
    torchvision==0.16.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Instalar Ultralytics e outras dependências básicas
RUN pip install --no-cache-dir \
    ultralytics==8.0.190 \
    opencv-python-headless==4.8.1.78 \
    pillow==10.0.1 \
    numpy==1.24.3 \
    requests==2.31.0 \
    fastapi==0.103.2 \
    uvicorn==0.23.2 \
    pydantic==2.4.2 \
    loguru==0.7.2

# Copiar arquivos do serviço
COPY ultralytics_service.py .
COPY requirements.txt .

# Criar usuário não-root
RUN useradd -m -u 1000 ultralytics && \
    chown -R ultralytics:ultralytics /app

USER ultralytics

# Expor porta
EXPOSE 8002

# Comando de inicialização
CMD ["python", "ultralytics_service.py"] 