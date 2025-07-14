"""
Analyzer para detecção de atributos de pessoas
Baseado no dataset WIDER Attribute (14 atributos binários)
"""

import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image

from .base_analyzer import BaseAnalyzer


class AttributeAnalyzer(BaseAnalyzer):
    """
    Analyzer especializado em detecção de atributos de pessoas
    
    Baseado no WIDER Attribute Dataset com 14 atributos:
    - Vestimentas: formal/casual, manga longa/curta, calças/saia
    - Acessórios: óculos, chapéu, bolsa/mochila
    - Características: gênero, idade aproximada
    - Estado: em pé/sentado, virado de frente/costas
    """
    
    # Mapeamento dos 14 atributos do WIDER Dataset
    WIDER_ATTRIBUTES = {
        0: 'Male',           # Masculino
        1: 'LongHair',       # Cabelo longo
        2: 'Eyeglasses',     # Óculos
        3: 'Hat',            # Chapéu/boné
        4: 'Shirt',          # Camisa
        5: 'LongPants',      # Calça comprida
        6: 'Skirt',          # Saia
        7: 'LongSleeve',     # Manga longa
        8: 'Bag',            # Bolsa/mochila
        9: 'FacingFront',    # Virado de frente
        10: 'Simple',        # Fundo simples
        11: 'Pose',          # Pose específica
        12: 'Action',        # Em ação/movimento
        13: 'Crowd'          # Em multidão
    }
    
    # Atributos críticos para vigilância corporativa
    CRITICAL_ATTRIBUTES = {
        'formal_attire': ['Shirt', 'LongPants'],  # Vestimenta formal
        'accessories': ['Eyeglasses', 'Hat', 'Bag'],  # Acessórios
        'identification_risk': ['Hat', 'Eyeglasses'],  # Pode dificultar identificação
        'professional_appearance': ['Shirt', 'LongPants', 'LongSleeve']  # Aparência profissional
    }
    
    def __init__(self, config: Dict[str, Any], device: torch.device):
        super().__init__(config, device)
        self.attribute_model = None
        self.person_detector = None
        
        # Configurações específicas para atributos
        self.attr_config = config.get('analyzers', {}).get('attributes', {
            'confidence_threshold': 0.7,
            'min_person_size': 100,
            'required_formal_score': 0.6,
            'detect_uniforms': True,
            'track_accessories': True
        })
        
    def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        Carrega modelo para detecção de atributos
        """
        try:
            # Modelo baseado em ResNet para classificação multi-atributo
            self.attribute_model = self._build_attribute_model()
            
            if model_path:
                checkpoint = torch.load(model_path, map_location=self.device)
                self.attribute_model.load_state_dict(checkpoint)
            
            self.attribute_model.to(self.device)
            self.attribute_model.eval()
            
            # Detector de pessoas (YOLO ou similar seria ideal)
            self.person_detector = self._load_person_detector()
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            print(f"Erro ao carregar modelo de atributos: {e}")
            return False
    
    def _build_attribute_model(self) -> nn.Module:
        """
        Constrói modelo para classificação multi-atributo
        """
        # Base ResNet-50
        backbone = models.resnet50(pretrained=True)
        
        # Remover classificador original
        backbone = nn.Sequential(*list(backbone.children())[:-1])
        
        # Classificador multi-atributo (14 atributos binários)
        model = nn.Sequential(
            backbone,
            nn.Flatten(),
            nn.Dropout(0.5),
            nn.Linear(2048, 1024),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Linear(512, 14),  # 14 atributos do WIDER
            nn.Sigmoid()  # Probabilidades independentes para cada atributo
        )
        
        return model
    
    def _load_person_detector(self):
        """
        Carrega detector de pessoas (placeholder - usar YOLO em produção)
        """
        # Placeholder: usar detector simples OpenCV
        # Em produção, usar YOLOv5/v8 ou similar
        return cv2.HOGDescriptor()
    
    def analyze(self, image: torch.Tensor, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Realiza análise completa de atributos
        """
        results = {
            'detected': False,
            'confidence': 0.0,
            'persons_count': 0,
            'persons': [],
            'dress_code_compliant': False,
            'formal_score': 0.0,
            'uniform_detected': False,
            'critical_attributes': {},
            'accessories_detected': []
        }
        
        try:
            # Converter tensor para array
            img_array = self._tensor_to_array(image)
            
            # Detectar pessoas
            persons = self._detect_persons(img_array)
            results['persons_count'] = len(persons)
            results['detected'] = len(persons) > 0
            
            if len(persons) > 0:
                # Analisar atributos de cada pessoa
                for i, person_bbox in enumerate(persons):
                    person_analysis = self._analyze_person_attributes(img_array, person_bbox)
                    results['persons'].append(person_analysis)
                    
                    # Atualizar métricas gerais
                    if person_analysis['confidence'] > results['confidence']:
                        results['confidence'] = person_analysis['confidence']
                
                # Análise consolidada
                results.update(self._analyze_dress_code(results['persons']))
                results.update(self._analyze_accessories(results['persons']))
                results.update(self._analyze_uniform_compliance(results['persons']))
            
        except Exception as e:
            print(f"Erro na análise de atributos: {e}")
            results['error'] = str(e)
        
        return self.postprocess_results(results)
    
    def _detect_persons(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detecta pessoas na imagem
        """
        persons = []
        
        try:
            # Placeholder: detecção simples com HOG
            # Em produção, usar YOLO ou detector mais robusto
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            
            # Detectar pessoas
            rects, weights = hog.detectMultiScale(
                image, 
                winStride=(8, 8),
                padding=(32, 32),
                scale=1.05
            )
            
            # Filtrar por tamanho mínimo e confiança
            for i, (x, y, w, h) in enumerate(rects):
                if w >= self.attr_config['min_person_size'] and h >= self.attr_config['min_person_size']:
                    if len(weights) > i and weights[i] > 0.5:
                        persons.append((x, y, w, h))
            
        except Exception as e:
            print(f"Erro na detecção de pessoas: {e}")
        
        return persons
    
    def _analyze_person_attributes(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> Dict[str, Any]:
        """
        Analisa atributos de uma pessoa específica
        """
        x, y, w, h = bbox
        
        analysis = {
            'bbox': [x, y, w, h],
            'confidence': 0.0,
            'attributes': {},
            'attribute_scores': {},
            'formal_score': 0.0,
            'risk_factors': []
        }
        
        try:
            # Extrair região da pessoa
            person_image = image[y:y+h, x:x+w]
            
            # Pré-processar para o modelo
            person_tensor = self._preprocess_person_image(person_image)
            
            # Predição de atributos
            with torch.no_grad():
                predictions = self.attribute_model(person_tensor)
                scores = predictions.cpu().numpy()[0]
            
            # Processar cada atributo
            for attr_id, attr_name in self.WIDER_ATTRIBUTES.items():
                score = float(scores[attr_id])
                analysis['attribute_scores'][attr_name] = score
                analysis['attributes'][attr_name] = score > 0.5
            
            # Calcular confiança geral
            analysis['confidence'] = np.mean(np.maximum(scores, 1 - scores))
            
            # Análise específica para contexto corporativo
            analysis.update(self._analyze_corporate_attributes(analysis['attributes'], analysis['attribute_scores']))
            
        except Exception as e:
            print(f"Erro na análise de atributos da pessoa: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_corporate_attributes(self, attributes: Dict[str, bool], scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Análise específica para contexto corporativo
        """
        corporate_analysis = {
            'formal_score': 0.0,
            'uniform_compliance': False,
            'identification_risk': False,
            'accessories': [],
            'dress_code_violations': []
        }
        
        # Score de formalidade
        formal_indicators = ['Shirt', 'LongPants', 'LongSleeve']
        formal_scores = [scores.get(attr, 0) for attr in formal_indicators]
        corporate_analysis['formal_score'] = np.mean(formal_scores)
        
        # Conformidade com uniforme
        if corporate_analysis['formal_score'] > self.attr_config['required_formal_score']:
            corporate_analysis['uniform_compliance'] = True
        
        # Risco de identificação (chapéu, óculos escuros, etc.)
        risk_factors = []
        if attributes.get('Hat', False):
            risk_factors.append('chapeu_bone')
        if attributes.get('Eyeglasses', False) and scores.get('Eyeglasses', 0) > 0.8:
            risk_factors.append('oculos_escuros')
        
        corporate_analysis['identification_risk'] = len(risk_factors) > 0
        corporate_analysis['risk_factors'] = risk_factors
        
        # Acessórios detectados
        accessories = []
        if attributes.get('Bag', False):
            accessories.append('bolsa_mochila')
        if attributes.get('Eyeglasses', False):
            accessories.append('oculos')
        if attributes.get('Hat', False):
            accessories.append('chapeu_bone')
        
        corporate_analysis['accessories'] = accessories
        
        # Violações do dress code
        violations = []
        if not attributes.get('Shirt', False):
            violations.append('sem_camisa_formal')
        if attributes.get('Skirt', False) and not attributes.get('LongPants', False):
            violations.append('saia_em_ambiente_restrito')
        
        corporate_analysis['dress_code_violations'] = violations
        
        return corporate_analysis
    
    def _analyze_dress_code(self, persons: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Análise consolidada do dress code
        """
        if not persons:
            return {'dress_code_compliant': False, 'formal_score': 0.0}
        
        # Score médio de formalidade
        formal_scores = [p.get('formal_score', 0) for p in persons]
        avg_formal_score = np.mean(formal_scores)
        
        # Conformidade geral
        compliant = avg_formal_score >= self.attr_config['required_formal_score']
        
        return {
            'dress_code_compliant': compliant,
            'formal_score': avg_formal_score,
            'formal_score_distribution': formal_scores
        }
    
    def _analyze_accessories(self, persons: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Análise consolidada de acessórios
        """
        all_accessories = []
        risk_persons = 0
        
        for person in persons:
            accessories = person.get('accessories', [])
            all_accessories.extend(accessories)
            
            if person.get('identification_risk', False):
                risk_persons += 1
        
        # Contar frequência de acessórios
        accessory_counts = {}
        for acc in all_accessories:
            accessory_counts[acc] = accessory_counts.get(acc, 0) + 1
        
        return {
            'accessories_detected': list(set(all_accessories)),
            'accessory_frequency': accessory_counts,
            'identification_risk_count': risk_persons,
            'total_accessories': len(all_accessories)
        }
    
    def _analyze_uniform_compliance(self, persons: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Análise de conformidade com uniforme
        """
        if not persons:
            return {'uniform_detected': False}
        
        # Verificar se a maioria está em conformidade
        compliant_persons = sum(1 for p in persons if p.get('uniform_compliance', False))
        compliance_rate = compliant_persons / len(persons)
        
        # Detectar se há padrão de uniforme
        uniform_detected = compliance_rate >= 0.7  # 70% das pessoas em conformidade
        
        return {
            'uniform_detected': uniform_detected,
            'compliance_rate': compliance_rate,
            'compliant_persons': compliant_persons,
            'non_compliant_persons': len(persons) - compliant_persons
        }
    
    def _preprocess_person_image(self, person_image: np.ndarray) -> torch.Tensor:
        """
        Pré-processa imagem da pessoa para o modelo
        """
        # Redimensionar para tamanho esperado
        person_image = cv2.resize(person_image, (224, 224))
        
        # Converter para tensor
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        pil_image = Image.fromarray(person_image)
        tensor = transform(pil_image).unsqueeze(0).to(self.device)
        
        return tensor
    
    def _tensor_to_array(self, tensor: torch.Tensor) -> np.ndarray:
        """
        Converte tensor para array numpy
        """
        if tensor.dim() == 4:
            tensor = tensor.squeeze(0)
        
        if tensor.dim() == 3 and tensor.shape[0] == 3:
            tensor = tensor.permute(1, 2, 0)
        
        if tensor.min() < 0:
            tensor = (tensor + 1) / 2
        
        array = (tensor.cpu().numpy() * 255).astype(np.uint8)
        return array
    
    def get_confidence_threshold(self) -> float:
        """
        Retorna threshold de confiança para atributos
        """
        return self.attr_config['confidence_threshold']
    
    def get_attribute_summary(self, results: Dict[str, Any]) -> Dict[str, str]:
        """
        Gera resumo legível dos atributos detectados
        """
        summary = {}
        
        if results.get('dress_code_compliant', False):
            summary['dress_code'] = '✅ Em conformidade'
        else:
            summary['dress_code'] = '❌ Fora do padrão'
        
        if results.get('uniform_detected', False):
            summary['uniform'] = '✅ Uniforme detectado'
        else:
            summary['uniform'] = '❌ Sem uniforme padrão'
        
        accessories = results.get('accessories_detected', [])
        if accessories:
            summary['accessories'] = f"🎒 {', '.join(accessories)}"
        else:
            summary['accessories'] = '👤 Sem acessórios visíveis'
        
        risk_count = results.get('identification_risk_count', 0)
        if risk_count > 0:
            summary['security'] = f'⚠️ {risk_count} pessoa(s) com risco de identificação'
        else:
            summary['security'] = '✅ Identificação clara'
        
        return summary 