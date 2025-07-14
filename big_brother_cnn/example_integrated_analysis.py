#!/usr/bin/env python3
"""
Exemplo de uso do sistema integrado de análise Big Brother CNN
Demonstra todas as funcionalidades dos analyzers especializados
"""

import os
import sys
import torch
import numpy as np
from PIL import Image
from datetime import datetime
import json

# Adicionar path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrated_analysis import IntegratedAnalysisSystem
from utils import load_config
from torchvision import transforms


def create_sample_image():
    """
    Cria uma imagem de exemplo para demonstração
    """
    # Criar imagem sintética de 224x224x3
    sample_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    
    # Simular uma pessoa (retângulo central)
    sample_image[80:180, 90:140] = [100, 150, 200]  # Área da "face"
    sample_image[120:200, 85:145] = [50, 100, 150]   # Área do "corpo"
    
    return sample_image


def prepare_image_tensor(image_array):
    """
    Converte array numpy para tensor PyTorch no formato esperado
    """
    # Converter para PIL Image
    pil_image = Image.fromarray(image_array)
    
    # Aplicar transformações
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    tensor = transform(pil_image)
    return tensor


def demo_comprehensive_analysis():
    """
    Demonstra análise completa do sistema integrado
    """
    print("🚀 DEMO: Sistema Integrado Big Brother CNN")
    print("=" * 60)
    
    try:
        # 1. Inicializar sistema
        print("1️⃣ Inicializando sistema integrado...")
        analysis_system = IntegratedAnalysisSystem('config.yaml')
        print("✅ Sistema inicializado com sucesso\n")
        
        # 2. Preparar dados de exemplo
        print("2️⃣ Preparando dados de exemplo...")
        sample_image = create_sample_image()
        image_tensor = prepare_image_tensor(sample_image)
        
        # Metadados de exemplo
        metadata = {
            'location': 'office_main',
            'timestamp': datetime.now().isoformat(),
            'camera_id': 'cam_001',
            'area_type': 'employee_area'
        }
        
        print(f"✅ Imagem preparada: {image_tensor.shape}")
        print(f"✅ Metadados: {metadata}\n")
        
        # 3. Executar análise completa
        print("3️⃣ Executando análise integrada...")
        print("   - Análise facial")
        print("   - Análise de atributos")
        print("   - Detecção de crachá")
        print("   - Verificação de horários")
        print("   - Análise de padrões")
        print()
        
        results = analysis_system.analyze_comprehensive(image_tensor, metadata)
        
        print(f"✅ Análise concluída em {results['execution_time']:.2f}s\n")
        
        # 4. Apresentar resultados
        print("4️⃣ RESULTADOS DA ANÁLISE")
        print("=" * 40)
        
        # Resumo geral
        summary = analysis_system.get_analysis_summary(results)
        print("📊 RESUMO GERAL:")
        for key, value in summary.items():
            print(f"   {value}")
        print()
        
        # Resultados individuais
        print("🔍 ANÁLISES INDIVIDUAIS:")
        individual_analyses = results.get('individual_analyses', {})
        
        for analyzer_name, analysis_result in individual_analyses.items():
            print(f"\n🔹 {analyzer_name.upper()} ANALYZER:")
            
            if 'error' in analysis_result:
                print(f"   ❌ Erro: {analysis_result['error']}")
                continue
            
            # Mostrar principais métricas
            confidence = analysis_result.get('confidence', 0.0)
            detected = analysis_result.get('detected', False)
            
            print(f"   Detectado: {'✅' if detected else '❌'}")
            print(f"   Confiança: {confidence:.1%}")
            
            # Informações específicas por analyzer
            if analyzer_name == 'face':
                if analysis_result.get('employee_detected', False):
                    employee_info = analysis_result.get('employee_info', {})
                    print(f"   👤 Funcionário: {employee_info.get('name', 'Unknown')}")
                else:
                    print("   👤 Funcionário: Não identificado")
                
            elif analyzer_name == 'attributes':
                formal_score = analysis_result.get('formal_score', 0.0)
                dress_compliant = analysis_result.get('dress_code_compliant', False)
                print(f"   👔 Dress Code: {'✅' if dress_compliant else '❌'}")
                print(f"   📊 Score Formal: {formal_score:.1%}")
                
            elif analyzer_name == 'badge':
                has_badge = analysis_result.get('has_valid_badge', False)
                visible = analysis_result.get('badge_visible', False)
                print(f"   🏷️ Crachá Válido: {'✅' if has_badge else '❌'}")
                print(f"   👁️ Visível: {'✅' if visible else '❌'}")
                
            elif analyzer_name == 'schedule':
                compliance = analysis_result.get('compliance_status', 'unknown')
                expected = analysis_result.get('expected_status', 'unknown')
                print(f"   ⏰ Status Esperado: {expected}")
                print(f"   ✅ Conformidade: {compliance}")
        
        # Análise integrada
        print("\n🔗 ANÁLISE INTEGRADA:")
        integrated_assessment = results.get('integrated_assessment', {})
        
        # Violações de política
        violations = integrated_assessment.get('policy_violations', [])
        if violations:
            print(f"   ⚠️ Violações: {len(violations)}")
            for violation in violations[:3]:  # Mostrar até 3
                print(f"      - {violation['description']}")
        else:
            print("   ✅ Nenhuma violação detectada")
        
        # Indicadores de risco
        risk_indicators = integrated_assessment.get('risk_indicators', {})
        risk_level = risk_indicators.get('overall_risk_level', 'low')
        print(f"   🎯 Nível de Risco: {risk_level.upper()}")
        
        # Alertas
        alerts = results.get('alerts', [])
        if alerts:
            print(f"\n🚨 ALERTAS ({len(alerts)}):")
            for alert in alerts:
                severity_icon = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}
                icon = severity_icon.get(alert.get('severity', 'low'), '⚪')
                print(f"   {icon} {alert['title']}")
                print(f"      {alert['description']}")
        else:
            print("\n✅ Nenhum alerta gerado")
        
        # Recomendações
        recommendations = results.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMENDAÇÕES:")
            for i, rec in enumerate(recommendations[:5], 1):  # Top 5
                print(f"   {i}. {rec}")
        
        # 5. Salvar resultados
        print("\n5️⃣ Salvando resultados...")
        
        # Criar diretório de relatórios se não existir
        os.makedirs('reports', exist_ok=True)
        
        # Salvar relatório completo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/integrated_analysis_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Relatório salvo: {report_file}")
        
        # Salvar resumo legível
        summary_file = f"reports/summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO DE ANÁLISE BIG BROTHER CNN\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Timestamp: {results['timestamp']}\n")
            f.write(f"Localização: {metadata['location']}\n")
            f.write(f"Tempo de Execução: {results['execution_time']:.2f}s\n\n")
            
            f.write("RESUMO GERAL:\n")
            for key, value in summary.items():
                f.write(f"  {value}\n")
            
            f.write(f"\nVIOLAÇÕES: {len(violations)}\n")
            f.write(f"ALERTAS: {len(alerts)}\n")
            f.write(f"NÍVEL DE RISCO: {risk_level.upper()}\n")
        
        print(f"✅ Resumo salvo: {summary_file}")
        print("\n🎉 Demo concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a demo: {e}")
        import traceback
        traceback.print_exc()


def demo_individual_analyzers():
    """
    Demonstra uso individual de cada analyzer
    """
    print("\n🔬 DEMO: Analyzers Individuais")
    print("=" * 40)
    
    try:
        config = load_config('config.yaml')
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Preparar imagem
        sample_image = create_sample_image()
        image_tensor = prepare_image_tensor(sample_image)
        
        # Testar cada analyzer individualmente
        from analyzers import FaceAnalyzer, AttributeAnalyzer, BadgeAnalyzer
        
        print("1. Face Analyzer...")
        face_analyzer = FaceAnalyzer(config, device)
        face_analyzer.load_model()
        face_results = face_analyzer.analyze(image_tensor)
        print(f"   Resultado: {face_results.get('faces_count', 0)} face(s) detectada(s)")
        
        print("2. Attribute Analyzer...")
        attr_analyzer = AttributeAnalyzer(config, device)
        attr_analyzer.load_model()
        attr_results = attr_analyzer.analyze(image_tensor)
        print(f"   Resultado: {attr_results.get('persons_count', 0)} pessoa(s) analisada(s)")
        
        print("3. Badge Analyzer...")
        badge_analyzer = BadgeAnalyzer(config, device)
        badge_analyzer.load_model()
        badge_results = badge_analyzer.analyze(image_tensor)
        print(f"   Resultado: {badge_results.get('badges_count', 0)} crachá(s) detectado(s)")
        
        print("\n✅ Teste individual dos analyzers concluído!")
        
    except Exception as e:
        print(f"❌ Erro no teste individual: {e}")


def main():
    """
    Função principal
    """
    print("🏢 BIG BROTHER CNN - SISTEMA DE VIGILÂNCIA INTELIGENTE")
    print("Sistema modular com analyzers especializados")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('config.yaml'):
        print("❌ Arquivo config.yaml não encontrado!")
        print("   Execute este script no diretório big_brother_cnn/")
        return
    
    try:
        # Menu de opções
        print("\nOpções disponíveis:")
        print("1. Demo Análise Integrada (Recomendado)")
        print("2. Demo Analyzers Individuais")
        print("3. Análise Completa + Individual")
        
        choice = input("\nEscolha uma opção (1-3): ").strip()
        
        if choice == "1":
            demo_comprehensive_analysis()
        elif choice == "2":
            demo_individual_analyzers()
        elif choice == "3":
            demo_comprehensive_analysis()
            demo_individual_analyzers()
        else:
            print("Executando demo padrão...")
            demo_comprehensive_analysis()
    
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 