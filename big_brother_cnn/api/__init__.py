"""
Módulo da API FastAPI para Big Brother CNN
"""

from .main import app
from .routes import *
from .models import *
from .dependencies import *

__all__ = ['app'] 