import os
import argparse
import torch
import matplotlib.pyplot as plt
from models.cnn_model import BigBrotherCNN
from utils import (
    load_config,
    create_data_loaders,
    create_directories,
    analyze_schedule_patterns,
    load_routines
)

def parse_args():
    parser = argparse.ArgumentParser(description='Treinar modelo CNN')
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Caminho para o arquivo de configuração'
    )
    parser.add_argument(
        '--data_dir',
        type=str,
        default='data',
        help='Diretório com os dados de treino'
    )
    parser.add_argument(
        '--resume',
        type=str,
        default=None,
        help='Caminho para checkpoint para continuar o treinamento'
    )
    return parser.parse_args()

def plot_training_history(train_losses, val_losses, save_path):
    """
    Plota o histórico de treinamento
    """
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Validation Loss')
    plt.title('Training History')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"Gráfico de treinamento salvo em: {save_path}")

def evaluate_model(model, test_loader, device):
    """
    Avalia o modelo no conjunto de teste
    """
    model.model.eval()
    correct = 0
    total = 0
    test_loss = 0
    
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            
            output = model.model(data)
            test_loss += model.loss_fn(output, target).item()
            
            _, predicted = torch.max(output.data, 1)
            total += target.size(0)
            correct += (predicted == target).sum().item()
    
    test_loss /= len(test_loader)
    accuracy = 100 * correct / total
    
    return test_loss, accuracy

def main():
    # Carregar argumentos
    args = parse_args()
    
    # Carregar configurações
    config = load_config(args.config)
    
    # Criar diretórios necessários
    create_directories(config)
    
    # Analisar padrões de horários
    print("Analisando padrões de horários...")
    schedule_patterns = analyze_schedule_patterns(
        os.path.join(args.data_dir, 'horarios.csv')
    )
    print(f"Padrões encontrados: {list(schedule_patterns.keys())}")
    
    # Carregar rotinas
    print("Carregando rotinas...")
    routines = load_routines(os.path.join(args.data_dir, 'rotinas.json'))
    
    # Criar DataLoaders
    print("Criando DataLoaders...")
    try:
        train_loader, val_loader, test_loader = create_data_loaders(args.data_dir, config)
        print(f"Dados carregados: {len(train_loader)} batches de treino, "
              f"{len(val_loader)} batches de validação, {len(test_loader)} batches de teste")
    except Exception as e:
        print(f"Erro ao criar DataLoaders: {e}")
        print("Certifique-se de que o diretório 'data/imagens' existe e contém imagens")
        return
    
    # Verificar se há imagens suficientes
    if len(train_loader) == 0:
        print("⚠️  Nenhuma imagem encontrada no diretório 'data/imagens'")
        print("Para testar o sistema, adicione algumas imagens de exemplo")
        return
    
    # Inicializar modelo
    print("Inicializando modelo...")
    device = torch.device('cuda' if torch.cuda.is_available() and config['device']['use_cuda'] else 'cpu')
    print(f"Usando device: {device}")
    
    model = BigBrotherCNN(config_path=args.config)
    model.device = device
    model.model = model.model.to(device)
    
    # Exibir sumário do modelo
    model_summary = model.get_model_summary()
    print("\n=== SUMÁRIO DO MODELO ===")
    print(f"Parâmetros totais: {model_summary['total_parameters']:,}")
    print(f"Parâmetros treináveis: {model_summary['trainable_parameters']:,}")
    print(f"Device: {model_summary['device']}")
    print(f"Número de classes: {model_summary['num_classes']}")
    
    # Carregar checkpoint se especificado
    start_epoch = 0
    if args.resume:
        print(f"Carregando checkpoint: {args.resume}")
        start_epoch = model.load_checkpoint(args.resume)
        print(f"Retomando treinamento a partir da época {start_epoch}")
    
    # Treinar modelo
    print("\n=== INICIANDO TREINAMENTO ===")
    try:
        train_losses, val_losses = model.train_model(train_loader, val_loader)
        print("Treinamento concluído com sucesso!")
        
        # Plotar histórico de treinamento
        plot_path = os.path.join(config['training']['checkpoint_dir'], 'training_history.png')
        plot_training_history(train_losses, val_losses, plot_path)
        
    except Exception as e:
        print(f"Erro durante o treinamento: {e}")
        return
    
    # Avaliar modelo no conjunto de teste
    print("\n=== AVALIAÇÃO NO CONJUNTO DE TESTE ===")
    try:
        test_loss, test_accuracy = evaluate_model(model, test_loader, device)
        print(f"Loss no teste: {test_loss:.4f}")
        print(f"Acurácia no teste: {test_accuracy:.2f}%")
        
        # Salvar resultados finais
        final_results = {
            'test_loss': test_loss,
            'test_accuracy': test_accuracy,
            'model_summary': model_summary,
            'config': config,
            'schedule_patterns': schedule_patterns
        }
        
        results_path = os.path.join(config['training']['checkpoint_dir'], 'final_results.json')
        import json
        with open(results_path, 'w') as f:
            json.dump(final_results, f, indent=4)
        
        print(f"\nResultados finais salvos em: {results_path}")
        
    except Exception as e:
        print(f"Erro durante a avaliação: {e}")

if __name__ == '__main__':
    main() 