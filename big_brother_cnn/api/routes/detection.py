"""
Rotas para controle de detecção em tempo real
"""

from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import get_current_user

router = APIRouter()

@router.post("/start")
async def start_detection(
    current_user: dict = Depends(get_current_user)
):
    """
    Inicia detecção em tempo real
    """
    return {"message": "Detecção iniciada", "status": "active"}

@router.post("/stop")
async def stop_detection(
    current_user: dict = Depends(get_current_user)
):
    """
    Para detecção em tempo real
    """
    return {"message": "Detecção parada", "status": "stopped"}

@router.get("/status")
async def get_detection_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Status da detecção
    """
    return {"status": "stopped", "uptime": "0s"} 