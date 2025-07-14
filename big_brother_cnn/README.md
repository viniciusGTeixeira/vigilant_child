# Big Brother CNN

Sistema de vigilância inteligente usando CNN (Rede Neural Convolucional) com **PyTorch** e **ResNet-18** para detecção e classificação de funcionários, integrado com análise de horários e rotinas de trabalho.

## 🚀 Características Principais

- **Transfer Learning** com ResNet-18 pré-treinado
- **PyTorch** como framework principal
- **Análise de horários** integrada com padrões de trabalho
- **Relatórios detalhados** com estatísticas e anomalias
- **Suporte a GPU** para treinamento e inferência
- **Configuração flexível** via YAML

## 📁 Estrutura do Projeto

```
big_brother_cnn/
│
├── _DOCS/                 # Documentação
│   ├── PRD.md             # Documento de Requisitos
│   └── SVIRO_dataset_info.md  # Informações sobre dataset SVIRO
│
├── data/                   # Dataset e metadados
│   ├── imagens/           # Imagens para treinamento/inferência
│   ├── horarios.csv       # Horários de funcionamento dos sistemas
│   └── rotinas.json       # Configuração de rotinas e padrões
│
├── models/
│   └── cnn_model.py       # Implementação CNN com ResNet-18
│
├── checkpoints/           # Modelos salvos (criado automaticamente)
├── reports/              # Relatórios de inferência (criado automaticamente)
│
├── train.py              # Script de treinamento
├── inference.py          # Script de inferência
├── utils.py              # Funções auxiliares
├── test_system.py        # Script de teste do sistema
├── config.yaml           # Configurações do modelo
├── requirements.txt      # Dependências Python
└── README.md            # Este arquivo
```

## Instalação

### 1. Clonar o repositório
```bash
git clone <repositório>
cd big_brother_cnn
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Testar o sistema
```bash
python test_system.py
```

## Uso Rápido

### 1. Preparar dados
Coloque suas imagens na pasta `data/imagens/` com nomes no formato:
```
funcionario_001_classe_0.jpg
funcionario_002_classe_1.jpg
...
```

### 2. Treinar modelo
```bash
python train.py --data_dir data --config config.yaml
```

### 3. Fazer inferência
```bash
python inference.py --model_path checkpoints/best_model.pth --image_dir data/imagens
```

## ⚙️ Configuração

Edite o arquivo `config.yaml` para ajustar:

```yaml
model:
  num_classes: 10              # Número de classes
  learning_rate: 0.0001        # Taxa de aprendizado
  batch_size: 32               # Tamanho do batch
  epochs: 50                   # Número de épocas
  freeze_backbone: true        # Congelar ResNet-18

data:
  train_split: 0.8            # 80% para treino
  validation_split: 0.1       # 10% para validação
  test_split: 0.1            # 10% para teste
```

## Classes de Detecção

O sistema suporta as seguintes classes (configurável):

```
0: Vazio (sem funcionário)
1: Funcionário presente
2: Funcionário com equipamento
3: Funcionário em movimento
4: Múltiplos funcionários
5: Situação anômala
6: Baixa visibilidade
7: Equipamento sem funcionário
8: Visitante/não funcionário
9: Incerto/baixa confiança
```

## Análise de Horários

O sistema integra análise de horários através de:

### Padrões de Trabalho
- **Horário comercial**: 06:30 - 18:30
- **Plantão 24h**: 00:00 - 23:59
- **Horários especiais**: Feriados e eventos

### Detecção de Anomalias
- Funcionários fora do horário
- Ausência durante horário de trabalho
- Padrões atípicos de presença

## Relatórios

O sistema gera relatórios detalhados incluindo:

### Estatísticas
- Total de imagens processadas
- Taxa de detecção
- Distribuição por classe
- Confiança média/máxima/mínima

### Análise de Padrões
- Correlação com horários de trabalho
- Identificação de anomalias
- Sugestões de ações

### Formatos de Saída
- **JSON**: Dados estruturados para integração
- **TXT**: Resumo legível para humanos

## Arquitetura do Modelo

### ResNet-18 Base
- **Backbone**: ResNet-18 pré-treinado no ImageNet
- **Transfer Learning**: Camadas congeladas para efficiency
- **Camadas customizadas**: Classificador adaptado ao domínio

### Otimizações
- **Adam Optimizer**: Taxa de aprendizado adaptativa
- **Early Stopping**: Previne overfitting
- **Data Augmentation**: Aumenta diversidade dos dados

## Métricas de Performance

### Métricas Principais
- **Accuracy**: Precisão geral do modelo
- **Precision/Recall**: Por classe individual
- **F1-Score**: Métrica balanceada
- **Confidence**: Distribuição de confiança

### Benchmarking
- Comparação com dataset SVIRO
- Validação cruzada
- Testes de robustez

## 🔗 Integração com Datasets

### SVIRO Dataset
O sistema é compatível com o dataset SVIRO para:
- **Treinamento inicial**: Transfer learning
- **Validação**: Benchmark de performance
- **Teste de robustez**: Diferentes condições

Consulte `_DOCS/SVIRO_dataset_info.md` para mais detalhes.

### Outros Datasets
- **Market-1501**: Re-identificação de pessoas
- **CASIA-WebFace**: Reconhecimento facial
- **WIDER**: Atributos de pessoas

## 🛠️ Scripts Disponíveis

### `train.py`
Treinamento do modelo com features:
- Validação cruzada
- Checkpoints automáticos
- Gráficos de treinamento
- Early stopping

```bash
python train.py --config config.yaml --data_dir data
```

### `inference.py`
Inferência com opções:
- Imagem única ou lote
- Relatórios detalhados
- Análise de anomalias
- Integração com horários

```bash
python inference.py --model_path checkpoints/best_model.pth --image_dir data/imagens
```

### `test_system.py`
Testes automatizados:
- Validação de configuração
- Teste de modelo
- Verificação de dados
- Análise de horários

```bash
python test_system.py
```

## 🐛 Solução de Problemas

### Erro: "Nenhuma imagem encontrada"
```bash
# Criar imagens dummy para teste
python test_system.py
```

### Erro: "CUDA out of memory"
```yaml
# Reduzir batch_size no config.yaml
model:
  batch_size: 16  # ou menor
```

### Erro: "Module not found"
```bash
# Reinstalar dependências
pip install -r requirements.txt
```

## 📋 Requisitos do Sistema

### Hardware
- **RAM**: 8GB mínimo, 16GB recomendado
- **GPU**: NVIDIA com CUDA (opcional, mas recomendado)
- **Armazenamento**: 2GB livres

### Software
- **Python**: 3.8+
- **PyTorch**: 1.13+
- **CUDA**: 11.0+ (se usando GPU)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto segue as diretrizes:
- **Dataset SVIRO**: CC BY-NC-SA 4.0 (não comercial)
- **Código próprio**: A definir pelo projeto

## 🔍 Monitoramento e Logs

### Logs de Treinamento
```
Epoch 1/50: Train Loss: 0.8456, Val Loss: 0.7234, Val Acc: 72.34%
Epoch 2/50: Train Loss: 0.6789, Val Loss: 0.6123, Val Acc: 78.90%
...
```

### Relatórios de Inferência
```
=== RESUMO DA INFERÊNCIA ===
Imagens processadas: 150
Detecções com alta confiança: 132
Taxa de detecção: 88.0%
Anomalias detectadas: 3
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a documentação em `_DOCS/`
2. Execute `python test_system.py`
3. Consulte os logs em `checkpoints/`
4. Abra uma issue no repositório

---

**Desenvolvido para vigilância inteligente com foco em detecção de funcionários e análise de padrões de trabalho.** 