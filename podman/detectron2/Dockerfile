FROM python:3.7-slim

WORKDIR /app

# Instalar dependências do sistema para Detectron2
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Instalar PyTorch compatível com Python 3.7
RUN pip install --no-cache-dir \
    torch==1.10.0+cpu \
    torchvision==0.11.0+cpu \
    -f https://download.pytorch.org/whl/torch_stable.html

# Instalar Detectron2
RUN pip install --no-cache-dir \
    detectron2==0.6 \
    -f https://dl.fbaipublicfiles.com/detectron2/wheels/cpu/torch1.10/index.html

# Instalar outras dependências
RUN pip install --no-cache-dir \
    opencv-python-headless==4.5.5.64 \
    numpy==1.21.6 \
    pillow==8.4.0 \
    requests==2.27.1 \
    kafka-python==2.0.2 \
    prometheus-client==0.14.1 \
    loguru==0.6.0 \
    pydantic==1.10.12 \
    fastapi==0.68.2 \
    uvicorn==0.15.0

# Copiar código do serviço
COPY detectron2_service.py .

# Criar usuário não-root
RUN useradd -m -u 1000 detectron2 && \
    chown -R detectron2:detectron2 /app

USER detectron2

# Expor porta
EXPOSE 8001

# Comando de inicialização
CMD ["python", "detectron2_service.py"] 