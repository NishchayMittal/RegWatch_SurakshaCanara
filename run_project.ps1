Write-Host "=============================================" -ForegroundColor Green
Write-Host "   Starting RegWatch | SurakshaCanara Stack   " -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Ensure working directory is the script folder itself
Set-Location $PSScriptRoot

# Start FastAPI backend
Write-Host "--> Launching FastAPI Backend on Port 8000..." -ForegroundColor Cyan
$BackendProcess = Start-Process -NoNewWindow -FilePath "uvicorn" -ArgumentList "main:app --port 8000 --reload" -PassThru

# Give backend a moment to boot
Start-Sleep -Seconds 3

# Start Next.js frontend
Write-Host "--> Launching Next.js Frontend on Port 3000..." -ForegroundColor Cyan
Write-Host "--> Please open http://localhost:3000 in your browser." -ForegroundColor Green
cd frontend
npm run dev

# Kill backend process when frontend exits
Stop-Process -Id $BackendProcess.Id
