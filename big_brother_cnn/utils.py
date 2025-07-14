import os
import cv2
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import yaml
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import json

def load_config(config_path='config.yaml'):
    """
    Carrega o arquivo de configuração
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_image(image_path, target_size=None):
    """
    Carrega e pré-processa uma imagem usando PIL
    """
    try:
        img = Image.open(image_path).convert('RGB')
        
        if target_size:
            img = img.resize(target_size)
        
        return img
    except Exception as e:
        print(f"Erro ao carregar imagem {image_path}: {e}")
        return None

class CustomDataset(Dataset):
    """
    Dataset personalizado para PyTorch
    """
    def __init__(self, images_dir, labels, transform=None):
        self.images_dir = images_dir
        self.labels = labels
        self.transform = transform
        self.image_files = [f for f in os.listdir(images_dir) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    def __len__(self):
        return len(self.image_files)
    
    def __getitem__(self, idx):
        img_path = os.path.join(self.images_dir, self.image_files[idx])
        image = load_image(img_path)
        
        if image is None:
            # Retorna imagem preta se houver erro
            image = Image.new('RGB', (224, 224), color='black')
        
        # Obter label (implementar lógica específica baseada no nome do arquivo)
        label = self._get_label_from_filename(self.image_files[idx])
        
        if self.transform:
            image = self.transform(image)
        
        return image, label
    
    def _get_label_from_filename(self, filename):
        """
        Extrai o label do nome do arquivo
        Implementar lógica específica baseada no padrão dos nomes
        """
        # Exemplo: se o nome do arquivo contém a classe
        # funcionario_01_classe_0.jpg -> classe 0
        if 'classe_' in filename:
            try:
                return int(filename.split('classe_')[1].split('.')[0])
            except:
                return 0
        return 0

def create_data_transforms(config):
    """
    Cria transformações para dados de treino e validação
    """
    # Transformações para treino (com augmentation)
    train_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomRotation(config['data']['augmentation']['rotation_range']),
        transforms.RandomHorizontalFlip(p=0.5 if config['data']['augmentation']['horizontal_flip'] else 0),
        transforms.ColorJitter(
            brightness=config['data']['augmentation']['brightness_range'][0],
            contrast=config['data']['augmentation']['brightness_range'][0]
        ),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Transformações para validação/teste (sem augmentation)
    val_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    return train_transforms, val_transforms

def create_data_loaders(data_dir, config):
    """
    Cria DataLoaders para treino, validação e teste
    """
    images_dir = os.path.join(data_dir, 'imagens')
    
    # Obter lista de imagens e labels
    image_files = [f for f in os.listdir(images_dir) 
                  if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    # Criar labels baseados nos arquivos (implementar lógica específica)
    labels = [0] * len(image_files)  # Placeholder - implementar lógica real
    
    # Dividir dados
    train_files, temp_files, train_labels, temp_labels = train_test_split(
        image_files, labels, 
        test_size=config['data']['validation_split'] + config['data']['test_split'],
        random_state=42
    )
    
    val_files, test_files, val_labels, test_labels = train_test_split(
        temp_files, temp_labels,
        test_size=config['data']['test_split'] / (config['data']['validation_split'] + config['data']['test_split']),
        random_state=42
    )
    
    # Criar transformações
    train_transforms, val_transforms = create_data_transforms(config)
    
    # Criar datasets
    train_dataset = CustomDataset(images_dir, train_labels, train_transforms)
    val_dataset = CustomDataset(images_dir, val_labels, val_transforms)
    test_dataset = CustomDataset(images_dir, test_labels, val_transforms)
    
    # Criar DataLoaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=config['model']['batch_size'],
        shuffle=True,
        num_workers=config['device']['num_workers']
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=config['model']['batch_size'],
        shuffle=False,
        num_workers=config['device']['num_workers']
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=config['model']['batch_size'],
        shuffle=False,
        num_workers=config['device']['num_workers']
    )
    
    return train_loader, val_loader, test_loader

def analyze_schedule_patterns(horarios_csv_path):
    """
    Analisa padrões de horários para identificar anomalias
    """
    try:
        df = pd.read_csv(horarios_csv_path)
        
        # Análise básica dos horários
        patterns = {}
        
        for _, row in df.iterrows():
            grade = row['Grade']
            horario = row['Horário Funcionamento']
            
            if grade not in patterns:
                patterns[grade] = []
            patterns[grade].append(horario)
        
        return patterns
    except Exception as e:
        print(f"Erro ao analisar horários: {e}")
        return {}

def load_routines(rotinas_json_path):
    """
    Carrega rotinas do arquivo JSON
    """
    try:
        with open(rotinas_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar rotinas: {e}")
        return {}

def save_results(results, output_path):
    """
    Salva os resultados da inferência
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        
        print(f"Resultados salvos em: {output_path}")
    except Exception as e:
        print(f"Erro ao salvar resultados: {e}")

def create_directories(config):
    """
    Cria diretórios necessários para o projeto
    """
    directories = [
        config['training']['checkpoint_dir'],
        config['inference']['report_output']
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Diretório criado: {directory}") 