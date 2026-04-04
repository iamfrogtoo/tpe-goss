@echo off
chcp 65001 >nul

echo ======================================================
echo  TPE-GOSS v3.0 - Architecture Upgrade Deployment
echo  This script will upload all backend files and 
echo  restart all services on the server.
echo ======================================================
echo.

REM Change directory to the location of the python script
cd /d "%~dp0\Flight_Project"

echo [Step 1] Activating virtual environment...
call "%~dp0.venv\Scripts\activate.bat"

echo [Step 2] Executing Python deployment script...
python deploy_script.py

echo.
echo ======================================================
echo  Deployment process finished.
echo  Please check the console output above for details.
echo ======================================================

pause
