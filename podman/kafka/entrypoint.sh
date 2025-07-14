#!/bin/bash

# Script de entrypoint para Kafka com KRaft
set -e

echo "Iniciando Kafka com KRaft..."

# Verificar se o diretório de logs existe
if [ ! -d "${KAFKA_LOG_DIRS}" ]; then
    echo "Criando diretório de logs: ${KAFKA_LOG_DIRS}"
    mkdir -p "${KAFKA_LOG_DIRS}"
fi

# Verificar se o cluster já foi formatado
if [ ! -f "${KAFKA_LOG_DIRS}/meta.properties" ]; then
    echo "Formatando cluster Kafka..."
    kafka-storage format -t "${KAFKA_CLUSTER_ID}" -c /etc/kafka/server.properties
fi

# Iniciar Kafka em background
echo "Iniciando servidor Kafka..."
kafka-server-start /etc/kafka/server.properties &

# Aguardar Kafka estar pronto
echo "Aguardando Kafka ficar disponível..."
timeout=60
while [ $timeout -gt 0 ]; do
    if kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1; then
        echo "Kafka está pronto!"
        break
    fi
    sleep 2
    timeout=$((timeout - 2))
done

if [ $timeout -le 0 ]; then
    echo "Timeout aguardando Kafka ficar disponível!"
    exit 1
fi

# Executar script de inicialização dos tópicos
echo "Executando inicialização dos tópicos..."
/usr/local/bin/init-topics.sh &

# Manter o processo principal em execução
wait 