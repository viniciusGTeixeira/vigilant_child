"""
Modelos Pydantic para a API FastAPI
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import base64


class StatusEnum(str, Enum):
    """Status enum para respostas"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class AnalysisTypeEnum(str, Enum):
    """Tipos de análise disponíveis"""
    FACE = "face"
    BADGE = "badge"
    ATTRIBUTE = "attribute"
    SCHEDULE = "schedule"
    PATTERN = "pattern"
    INTEGRATED = "integrated"


class RiskLevelEnum(str, Enum):
    """Níveis de risco"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Modelos base
class BaseResponse(BaseModel):
    """Resposta base para todas as APIs"""
    status: StatusEnum
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[Dict[str, Any]] = None


class ImageInput(BaseModel):
    """Entrada de imagem para análise"""
    image_data: str = Field(..., description="Imagem em base64")
    filename: Optional[str] = Field(None, description="Nome do arquivo")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados da imagem")
    
    @validator('image_data')
    def validate_base64(cls, v):
        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("image_data deve ser uma string base64 válida")


class DetectionRequest(BaseModel):
    """Requisição de detecção"""
    image: ImageInput
    analysis_types: List[AnalysisTypeEnum] = Field(default=[AnalysisTypeEnum.INTEGRATED])
    location: Optional[str] = Field(None, description="Localização da câmera")
    camera_id: Optional[str] = Field(None, description="ID da câmera")
    save_image: bool = Field(True, description="Salvar imagem no MinIO")
    publish_event: bool = Field(True, description="Publicar evento no Kafka")


class DetectionResult(BaseModel):
    """Resultado de detecção"""
    detection_id: str
    analysis_type: AnalysisTypeEnum
    confidence: float = Field(..., ge=0.0, le=1.0)
    detected: bool
    details: Dict[str, Any]
    risk_level: RiskLevelEnum
    timestamp: datetime
    processing_time_ms: float


class AnalysisRequest(BaseModel):
    """Requisição de análise"""
    image: ImageInput
    analysis_type: AnalysisTypeEnum
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parâmetros específicos")


class AnalysisResult(BaseModel):
    """Resultado de análise"""
    analysis_id: str
    analysis_type: AnalysisTypeEnum
    result: Dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float
    timestamp: datetime


class FaceDetectionResult(BaseModel):
    """Resultado específico de detecção facial"""
    faces_detected: int
    faces: List[Dict[str, Any]]
    recognized_employees: List[Dict[str, str]]
    unknown_faces: int
    confidence_threshold: float


class BadgeDetectionResult(BaseModel):
    """Resultado específico de detecção de crachá"""
    badges_detected: int
    badges: List[Dict[str, Any]]
    valid_badges: int
    invalid_badges: int
    ocr_results: List[Dict[str, str]]


class AttributeAnalysisResult(BaseModel):
    """Resultado específico de análise de atributos"""
    person_detected: bool
    attributes: Dict[str, Any]
    dress_code_compliance: bool
    uniform_detected: bool
    accessories: List[str]


class ScheduleAnalysisResult(BaseModel):
    """Resultado específico de análise de horário"""
    compliance_status: str
    expected_status: str
    current_status: str
    schedule_match: bool
    anomalies: List[Dict[str, Any]]
    risk_level: RiskLevelEnum


class PatternAnalysisResult(BaseModel):
    """Resultado específico de análise de padrões"""
    patterns_detected: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    behavior_score: float
    risk_assessment: Dict[str, Any]


class ModelInfo(BaseModel):
    """Informações do modelo"""
    model_name: str
    version: str
    stage: str
    accuracy: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    metrics: Optional[Dict[str, float]] = None


class ModelListResponse(BaseModel):
    """Resposta da lista de modelos"""
    models: List[ModelInfo]
    total: int


class ModelTrainingRequest(BaseModel):
    """Requisição de treinamento de modelo"""
    model_type: str
    dataset_path: str
    parameters: Dict[str, Any]
    experiment_name: Optional[str] = None


class ModelTrainingResponse(BaseModel):
    """Resposta do treinamento de modelo"""
    training_id: str
    status: str
    experiment_id: str
    run_id: str
    estimated_duration_minutes: Optional[int] = None


class SystemMetrics(BaseModel):
    """Métricas do sistema"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    gpu_usage: Optional[float] = None
    active_connections: int
    requests_per_minute: float
    average_response_time_ms: float


class AlertConfig(BaseModel):
    """Configuração de alerta"""
    alert_type: str
    enabled: bool
    threshold: float
    notification_channels: List[str]
    conditions: Dict[str, Any]


class AlertResponse(BaseModel):
    """Resposta de alerta"""
    alert_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    resolved: bool
    metadata: Dict[str, Any]


class EventFilter(BaseModel):
    """Filtro para eventos"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_type: Optional[str] = None
    location: Optional[str] = None
    risk_level: Optional[RiskLevelEnum] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class EventResponse(BaseModel):
    """Resposta de evento"""
    event_id: str
    event_type: str
    timestamp: datetime
    location: Optional[str] = None
    details: Dict[str, Any]
    risk_level: RiskLevelEnum
    processed: bool


class EventListResponse(BaseModel):
    """Resposta da lista de eventos"""
    events: List[EventResponse]
    total: int
    has_more: bool


class ConfigUpdate(BaseModel):
    """Atualização de configuração"""
    section: str
    key: str
    value: Any
    description: Optional[str] = None


class ConfigResponse(BaseModel):
    """Resposta de configuração"""
    section: str
    key: str
    value: Any
    description: Optional[str] = None
    updated_at: datetime


class HealthCheckResponse(BaseModel):
    """Resposta do health check"""
    status: str
    services: Dict[str, str]
    timestamp: datetime
    version: str = "1.0.0"


class StatisticsResponse(BaseModel):
    """Resposta de estatísticas"""
    total_detections: int
    detections_today: int
    average_confidence: float
    most_common_alerts: List[Dict[str, Any]]
    system_uptime: str
    performance_metrics: Dict[str, float]


class BatchAnalysisRequest(BaseModel):
    """Requisição de análise em lote"""
    images: List[ImageInput]
    analysis_type: AnalysisTypeEnum
    batch_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class BatchAnalysisResponse(BaseModel):
    """Resposta de análise em lote"""
    batch_id: str
    status: str
    total_images: int
    processed_images: int
    results: List[AnalysisResult]
    started_at: datetime
    estimated_completion: Optional[datetime] = None 