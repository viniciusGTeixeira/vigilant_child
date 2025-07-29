#!/usr/bin/env pwsh
# Script para iniciar o Big Brother CNN em ambiente local

Write-Host "🚀 Iniciando Big Brother CNN Demo" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Função para verificar se um comando existe
function Test-Command($command) {
    try {
        Get-Command $command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Verificar pré-requisitos
Write-Host "🔍 Verificando pré-requisitos..." -ForegroundColor Yellow

if (-not (Test-Command "podman")) {
    Write-Host "❌ Podman não encontrado. Instale o Podman primeiro." -ForegroundColor Red
    Write-Host "   Baixe em: https://podman.io/getting-started/installation" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Command "podman-compose")) {
    Write-Host "❌ Podman-compose não encontrado. Instale com: pip install podman-compose" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Pré-requisitos verificados!" -ForegroundColor Green

# Navegar para diretório podman
Write-Host "📁 Navegando para diretório podman..." -ForegroundColor Yellow
Set-Location "podman"

# Parar serviços existentes
Write-Host "🛑 Parando serviços existentes..." -ForegroundColor Yellow
podman-compose down 2>$null

# Construir imagens
Write-Host "🏗️ Construindo imagens..." -ForegroundColor Yellow
podman-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao construir imagens!" -ForegroundColor Red
    exit 1
}

# Iniciar serviços
Write-Host "🚀 Iniciando serviços..." -ForegroundColor Yellow
podman-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao iniciar serviços!" -ForegroundColor Red
    exit 1
}

# Aguardar serviços subirem
Write-Host "⏳ Aguardando serviços iniciarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Verificar status
Write-Host "🔍 Verificando status dos serviços..." -ForegroundColor Yellow
podman-compose ps

# Testar API
Write-Host "🧪 Testando API..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
    Write-Host "✅ API funcionando!" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️ API ainda não está respondendo. Verifique logs." -ForegroundColor Yellow
}

# Mostrar informações de acesso
Write-Host ""
Write-Host "🎉 Sistema iniciado com sucesso!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Serviços disponíveis:" -ForegroundColor Cyan
Write-Host "   🌐 API FastAPI:        http://localhost:8000" -ForegroundColor White
Write-Host "   📚 Documentação:       http://localhost:8000/docs" -ForegroundColor White
Write-Host "   📊 Grafana:            http://localhost:3000 (admin/admin)" -ForegroundColor White
Write-Host "   📈 Prometheus:         http://localhost:9090" -ForegroundColor White
Write-Host "   💾 MinIO Console:      http://localhost:9001 (minioadmin/minioadmin)" -ForegroundColor White
Write-Host "   🔬 MLflow:             http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "🧪 Comandos de teste:" -ForegroundColor Cyan
Write-Host "   Health Check:          Invoke-RestMethod -Uri 'http://localhost:8000/health'" -ForegroundColor White
Write-Host "   Métricas:              Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/monitoring/metrics'" -ForegroundColor White
Write-Host "   Sistema:               Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/monitoring/system'" -ForegroundColor White
Write-Host ""
Write-Host "📝 Logs em tempo real:    podman-compose logs -f" -ForegroundColor Cyan
Write-Host "🛑 Parar sistema:         podman-compose down" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pronto para testar!" -ForegroundColor Green 