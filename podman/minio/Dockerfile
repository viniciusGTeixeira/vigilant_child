FROM minio/minio:RELEASE.2023-09-07T02-05-02Z

# Set MinIO root credentials
ENV MINIO_ROOT_USER=minioadmin
ENV MINIO_ROOT_PASSWORD=minioadmin

# Expose MinIO ports
EXPOSE 9000 9001

# Start MinIO in server mode
CMD ["server", "/data", "--console-address", ":9001"] 