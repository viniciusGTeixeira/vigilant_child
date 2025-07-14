FROM confluentinc/cp-kafka:7.3.0

# Configurações do KRaft (sem Zookeeper)
ENV KAFKA_PROCESS_ROLES=broker,controller
ENV KAFKA_NODE_ID=1
ENV KAFKA_CONTROLLER_QUORUM_VOTERS=1@kafka:9093
ENV KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
ENV KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
ENV KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER
ENV KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT
ENV KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT

# Configurações de cluster
ENV KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
ENV KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1
ENV KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1
ENV KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=0

# Configurações de log
ENV KAFKA_LOG_DIRS=/var/lib/kafka/data
ENV KAFKA_CLUSTER_ID=MkU3OEVBNTcwNTJENDM2Qk

# Copiar arquivos de configuração
COPY topics.json /etc/kafka/topics.json
COPY init-topics.sh /usr/local/bin/init-topics.sh

# Tornar script executável
RUN chmod +x /usr/local/bin/init-topics.sh

# Expor portas
EXPOSE 9092 9093

# Script de inicialização personalizado
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Comando de inicialização
CMD ["/usr/local/bin/entrypoint.sh"] 