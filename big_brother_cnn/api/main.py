"""
Aplicação principal FastAPI para Big Brother CNN
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import yaml
import logging
from typing import Dict, Any

from .routes import (
    analysis_router,
    detection_router,
    model_router,
    monitoring_router,
    admin_router
)
from .dependencies import get_config, get_storage_manager, get_mlflow_tracker
from ..utils.storage import StorageManager
from ..utils.mlflow_integration import MLflowTracker

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gerenciadores globais
storage_manager: StorageManager = None
mlflow_tracker: MLflowTracker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerenciador de ciclo de vida da aplicação
    """
    global storage_manager, mlflow_tracker
    
    # Startup
    logger.info("Iniciando Big Brother CNN API...")
    
    try:
        # Carregar configuração
        with open('big_brother_cnn/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Inicializar gerenciadores
        storage_manager = StorageManager(config)
        mlflow_tracker = MLflowTracker(config)
        
        logger.info("Serviços inicializados com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro na inicialização: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Finalizando Big Brother CNN API...")
    
    try:
        if storage_manager:
            storage_manager.close()
        if mlflow_tracker:
            mlflow_tracker.close()
        logger.info("Serviços finalizados com sucesso!")
    except Exception as e:
        logger.error(f"Erro na finalização: {e}")


# Criar aplicação FastAPI
app = FastAPI(
    title="Big Brother CNN API",
    description="API para sistema de vigilância com IA - Big Brother CNN",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Routers
app.include_router(
    analysis_router,
    prefix="/api/v1/analysis",
    tags=["Analysis"]
)

app.include_router(
    detection_router,
    prefix="/api/v1/detection",
    tags=["Detection"]
)

app.include_router(
    model_router,
    prefix="/api/v1/models",
    tags=["Models"]
)

app.include_router(
    monitoring_router,
    prefix="/api/v1/monitoring",
    tags=["Monitoring"]
)

app.include_router(
    admin_router,
    prefix="/api/v1/admin",
    tags=["Admin"]
)

# Endpoints principais
@app.get("/")
async def root():
    """
    Endpoint raiz
    """
    return {
        "message": "Big Brother CNN API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """
    Endpoint de health check
    """
    global storage_manager, mlflow_tracker
    
    services_status = {
        "api": "healthy",
        "storage": "unknown",
        "mlflow": "unknown"
    }
    
    # Verificar Storage Manager
    try:
        if storage_manager and storage_manager.kafka_producer:
            services_status["storage"] = "healthy"
        else:
            services_status["storage"] = "unhealthy"
    except Exception:
        services_status["storage"] = "unhealthy"
    
    # Verificar MLflow Tracker
    try:
        if mlflow_tracker and mlflow_tracker.client:
            services_status["mlflow"] = "healthy"
        else:
            services_status["mlflow"] = "unhealthy"
    except Exception:
        services_status["mlflow"] = "unhealthy"
    
    overall_status = "healthy" if all(
        status == "healthy" for status in services_status.values()
    ) else "degraded"
    
    return {
        "status": overall_status,
        "services": services_status,
        "timestamp": "2024-01-01T00:00:00Z"  # Placeholder
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Handler para exceções HTTP
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": "2024-01-01T00:00:00Z"  # Placeholder
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Handler para exceções gerais
    """
    logger.error(f"Erro interno: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "status_code": 500,
            "timestamp": "2024-01-01T00:00:00Z"  # Placeholder
        }
    )

# Função para executar a aplicação
def run_server():
    """
    Executa o servidor FastAPI
    """
    uvicorn.run(
        "big_brother_cnn.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    run_server() 