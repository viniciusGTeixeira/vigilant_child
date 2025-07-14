import os
import argparse
import json
from datetime import datetime
import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from models.cnn_model import BigBrotherCNN
from utils import load_config, load_image, save_results, load_routines, analyze_schedule_patterns

def parse_args():
    parser = argparse.ArgumentParser(description='Realizar inferência com modelo CNN')
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Caminho para o arquivo de configuração'
    )
    parser.add_argument(
        '--model_path',
        type=str,
        required=True,
        help='Caminho para o checkpoint do modelo treinado'
    )
    parser.add_argument(
        '--image_dir',
        type=str,
        required=True,
        help='Diretório com as imagens para inferência'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='reports',
        help='Diretório para salvar os resultados'
    )
    parser.add_argument(
        '--single_image',
        type=str,
        default=None,
        help='Caminho para uma única imagem para inferência'
    )
    return parser.parse_args()

def create_inference_transform():
    """
    Cria transformações para inferência
    """
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

def process_single_image(image_path, model, transform, device, config):
    """
    Processa uma única imagem para inferência
    """
    try:
        # Carregar e processar imagem
        image = load_image(image_path)
        if image is None:
            return None
        
        # Aplicar transformações
        image_tensor = transform(image).unsqueeze(0).to(device)
        
        # Realizar predição
        with torch.no_grad():
            model.model.eval()
            outputs = model.model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            
            # Converter para numpy
            probs_np = probabilities.cpu().numpy()[0]
            predicted_class = int(np.argmax(probs_np))
            confidence = float(np.max(probs_np))
        
        return {
            'probabilities': probs_np.tolist(),
            'predicted_class': predicted_class,
            'confidence': confidence,
            'above_threshold': confidence >= config['inference']['confidence_threshold']
        }
    
    except Exception as e:
        print(f"Erro ao processar imagem {image_path}: {e}")
        return None

def process_batch_images(image_dir, model, transform, device, config):
    """
    Processa um diretório inteiro de imagens
    """
    results = {}
    
    # Listar arquivos de imagem
    image_files = [f for f in os.listdir(image_dir) 
                  if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]
    
    if not image_files:
        print(f"Nenhuma imagem encontrada em {image_dir}")
        return results
    
    print(f"Processando {len(image_files)} imagens...")
    
    for i, img_name in enumerate(image_files):
        img_path = os.path.join(image_dir, img_name)
        
        result = process_single_image(img_path, model, transform, device, config)
        if result:
            results[img_name] = result
            
            # Mostrar progresso
            if (i + 1) % 10 == 0 or (i + 1) == len(image_files):
                print(f"Processadas {i + 1}/{len(image_files)} imagens")
    
    return results

def analyze_detection_patterns(results, schedule_patterns, routines):
    """
    Analisa padrões de detecção baseados nos horários e rotinas
    """
    analysis = {
        'total_detections': len(results),
        'high_confidence_detections': 0,
        'class_distribution': {},
        'anomaly_indicators': []
    }
    
    for img_name, result in results.items():
        if result['above_threshold']:
            analysis['high_confidence_detections'] += 1
        
        # Distribuição de classes
        predicted_class = result['predicted_class']
        if predicted_class not in analysis['class_distribution']:
            analysis['class_distribution'][predicted_class] = 0
        analysis['class_distribution'][predicted_class] += 1
        
        # Detectar possíveis anomalias
        if result['confidence'] < 0.7:  # Baixa confiança
            analysis['anomaly_indicators'].append({
                'image': img_name,
                'type': 'low_confidence',
                'confidence': result['confidence']
            })
    
    return analysis

def generate_comprehensive_report(results, config, schedule_patterns, routines, analysis, output_dir):
    """
    Gera relatório abrangente com os resultados da inferência
    """
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f'inference_report_{timestamp}.json')
    
    # Filtrar resultados com base no limiar de confiança
    threshold = config['inference']['confidence_threshold']
    filtered_results = {
        k: v for k, v in results.items()
        if v['confidence'] >= threshold
    }
    
    # Preparar relatório completo
    report = {
        'metadata': {
            'timestamp': timestamp,
            'threshold': threshold,
            'model_config': config['model'],
            'total_images_processed': len(results),
            'high_confidence_detections': len(filtered_results)
        },
        'results': {
            'all_detections': results,
            'filtered_detections': filtered_results
        },
        'analysis': analysis,
        'schedule_patterns': schedule_patterns,
        'routines_summary': {
            'total_routines': len(routines.get('rotinas', {})),
            'routine_types': list(routines.get('rotinas', {}).keys())
        },
        'statistics': {
            'average_confidence': np.mean([r['confidence'] for r in results.values()]),
            'max_confidence': np.max([r['confidence'] for r in results.values()]),
            'min_confidence': np.min([r['confidence'] for r in results.values()]),
            'confidence_std': np.std([r['confidence'] for r in results.values()])
        }
    }
    
    # Salvar relatório
    save_results(report, report_path)
    
    # Criar resumo em texto
    summary_path = os.path.join(output_dir, f'summary_{timestamp}.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"=== RELATÓRIO DE INFERÊNCIA ===\n")
        f.write(f"Data/Hora: {timestamp}\n")
        f.write(f"Threshold: {threshold}\n\n")
        
        f.write(f"=== RESULTADOS ===\n")
        f.write(f"Total de imagens processadas: {len(results)}\n")
        f.write(f"Detecções com alta confiança: {len(filtered_results)}\n")
        f.write(f"Taxa de detecção: {len(filtered_results)/len(results)*100:.1f}%\n\n")
        
        f.write(f"=== ESTATÍSTICAS ===\n")
        f.write(f"Confiança média: {report['statistics']['average_confidence']:.3f}\n")
        f.write(f"Confiança máxima: {report['statistics']['max_confidence']:.3f}\n")
        f.write(f"Confiança mínima: {report['statistics']['min_confidence']:.3f}\n\n")
        
        f.write(f"=== DISTRIBUIÇÃO DE CLASSES ===\n")
        for class_id, count in analysis['class_distribution'].items():
            f.write(f"Classe {class_id}: {count} detecções\n")
        
        if analysis['anomaly_indicators']:
            f.write(f"\n=== ANOMALIAS DETECTADAS ===\n")
            for anomaly in analysis['anomaly_indicators']:
                f.write(f"- {anomaly['image']}: {anomaly['type']} (confiança: {anomaly['confidence']:.3f})\n")
    
    print(f"Relatório completo salvo em: {report_path}")
    print(f"Resumo salvo em: {summary_path}")
    
    return report_path

def main():
    # Carregar argumentos
    args = parse_args()
    
    # Carregar configurações
    config = load_config(args.config)
    
    # Configurar device
    device = torch.device('cuda' if torch.cuda.is_available() and config['device']['use_cuda'] else 'cpu')
    print(f"Usando device: {device}")
    
    # Carregar modelo
    print("Carregando modelo...")
    try:
        model = BigBrotherCNN(config_path=args.config)
        model.device = device
        model.model = model.model.to(device)
        
        # Carregar checkpoint
        checkpoint = torch.load(args.model_path, map_location=device)
        model.model.load_state_dict(checkpoint['model_state_dict'])
        print(f"Modelo carregado de: {args.model_path}")
        
    except Exception as e:
        print(f"Erro ao carregar modelo: {e}")
        return
    
    # Criar transformações para inferência
    transform = create_inference_transform()
    
    # Carregar dados auxiliares
    schedule_patterns = analyze_schedule_patterns('data/horarios.csv')
    routines = load_routines('data/rotinas.json')
    
    # Processar imagens
    results = {}
    
    if args.single_image:
        # Processar uma única imagem
        print(f"Processando imagem: {args.single_image}")
        result = process_single_image(args.single_image, model, transform, device, config)
        if result:
            results[os.path.basename(args.single_image)] = result
            print(f"Classe predita: {result['predicted_class']}")
            print(f"Confiança: {result['confidence']:.3f}")
    else:
        # Processar diretório de imagens
        print(f"Processando diretório: {args.image_dir}")
        results = process_batch_images(args.image_dir, model, transform, device, config)
    
    if not results:
        print("Nenhum resultado obtido. Verifique os caminhos das imagens.")
        return
    
    # Analisar padrões
    print("Analisando padrões de detecção...")
    analysis = analyze_detection_patterns(results, schedule_patterns, routines)
    
    # Gerar relatório
    print("Gerando relatório...")
    report_path = generate_comprehensive_report(
        results, config, schedule_patterns, routines, analysis, args.output_dir
    )
    
    print(f"\n=== RESUMO DA INFERÊNCIA ===")
    print(f"Imagens processadas: {len(results)}")
    print(f"Detecções com alta confiança: {analysis['high_confidence_detections']}")
    print(f"Taxa de detecção: {analysis['high_confidence_detections']/len(results)*100:.1f}%")
    print(f"Anomalias detectadas: {len(analysis['anomaly_indicators'])}")
    
    print(f"\nInferência concluída! Relatório salvo em: {report_path}")

if __name__ == '__main__':
    main() 