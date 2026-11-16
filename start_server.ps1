Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Starting OmniRoute Fullstack Application" -ForegroundColor Cyan
Write-Host " Backend: FastAPI (Python)" -ForegroundColor White
Write-Host " Frontend: React SPA (http://127.0.0.1:8001/)" -ForegroundColor White
Write-Host " Database: MongoDB / High-Performance Document Store" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Cyan

Set-Location "$PSScriptRoot"
Start-Process "http://127.0.0.1:8001/"
python run_app.py
