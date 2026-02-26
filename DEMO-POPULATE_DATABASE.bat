@echo off
setlocal EnableExtensions
echo.
echo =================================================================
echo    !! AVISO !! ESTA ACAO IRA APAGAR TODOS OS DADOS ATUAIS
echo          E PREENCHER O BANCO COM DADOS DE DEMONSTRACAO.
echo =================================================================
echo.
echo    Use este script apenas para demonstrar o potencial dos
echo    dashboards com um ano de dados simulados.
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
echo Populando o banco de dados com dados de demonstracao...
echo (Este processo pode levar alguns segundos)

REM Executa o script SQL dentro do container do banco.
REM -Raw evita problemas de encoding/linhas no PowerShell.
powershell -NoProfile -Command "Get-Content -Raw 'back-end/scripts/populate_db.sql' | docker compose exec -T db psql -U postgres -d terelina_db"

if errorlevel 1 (
    echo.
    echo ERRO: Falhou ao executar o script no banco. Verifique se os containers estao ativos (docker compose ps).
    pause
    exit /b 1
)

echo.
echo Banco de dados populado com sucesso para demonstracao!
echo.
echo (Nota: neste compose atual nao ha Grafana. Se voce usar Grafana separado, atualize os dashboards.)
echo.
pause
:eof
endlocal