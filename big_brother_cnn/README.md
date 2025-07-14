# Big Brother CNN - Sistema de Vigilância Inteligente Modular

Sistema avançado de vigilância corporativa usando **CNNs modulares** com **PyTorch** e **analyzers especializados** para monitoramento completo de funcionários, incluindo reconhecimento facial, análise de vestimentas, detecção de crachás, verificação de horários e análise de padrões comportamentais.

## Características Principais

- **Sistema Modular**: Analyzers especializados com responsabilidades separadas
- **Reconhecimento Facial**: CASIA-WebFace + VGG Face2 + face_recognition
- **Análise de Atributos**: WIDER Attribute Dataset (14 atributos corporativos)
- **Detecção de Crachás**: OCR + CNN para validação obrigatória
- **Análise de Horários**: Verificação automática de conformidade
- **Análise de Padrões**: Detecção de mudanças comportamentais
- **Sistema de Alertas**: Notificações em tempo real
- **Relatórios Integrados**: Análise multi-modal consolidada

## Estrutura do Projeto

```
big_brother_cnn/
│
├── _DOCS/                    # Documentação
│   ├── PRD.md                # Documento de Requisitos
│   └── SVIRO_dataset_info.md # Informações sobre dataset SVIRO
│
├── analyzers/                # ANALYZERS ESPECIALIZADOS
│   ├── __init__.py           # Imports dos analyzers
│   ├── base_analyzer.py      # Classe base para todos analyzers
│   ├── face_analyzer.py      # Reconhecimento facial
│   ├── attribute_analyzer.py # Análise de roupas/acessórios
│   ├── badge_analyzer.py     # Detecção de crachás + OCR
│   ├── schedule_analyzer.py  # Análise de horários/rotinas
│   └── pattern_analyzer.py   # Análise de padrões comportamentais
│
├── data/                    # Dataset e metadados
│   ├── imagens/             # Imagens para treinamento/inferência
│   ├── horarios.csv         # Horários de funcionamento
│   ├── rotinas.json         # Configuração de rotinas
│   └── patterns.db          # Base de dados de padrões (SQLite)
│
├── models/                   # Modelos treinados
│   ├── cnn_model.py          # ResNet-18 principal
│   ├── employee_faces.pkl    # Base de faces conhecidas
│   ├── attribute_model.pth   # Modelo de atributos
│   └── badge_detector.pth    # Detector de crachás
│
├── checkpoints/             # Checkpoints do modelo principal
├── reports/                 # Relatórios de análise
├── logs/                    # Logs de debugging
│
├── integrated_analysis.py   # SISTEMA INTEGRADO PRINCIPAL
├── train.py                 # Script de treinamento
├── inference.py             # Script de inferência
├── utils.py                 # Funções auxiliares
├── test_system.py           # Testes automatizados
├── example_integrated_analysis.py  # DEMO COMPLETA
├── config.yaml              # Configurações detalhadas
├── requirements.txt         # Dependências completas
└── README.md               # Este arquivo
```

## Analyzers Especializados

### 1. Face Analyzer
**Baseado em**: CASIA-WebFace, VGG Face2, face_recognition
```python
# Funcionalidades
- Detecção de múltiplas faces
- Reconhecimento de funcionários conhecidos
- Análise de qualidade facial
- Base de dados de funcionários
- Confiança de reconhecimento
```

### 2. Attribute Analyzer  
**Baseado em**: WIDER Attribute Dataset (14 atributos)
```python
# Atributos Detectados
- Vestimenta: formal/casual, manga longa/curta
- Acessórios: óculos, chapéu, bolsa/mochila
- Conformidade: dress code corporativo
- Identificação: riscos de obstrução facial
```

### 3. Badge Analyzer
**Baseado em**: CNN + Tesseract OCR + EasyOCR
```python
# Funcionalidades
- Detecção automática de crachás
- OCR para extração de texto
- Validação de posicionamento
- Verificação de visibilidade
- Conformidade obrigatória
```

### 4. Schedule Analyzer
**Integrado com**: horarios.csv + rotinas.json
```python
# Monitoramento
- Horários de entrada/saída
- Intervalos de almoço
- Trabalho em fins de semana
- Horas extras não autorizadas
- Presença fora do expediente
```

### 5. Pattern Analyzer
**Base de dados**: SQLite com histórico comportamental
```python
# Análise de Padrões
- Trajetos habituais
- Mudanças de rotina
- Acesso a áreas restritas
- Horários atípicos
- Comportamento social
```

## Instalação

### 1. Clonar repositório
```bash
git clone <repositório>
cd big_brother_cnn
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar Tesseract (Windows)
```bash
# Baixar e instalar Tesseract OCR
# https://github.com/UB-Mannheim/tesseract/wiki
```

### 4. Testar sistema
```bash
python test_system.py
```

## Uso Rápido

### Demo Completa
```bash
python example_integrated_analysis.py
```

### Configuração
Edite `config.yaml` para ajustar:
```yaml
analyzers:
  face:
    confidence_threshold: 0.6
    recognition_tolerance: 0.6
  
  attributes:
    required_formal_score: 0.6
    detect_uniforms: true
  
  badge:
    ocr_enabled: true
    confidence_threshold: 0.7
  
  schedule:
    tolerance_minutes: 15
    weekend_work_alert: true
    
  patterns:
    behavior_change_threshold: 0.3
    restricted_areas: ['server_room', 'finance']
```

### Análise Integrada
```python
from integrated_analysis import IntegratedAnalysisSystem

# Inicializar sistema
system = IntegratedAnalysisSystem('config.yaml')

# Carregar imagem
image_tensor = load_image_as_tensor('path/to/image.jpg')

# Metadados
metadata = {
    'location': 'office_main',
    'timestamp': datetime.now().isoformat(),
    'camera_id': 'cam_001'
}

# Análise completa
results = system.analyze_comprehensive(image_tensor, metadata)

# Resumo
summary = system.get_analysis_summary(results)
print(summary)
```

## Casos de Uso Específicos

### 1. **Detectar Funcionários Sem Crachá**
```python
badge_results = results['individual_analyses']['badge']
if not badge_results['has_valid_badge']:
    print("🚨 ALERTA: Funcionário sem crachá detectado")
```

### 2. **Analisar Conformidade de Vestimenta**
```python
attr_results = results['individual_analyses']['attributes']
if not attr_results['dress_code_compliant']:
    print("⚠️ Dress code fora do padrão corporativo")
```

### 3. **Monitorar Horários de Trabalho**
```python
schedule_results = results['individual_analyses']['schedule']
if schedule_results['compliance_status'] == 'violation':
    print("⏰ Funcionário fora do horário autorizado")
```

### 4. **Detectar Mudanças de Padrão**
```python
if 'pattern_analysis' in results:
    changes = results['pattern_analysis']['behavioral_changes']
    if changes:
        print(f"📊 {len(changes)} mudanças comportamentais detectadas")
```

### 5. **Sistema de Alertas**
```python
alerts = results['alerts']
critical_alerts = [a for a in alerts if a['severity'] == 'critical']
if critical_alerts:
    print(f"🚨 {len(critical_alerts)} alertas críticos!")
```

## Métricas e Relatórios

### Relatório Integrado
```json
{
  "timestamp": "2024-01-15T14:30:00",
  "individual_analyses": {
    "face": {"employee_detected": true, "confidence": 0.92},
    "attributes": {"dress_code_compliant": true, "formal_score": 0.85},
    "badge": {"has_valid_badge": true, "badge_visible": true},
    "schedule": {"compliance_status": "compliant"},
    "patterns": {"anomalies": [], "risk_level": "low"}
  },
  "integrated_assessment": {
    "overall_assessment": {
      "status": "normal",
      "confidence": 0.89,
      "action_required": false
    }
  },
  "alerts": [],
  "recommendations": ["Continuar monitoramento de rotina"]
}
```

### Dashboard de Conformidade
- ✅ **Identificação**: João Silva (92% confiança)
- ✅ **Crachá**: Visível e válido
- ✅ **Vestimenta**: Conformidade total (85% formal)
- ✅ **Horário**: Dentro do expediente
- ✅ **Padrão**: Comportamento normal

## Integração com Datasets

### SVIRO Dataset
Compatível com [SVIRO Dataset](https://sviro.kl.dfki.de/) para:
- Treinamento inicial com transfer learning
- Validação de robustez em diferentes condições
- Benchmark de performance

### Unity Perception
Integração com [Unity Perception](https://github.com/Unity-Technologies/com.unity.perception) para:
- Geração de dados sintéticos
- Simulação de cenários corporativos
- Aumento de dataset

### Outros Datasets Suportados
- **Market-1501**: Re-identificação de pessoas
- **CASIA-WebFace**: Reconhecimento facial robusto
- **WIDER Attribute**: Análise detalhada de atributos

## Sistema de Alertas

### Níveis de Severidade
- 🔴 **Critical**: Pessoa não identificada, acesso não autorizado
- 🟠 **High**: Violação de horário, sem crachá
- 🟡 **Medium**: Dress code inadequado, padrão atípico
- 🟢 **Low**: Variações menores nos padrões

### Políticas Configuráveis
```yaml
policies:
  mandatory_badge: true          # Crachá obrigatório
  dress_code_enforcement: true   # Enforçar dress code
  restricted_area_monitoring: true  # Monitorar áreas restritas
  after_hours_alerts: true      # Alertas fora do horário
  unknown_person_alerts: true   # Alertas pessoa desconhecida
```

## Scripts Disponíveis

### `integrated_analysis.py`
Sistema principal que orquestra todos os analyzers

### `example_integrated_analysis.py`
Demo completa com casos de uso reais

### `train.py`
```bash
python train.py --config config.yaml --data_dir data
```

### `inference.py`
```bash
python inference.py --model_path checkpoints/best_model.pth --image_dir data/imagens
```

### `test_system.py`
```bash
python test_system.py  # Testa todos os componentes
```

## 🐛 Solução de Problemas

### Erro: "Face recognition não instalado"
```bash
pip install face-recognition
# No Windows, pode precisar de Visual Studio Build Tools
```

### Erro: "Tesseract não encontrado"
```bash
# Windows: Instalar Tesseract OCR
# Linux: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract
```

### Erro: "CUDA out of memory"
```yaml
# config.yaml
device:
  use_cuda: false  # Forçar CPU
# ou
model:
  batch_size: 8    # Reduzir batch size
```

### Erro: "Sem base de funcionários"
```python
# Criar base de faces conhecidas
from analyzers import FaceAnalyzer
face_analyzer = FaceAnalyzer(config, device)
face_analyzer.add_employee_face('path/to/photo.jpg', 'Nome Funcionario')
face_analyzer.save_employee_database('models/employee_faces.pkl')
```

## Requisitos do Sistema

### Hardware Mínimo
- **RAM**: 8GB (16GB recomendado)
- **GPU**: NVIDIA GTX 1060+ (opcional, mas acelera 10x)
- **Armazenamento**: 5GB livres
- **CPU**: Intel i5 ou AMD Ryzen 5+

### Software
- **Python**: 3.8+
- **PyTorch**: 1.13+
- **CUDA**: 11.0+ (para GPU)
- **Tesseract OCR**: 4.0+

## Segurança e Privacidade

### Dados Biométricos
- Encodings faciais criptografados
- Não armazena imagens originais
- Conformidade com LGPD/GDPR

### Logs e Auditoria
- Histórico completo de detecções
- Logs de acesso e modificações
- Relatórios de conformidade


### Criando Novo Analyzer
```python
from analyzers.base_analyzer import BaseAnalyzer

class MyCustomAnalyzer(BaseAnalyzer):
    def load_model(self, model_path=None):
        # Implementar carregamento
        pass
    
    def analyze(self, image, metadata=None):
        # Implementar análise
        return self.postprocess_results(results)
    
    def get_confidence_threshold(self):
        return 0.7
```

### Datasets Utilizados
- **SVIRO**: CC BY-NC-SA 4.0 (não comercial)
- **WIDER**: Uso acadêmico
- **CASIA-WebFace**: Uso de pesquisa

### Bibliotecas
- PyTorch: BSD License
- face_recognition: MIT License
- OpenCV: Apache License 2.0

### Documentação
1. Consulte `_DOCS/` para detalhes técnicos
2. Execute `python test_system.py` para diagnósticos
3. Verifique logs em `logs/`

### Issues Comuns
- Falha na detecção → Verificar iluminação e qualidade da imagem
- Baixa performance → Configurar GPU ou reduzir batch_size
- Problemas de OCR → Instalar Tesseract corretamente

---

**🏢 Sistema Big Brother CNN - Vigilância Corporativa Inteligente com Analyzers Especializados**

*Desenvolvido para monitoramento completo e análise comportamental avançada em ambientes corporativos.* 