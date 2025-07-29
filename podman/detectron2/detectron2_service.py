#!/usr/bin/env python3
"""
Serviço Detectron2 para detecção avançada de pessoas
Python 3.7 compatível
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
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from loguru import logger

# Configurar logging
logger.add("detectron2_service.log", rotation="1 MB")

app = FastAPI(title="Detectron2 Service", version="1.0.0")

# Configuração global
predictor = None

class DetectionRequest(BaseModel):
    image_data: str  # Base64 encoded image
    confidence_threshold: float = 0.5

class DetectionResponse(BaseModel):
    detections: List[Dict[str, Any]]
    processing_time_ms: float
    model_info: Dict[str, str]

def initialize_model():
    """Inicializar modelo Detectron2"""
    global predictor
    
    try:
        cfg = get_cfg()
        # Usar modelo pré-treinado para detecção de pessoas
        cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml")
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
        cfg.MODEL.DEVICE = "cpu"  # Usar CPU
        
        predictor = DefaultPredictor(cfg)
        logger.info("Modelo Detectron2 inicializado com sucesso")
        
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

def detect_persons(image: np.ndarray, confidence_threshold: float = 0.5) -> List[Dict[str, Any]]:
    """Detectar pessoas na imagem"""
    try:
        # Executar detecção
        outputs = predictor(image)
        
        # Extrair detecções
        instances = outputs["instances"].to("cpu")
        boxes = instances.pred_boxes.tensor.numpy()
        scores = instances.scores.numpy()
        classes = instances.pred_classes.numpy()
        
        # Filtrar apenas pessoas (classe 0 no COCO)
        person_detections = []
        for i, (box, score, cls) in enumerate(zip(boxes, scores, classes)):
            if cls == 0 and score >= confidence_threshold:  # Classe 0 = pessoa
                x1, y1, x2, y2 = box
                
                detection = {
                    "id": i,
                    "class": "person",
                    "confidence": float(score),
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
                person_detections.append(detection)
        
        return person_detections
        
    except Exception as e:
        logger.error(f"Erro na detecção: {e}")
        raise HTTPException(status_code=500, detail="Erro na detecção")

@app.on_event("startup")
async def startup_event():
    """Inicializar serviço"""
    logger.info("Iniciando serviço Detectron2...")
    initialize_model()

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "detectron2",
        "model_loaded": predictor is not None,
        "python_version": "3.7"
    }

@app.post("/detect", response_model=DetectionResponse)
async def detect_persons_endpoint(request: DetectionRequest):
    """Endpoint para detecção de pessoas"""
    start_time = time.time()
    
    try:
        # Decodificar imagem
        image = decode_image(request.image_data)
        
        # Detectar pessoas
        detections = detect_persons(image, request.confidence_threshold)
        
        # Calcular tempo de processamento
        processing_time = (time.time() - start_time) * 1000
        
        return DetectionResponse(
            detections=detections,
            processing_time_ms=processing_time,
            model_info={
                "name": "Detectron2",
                "version": "0.6",
                "python_version": "3.7"
            }
        )
        
    except Exception as e:
        logger.error(f"Erro no endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/info")
async def get_model_info():
    """Informações do modelo"""
    return {
        "service": "detectron2",
        "model": "Faster R-CNN R50 FPN",
        "framework": "Detectron2 0.6",
        "python_version": "3.7",
        "capabilities": ["person_detection", "advanced_detection"],
        "input_formats": ["base64_image"],
        "output_format": "json"
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    ) 