"""
Módulo para integração com Kafka e MinIO
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import io
import os

from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from minio import Minio
from minio.error import S3Error
import numpy as np
import cv2
import torch
from PIL import Image


class StorageManager:
    """
    Gerenciador de armazenamento integrado com Kafka e MinIO
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Configurar Kafka
        kafka_config = config.get('kafka', {})
        self.kafka_bootstrap_servers = kafka_config.get('bootstrap_servers', 'localhost:9092')
        self.kafka_producer = None
        self.kafka_consumer = None
        self.kafka_admin = None
        
        # Configurar MinIO
        minio_config = config.get('minio', {})
        self.minio_client = Minio(
            minio_config.get('endpoint', 'localhost:9000'),
            access_key=minio_config.get('access_key', 'bigbrother'),
            secret_key=minio_config.get('secret_key', 'bigbrother'),
            secure=minio_config.get('secure', False)
        )
        
        # Inicializar conexões
        self._init_kafka()
        self._init_minio()
    
    def _init_kafka(self) -> None:
        """
        Inicializa conexões com Kafka
        """
        try:
            # Criar producer
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=self.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            
            # Criar consumer
            self.kafka_consumer = KafkaConsumer(
                bootstrap_servers=self.kafka_bootstrap_servers,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            # Criar admin client
            self.kafka_admin = KafkaAdminClient(
                bootstrap_servers=self.kafka_bootstrap_servers
            )
            
            # Criar tópicos se não existirem
            self._ensure_topics_exist()
            
        except Exception as e:
            print(f"Erro ao inicializar Kafka: {e}")
            raise
    
    def _init_minio(self) -> None:
        """
        Inicializa buckets no MinIO
        """
        try:
            # Carregar configuração dos buckets
            buckets_config = self._load_buckets_config()
            
            # Criar buckets se não existirem
            for bucket in buckets_config.get('buckets', []):
                bucket_name = bucket['name']
                if not self.minio_client.bucket_exists(bucket_name):
                    self.minio_client.make_bucket(bucket_name)
                    
                    # Aplicar política
                    if 'policy' in bucket:
                        policy = buckets_config['policies'].get(bucket['policy'])
                        if policy:
                            self.minio_client.set_bucket_policy(bucket_name, json.dumps(policy))
                    
                    # Aplicar regras de lifecycle
                    if bucket_name in buckets_config.get('lifecycle_rules', {}):
                        rules = buckets_config['lifecycle_rules'][bucket_name]
                        self.minio_client.set_bucket_lifecycle(bucket_name, rules)
            
        except Exception as e:
            print(f"Erro ao inicializar MinIO: {e}")
            raise
    
    def _load_buckets_config(self) -> Dict[str, Any]:
        """
        Carrega configuração dos buckets
        """
        config_path = os.path.join('podman', 'minio', 'buckets.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar configuração dos buckets: {e}")
            return {'buckets': [], 'policies': {}, 'lifecycle_rules': {}}
    
    def _ensure_topics_exist(self) -> None:
        """
        Garante que os tópicos necessários existem
        """
        try:
            # Carregar configuração dos tópicos
            config_path = os.path.join('podman', 'kafka', 'topics.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                topics_config = json.load(f)
            
            # Listar tópicos existentes
            existing_topics = self.kafka_admin.list_topics()
            
            # Criar tópicos que não existem
            topics_to_create = []
            for topic in topics_config.get('topics', []):
                if topic['name'] not in existing_topics:
                    topics_to_create.append(NewTopic(
                        name=topic['name'],
                        num_partitions=topic['partitions'],
                        replication_factor=topic['replication_factor'],
                        topic_configs=topic.get('config', {})
                    ))
            
            if topics_to_create:
                self.kafka_admin.create_topics(topics_to_create)
            
        except Exception as e:
            print(f"Erro ao verificar/criar tópicos: {e}")
            raise
    
    def save_image(self, image: np.ndarray, bucket: str, 
                  object_name: str, metadata: Optional[Dict[str, str]] = None) -> str:
        """
        Salva imagem no MinIO
        """
        try:
            # Converter imagem para bytes
            is_success, buffer = cv2.imencode(".jpg", image)
            if not is_success:
                raise ValueError("Falha ao codificar imagem")
            
            image_bytes = io.BytesIO(buffer)
            
            # Upload para MinIO
            self.minio_client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=image_bytes,
                length=image_bytes.getbuffer().nbytes,
                content_type='image/jpeg',
                metadata=metadata
            )
            
            return object_name
            
        except Exception as e:
            print(f"Erro ao salvar imagem: {e}")
            raise
    
    def load_image(self, bucket: str, object_name: str) -> np.ndarray:
        """
        Carrega imagem do MinIO
        """
        try:
            # Download do MinIO
            data = self.minio_client.get_object(bucket, object_name)
            
            # Converter para numpy array
            image_bytes = io.BytesIO(data.read())
            image = cv2.imdecode(
                np.frombuffer(image_bytes.getvalue(), np.uint8),
                cv2.IMREAD_COLOR
            )
            
            return image
            
        except Exception as e:
            print(f"Erro ao carregar imagem: {e}")
            raise
    
    def save_model(self, model: torch.nn.Module, bucket: str, 
                  object_name: str, metadata: Optional[Dict[str, str]] = None) -> str:
        """
        Salva modelo no MinIO
        """
        try:
            # Salvar modelo em buffer
            buffer = io.BytesIO()
            torch.save(model.state_dict(), buffer)
            buffer.seek(0)
            
            # Upload para MinIO
            self.minio_client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=buffer,
                length=buffer.getbuffer().nbytes,
                content_type='application/octet-stream',
                metadata=metadata
            )
            
            return object_name
            
        except Exception as e:
            print(f"Erro ao salvar modelo: {e}")
            raise
    
    def load_model(self, model: torch.nn.Module, bucket: str, 
                  object_name: str) -> torch.nn.Module:
        """
        Carrega modelo do MinIO
        """
        try:
            # Download do MinIO
            data = self.minio_client.get_object(bucket, object_name)
            
            # Carregar estado do modelo
            buffer = io.BytesIO(data.read())
            model.load_state_dict(torch.load(buffer))
            
            return model
            
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
            raise
    
    def publish_event(self, topic: str, event: Dict[str, Any], 
                     key: Optional[str] = None) -> None:
        """
        Publica evento no Kafka
        """
        try:
            # Adicionar timestamp
            if 'timestamp' not in event:
                event['timestamp'] = datetime.now().isoformat()
            
            # Publicar mensagem
            future = self.kafka_producer.send(topic, value=event, key=key)
            self.kafka_producer.flush()
            
            # Verificar se houve erro
            future.get(timeout=10)
            
        except Exception as e:
            print(f"Erro ao publicar evento: {e}")
            raise
    
    def subscribe_to_events(self, topics: List[str], 
                          group_id: Optional[str] = None) -> KafkaConsumer:
        """
        Inscreve-se em tópicos do Kafka
        """
        try:
            # Criar consumer específico para os tópicos
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=self.kafka_bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            return consumer
            
        except Exception as e:
            print(f"Erro ao inscrever em tópicos: {e}")
            raise
    
    def close(self) -> None:
        """
        Fecha conexões
        """
        try:
            if self.kafka_producer:
                self.kafka_producer.close()
            if self.kafka_consumer:
                self.kafka_consumer.close()
            if self.kafka_admin:
                self.kafka_admin.close()
        except Exception as e:
            print(f"Erro ao fechar conexões: {e}") 