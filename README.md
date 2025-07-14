# Big Brother CNN - Sistema de Vigilância com IA

Sistema completo de vigilância inteligente usando CNNs para análise de imagens, detecção facial, reconhecimento de crachás e monitoramento de conformidade.

## 🏗️ Arquitetura

O sistema é composto por:

- **API FastAPI**: Interface REST para todas as funcionalidades
- **Analyzers Especializados**: Módulos de análise (Face, Badge, Attribute, Schedule, Pattern)
- **PostgreSQL**: Dados estruturados (funcionários, horários, configurações)
- **Cassandra**: Séries temporais (detecções, padrões)
- **Kafka**: Streaming de eventos em tempo real
- **MinIO**: Armazenamento de imagens e modelos
- **MLflow**: Tracking de experimentos e modelos
- **Prometheus**: Métricas e monitoramento
- **Grafana**: Dashboards e visualizações

## 🚀 Funcionalidades

### Análise de Imagens
- **Detecção Facial**: Reconhecimento de funcionários conhecidos
- **Detecção de Crachás**: Verificação de uso correto de identificação
- **Análise de Atributos**: Verificação de dress code e uniformes
- **Análise de Horários**: Conformidade com horários de trabalho
- **Análise de Padrões**: Detecção de comportamentos anômalos

### Monitoramento
- **Métricas Prometheus**: Coleta automática de métricas
- **Dashboards Grafana**: Visualização em tempo real
- **Alertas**: Notificações automáticas de eventos
- **Logs**: Sistema completo de auditoria

### Streaming
- **Kafka**: Processamento de eventos em tempo real
- **MinIO**: Armazenamento escalável de imagens
- **MLflow**: Versionamento e deploy de modelos

## 📦 Instalação

### Pré-requisitos
- Docker/Podman
- Python 3.11+
- Git

### Configuração Rápida

1. **Clone o repositório**
```bash
git clone <repository-url>
cd bigbrother_Project
```

2. **Inicie os serviços**
```bash
cd podman
docker-compose up -d
```

3. **Verifique o status**
```bash
docker-compose ps
```

### Serviços Disponíveis

| Serviço | Porta | URL | Credenciais |
|---------|-------|-----|-------------|
| API FastAPI | 8000 | http://localhost:8000 | - |
| Grafana | 3000 | http://localhost:3000 | admin/admin |
| Prometheus | 9090 | http://localhost:9090 | - |
| MinIO Console | 9001 | http://localhost:9001 | bigbrother/bigbrother |
| MLflow | 5000 | http://localhost:5000 | - |
| PostgreSQL | 5432 | localhost:5432 | bigbrother/bigbrother |

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Banco de dados
DB_HOST=postgres
DB_PORT=5432
DB_NAME=bigbrother
DB_USER=bigbrother
DB_PASSWORD=bigbrother

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=bigbrother
MINIO_SECRET_KEY=bigbrother

# MLflow
MLFLOW_TRACKING_URI=http://mlflow:5000

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
```

### Configuração dos Analyzers

Edite `big_brother_cnn/config.yaml` para ajustar:

```yaml
analyzers:
  face:
    confidence_threshold: 0.6
    detection_method: 'hog'
  
  badge:
    confidence_threshold: 0.7
    ocr_enabled: true
  
  schedule:
    tolerance_minutes: 15
    weekend_work_alert: true
```

## 📊 API Endpoints

### Análise
- `POST /api/v1/analysis/analyze` - Análise geral
- `POST /api/v1/analysis/analyze/face` - Análise facial
- `POST /api/v1/analysis/analyze/badge` - Análise de crachá
- `POST /api/v1/analysis/analyze/schedule` - Análise de horário
- `POST /api/v1/analysis/analyze/pattern` - Análise de padrões

### Monitoramento
- `GET /api/v1/monitoring/metrics` - Métricas Prometheus
- `GET /api/v1/monitoring/health` - Health check
- `GET /api/v1/monitoring/statistics` - Estatísticas
- `GET /api/v1/monitoring/alerts` - Lista de alertas

### Documentação
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc

## 🔍 Monitoramento

### Métricas Principais

- `bigbrother_analysis_requests_total` - Total de análises
- `bigbrother_analysis_duration_seconds` - Duração das análises
- `bigbrother_detections_total` - Total de detecções
- `bigbrother_system_cpu_usage_percent` - Uso de CPU
- `bigbrother_anomalies_detected_total` - Anomalias detectadas

### Dashboards Grafana

Acesse http://localhost:3000 e use:
- **Big Brother CNN - Overview**: Dashboard principal
- **System Metrics**: Métricas do sistema
- **Analysis Performance**: Performance das análises

## 🧪 Desenvolvimento

### Estrutura do Projeto

```
bigbrother_Project/
├── big_brother_cnn/
│   ├── analyzers/          # Módulos de análise
│   ├── api/               # API FastAPI
│   ├── models/            # Modelos ML
│   ├── utils/             # Utilitários
│   └── config.yaml        # Configuração
├── podman/                # Infraestrutura
│   ├── postgres/          # PostgreSQL
│   ├── kafka/             # Kafka
│   ├── minio/             # MinIO
│   ├── mlflow/            # MLflow
│   ├── prometheus/        # Prometheus
│   └── grafana/           # Grafana
└── Dockerfile             # Container principal
```

### Executar Localmente

```bash
# Instalar dependências
pip install -r big_brother_cnn/requirements.txt

# Executar API
cd big_brother_cnn
python -m uvicorn api.main:app --reload

# Executar testes
python -m pytest tests/
```

### Adicionar Novo Analyzer

1. Crie a classe herdando de `BaseAnalyzer`
2. Implemente os métodos abstratos
3. Adicione à configuração
4. Registre na API

## 🔒 Segurança

- **Autenticação JWT**: Tokens para acesso à API
- **HTTPS**: Comunicação segura (configurar em produção)
- **Usuários não-root**: Containers executam com usuários limitados
- **Secrets**: Variáveis sensíveis em arquivos separados

## 📈 Performance

### Otimizações Implementadas

- **Cache de Analyzers**: Reutilização de modelos carregados
- **Processamento Assíncrono**: FastAPI com async/await
- **Batch Processing**: Análise em lote para múltiplas imagens
- **Métricas**: Monitoramento de performance em tempo real

### Benchmarks

- **Análise Facial**: ~300ms por imagem
- **Detecção de Crachá**: ~400ms por imagem
- **Análise de Horário**: ~100ms por verificação
- **Throughput**: ~10 análises/segundo

## 🐛 Troubleshooting

### Problemas Comuns

1. **Erro de conexão com banco**
   ```bash
   docker-compose logs postgres
   ```

2. **Kafka não conecta**
   ```bash
   docker-compose restart kafka
   ```

3. **MinIO não acessível**
   ```bash
   docker-compose logs minio
   ```

4. **Métricas não aparecem**
   ```bash
   curl http://localhost:8000/api/v1/monitoring/metrics
   ```

### Logs

```bash
# Logs de todos os serviços
docker-compose logs -f

# Logs específicos
docker-compose logs -f fastapi
docker-compose logs -f prometheus
```

## 🚀 Deploy em Produção

### Configurações Necessárias

1. **Variáveis de Ambiente**
   - Senhas seguras
   - URLs corretas
   - Certificados SSL

2. **Volumes Persistentes**
   - Dados do PostgreSQL
   - Imagens do MinIO
   - Métricas do Prometheus

3. **Backup**
   - Banco de dados
   - Configurações
   - Modelos ML

### Exemplo Docker Compose Produção

```yaml
version: '3.8'
services:
  fastapi:
    image: bigbrother:latest
    environment:
      - ENV=production
      - DB_PASSWORD=${DB_PASSWORD}
    volumes:
      - /data/models:/app/models
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## 🆘 Suporte

Para suporte, abra uma issue no GitHub ou entre em contato com a equipe de desenvolvimento.

---

**Big Brother CNN** - Sistema de Vigilância Inteligente com IA 🤖👁️ 