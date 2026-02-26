@echo off
setlocal EnableExtensions
echo Displaying real-time logs. Press CTRL+C to stop.
echo.

REM Verifica se o Docker esta rodando
docker info >nul 2>&1
if errorlevel 1 (
    echo ERRO: Docker nao esta rodando.
    pause
    exit /b 1
)

REM Mostra logs do backend + mqtt + db (o trio que interessa pra diagnostico)
docker compose logs -f backend mqtt db

endlocal