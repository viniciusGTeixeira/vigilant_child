"""
Rotas da API FastAPI
"""

from .analysis import router as analysis_router
from .detection import router as detection_router
from .models import router as model_router
from .monitoring import router as monitoring_router
from .admin import router as admin_router

__all__ = [
    'analysis_router',
    'detection_router', 
    'model_router',
    'monitoring_router',
    'admin_router'
] 