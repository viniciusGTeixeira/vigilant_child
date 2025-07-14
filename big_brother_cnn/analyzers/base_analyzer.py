"""
Classe base para todos os analyzers do sistema
"""

from abc import ABC, abstractmethod
import torch
import numpy as np
from typing import Dict, Any, List, Optional
import json
from datetime import datetime


class BaseAnalyzer(ABC):
    
    def __init__(self, config: Dict[str, Any], device: torch.device):
        self.config = config
        self.device = device
        self.model = None
        self.is_loaded = False
        self.analyzer_name = self.__class__.__name__
        
    @abstractmethod
    def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        Carrega o modelo específico do analyzer
        """
        pass
    
    @abstractmethod
    def analyze(self, image: torch.Tensor, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Realiza análise específica na imagem
        """
        pass
    
    @abstractmethod
    def get_confidence_threshold(self) -> float:
        """
        Retorna threshold de confiança específico do analyzer
        """
        pass
    
    def preprocess_image(self, image: torch.Tensor) -> torch.Tensor:
        """
        Pré-processamento padrão da imagem
        Pode ser sobrescrito pelos analyzers específicos
        """
        if image.dim() == 3:
            image = image.unsqueeze(0)
        return image.to(self.device)
    
    def postprocess_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pós-processamento padrão dos resultados
        """
        # Adicionar metadados comuns
        results['analyzer'] = self.analyzer_name
        results['timestamp'] = datetime.now().isoformat()
        results['confidence_threshold'] = self.get_confidence_threshold()
        
        return results
    
    def validate_results(self, results: Dict[str, Any]) -> bool:
        """
        Valida se os resultados estão no formato esperado
        """
        required_fields = ['analyzer', 'timestamp', 'confidence', 'detected']
        return all(field in results for field in required_fields)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o modelo carregado
        """
        return {
            'analyzer_name': self.analyzer_name,
            'is_loaded': self.is_loaded,
            'device': str(self.device),
            'model_type': type(self.model).__name__ if self.model else None
        }
    
    def save_analysis_log(self, results: Dict[str, Any], log_dir: str = "logs") -> str:
        """
        Salva log da análise para debugging
        """
        import os
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        log_file = os.path.join(log_dir, f"{self.analyzer_name}_{timestamp}.json")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return log_file 