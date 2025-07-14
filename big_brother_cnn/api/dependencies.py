"""
Dependências para injeção na API FastAPI
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import yaml
import os
from typing import Dict, Any
import jwt
from datetime import datetime, timedelta

from ..utils.storage import StorageManager
from ..utils.mlflow_integration import MLflowTracker

# Configuração global
_config: Dict[str, Any] = None
_storage_manager: StorageManager = None
_mlflow_tracker: MLflowTracker = None

# Segurança
security = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_config() -> Dict[str, Any]:
    """
    Dependência para obter configuração
    """
    global _config
    if _config is None:
        try:
            with open('big_brother_cnn/config.yaml', 'r') as f:
                _config = yaml.safe_load(f)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao carregar configuração: {e}"
            )
    return _config


def get_storage_manager() -> StorageManager:
    """
    Dependência para obter Storage Manager
    """
    global _storage_manager
    if _storage_manager is None:
        config = get_config()
        try:
            _storage_manager = StorageManager(config)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao inicializar Storage Manager: {e}"
            )
    return _storage_manager


def get_mlflow_tracker() -> MLflowTracker:
    """
    Dependência para obter MLflow Tracker
    """
    global _mlflow_tracker
    if _mlflow_tracker is None:
        config = get_config()
        try:
            _mlflow_tracker = MLflowTracker(config)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao inicializar MLflow Tracker: {e}"
            )
    return _mlflow_tracker


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Cria token JWT
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifica token JWT
    """
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token: str = Depends(verify_token)):
    """
    Obtém usuário atual baseado no token
    """
    # Aqui você pode implementar a lógica para buscar o usuário no banco
    # Por enquanto, retornamos um usuário mockado
    return {
        "username": token,
        "role": "admin",  # ou buscar do banco
        "permissions": ["read", "write", "admin"]
    }


def require_admin(current_user: dict = Depends(get_current_user)):
    """
    Requer permissão de administrador
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Permissão de administrador necessária."
        )
    return current_user


def require_write_permission(current_user: dict = Depends(get_current_user)):
    """
    Requer permissão de escrita
    """
    if "write" not in current_user.get("permissions", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Permissão de escrita necessária."
        )
    return current_user


def get_pagination_params(limit: int = 100, offset: int = 0):
    """
    Parâmetros de paginação
    """
    if limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit não pode ser maior que 1000"
        )
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offset não pode ser negativo"
        )
    return {"limit": limit, "offset": offset}


def validate_image_size(image_data: str, max_size_mb: int = 10):
    """
    Valida tamanho da imagem
    """
    import base64
    try:
        decoded = base64.b64decode(image_data)
        size_mb = len(decoded) / (1024 * 1024)
        if size_mb > max_size_mb:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Imagem muito grande. Máximo: {max_size_mb}MB"
            )
        return True
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao validar imagem: {e}"
        )


def get_rate_limit_info():
    """
    Informações sobre rate limiting
    """
    # Implementar lógica de rate limiting aqui
    return {
        "requests_per_minute": 100,
        "requests_remaining": 95,
        "reset_time": datetime.utcnow() + timedelta(minutes=1)
    }


class DatabaseSession:
    """
    Contexto de sessão do banco de dados
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = None
    
    def __enter__(self):
        # Implementar criação de sessão
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Implementar fechamento de sessão
        if self.session:
            self.session.close()


def get_db_session(config: Dict[str, Any] = Depends(get_config)):
    """
    Dependência para sessão do banco de dados
    """
    return DatabaseSession(config)


def log_api_call(endpoint: str, method: str, user: str = None):
    """
    Log de chamadas da API
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"API Call: {method} {endpoint} by {user or 'anonymous'}")


def get_system_status():
    """
    Status do sistema
    """
    import psutil
    
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "timestamp": datetime.utcnow()
    }


def validate_analysis_type(analysis_type: str):
    """
    Valida tipo de análise
    """
    valid_types = ["face", "badge", "attribute", "schedule", "pattern", "integrated"]
    if analysis_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de análise inválido. Válidos: {valid_types}"
        )
    return analysis_type


def get_cache_manager():
    """
    Gerenciador de cache
    """
    # Implementar cache (Redis, etc.)
    class MockCache:
        def get(self, key):
            return None
        def set(self, key, value, ttl=300):
            pass
        def delete(self, key):
            pass
    
    return MockCache()


def get_metrics_collector():
    """
    Coletor de métricas
    """
    class MetricsCollector:
        def __init__(self):
            self.metrics = {}
        
        def increment(self, metric_name: str, value: int = 1):
            self.metrics[metric_name] = self.metrics.get(metric_name, 0) + value
        
        def gauge(self, metric_name: str, value: float):
            self.metrics[metric_name] = value
        
        def get_metrics(self):
            return self.metrics
    
    return MetricsCollector()


def cleanup_resources():
    """
    Limpeza de recursos
    """
    global _storage_manager, _mlflow_tracker
    try:
        if _storage_manager:
            _storage_manager.close()
        if _mlflow_tracker:
            _mlflow_tracker.close()
    except Exception as e:
        print(f"Erro na limpeza de recursos: {e}")


# Middleware personalizado para logging
class APILoggingMiddleware:
    """
    Middleware para logging de requisições
    """
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Log da requisição
            log_api_call(
                endpoint=scope["path"],
                method=scope["method"]
            )
        
        await self.app(scope, receive, send) 