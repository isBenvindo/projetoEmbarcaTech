# ============================================================
# Sistema Terelina - Script de Inicialização (Windows PowerShell)
# ============================================================

Write-Host "==============================================="
Write-Host "  SISTEMA TERELINA - INICIALIZAÇÃO AUTOMÁTICA  "
Write-Host "==============================================="

# Verifica se o Docker Desktop está em execução
$dockerProcess = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
if (-not $dockerProcess) {
    Write-Host "Docker Desktop não está aberto. Iniciando..."
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Write-Host "Aguardando inicialização do Docker..."
    Start-Sleep -Seconds 20
}

# Define o diretório do projeto
Set-Location "$PSScriptRoot"

Write-Host "`nLimpando containers antigos..."
docker compose down -v

Write-Host "`nConstruindo e inicializando containers..."
docker compose up --build -d

# Exibe status geral
Write-Host "`nStatus dos containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host "`n------------------------------------------------"
Write-Host "API disponível em: http://localhost:8000"
Write-Host "Banco de dados PostgreSQL ativo: container 'terelina_db'"
Write-Host "------------------------------------------------"
Write-Host "`nInicialização concluída com sucesso."
