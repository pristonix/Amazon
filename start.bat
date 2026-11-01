@echo off
cd /d "%~dp0"
where docker >nul 2>&1
if errorlevel 1 (
 echo Docker is not installed. Install Docker Desktop first.
 pause
 exit /b 1
)
docker info >nul 2>&1
if errorlevel 1 (
 echo Start Docker Desktop and retry.
 pause
 exit /b 1
)
echo Building and starting Shopora...
docker compose up -d --build
if errorlevel 1 (
 echo Docker start failed. Check the error shown above.
 pause
 exit /b 1
)
echo.
echo Store: http://localhost:8080
start "" "http://localhost:8080"
pause
