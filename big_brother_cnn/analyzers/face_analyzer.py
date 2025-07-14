"""
Analyzer para reconhecimento facial
Baseado nos datasets CASIA-WebFace e VGG Face2
"""

import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import face_recognition

from .base_analyzer import BaseAnalyzer


class FaceAnalyzer(BaseAnalyzer):
    """
    Analyzer especializado em reconhecimento facial
    
    Funcionalidades:
    - Detecção de faces na imagem
    - Reconhecimento de funcionários conhecidos
    - Verificação de identidade
    - Análise de qualidade da face (iluminação, ângulo, etc.)
    """
    
    def __init__(self, config: Dict[str, Any], device: torch.device):
        super().__init__(config, device)
        self.face_cascade = None
        self.known_encodings = []
        self.known_names = []
        self.recognition_model = None
        
        # Configurações específicas para faces
        self.face_config = config.get('analyzers', {}).get('face', {
            'min_face_size': 50,
            'confidence_threshold': 0.6,
            'detection_method': 'hog',  # 'hog' ou 'cnn'
            'recognition_tolerance': 0.6
        })
        
    def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        Carrega modelos para detecção e reconhecimento facial
        """
        try:
            # Carregar detector de faces OpenCV (backup)
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            # Carregar encodings de funcionários conhecidos
            if model_path:
                self._load_known_faces(model_path)
            
            # Modelo de reconhecimento personalizado (ResNet para features)
            self.recognition_model = models.resnet50(pretrained=True)
            self.recognition_model.fc = nn.Linear(2048, 512)  # Embedding de 512 dimensões
            self.recognition_model.to(self.device)
            self.recognition_model.eval()
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            print(f"Erro ao carregar modelo facial: {e}")
            return False
    
    def _load_known_faces(self, encodings_path: str):
        """
        Carrega encodings de faces conhecidas de funcionários
        """
        try:
            import pickle
            with open(encodings_path, 'rb') as f:
                data = pickle.load(f)
                self.known_encodings = data['encodings']
                self.known_names = data['names']
            
            print(f"Carregados {len(self.known_names)} funcionários conhecidos")
            
        except Exception as e:
            print(f"Erro ao carregar faces conhecidas: {e}")
    
    def analyze(self, image: torch.Tensor, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Realiza análise completa de reconhecimento facial
        """
        results = {
            'detected': False,
            'confidence': 0.0,
            'faces_count': 0,
            'faces': [],
            'employee_detected': False,
            'employee_info': None,
            'quality_score': 0.0
        }
        
        try:
            # Converter tensor para array numpy
            img_array = self._tensor_to_array(image)
            
            # Detectar faces
            faces = self._detect_faces(img_array)
            results['faces_count'] = len(faces)
            results['detected'] = len(faces) > 0
            
            if len(faces) > 0:
                # Analisar cada face detectada
                for i, face_location in enumerate(faces):
                    face_analysis = self._analyze_single_face(img_array, face_location)
                    results['faces'].append(face_analysis)
                    
                    # Atualizar confiança geral (maior confiança entre as faces)
                    if face_analysis['confidence'] > results['confidence']:
                        results['confidence'] = face_analysis['confidence']
                    
                    # Se encontrou funcionário conhecido
                    if face_analysis.get('employee_match'):
                        results['employee_detected'] = True
                        results['employee_info'] = face_analysis['employee_info']
                
                # Calcular score de qualidade geral
                if results['faces']:
                    results['quality_score'] = np.mean([f['quality_score'] for f in results['faces']])
            
        except Exception as e:
            print(f"Erro na análise facial: {e}")
            results['error'] = str(e)
        
        return self.postprocess_results(results)
    
    def _detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detecta faces na imagem usando face_recognition e OpenCV
        """
        faces = []
        
        try:
            # Método 1: face_recognition (mais preciso)
            face_locations = face_recognition.face_locations(
                image, 
                model=self.face_config['detection_method']
            )
            
            # Converter formato de face_recognition para OpenCV
            for (top, right, bottom, left) in face_locations:
                width = right - left
                height = bottom - top
                if width >= self.face_config['min_face_size'] and height >= self.face_config['min_face_size']:
                    faces.append((left, top, width, height))
            
            # Método 2: OpenCV (backup)
            if len(faces) == 0 and self.face_cascade:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                opencv_faces = self.face_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.1, 
                    minNeighbors=5, 
                    minSize=(self.face_config['min_face_size'], self.face_config['min_face_size'])
                )
                faces.extend(opencv_faces)
                
        except Exception as e:
            print(f"Erro na detecção de faces: {e}")
        
        return faces
    
    def _analyze_single_face(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> Dict[str, Any]:
        """
        Analisa uma única face detectada
        """
        x, y, w, h = face_location
        
        analysis = {
            'bbox': [x, y, w, h],
            'confidence': 0.0,
            'quality_score': 0.0,
            'employee_match': False,
            'employee_info': None,
            'face_encoding': None
        }
        
        try:
            # Extrair região da face
            face_image = image[y:y+h, x:x+w]
            
            # Calcular score de qualidade
            quality_score = self._calculate_face_quality(face_image)
            analysis['quality_score'] = quality_score
            
            # Se qualidade é boa o suficiente, fazer reconhecimento
            if quality_score > 0.5:
                # Gerar encoding da face
                face_encoding = face_recognition.face_encodings(
                    image, 
                    [(y, x+w, y+h, x)]  # Converter para formato face_recognition
                )
                
                if len(face_encoding) > 0:
                    analysis['face_encoding'] = face_encoding[0].tolist()
                    
                    # Comparar com funcionários conhecidos
                    if len(self.known_encodings) > 0:
                        matches = face_recognition.compare_faces(
                            self.known_encodings, 
                            face_encoding[0],
                            tolerance=self.face_config['recognition_tolerance']
                        )
                        
                        face_distances = face_recognition.face_distance(
                            self.known_encodings, 
                            face_encoding[0]
                        )
                        
                        if True in matches:
                            best_match_index = np.argmin(face_distances)
                            confidence = 1 - face_distances[best_match_index]
                            
                            analysis['confidence'] = confidence
                            analysis['employee_match'] = True
                            analysis['employee_info'] = {
                                'name': self.known_names[best_match_index],
                                'match_distance': face_distances[best_match_index],
                                'confidence': confidence
                            }
                        else:
                            # Face desconhecida
                            analysis['confidence'] = 0.3  # Baixa confiança para desconhecidos
                    else:
                        # Sem base de funcionários conhecidos
                        analysis['confidence'] = 0.5
            
        except Exception as e:
            print(f"Erro na análise de face individual: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def _calculate_face_quality(self, face_image: np.ndarray) -> float:
        """
        Calcula score de qualidade da face (0-1)
        Considera: tamanho, nitidez, iluminação, ângulo
        """
        try:
            h, w = face_image.shape[:2]
            
            # Score baseado no tamanho
            size_score = min(1.0, (h * w) / (100 * 100))  # Normalizado para 100x100
            
            # Score de nitidez (variância do Laplaciano)
            gray = cv2.cvtColor(face_image, cv2.COLOR_RGB2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(1.0, sharpness / 500.0)  # Normalizado
            
            # Score de iluminação (desvio padrão)
            brightness = np.mean(gray)
            brightness_score = 1.0 - abs(brightness - 128) / 128.0  # Ótimo em ~128
            
            # Score final combinado
            quality_score = (size_score * 0.3 + sharpness_score * 0.4 + brightness_score * 0.3)
            
            return np.clip(quality_score, 0.0, 1.0)
            
        except Exception as e:
            print(f"Erro no cálculo de qualidade: {e}")
            return 0.0
    
    def _tensor_to_array(self, tensor: torch.Tensor) -> np.ndarray:
        """
        Converte tensor PyTorch para array numpy no formato correto
        """
        if tensor.dim() == 4:
            tensor = tensor.squeeze(0)
        
        if tensor.dim() == 3 and tensor.shape[0] == 3:
            # CHW para HWC
            tensor = tensor.permute(1, 2, 0)
        
        # Desnormalizar se necessário
        if tensor.min() < 0:
            tensor = (tensor + 1) / 2
        
        # Converter para uint8
        array = (tensor.cpu().numpy() * 255).astype(np.uint8)
        
        return array
    
    def get_confidence_threshold(self) -> float:
        """
        Retorna threshold de confiança para reconhecimento facial
        """
        return self.face_config['confidence_threshold']
    
    def add_employee_face(self, image_path: str, employee_name: str) -> bool:
        """
        Adiciona nova face de funcionário à base de conhecimento
        """
        try:
            # Carregar imagem
            image = face_recognition.load_image_file(image_path)
            
            # Gerar encoding
            encodings = face_recognition.face_encodings(image)
            
            if len(encodings) > 0:
                self.known_encodings.append(encodings[0])
                self.known_names.append(employee_name)
                return True
            else:
                print(f"Nenhuma face detectada em {image_path}")
                return False
                
        except Exception as e:
            print(f"Erro ao adicionar funcionário: {e}")
            return False
    
    def save_employee_database(self, save_path: str) -> bool:
        """
        Salva base de dados de funcionários
        """
        try:
            import pickle
            data = {
                'encodings': self.known_encodings,
                'names': self.known_names
            }
            
            with open(save_path, 'wb') as f:
                pickle.dump(data, f)
            
            return True
            
        except Exception as e:
            print(f"Erro ao salvar base de funcionários: {e}")
            return False 