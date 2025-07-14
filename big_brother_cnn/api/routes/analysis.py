"""
Rotas para análise de imagens
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import uuid
import time
import base64
import numpy as np
import cv2
from datetime import datetime

from ..models import (
    AnalysisRequest, AnalysisResult, BatchAnalysisRequest, 
    BatchAnalysisResponse, BaseResponse, StatusEnum,
    FaceDetectionResult, BadgeDetectionResult, AttributeAnalysisResult,
    ScheduleAnalysisResult, PatternAnalysisResult
)
from ..dependencies import (
    get_storage_manager, get_mlflow_tracker, get_current_user,
    validate_image_size, get_metrics_collector
)
from ...analyzers.face_analyzer import FaceAnalyzer
from ...analyzers.badge_analyzer import BadgeAnalyzer
from ...analyzers.attribute_analyzer import AttributeAnalyzer
from ...analyzers.schedule_analyzer import ScheduleAnalyzer
from ...analyzers.pattern_analyzer import PatternAnalyzer
from ...utils.storage import StorageManager
from ...utils.mlflow_integration import MLflowTracker

router = APIRouter()

# Cache de analyzers
_analyzers = {}

def get_analyzer(analysis_type: str, config: Dict[str, Any], device):
    """
    Obtém analyzer com cache
    """
    if analysis_type not in _analyzers:
        if analysis_type == "face":
            _analyzers[analysis_type] = FaceAnalyzer(config, device)
        elif analysis_type == "badge":
            _analyzers[analysis_type] = BadgeAnalyzer(config, device)
        elif analysis_type == "attribute":
            _analyzers[analysis_type] = AttributeAnalyzer(config, device)
        elif analysis_type == "schedule":
            _analyzers[analysis_type] = ScheduleAnalyzer(config, device)
        elif analysis_type == "pattern":
            _analyzers[analysis_type] = PatternAnalyzer(config, device)
        else:
            raise ValueError(f"Tipo de análise não suportado: {analysis_type}")
    
    return _analyzers[analysis_type]

def decode_image(image_data: str) -> np.ndarray:
    """
    Decodifica imagem base64 para numpy array
    """
    try:
        decoded = base64.b64decode(image_data)
        nparr = np.frombuffer(decoded, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return image
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao decodificar imagem: {e}")

@router.post("/analyze", response_model=AnalysisResult)
async def analyze_image(
    request: AnalysisRequest,
    storage_manager: StorageManager = Depends(get_storage_manager),
    mlflow_tracker: MLflowTracker = Depends(get_mlflow_tracker),
    current_user: dict = Depends(get_current_user),
    metrics_collector = Depends(get_metrics_collector)
):
    """
    Analisa uma imagem usando o analyzer especificado
    """
    start_time = time.time()
    analysis_id = str(uuid.uuid4())
    
    try:
        # Validar tamanho da imagem
        validate_image_size(request.image.image_data)
        
        # Decodificar imagem
        image = decode_image(request.image.image_data)
        
        # Obter analyzer
        import torch
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        config = storage_manager.config  # Assumindo que config está no storage_manager
        analyzer = get_analyzer(request.analysis_type, config, device)
        
        # Preparar metadados
        metadata = {
            'detection_time': datetime.now(),
            'employee_info': {},
            'location': request.image.metadata.get('location') if request.image.metadata else None
        }
        
        # Executar análise
        import torch
        image_tensor = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        result = analyzer.analyze(image_tensor, metadata)
        
        # Calcular tempo de processamento
        processing_time = (time.time() - start_time) * 1000
        
        # Salvar imagem no MinIO se necessário
        if request.image.filename:
            object_name = f"analysis/{analysis_id}/{request.image.filename}"
            storage_manager.save_image(image, "processed-images", object_name)
        
        # Publicar evento no Kafka
        event = {
            "analysis_id": analysis_id,
            "analysis_type": request.analysis_type,
            "result": result,
            "user": current_user["username"],
            "processing_time_ms": processing_time
        }
        storage_manager.publish_event("analyzed-events", event, key=analysis_id)
        
        # Coletar métricas
        metrics_collector.increment(f"analysis_{request.analysis_type}_count")
        metrics_collector.gauge(f"analysis_{request.analysis_type}_time", processing_time)
        
        return AnalysisResult(
            analysis_id=analysis_id,
            analysis_type=request.analysis_type,
            result=result,
            confidence=result.get('confidence', 0.0),
            processing_time_ms=processing_time,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        metrics_collector.increment("analysis_errors")
        raise HTTPException(status_code=500, detail=f"Erro na análise: {e}")

@router.post("/analyze/face", response_model=FaceDetectionResult)
async def analyze_face(
    request: AnalysisRequest,
    storage_manager: StorageManager = Depends(get_storage_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    Análise específica de detecção facial
    """
    try:
        # Validar que é análise facial
        if request.analysis_type != "face":
            raise HTTPException(status_code=400, detail="Tipo de análise deve ser 'face'")
        
        # Executar análise
        result = await analyze_image(request, storage_manager, current_user)
        
        # Converter para formato específico
        face_result = result.result
        return FaceDetectionResult(
            faces_detected=face_result.get('faces_detected', 0),
            faces=face_result.get('faces', []),
            recognized_employees=face_result.get('recognized_employees', []),
            unknown_faces=face_result.get('unknown_faces', 0),
            confidence_threshold=face_result.get('confidence_threshold', 0.6)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise facial: {e}")

@router.post("/analyze/badge", response_model=BadgeDetectionResult)
async def analyze_badge(
    request: AnalysisRequest,
    storage_manager: StorageManager = Depends(get_storage_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    Análise específica de detecção de crachá
    """
    try:
        if request.analysis_type != "badge":
            raise HTTPException(status_code=400, detail="Tipo de análise deve ser 'badge'")
        
        result = await analyze_image(request, storage_manager, current_user)
        
        badge_result = result.result
        return BadgeDetectionResult(
            badges_detected=badge_result.get('badges_detected', 0),
            badges=badge_result.get('badges', []),
            valid_badges=badge_result.get('valid_badges', 0),
            invalid_badges=badge_result.get('invalid_badges', 0),
            ocr_results=badge_result.get('ocr_results', [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise de crachá: {e}")

@router.post("/analyze/attribute", response_model=AttributeAnalysisResult)
async def analyze_attributes(
    request: AnalysisRequest,
    storage_manager: StorageManager = Depends(get_storage_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    Análise específica de atributos
    """
    try:
        if request.analysis_type != "attribute":
            raise HTTPException(status_code=400, detail="Tipo de análise deve ser 'attribute'")
        
        result = await analyze_image(request, storage_manager, current_user)
        
        attr_result = result.result
        return AttributeAnalysisResult(
            person_detected=attr_result.get('person_detected', False),
            attributes=attr_result.get('attributes', {}),
            dress_code_compliance=attr_result.get('dress_code_compliance', False),
            uniform_detected=attr_result.get('uniform_detected', False),
            accessories=attr_result.get('accessories', [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise de atributos: {e}")

@router.post("/analyze/schedule", response_model=ScheduleAnalysisResult)
async def analyze_schedule(
    request: AnalysisRequest,
    storage_manager: StorageManager = Depends(get_storage_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    Análise específica de horários
    """
    try:
        if request.analysis_type != "schedule":
            raise HTTPException(status_code=400, detail="Tipo de análise deve ser 'schedule'")
        
        result = await analyze_image(request, storage_manager, current_user)
        
        schedule_result = result.result
        return ScheduleAnalysisResult(
            compliance_status=schedule_result.get('compliance_status', 'unknown'),
            expected_status=schedule_result.get('expected_status', 'unknown'),
            current_status=schedule_result.get('current_status', 'present'),
            schedule_match=schedule_result.get('schedule_match', False),
            anomalies=schedule_result.get('anomalies', []),
            risk_level=schedule_result.get('risk_level', 'low')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise de horários: {e}")

@router.post("/analyze/pattern", response_model=PatternAnalysisResult)
async def analyze_patterns(
    request: AnalysisRequest,
    storage_manager: StorageManager = Depends(get_storage_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    Análise específica de padrões
    """
    try:
        if request.analysis_type != "pattern":
            raise HTTPException(status_code=400, detail="Tipo de análise deve ser 'pattern'")
        
        result = await analyze_image(request, storage_manager, current_user)
        
        pattern_result = result.result
        return PatternAnalysisResult(
            patterns_detected=pattern_result.get('patterns_detected', []),
            anomalies=pattern_result.get('anomalies', []),
            behavior_score=pattern_result.get('behavior_score', 0.0),
            risk_assessment=pattern_result.get('risk_assessment', {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise de padrões: {e}")

@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    storage_manager: StorageManager = Depends(get_storage_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    Análise em lote de múltiplas imagens
    """
    batch_id = request.batch_id or str(uuid.uuid4())
    
    try:
        # Validar imagens
        for img in request.images:
            validate_image_size(img.image_data)
        
        # Criar resposta inicial
        response = BatchAnalysisResponse(
            batch_id=batch_id,
            status="processing",
            total_images=len(request.images),
            processed_images=0,
            results=[],
            started_at=datetime.now()
        )
        
        # Processar imagens em background
        background_tasks.add_task(
            process_batch_analysis,
            batch_id,
            request,
            storage_manager,
            current_user
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise em lote: {e}")

async def process_batch_analysis(
    batch_id: str,
    request: BatchAnalysisRequest,
    storage_manager: StorageManager,
    current_user: dict
):
    """
    Processa análise em lote em background
    """
    results = []
    
    for i, image in enumerate(request.images):
        try:
            # Criar requisição individual
            analysis_request = AnalysisRequest(
                image=image,
                analysis_type=request.analysis_type,
                parameters=request.parameters
            )
            
            # Executar análise
            result = await analyze_image(analysis_request, storage_manager, current_user)
            results.append(result)
            
            # Publicar progresso
            progress_event = {
                "batch_id": batch_id,
                "processed": i + 1,
                "total": len(request.images),
                "status": "processing"
            }
            storage_manager.publish_event("batch-progress", progress_event, key=batch_id)
            
        except Exception as e:
            # Log erro mas continua processamento
            print(f"Erro ao processar imagem {i}: {e}")
    
    # Publicar conclusão
    completion_event = {
        "batch_id": batch_id,
        "status": "completed",
        "total_results": len(results),
        "completed_at": datetime.now().isoformat()
    }
    storage_manager.publish_event("batch-completed", completion_event, key=batch_id)

@router.get("/batch/{batch_id}", response_model=BatchAnalysisResponse)
async def get_batch_status(
    batch_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém status de análise em lote
    """
    # Implementar busca do status no banco/cache
    # Por enquanto, retorna resposta mockada
    return BatchAnalysisResponse(
        batch_id=batch_id,
        status="completed",
        total_images=10,
        processed_images=10,
        results=[],
        started_at=datetime.now()
    )

@router.get("/history")
async def get_analysis_history(
    limit: int = 100,
    offset: int = 0,
    analysis_type: str = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém histórico de análises
    """
    # Implementar busca no banco de dados
    # Por enquanto, retorna resposta mockada
    return {
        "analyses": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    } 