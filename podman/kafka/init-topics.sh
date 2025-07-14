#!/bin/bash

# Script para inicializar tópicos do Kafka
set -e

echo "Aguardando Kafka inicializar..."
sleep 30

# Função para criar tópico
create_topic() {
    local name=$1
    local partitions=$2
    local replication_factor=$3
    local config=$4
    
    echo "Criando tópico: $name"
    kafka-topics --bootstrap-server localhost:9092 \
        --create \
        --topic "$name" \
        --partitions "$partitions" \
        --replication-factor "$replication_factor" \
        --config "$config" \
        --if-not-exists
}

# Ler configuração dos tópicos
if [ -f "/etc/kafka/topics.json" ]; then
    echo "Carregando configuração dos tópicos..."
    
    # Criar tópicos principais
    create_topic "raw-detections" 3 1 "retention.ms=604800000"
    create_topic "analyzed-events" 3 1 "retention.ms=604800000"
    create_topic "pattern-alerts" 2 1 "retention.ms=259200000"
    create_topic "system-metrics" 1 1 "retention.ms=86400000"
    
    echo "Tópicos criados com sucesso!"
else
    echo "Arquivo de configuração não encontrado!"
    exit 1
fi

# Listar tópicos criados
echo "Tópicos disponíveis:"
kafka-topics --bootstrap-server localhost:9092 --list

echo "Inicialização dos tópicos concluída!" 