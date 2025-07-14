FROM minio/minio:RELEASE.2024-01-18T22-51-28Z

# Argumentos para configuração
ARG MINIO_ROOT_USER=bigbrother
ARG MINIO_ROOT_PASSWORD=bigbrother

# Variáveis de ambiente
ENV MINIO_ROOT_USER=${MINIO_ROOT_USER}
ENV MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
ENV MINIO_PROMETHEUS_AUTH_TYPE=public

# Copiar script de inicialização
COPY buckets.json /data/config/buckets.json

# Expor portas (API e Console)
EXPOSE 9000 9001

# Configurar volume
VOLUME ["/data"]

# Comando para iniciar o MinIO
CMD ["server", "/data", "--console-address", ":9001"] 