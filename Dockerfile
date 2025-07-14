FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de requisitos
COPY big_brother_cnn/requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Criar usuário não-root
RUN useradd -m -u 1000 bigbrother && \
    chown -R bigbrother:bigbrother /app

# Copiar código da aplicação
COPY big_brother_cnn/ ./big_brother_cnn/

# Criar diretórios necessários
RUN mkdir -p /app/logs \
    && mkdir -p /app/models \
    && mkdir -p /app/data \
    && chown -R bigbrother:bigbrother /app

# Expor porta
EXPOSE 8000

# Mudar para usuário não-root
USER bigbrother

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando para iniciar a aplicação
CMD ["python", "-m", "uvicorn", "big_brother_cnn.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"] 