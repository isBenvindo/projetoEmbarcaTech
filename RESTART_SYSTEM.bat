@echo off
setlocal EnableExtensions
echo Starting Terelina System (db + mqtt + backend)...

REM Verifica se o Docker esta rodando
docker info >nul 2>&1
if errorlevel 1 (
    echo ERRO: Docker nao esta rodando. Abra o Docker Desktop e tente novamente.
    pause
    exit /b 1
)

docker compose up -d

if errorlevel 1 (
    echo.
    echo ERRO: Falhou ao iniciar os containers.
    echo Dica: rode "docker compose ps" para ver o status.
    pause
    exit /b 1
)

echo.
echo System is running in the background.
echo.
echo Status:
docker compose ps
echo.
pause
endlocal