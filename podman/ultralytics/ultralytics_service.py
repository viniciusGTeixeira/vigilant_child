#!/usr/bin/env python3
"""
Serviço Ultralytics para detecção de badges e objetos
Python 3.12 compatível
"""

import os
import json
import base64
import time
from typing import Dict, List, Any
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
import torch
from ultralytics import YOLO

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from loguru import logger

# Configurar logging
logger.add("ultralytics_service.log", rotation="1 MB")

app = FastAPI(title="Ultralytics Service", version="1.0.0")

# Configuração global
yolo_model = None

class DetectionRequest(BaseModel):
    image_data: str  # Base64 encoded image
    confidence_threshold: float = 0.5
    detection_type: str = "badge"  # badge, object, person

class DetectionResponse(BaseModel):
    detections: List[Dict[str, Any]]
    processing_time_ms: float
    model_info: Dict[str, str]

def initialize_model():
    """Inicializar modelo YOLO"""
    global yolo_model
    
    try:
        # Usar YOLOv8 pré-treinado
        yolo_model = YOLO('yolov8n.pt')  # Modelo nano para rapidez
        logger.info("Modelo YOLOv8 inicializado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar modelo: {e}")
        raise

def decode_image(image_data: str) -> np.ndarray:
    """Decodificar imagem base64"""
    try:
        # Remover prefixo data:image se existir
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decodificar base64
        image_bytes = base64.b64decode(image_data)
        
        # Converter para numpy array
        image = Image.open(BytesIO(image_bytes))
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        return image
        
    except Exception as e:
        logger.error(f"Erro ao decodificar imagem: {e}")
        raise HTTPException(status_code=400, detail="Erro ao decodificar imagem")

def detect_objects(image: np.ndarray, confidence_threshold: float = 0.5, detection_type: str = "badge") -> List[Dict[str, Any]]:
    """Detectar objetos na imagem"""
    try:
        # Executar detecção
        results = yolo_model(image, conf=confidence_threshold)
        
        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for i, box in enumerate(boxes):
                    # Extrair informações da detecção
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = yolo_model.names[class_id]
                    
                    # Filtrar por tipo de detecção
                    if detection_type == "badge":
                        # Para badges, procurar por objetos que podem ser badges
                        if class_name in ["person", "handbag", "backpack", "tie", "cell phone", "book"]:
                            detection_class = "badge_candidate"
                        else:
                            continue
                    elif detection_type == "person":
                        if class_name != "person":
                            continue
                        detection_class = "person"
                    else:
                        detection_class = class_name
                    
                    detection = {
                        "id": i,
                        "class": detection_class,
                        "original_class": class_name,
                        "confidence": confidence,
                        "bbox": {
                            "x1": float(x1),
                            "y1": float(y1),
                            "x2": float(x2),
                            "y2": float(y2),
                            "width": float(x2 - x1),
                            "height": float(y2 - y1)
                        },
                        "center": {
                            "x": float((x1 + x2) / 2),
                            "y": float((y1 + y2) / 2)
                        }
                    }
                    detections.append(detection)
        
        return detections
        
    except Exception as e:
        logger.error(f"Erro na detecção: {e}")
        raise HTTPException(status_code=500, detail="Erro na detecção")

@app.on_event("startup")
async def startup_event():
    """Inicializar serviço"""
    logger.info("Iniciando serviço Ultralytics...")
    initialize_model()

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "ultralytics",
        "model_loaded": yolo_model is not None,
        "python_version": "3.12"
    }

@app.post("/detect", response_model=DetectionResponse)
async def detect_objects_endpoint(request: DetectionRequest):
    """Endpoint para detecção de objetos"""
    start_time = time.time()
    
    try:
        # Decodificar imagem
        image = decode_image(request.image_data)
        
        # Detectar objetos
        detections = detect_objects(image, request.confidence_threshold, request.detection_type)
        
        # Calcular tempo de processamento
        processing_time = (time.time() - start_time) * 1000
        
        return DetectionResponse(
            detections=detections,
            processing_time_ms=processing_time,
            model_info={
                "name": "YOLOv8",
                "version": "latest",
                "python_version": "3.12"
            }
        )
        
    except Exception as e:
        logger.error(f"Erro no endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/info")
async def get_model_info():
    """Informações do modelo"""
    return {
        "service": "ultralytics",
        "model": "YOLOv8n",
        "framework": "Ultralytics latest",
        "python_version": "3.12",
        "capabilities": ["badge_detection", "object_detection", "person_detection"],
        "input_formats": ["base64_image"],
        "output_format": "json"
    }

@app.get("/classes")
async def get_supported_classes():
    """Classes suportadas pelo modelo"""
    if yolo_model:
        return {
            "classes": yolo_model.names,
            "total_classes": len(yolo_model.names)
        }
    return {"error": "Modelo não carregado"}

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    ) 