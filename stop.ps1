Write-Host "Остановка Wave Music..." -ForegroundColor Cyan

Get-CimInstance Win32_Process -Filter "Name = 'python.exe' or Name = 'pythonw.exe'" -ErrorAction SilentlyContinue | Where-Object { 
    $_.CommandLine -like '*run_app.py*' 
} | ForEach-Object { 
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    Write-Host "Остановлен Python PID: $($_.ProcessId)" -ForegroundColor Yellow
}

Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Остановлен Cloudflare PID: $($_.Id)" -ForegroundColor Yellow
}

Write-Host ">> Wave Music полностью остановлен!" -ForegroundColor Green
