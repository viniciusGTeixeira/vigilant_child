"""
Analyzer para detecção de crachás de funcionários
Baseado em técnicas de detecção de objetos e OCR
"""

import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import pytesseract

from .base_analyzer import BaseAnalyzer


class BadgeAnalyzer(BaseAnalyzer):
    """
    Analyzer especializado em detecção de crachás
    
    Funcionalidades:
    - Detecção de presença de crachá
    - Verificação de visibilidade do crachá
    - OCR para extrair informações do crachá
    - Validação de formato e posicionamento
    - Detecção de funcionários sem crachá
    """
    
    def __init__(self, config: Dict[str, Any], device: torch.device):
        super().__init__(config, device)
        self.badge_detector = None
        self.ocr_engine = None
        
        # Configurações específicas para crachás
        self.badge_config = config.get('analyzers', {}).get('badge', {
            'min_badge_size': 30,
            'confidence_threshold': 0.7,
            'ocr_enabled': True,
            'required_badge_areas': ['chest', 'neck', 'waist'],
            'badge_colors': ['white', 'blue', 'red', 'yellow'],
            'text_confidence_threshold': 60
        })
        
    def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        Carrega modelos para detecção de crachás
        """
        try:
            # Modelo YOLOv5 customizado para detecção de crachás
            # Em produção, treinar modelo específico para crachás
            self.badge_detector = self._load_badge_detector(model_path)
            
            # Configurar OCR
            if self.badge_config['ocr_enabled']:
                self._setup_ocr()
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            print(f"Erro ao carregar modelo de crachás: {e}")
            return False
    
    def _load_badge_detector(self, model_path: Optional[str] = None):
        """
        Carrega detector de crachás baseado em CNN
        """
        # Modelo personalizado para detecção de objetos retangulares (crachás)
        model = models.resnet34(pretrained=True)
        
        # Modificar para detecção de objetos
        model.fc = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 5)  # [confidence, x, y, width, height]
        )
        
        if model_path:
            checkpoint = torch.load(model_path, map_location=self.device)
            model.load_state_dict(checkpoint)
        
        model.to(self.device)
        model.eval()
        
        return model
    
    def _setup_ocr(self):
        """
        Configura engine de OCR para leitura de texto em crachás
        """
        try:
            # Configurar Tesseract para melhor reconhecimento de texto em crachás
            self.ocr_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
            self.ocr_engine = pytesseract
            print("OCR configurado com sucesso")
        except Exception as e:
            print(f"Erro ao configurar OCR: {e}")
            self.badge_config['ocr_enabled'] = False
    
    def analyze(self, image: torch.Tensor, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Realiza análise completa de detecção de crachás
        """
        results = {
            'detected': False,
            'confidence': 0.0,
            'badges_count': 0,
            'badges': [],
            'has_valid_badge': False,
            'badge_visible': False,
            'employee_info_extracted': False,
            'extracted_text': [],
            'compliance_score': 0.0
        }
        
        try:
            # Converter tensor para array
            img_array = self._tensor_to_array(image)
            
            # Detectar crachás na imagem
            badges = self._detect_badges(img_array)
            results['badges_count'] = len(badges)
            results['detected'] = len(badges) > 0
            
            if len(badges) > 0:
                # Analisar cada crachá detectado
                for i, badge_region in enumerate(badges):
                    badge_analysis = self._analyze_single_badge(img_array, badge_region)
                    results['badges'].append(badge_analysis)
                    
                    # Atualizar confiança geral
                    if badge_analysis['confidence'] > results['confidence']:
                        results['confidence'] = badge_analysis['confidence']
                    
                    # Verificar se é um crachá válido
                    if badge_analysis.get('is_valid', False):
                        results['has_valid_badge'] = True
                    
                    # Verificar visibilidade
                    if badge_analysis.get('visibility_score', 0) > 0.7:
                        results['badge_visible'] = True
                    
                    # Coletar texto extraído
                    extracted_text = badge_analysis.get('extracted_text', '')
                    if extracted_text:
                        results['extracted_text'].append(extracted_text)
                        results['employee_info_extracted'] = True
                
                # Calcular score de conformidade
                results['compliance_score'] = self._calculate_compliance_score(results)
            else:
                # Analisar áreas típicas de crachá para verificar ausência
                results.update(self._analyze_badge_absence(img_array))
        
        except Exception as e:
            print(f"Erro na análise de crachás: {e}")
            results['error'] = str(e)
        
        return self.postprocess_results(results)
    
    def _detect_badges(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detecta crachás na imagem usando múltiplas técnicas
        """
        badges = []
        
        try:
            # Método 1: Detecção por cor e forma
            color_badges = self._detect_badges_by_color_shape(image)
            badges.extend(color_badges)
            
            # Método 2: Detecção por contornos retangulares
            contour_badges = self._detect_badges_by_contours(image)
            badges.extend(contour_badges)
            
            # Método 3: CNN detector (se disponível)
            if self.badge_detector:
                cnn_badges = self._detect_badges_cnn(image)
                badges.extend(cnn_badges)
            
            # Filtrar detecções duplicadas
            badges = self._filter_duplicate_detections(badges)
            
        except Exception as e:
            print(f"Erro na detecção de crachás: {e}")
        
        return badges
    
    def _detect_badges_by_color_shape(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detecta crachás baseado em cores típicas e formas retangulares
        """
        badges = []
        
        try:
            # Converter para HSV para melhor detecção de cores
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            # Definir ranges de cores para crachás típicos
            color_ranges = {
                'white': ([0, 0, 200], [180, 30, 255]),
                'blue': ([100, 50, 50], [130, 255, 255]),
                'red': ([0, 50, 50], [10, 255, 255]),
                'yellow': ([20, 50, 50], [30, 255, 255])
            }
            
            for color_name, (lower, upper) in color_ranges.items():
                if color_name in self.badge_config['badge_colors']:
                    # Criar máscara para a cor
                    mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                    
                    # Encontrar contornos
                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    for contour in contours:
                        # Verificar se o contorno é retangular e do tamanho adequado
                        if self._is_badge_candidate(contour):
                            x, y, w, h = cv2.boundingRect(contour)
                            badges.append({
                                'bbox': [x, y, w, h],
                                'detection_method': f'color_{color_name}',
                                'confidence': 0.6,
                                'color': color_name
                            })
        
        except Exception as e:
            print(f"Erro na detecção por cor: {e}")
        
        return badges
    
    def _detect_badges_by_contours(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detecta crachás baseado em contornos retangulares
        """
        badges = []
        
        try:
            # Converter para cinza
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Aplicar filtro bilateral para reduzir ruído
            filtered = cv2.bilateralFilter(gray, 9, 75, 75)
            
            # Detectar bordas
            edges = cv2.Canny(filtered, 50, 150, apertureSize=3)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                if self._is_badge_candidate(contour):
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Calcular características do retângulo
                    aspect_ratio = w / h
                    rectangularity = cv2.contourArea(contour) / (w * h)
                    
                    # Crachás típicos têm aspect ratio entre 1.2 e 2.0
                    if 1.2 <= aspect_ratio <= 2.0 and rectangularity > 0.7:
                        badges.append({
                            'bbox': [x, y, w, h],
                            'detection_method': 'contour',
                            'confidence': min(0.8, rectangularity),
                            'aspect_ratio': aspect_ratio,
                            'rectangularity': rectangularity
                        })
        
        except Exception as e:
            print(f"Erro na detecção por contornos: {e}")
        
        return badges
    
    def _detect_badges_cnn(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detecta crachás usando CNN treinado
        """
        badges = []
        
        try:
            if not self.badge_detector:
                return badges
            
            # Pré-processar imagem
            processed_image = self._preprocess_for_cnn(image)
            
            # Fazer predição
            with torch.no_grad():
                prediction = self.badge_detector(processed_image)
                confidence, x, y, w, h = prediction[0].cpu().numpy()
            
            # Se confiança é alta o suficiente
            if confidence > self.badge_config['confidence_threshold']:
                badges.append({
                    'bbox': [int(x), int(y), int(w), int(h)],
                    'detection_method': 'cnn',
                    'confidence': float(confidence)
                })
        
        except Exception as e:
            print(f"Erro na detecção CNN: {e}")
        
        return badges
    
    def _is_badge_candidate(self, contour) -> bool:
        """
        Verifica se um contorno pode ser um crachá
        """
        try:
            # Calcular área
            area = cv2.contourArea(contour)
            
            # Verificar tamanho mínimo
            x, y, w, h = cv2.boundingRect(contour)
            min_size = self.badge_config['min_badge_size']
            
            if w < min_size or h < min_size:
                return False
            
            # Verificar proporção (crachás são tipicamente retangulares)
            aspect_ratio = w / h
            if not (0.8 <= aspect_ratio <= 3.0):
                return False
            
            # Verificar se é suficientemente retangular
            hull_area = cv2.contourArea(cv2.convexHull(contour))
            if area / hull_area < 0.6:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _analyze_single_badge(self, image: np.ndarray, badge_region: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa um único crachá detectado
        """
        bbox = badge_region['bbox']
        x, y, w, h = bbox
        
        analysis = {
            'bbox': bbox,
            'confidence': badge_region.get('confidence', 0.0),
            'detection_method': badge_region.get('detection_method', 'unknown'),
            'is_valid': False,
            'visibility_score': 0.0,
            'extracted_text': '',
            'text_confidence': 0,
            'badge_quality': {},
            'position_analysis': {}
        }
        
        try:
            # Extrair região do crachá
            badge_image = image[y:y+h, x:x+w]
            
            # Analisar qualidade do crachá
            analysis['badge_quality'] = self._analyze_badge_quality(badge_image)
            
            # Analisar posição do crachá na pessoa
            analysis['position_analysis'] = self._analyze_badge_position(bbox, image.shape)
            
            # Calcular score de visibilidade
            analysis['visibility_score'] = self._calculate_visibility_score(
                analysis['badge_quality'], 
                analysis['position_analysis']
            )
            
            # Verificar se é um crachá válido
            analysis['is_valid'] = analysis['visibility_score'] > 0.6
            
            # Extrair texto se OCR estiver habilitado
            if self.badge_config['ocr_enabled'] and analysis['visibility_score'] > 0.5:
                text_result = self._extract_text_from_badge(badge_image)
                analysis.update(text_result)
            
        except Exception as e:
            print(f"Erro na análise do crachá: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_badge_quality(self, badge_image: np.ndarray) -> Dict[str, float]:
        """
        Analisa qualidade visual do crachá
        """
        try:
            gray = cv2.cvtColor(badge_image, cv2.COLOR_RGB2GRAY)
            
            # Score de nitidez
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(1.0, sharpness / 300.0)
            
            # Score de contraste
            contrast = gray.std()
            contrast_score = min(1.0, contrast / 50.0)
            
            # Score de brilho (muito escuro ou claro prejudica leitura)
            brightness = gray.mean()
            brightness_score = 1.0 - abs(brightness - 128) / 128.0
            
            # Score de tamanho
            h, w = badge_image.shape[:2]
            size_score = min(1.0, (h * w) / (50 * 50))
            
            return {
                'sharpness': sharpness_score,
                'contrast': contrast_score,
                'brightness': brightness_score,
                'size': size_score,
                'overall': (sharpness_score + contrast_score + brightness_score + size_score) / 4
            }
            
        except Exception as e:
            print(f"Erro na análise de qualidade: {e}")
            return {'overall': 0.0}
    
    def _analyze_badge_position(self, bbox: List[int], image_shape: Tuple[int, int, int]) -> Dict[str, Any]:
        """
        Analisa posição do crachá na imagem
        """
        x, y, w, h = bbox
        img_h, img_w = image_shape[:2]
        
        # Posição relativa
        center_x = (x + w/2) / img_w
        center_y = (y + h/2) / img_h
        
        # Verificar se está em área típica de crachá
        typical_areas = {
            'chest': (0.3 <= center_x <= 0.7) and (0.3 <= center_y <= 0.6),
            'neck': (0.4 <= center_x <= 0.6) and (0.2 <= center_y <= 0.4),
            'waist': (0.3 <= center_x <= 0.7) and (0.6 <= center_y <= 0.8)
        }
        
        in_typical_area = any(typical_areas.values())
        
        return {
            'center_x': center_x,
            'center_y': center_y,
            'in_typical_area': in_typical_area,
            'area_analysis': typical_areas,
            'position_score': 0.8 if in_typical_area else 0.3
        }
    
    def _calculate_visibility_score(self, quality: Dict[str, float], position: Dict[str, Any]) -> float:
        """
        Calcula score geral de visibilidade do crachá
        """
        quality_score = quality.get('overall', 0.0)
        position_score = position.get('position_score', 0.0)
        
        # Peso: 70% qualidade, 30% posição
        visibility_score = quality_score * 0.7 + position_score * 0.3
        
        return np.clip(visibility_score, 0.0, 1.0)
    
    def _extract_text_from_badge(self, badge_image: np.ndarray) -> Dict[str, Any]:
        """
        Extrai texto do crachá usando OCR
        """
        result = {
            'extracted_text': '',
            'text_confidence': 0,
            'detected_words': [],
            'potential_name': '',
            'potential_id': ''
        }
        
        try:
            if not self.ocr_engine:
                return result
            
            # Pré-processar imagem para melhor OCR
            processed = self._preprocess_for_ocr(badge_image)
            
            # Extrair texto com confiança
            text_data = pytesseract.image_to_data(
                processed, 
                config=self.ocr_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Filtrar palavras com confiança suficiente
            words = []
            confidences = []
            
            for i, conf in enumerate(text_data['conf']):
                if int(conf) > self.badge_config['text_confidence_threshold']:
                    word = text_data['text'][i].strip()
                    if len(word) > 1:  # Ignorar caracteres únicos
                        words.append(word)
                        confidences.append(int(conf))
            
            if words:
                result['extracted_text'] = ' '.join(words)
                result['text_confidence'] = np.mean(confidences)
                result['detected_words'] = words
                
                # Tentar identificar nome e ID
                result.update(self._parse_badge_text(words))
        
        except Exception as e:
            print(f"Erro na extração de texto: {e}")
        
        return result
    
    def _preprocess_for_ocr(self, badge_image: np.ndarray) -> np.ndarray:
        """
        Pré-processa imagem do crachá para melhor OCR
        """
        # Converter para cinza
        gray = cv2.cvtColor(badge_image, cv2.COLOR_RGB2GRAY)
        
        # Redimensionar se muito pequeno
        h, w = gray.shape
        if h < 100 or w < 100:
            scale_factor = max(100/h, 100/w)
            new_h, new_w = int(h * scale_factor), int(w * scale_factor)
            gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        
        # Aplicar filtro bilateral
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Melhorar contraste
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(filtered)
        
        # Binarização adaptativa
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    
    def _parse_badge_text(self, words: List[str]) -> Dict[str, str]:
        """
        Analisa texto extraído para identificar nome e ID
        """
        result = {'potential_name': '', 'potential_id': ''}
        
        try:
            for word in words:
                # Verificar se é um ID (números)
                if word.isdigit() and len(word) >= 3:
                    result['potential_id'] = word
                
                # Verificar se é um nome (letras, possivelmente primeira palavra em maiúscula)
                elif word.isalpha() and len(word) >= 2:
                    if word[0].isupper():
                        if result['potential_name']:
                            result['potential_name'] += ' ' + word
                        else:
                            result['potential_name'] = word
        
        except Exception as e:
            print(f"Erro no parsing do texto: {e}")
        
        return result
    
    def _analyze_badge_absence(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analisa possível ausência de crachá
        """
        return {
            'no_badge_detected': True,
            'searched_areas': self.badge_config['required_badge_areas'],
            'compliance_violation': True,
            'violation_type': 'missing_badge'
        }
    
    def _calculate_compliance_score(self, results: Dict[str, Any]) -> float:
        """
        Calcula score de conformidade com política de crachás
        """
        if not results['detected']:
            return 0.0
        
        # Verificar se há pelo menos um crachá válido e visível
        if results['has_valid_badge'] and results['badge_visible']:
            base_score = 0.8
        else:
            base_score = 0.3
        
        # Bonus se conseguiu extrair informações
        if results['employee_info_extracted']:
            base_score += 0.2
        
        return min(1.0, base_score)
    
    def _filter_duplicate_detections(self, badges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove detecções duplicadas baseado em IoU
        """
        if len(badges) <= 1:
            return badges
        
        # Calcular IoU entre todas as detecções
        filtered_badges = []
        
        for i, badge1 in enumerate(badges):
            is_duplicate = False
            
            for j, badge2 in enumerate(filtered_badges):
                iou = self._calculate_iou(badge1['bbox'], badge2['bbox'])
                if iou > 0.5:  # Threshold para considerar duplicata
                    # Manter o de maior confiança
                    if badge1['confidence'] <= badge2['confidence']:
                        is_duplicate = True
                        break
                    else:
                        # Remover o anterior e adicionar o atual
                        filtered_badges.remove(badge2)
            
            if not is_duplicate:
                filtered_badges.append(badge1)
        
        return filtered_badges
    
    def _calculate_iou(self, bbox1: List[int], bbox2: List[int]) -> float:
        """
        Calcula Intersection over Union entre duas bounding boxes
        """
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Coordenadas da interseção
        x_inter = max(x1, x2)
        y_inter = max(y1, y2)
        w_inter = max(0, min(x1 + w1, x2 + w2) - x_inter)
        h_inter = max(0, min(y1 + h1, y2 + h2) - y_inter)
        
        # Áreas
        area_inter = w_inter * h_inter
        area_union = w1 * h1 + w2 * h2 - area_inter
        
        return area_inter / area_union if area_union > 0 else 0.0
    
    def _preprocess_for_cnn(self, image: np.ndarray) -> torch.Tensor:
        """
        Pré-processa imagem para CNN
        """
        # Redimensionar
        resized = cv2.resize(image, (224, 224))
        
        # Converter para tensor
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        pil_image = Image.fromarray(resized)
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
        Retorna threshold de confiança para detecção de crachás
        """
        return self.badge_config['confidence_threshold']
    
    def get_compliance_summary(self, results: Dict[str, Any]) -> Dict[str, str]:
        """
        Gera resumo de conformidade de crachás
        """
        summary = {}
        
        if results.get('has_valid_badge', False):
            summary['badge_status'] = '✅ Crachá detectado e válido'
        elif results.get('detected', False):
            summary['badge_status'] = '⚠️ Crachá detectado mas com problemas'
        else:
            summary['badge_status'] = '❌ Nenhum crachá detectado'
        
        if results.get('badge_visible', False):
            summary['visibility'] = '✅ Crachá claramente visível'
        else:
            summary['visibility'] = '❌ Crachá não visível ou obstruído'
        
        if results.get('employee_info_extracted', False):
            summary['information'] = '✅ Informações extraídas do crachá'
        else:
            summary['information'] = '❌ Não foi possível ler informações'
        
        compliance_score = results.get('compliance_score', 0.0)
        if compliance_score >= 0.8:
            summary['compliance'] = '✅ Em total conformidade'
        elif compliance_score >= 0.5:
            summary['compliance'] = '⚠️ Conformidade parcial'
        else:
            summary['compliance'] = '❌ Fora de conformidade'
        
        return summary 