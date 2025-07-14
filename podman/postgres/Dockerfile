FROM postgres:15.5

# Argumentos para configuração
ARG POSTGRES_DB=bigbrother
ARG POSTGRES_USER=bigbrother
ARG POSTGRES_PASSWORD=bigbrother

# Variáveis de ambiente
ENV POSTGRES_DB=${POSTGRES_DB}
ENV POSTGRES_USER=${POSTGRES_USER}
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
ENV PGDATA=/var/lib/postgresql/data/pgdata

# Copiar script de inicialização
COPY init.sql /docker-entrypoint-initdb.d/

# Configurações do PostgreSQL
RUN echo "host all  all    0.0.0.0/0  md5" >> /usr/share/postgresql/15/pg_hba.conf.sample && \
    echo "listen_addresses='*'" >> /usr/share/postgresql/15/postgresql.conf.sample

# Expor porta
EXPOSE 5432

# Criar diretório de dados
RUN mkdir -p ${PGDATA} && chown -R postgres:postgres ${PGDATA}

# Configurar volume
VOLUME ${PGDATA} 