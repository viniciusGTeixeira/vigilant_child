"""
Rotas administrativas
"""

from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import get_current_user

router = APIRouter()

@router.get("/users")
async def list_users(
    current_user: dict = Depends(get_current_user)
):
    """
    Lista usuários
    """
    return {"users": [{"id": 1, "username": "admin", "role": "admin"}]}

@router.get("/config")
async def get_config(
    current_user: dict = Depends(get_current_user)
):
    """
    Configuração do sistema
    """
    return {"config": {"debug": True, "version": "1.0.0"}}

@router.get("/logs")
async def get_logs(
    current_user: dict = Depends(get_current_user)
):
    """
    Logs do sistema
    """
    return {"logs": ["Sistema iniciado", "API funcionando"]}

@router.get("/system")
async def get_system_info(
    current_user: dict = Depends(get_current_user)
):
    """
    Informações do sistema
    """
    return {"system": {"status": "running", "uptime": "1h 30m"}} 