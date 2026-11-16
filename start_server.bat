@echo off
echo ========================================================
echo  Starting OmniRoute Fullstack Application
echo  Backend: FastAPI (Python)
echo  Frontend: React SPA (Served at http://127.0.0.1:8001/)
echo  Database: MongoDB / High-Performance Document Store
echo ========================================================
cd /d "%~dp0"
start http://127.0.0.1:8001/
python run_app.py
pause
