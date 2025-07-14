#!/usr/bin/env python3
"""
Script de teste para validar o sistema Big Brother CNN
"""

import os
import sys
import torch
import numpy as np
from PIL import Image
from utils import load_config, create_directories
from models.cnn_model import BigBrotherCNN

def create_dummy_images(num_images=20):
    """
    Cria imagens dummy para teste do sistema
    """
    images_dir = "data/imagens"
    os.makedirs(images_dir, exist_ok=True)
    
    print(f"Criando {num_images} imagens dummy para teste...")
    
    for i in range(num_images):
        # Criar imagem aleatória
        img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        
        # Salvar com nome que inclui a classe
        class_id = i % 10  # Distribuir entre 10 classes
        filename = f"funcionario_{i:03d}_classe_{class_id}.jpg"
        img.save(os.path.join(images_dir, filename))
    
    print(f"✅ {num_images} imagens criadas em {images_dir}")

def test_model_creation():
    """
    Testa a criação do modelo
    """
    print("\n=== TESTANDO CRIAÇÃO DO MODELO ===")
    
    try:
        # Carregar configuração
        config = load_config('config.yaml')
        
        # Criar modelo
        model = BigBrotherCNN('config.yaml')
        
        # Verificar device
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model.device = device
        model.model = model.model.to(device)
        
        # Obter sumário
        summary = model.get_model_summary()
        
        print(f"✅ Modelo criado com sucesso!")
        print(f"   - Device: {summary['device']}")
        print(f"   - Parâmetros totais: {summary['total_parameters']:,}")
        print(f"   - Parâmetros treináveis: {summary['trainable_parameters']:,}")
        print(f"   - Número de classes: {summary['num_classes']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar modelo: {e}")
        return False

def test_data_loading():
    """
    Testa o carregamento de dados
    """
    print("\n=== TESTANDO CARREGAMENTO DE DADOS ===")
    
    try:
        from utils import create_data_loaders
        
        # Carregar configuração
        config = load_config('config.yaml')
        
        # Criar DataLoaders
        train_loader, val_loader, test_loader = create_data_loaders('data', config)
        
        print(f"✅ DataLoaders criados com sucesso!")
        print(f"   - Batches de treino: {len(train_loader)}")
        print(f"   - Batches de validação: {len(val_loader)}")
        print(f"   - Batches de teste: {len(test_loader)}")
        
        # Testar um batch
        if len(train_loader) > 0:
            batch = next(iter(train_loader))
            images, labels = batch
            print(f"   - Formato do batch: {images.shape}")
            print(f"   - Labels: {labels.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {e}")
        return False

def test_inference():
    """
    Testa a inferência do modelo
    """
    print("\n=== TESTANDO INFERÊNCIA ===")
    
    try:
        # Carregar configuração
        config = load_config('config.yaml')
        
        # Criar modelo
        model = BigBrotherCNN('config.yaml')
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model.device = device
        model.model = model.model.to(device)
        
        # Criar imagem dummy
        dummy_image = torch.randn(1, 3, 224, 224).to(device)
        
        # Fazer predição
        predictions = model.predict(dummy_image)
        
        print(f"✅ Inferência realizada com sucesso!")
        print(f"   - Formato da predição: {predictions.shape}")
        print(f"   - Classe predita: {np.argmax(predictions[0])}")
        print(f"   - Confiança: {np.max(predictions[0]):.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na inferência: {e}")
        return False

def test_schedule_analysis():
    """
    Testa a análise de horários
    """
    print("\n=== TESTANDO ANÁLISE DE HORÁRIOS ===")
    
    try:
        from utils import analyze_schedule_patterns, load_routines
        
        # Analisar padrões de horário
        patterns = analyze_schedule_patterns('data/horarios.csv')
        
        if patterns:
            print(f"✅ Padrões de horário analisados!")
            print(f"   - Grades encontradas: {list(patterns.keys())}")
            
            # Mostrar alguns exemplos
            for grade, horarios in list(patterns.items())[:3]:
                print(f"   - {grade}: {len(horarios)} horários")
        
        # Carregar rotinas
        routines = load_routines('data/rotinas.json')
        
        if routines:
            print(f"✅ Rotinas carregadas!")
            print(f"   - Tipos de rotina: {list(routines.get('rotinas', {}).keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na análise de horários: {e}")
        return False

def test_configuration():
    """
    Testa a configuração do sistema
    """
    print("\n=== TESTANDO CONFIGURAÇÃO ===")
    
    try:
        # Carregar configuração
        config = load_config('config.yaml')
        
        # Verificar seções principais
        required_sections = ['model', 'data', 'training', 'inference', 'device']
        
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Seção '{section}' não encontrada na configuração")
        
        print(f"✅ Configuração validada!")
        print(f"   - Seções encontradas: {list(config.keys())}")
        print(f"   - Número de classes: {config['model']['num_classes']}")
        print(f"   - Batch size: {config['model']['batch_size']}")
        print(f"   - Épocas: {config['model']['epochs']}")
        
        # Criar diretórios
        create_directories(config)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
        return False

def main():
    """
    Função principal de teste
    """
    print("🚀 INICIANDO TESTES DO SISTEMA BIG BROTHER CNN")
    print("=" * 50)
    
    tests = [
        ("Configuração", test_configuration),
        ("Criação de imagens dummy", lambda: create_dummy_images(20)),
        ("Criação do modelo", test_model_creation),
        ("Carregamento de dados", test_data_loading),
        ("Inferência", test_inference),
        ("Análise de horários", test_schedule_analysis),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if test_func is create_dummy_images:
                test_func()
                results.append((test_name, True))
            else:
                result = test_func()
                results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro no teste '{test_name}': {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram! Sistema pronto para uso.")
    else:
        print("⚠️  Alguns testes falharam. Verifique os erros acima.")
    
    return passed == total

if __name__ == "__main__":
    # Mudar para o diretório correto
    if os.path.basename(os.getcwd()) != 'big_brother_cnn':
        if os.path.exists('big_brother_cnn'):
            os.chdir('big_brother_cnn')
        else:
            print("❌ Diretório 'big_brother_cnn' não encontrado!")
            sys.exit(1)
    
    success = main()
    sys.exit(0 if success else 1) 