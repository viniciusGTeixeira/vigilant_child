"""
Sistema de métricas Prometheus para Big Brother CNN
"""

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from prometheus_client.core import REGISTRY
from typing import Dict, Any, Optional
import time
import psutil
import threading
from datetime import datetime
import functools


class PrometheusMetrics:
    """
    Classe para gerenciar métricas Prometheus
    """
    
    def __init__(self, registry: CollectorRegistry = None):
        self.registry = registry or REGISTRY
        self._setup_metrics()
        
        # Thread para métricas do sistema
        self._system_metrics_thread = None
        self._stop_system_metrics = False
        
    def _setup_metrics(self):
        """
        Configura todas as métricas Prometheus
        """
        # Métricas de análise
        self.analysis_requests_total = Counter(
            'bigbrother_analysis_requests_total',
            'Total de requisições de análise',
            ['analysis_type', 'status'],
            registry=self.registry
        )
        
        self.analysis_duration_seconds = Histogram(
            'bigbrother_analysis_duration_seconds',
            'Duração das análises em segundos',
            ['analysis_type'],
            registry=self.registry
        )
        
        self.analysis_confidence = Histogram(
            'bigbrother_analysis_confidence',
            'Confiança das análises',
            ['analysis_type'],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry
        )
        
        # Métricas de detecção
        self.detections_total = Counter(
            'bigbrother_detections_total',
            'Total de detecções',
            ['detection_type', 'location'],
            registry=self.registry
        )
        
        self.faces_detected = Counter(
            'bigbrother_faces_detected_total',
            'Total de faces detectadas',
            ['recognized'],
            registry=self.registry
        )
        
        self.badges_detected = Counter(
            'bigbrother_badges_detected_total',
            'Total de crachás detectados',
            ['valid'],
            registry=self.registry
        )
        
        # Métricas de conformidade
        self.schedule_compliance = Counter(
            'bigbrother_schedule_compliance_total',
            'Conformidade com horários',
            ['status', 'location'],
            registry=self.registry
        )
        
        self.anomalies_detected = Counter(
            'bigbrother_anomalies_detected_total',
            'Anomalias detectadas',
            ['type', 'severity'],
            registry=self.registry
        )
        
        # Métricas de sistema
        self.system_cpu_usage = Gauge(
            'bigbrother_system_cpu_usage_percent',
            'Uso de CPU do sistema',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'bigbrother_system_memory_usage_percent',
            'Uso de memória do sistema',
            registry=self.registry
        )
        
        self.system_disk_usage = Gauge(
            'bigbrother_system_disk_usage_percent',
            'Uso de disco do sistema',
            registry=self.registry
        )
        
        self.gpu_usage = Gauge(
            'bigbrother_gpu_usage_percent',
            'Uso de GPU',
            ['gpu_id'],
            registry=self.registry
        )
        
        self.gpu_memory_usage = Gauge(
            'bigbrother_gpu_memory_usage_percent',
            'Uso de memória GPU',
            ['gpu_id'],
            registry=self.registry
        )
        
        # Métricas de API
        self.api_requests_total = Counter(
            'bigbrother_api_requests_total',
            'Total de requisições da API',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.api_request_duration = Histogram(
            'bigbrother_api_request_duration_seconds',
            'Duração das requisições da API',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.active_connections = Gauge(
            'bigbrother_active_connections',
            'Conexões ativas',
            registry=self.registry
        )
        
        # Métricas de armazenamento
        self.storage_operations_total = Counter(
            'bigbrother_storage_operations_total',
            'Operações de armazenamento',
            ['operation', 'backend', 'status'],
            registry=self.registry
        )
        
        self.storage_size_bytes = Gauge(
            'bigbrother_storage_size_bytes',
            'Tamanho do armazenamento em bytes',
            ['backend', 'bucket'],
            registry=self.registry
        )
        
        # Métricas de ML
        self.model_predictions_total = Counter(
            'bigbrother_model_predictions_total',
            'Total de predições do modelo',
            ['model_name', 'model_version'],
            registry=self.registry
        )
        
        self.model_accuracy = Gauge(
            'bigbrother_model_accuracy',
            'Acurácia do modelo',
            ['model_name', 'model_version'],
            registry=self.registry
        )
        
        self.model_inference_duration = Histogram(
            'bigbrother_model_inference_duration_seconds',
            'Duração da inferência do modelo',
            ['model_name'],
            registry=self.registry
        )
        
        # Métricas de streaming
        self.kafka_messages_produced = Counter(
            'bigbrother_kafka_messages_produced_total',
            'Mensagens produzidas no Kafka',
            ['topic'],
            registry=self.registry
        )
        
        self.kafka_messages_consumed = Counter(
            'bigbrother_kafka_messages_consumed_total',
            'Mensagens consumidas do Kafka',
            ['topic', 'consumer_group'],
            registry=self.registry
        )
        
        # Informações do sistema
        self.system_info = Info(
            'bigbrother_system_info',
            'Informações do sistema',
            registry=self.registry
        )
        
        # Definir informações do sistema
        self.system_info.info({
            'version': '1.0.0',
            'python_version': '3.11',
            'platform': 'linux'
        })
    
    def record_analysis_request(self, analysis_type: str, status: str, duration: float, confidence: float = None):
        """
        Registra métricas de requisição de análise
        """
        self.analysis_requests_total.labels(analysis_type=analysis_type, status=status).inc()
        self.analysis_duration_seconds.labels(analysis_type=analysis_type).observe(duration)
        
        if confidence is not None:
            self.analysis_confidence.labels(analysis_type=analysis_type).observe(confidence)
    
    def record_detection(self, detection_type: str, location: str = "unknown"):
        """
        Registra detecção
        """
        self.detections_total.labels(detection_type=detection_type, location=location).inc()
    
    def record_face_detection(self, recognized: bool):
        """
        Registra detecção facial
        """
        self.faces_detected.labels(recognized=str(recognized).lower()).inc()
    
    def record_badge_detection(self, valid: bool):
        """
        Registra detecção de crachá
        """
        self.badges_detected.labels(valid=str(valid).lower()).inc()
    
    def record_schedule_compliance(self, status: str, location: str = "unknown"):
        """
        Registra conformidade com horário
        """
        self.schedule_compliance.labels(status=status, location=location).inc()
    
    def record_anomaly(self, anomaly_type: str, severity: str):
        """
        Registra anomalia detectada
        """
        self.anomalies_detected.labels(type=anomaly_type, severity=severity).inc()
    
    def record_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """
        Registra requisição da API
        """
        self.api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_storage_operation(self, operation: str, backend: str, status: str):
        """
        Registra operação de armazenamento
        """
        self.storage_operations_total.labels(
            operation=operation,
            backend=backend,
            status=status
        ).inc()
    
    def record_model_prediction(self, model_name: str, model_version: str, duration: float):
        """
        Registra predição do modelo
        """
        self.model_predictions_total.labels(
            model_name=model_name,
            model_version=model_version
        ).inc()
        
        self.model_inference_duration.labels(model_name=model_name).observe(duration)
    
    def record_kafka_message(self, topic: str, operation: str, consumer_group: str = None):
        """
        Registra mensagem do Kafka
        """
        if operation == "produced":
            self.kafka_messages_produced.labels(topic=topic).inc()
        elif operation == "consumed" and consumer_group:
            self.kafka_messages_consumed.labels(topic=topic, consumer_group=consumer_group).inc()
    
    def update_system_metrics(self):
        """
        Atualiza métricas do sistema
        """
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)
            
            # Memória
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.percent)
            
            # Disco
            disk = psutil.disk_usage('/')
            self.system_disk_usage.set(disk.percent)
            
            # GPU (se disponível)
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                for gpu in gpus:
                    self.gpu_usage.labels(gpu_id=str(gpu.id)).set(gpu.load * 100)
                    self.gpu_memory_usage.labels(gpu_id=str(gpu.id)).set(gpu.memoryUtil * 100)
            except ImportError:
                pass
            
        except Exception as e:
            print(f"Erro ao atualizar métricas do sistema: {e}")
    
    def start_system_metrics_collection(self, interval: int = 30):
        """
        Inicia coleta automática de métricas do sistema
        """
        def collect_metrics():
            while not self._stop_system_metrics:
                self.update_system_metrics()
                time.sleep(interval)
        
        if self._system_metrics_thread is None or not self._system_metrics_thread.is_alive():
            self._stop_system_metrics = False
            self._system_metrics_thread = threading.Thread(target=collect_metrics, daemon=True)
            self._system_metrics_thread.start()
    
    def stop_system_metrics_collection(self):
        """
        Para coleta automática de métricas do sistema
        """
        self._stop_system_metrics = True
        if self._system_metrics_thread:
            self._system_metrics_thread.join(timeout=5)
    
    def get_metrics(self) -> str:
        """
        Obtém métricas no formato Prometheus
        """
        return generate_latest(self.registry)
    
    def reset_metrics(self):
        """
        Reseta todas as métricas
        """
        # Limpar registry
        collectors = list(self.registry._collector_to_names.keys())
        for collector in collectors:
            self.registry.unregister(collector)
        
        # Recriar métricas
        self._setup_metrics()


# Instância global
metrics = PrometheusMetrics()


def track_analysis_time(analysis_type: str):
    """
    Decorator para rastrear tempo de análise
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                confidence = result.get('confidence', 0.0) if isinstance(result, dict) else 0.0
                metrics.record_analysis_request(analysis_type, 'success', duration, confidence)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_analysis_request(analysis_type, 'error', duration)
                raise
        return wrapper
    return decorator


def track_api_request():
    """
    Decorator para rastrear requisições da API
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                # Extrair informações da requisição (implementar conforme necessário)
                metrics.record_api_request('POST', '/api/analysis', 200, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_api_request('POST', '/api/analysis', 500, duration)
                raise
        return wrapper
    return decorator


def track_model_inference(model_name: str, model_version: str = "1.0"):
    """
    Decorator para rastrear inferência de modelo
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.record_model_prediction(model_name, model_version, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_model_prediction(model_name, model_version, duration)
                raise
        return wrapper
    return decorator


class MetricsMiddleware:
    """
    Middleware para coletar métricas de requisições HTTP
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        method = scope["method"]
        path = scope["path"]
        
        # Wrapper para capturar status code
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                duration = time.time() - start_time
                metrics.record_api_request(method, path, status_code, duration)
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


# Inicializar coleta automática de métricas do sistema
metrics.start_system_metrics_collection() 