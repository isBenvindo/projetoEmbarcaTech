@echo off
setlocal EnableExtensions
echo Stopping Terelina System...

REM Verifica se o Docker esta rodando
docker info >nul 2>&1
if errorlevel 1 (
    echo ERRO: Docker nao esta rodando. Nada para parar.
    pause
    exit /b 1
)

docker compose down

if errorlevel 1 (
    echo.
    echo ERRO: Falhou ao parar o sistema.
    pause
    exit /b 1
)

echo.
echo System has been stopped.
echo.
pause
endlocal