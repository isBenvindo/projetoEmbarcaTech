@echo off
setlocal EnableExtensions
echo.
echo =================================================================
echo    !! AVISO !! ESTA ACAO IRA APAGAR PERMANENTEMENTE
echo             TODOS OS DADOS DE CONTAGEM DE PIZZAS.
echo =================================================================
echo.
echo    Os dados de teste serao removidos e o sistema sera
echo    zerado para o inicio da producao real.
echo.

set /p "confirm=Voce tem CERTEZA que deseja continuar? (s/n): "
if /i not "%confirm%"=="s" (
    echo Acao cancelada.
    goto :eof
)

REM Verifica se o Docker esta rodando
docker info >nul 2>&1
if errorlevel 1 (
    echo ERRO: Docker nao esta rodando. Abra o Docker Desktop e tente novamente.
    pause
    exit /b 1
)

echo.
echo Limpando o banco de dados...

REM Executa o script SQL dentro do container do banco.
REM -Raw evita problemas de encoding/linhas no PowerShell.
powershell -NoProfile -Command "Get-Content -Raw 'back-end/scripts/clear_counts.sql' | docker compose exec -T db psql -U postgres -d terelina_db"

if errorlevel 1 (
    echo.
    echo ERRO: Falhou ao executar o script no banco. Verifique se os containers estao ativos (docker compose ps).
    pause
    exit /b 1
)

echo.
echo Banco de dados limpo com sucesso! Todos os registros de contagem foram removidos.
echo.
pause
:eof
endlocal