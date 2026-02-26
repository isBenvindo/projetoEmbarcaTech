@echo off
setlocal EnableExtensions
echo.
echo ===============================================================
echo  TERELINA SYSTEM - INITIAL SETUP & START
echo ===============================================================
echo.
echo This will build the system components and start them.
echo The first time this runs, it may take several minutes to download
echo images and initialize the database. Please be patient.
echo.

REM Verifica se o Docker esta rodando
docker info >nul 2>&1
if errorlevel 1 (
    echo ERRO: Docker nao esta rodando. Abra o Docker Desktop e tente novamente.
    pause
    exit /b 1
)

REM Build + start
docker compose up -d --build

if errorlevel 1 (
    echo.
    echo ERRO: Falhou ao iniciar/buildar os containers.
    echo Dica: rode "docker compose logs -f" para ver o erro.
    pause
    exit /b 1
)

echo.
echo System has been started in the background.
echo.
echo Status:
docker compose ps
echo.
echo You can close this window now.
echo.
pause
endlocal