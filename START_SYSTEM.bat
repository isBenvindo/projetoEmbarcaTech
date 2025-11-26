@echo off
echo.
echo ===============================================================
echo  TERELINA SYSTEM - INITIAL SETUP & START
echo ===============================================================
echo.
echo This will build the system components and start them.
echo The first time this runs, it may take several minutes to download
echo and set up the database. Please be patient.
echo.

REM The '--build' flag ensures the backend image is built if it doesn't exist.
docker-compose up -d --build

echo.
echo System has been started in the background.
echo You can close this window now.
echo.
pause