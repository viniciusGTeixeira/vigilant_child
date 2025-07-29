# 🚀 Guia de Setup - Big Brother CNN

## Pré-requisitos

### 1. Instalar Podman
```bash
# Windows (via Chocolatey)
choco install podman-desktop

# Ou baixar diretamente:
# https://podman.io/getting-started/installation
```

### 2. Instalar Podman Compose
```bash
pip install podman-compose
```

### 3. Verificar Instalação
```bash
podman --version
podman-compose --version
```

## 📋 Roteiro de Execução

### Passo 1: Preparar o Ambiente
```bash
# Clonar/navegar para o projeto
cd C:\Users\kemersson.teixeira\Documents\Projetos-x\bigbrother_Project

# Verificar estrutura
dir
```

### Passo 2: Construir as Imagens
```bash
# Navegar para pasta podman
cd podman

# Construir todas as imagens
podman-compose build

# Ou construir individualmente se necessário:
podman build -t bigbrother-api -f ../Dockerfile ..
podman build -t bigbrother-kafka -f kafka/Dockerfile kafka/
podman build -t bigbrother-minio -f minio/Dockerfile minio/
podman build -t bigbrother-grafana -f grafana/Dockerfile grafana/
```

### Passo 3: Iniciar os Serviços
```bash
# Iniciar todos os serviços
podman-compose up -d

# Verificar status
podman-compose ps

# Ver logs em tempo real
podman-compose logs -f
```

### Passo 4: Verificar Serviços

#### 4.1 Health Check Básico
```bash
# API Health Check
curl http://localhost:8000/health

# Ou no PowerShell:
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

#### 4.2 Verificar Cada Serviço
- **API FastAPI**: http://localhost:8000 (Python 3.12 + Ultralytics)
- **Documentação Swagger**: http://localhost:8000/docs
- **Detectron2 Service**: http://localhost:8001 (Python 3.7)
- **Ultralytics Service**: http://localhost:8002 (Python 3.12)
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **MLflow**: http://localhost:5000

### Passo 5: Testar Funcionalidades

#### 5.1 Testar API Básica
```bash
# Endpoint raiz
curl http://localhost:8000/

# Métricas
curl http://localhost:8000/api/v1/monitoring/metrics

# Sistema
curl http://localhost:8000/api/v1/monitoring/system
```

#### 5.2 Testar Análise de Imagem (Exemplo)
```bash
# Criar arquivo de teste
echo '{
  "analysis_type": "face",
  "image": {
    "filename": "test.jpg",
    "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
    "metadata": {"location": "test"}
  }
}' > test_analysis.json

# Enviar para análise
curl -X POST http://localhost:8000/api/v1/analysis/analyze \
  -H "Content-Type: application/json" \
  -d @test_analysis.json
```

## 🔧 Troubleshooting

### Problema 1: Portas Ocupadas
```bash
# Verificar portas em uso
netstat -an | findstr :8000
netstat -an | findstr :3000
netstat -an | findstr :9090

# Parar serviços se necessário
podman-compose down
```

### Problema 2: Problemas de Permissão
```bash
# Executar como administrador
# Ou ajustar permissões do Podman
```

### Problema 3: Serviços Não Sobem
```bash
# Ver logs detalhados
podman-compose logs <service_name>

# Exemplo:
podman-compose logs api
podman-compose logs kafka
podman-compose logs postgres
```

### Problema 4: Dependências Python
```bash
# Reconstruir imagem da API
podman build -t bigbrother-api -f ../Dockerfile .. --no-cache
```

## 📊 Monitoramento

### Grafana Dashboards
1. Acesse http://localhost:3000
2. Login: admin/admin
3. Vá para Dashboards → Big Brother Overview

### Prometheus Metrics
1. Acesse http://localhost:9090
2. Teste queries:
   - `up` - Status dos serviços
   - `api_requests_total` - Total de requests
   - `system_cpu_usage` - Uso de CPU

## 🧪 Testes Funcionais

### Teste 1: API Funcionando
```bash
# Deve retornar status 200
curl -I http://localhost:8000/health
```

### Teste 2: Documentação
- Acesse http://localhost:8000/docs
- Deve mostrar interface Swagger

### Teste 3: Monitoramento
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

### Teste 4: Armazenamento
- MinIO: http://localhost:9001
- Deve mostrar buckets configurados

## 🚨 Comandos Úteis

### Gerenciamento de Containers
```bash
# Parar todos os serviços
podman-compose down

# Reiniciar um serviço específico
podman-compose restart api

# Ver logs de um serviço
podman-compose logs -f api

# Executar comando em container
podman-compose exec api bash
```

### Limpeza
```bash
# Remover containers parados
podman container prune

# Remover imagens não utilizadas
podman image prune

# Limpeza completa
podman system prune -a
```

## 📚 Organização dos Requirements

Os arquivos de dependências Python estão centralizados em `podman/requirements/`:

- `base.txt`: dependências comuns a todos os serviços.
- `fastapi.txt`: inclui o `base.txt` e adiciona dependências específicas da API.
- `cnn.txt`: inclui o `base.txt` e adiciona dependências de visão computacional e machine learning.

Cada serviço utiliza seu requirements específico durante o build do Docker:
- O serviço FastAPI usa `fastapi.txt`.
- Serviços de ML/CNN usam `cnn.txt`.

> **Sempre que precisar adicionar uma nova dependência, edite o arquivo requirements correspondente em `podman/requirements/`. Não use requirements.txt soltos em outras pastas para evitar inconsistências.**

## 📈 Próximos Passos

Após confirmar que tudo está funcionando:

1. **Testar análise de imagens reais**
2. **Configurar dados de teste**
3. **Explorar dashboards Grafana**
4. **Testar diferentes tipos de análise**
5. **Verificar logs e métricas**

## 🆘 Suporte

Se encontrar problemas:
1. Verifique logs: `podman-compose logs`
2. Verifique status: `podman-compose ps`
3. Reinicie serviços: `podman-compose restart`
4. Reconstrua se necessário: `podman-compose build --no-cache` 