# SVIRO Dataset - Informações Detalhadas

## Visão Geral

O **SVIRO** (Synthetic Vehicle Interior Rear seat Occupancy) é um dataset sintético para detecção e classificação de ocupação de assentos traseiros de veículos. O dataset consiste em 25.000 cenários através de dez veículos diferentes, fornecendo diversas entradas de sensores simulados e dados de ground truth.

## Características Principais

### 📊 Estatísticas do Dataset
- **25.000 cenários** gerados sinteticamente
- **10 veículos** diferentes
- **5 benchmarks** disponíveis
- Múltiplas modalidades de dados (RGB, infravermelho, profundidade)

### 🎯 Objetivos
- Avaliar capacidades de generalização de modelos de machine learning
- Testar confiabilidade quando treinados com variações limitadas
- Fornecer benchmark comum para aplicações de engenharia com recursos limitados

## Tipos de Dados Disponíveis

### 1. **Imagens RGB**
- Imagens coloridas padrão dos interiores dos veículos
- Resolução apropriada para CNNs (224x224 recomendado)

### 2. **Imitação de Infravermelho**
- Simulação de dados térmicos
- Útil para detecção em condições de baixa luminosidade

### 3. **Imagens de Profundidade**
- Dados de distância/profundidade
- Informações espaciais 3D

### 4. **Máscaras de Segmentação**
- Segmentação semântica e de instância
- Anotações pixel-level

### 5. **Keypoints**
- Pontos-chave para estimativa de pose
- Localização precisa de partes do corpo

### 6. **Bounding Boxes**
- Caixas delimitadoras para detecção de objetos
- Formato padrão para treinamento de detectores

## Variações do Dataset

### SVIRO-Illumination
- **500 imagens** por veículo (250 treino, 250 teste)
- **10 condições** de iluminação diferentes
- **3 interiores** de veículos
- Foco: robustez a mudanças de iluminação

### SVIRO-Uncertainty
- **Aplicações críticas** de segurança
- **Estimativa de incerteza** nas predições
- **3 posições** de assento no banco traseiro
- Datasets: adultos (4384 amostras, 8 classes) e misto (3515 amostras, 64 classes)

### SVIRO-NoCar
- **2938 treino** e **2981 teste**
- **10 fundos** diferentes por cenário
- Foco: invariância a fundos dominantes
- Transferência sintético → real

### SVIRO-InterCar
- **1000 cenários** (apenas adultos)
- **990 cenários** (adultos, crianças, bebês)
- **10 veículos** diferentes
- Mudança completa do interior do veículo

## Aplicações no Projeto Big Brother CNN

### 1. **Transfer Learning**
- Usar pesos pré-treinados no SVIRO
- Adaptar para detecção de funcionários
- Aproveitar features aprendidas

### 2. **Data Augmentation**
- Combinar dados reais com sintéticos
- Aumentar diversidade do dataset
- Melhorar generalização

### 3. **Benchmark e Validação**
- Comparar performance com outros métodos
- Validar robustez do modelo
- Testar em condições adversas

## Estrutura de Classificação Sugerida

```
Classes para Big Brother CNN:
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

## Integração com Horários

### Correlação com Rotinas
- Mapear detecções com horários de funcionamento
- Identificar padrões anômalos fora do horário
- Validar presença durante horário de trabalho

### Análise Temporal
- Monitorar mudanças ao longo do tempo
- Detectar padrões sazonais
- Alertas para atividades fora do padrão

## Métricas de Avaliação

### 1. **Accuracy**
- Precisão geral do modelo
- Comparação com baseline

### 2. **Precision/Recall**
- Por classe individual
- Matriz de confusão

### 3. **F1-Score**
- Balanço entre precisão e recall
- Métrica principal para avaliação

### 4. **Confidence Scores**
- Distribuição de confiança
- Threshold otimizado

## Citações Necessárias

Quando usar o dataset SVIRO, citar:

```bibtex
@INPROCEEDINGS{DiasDaCruz2020SVIRO,
  author = {Steve {Dias Da Cruz} and Oliver Wasenm\"uller and Hans-Peter Beise and Thomas Stifter and Didier Stricker},
  title = {SVIRO: Synthetic Vehicle Interior Rear Seat Occupancy Dataset and Benchmark},
  booktitle = {IEEE Winter Conference on Applications of Computer Vision (WACV)},
  year = {2020}
}
```

## Limitações e Considerações

### 1. **Dados Sintéticos**
- Pode haver gap entre sintético e real
- Necessário validação com dados reais

### 2. **Domínio Específico**
- Focado em interiores de veículos
- Adaptação necessária para outros ambientes

### 3. **Licença**
- Creative Commons Attribution-NonCommercial-ShareAlike 4.0
- Uso não comercial apenas
- Distribuição com mesma licença

## Recursos Adicionais

- **Website**: https://sviro.kl.dfki.de/
- **Benchmark**: Leaderboard público disponível
- **Suporte**: Labels para dados de teste disponíveis
- **Documentação**: Formato de dados detalhado

## Recomendações para Uso

1. **Começar com SVIRO base** para proof of concept
2. **Usar SVIRO-Illumination** para robustez
3. **Aplicar SVIRO-Uncertainty** para confiabilidade
4. **Combinar com dados reais** para melhor performance
5. **Validar em ambiente real** antes de produção 