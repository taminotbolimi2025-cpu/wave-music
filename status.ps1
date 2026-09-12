$py = Get-CimInstance Win32_Process -Filter "Name = 'python.exe' or Name = 'pythonw.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*run_app.py*' }
$cf = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "             СТАТУС WAVE MUSIC MINI-APP                 " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

if ($py) {
    Write-Host ">> Сервер Python:      [АКТИВЕН] PID: $($py.ProcessId)" -ForegroundColor Green
} else {
    Write-Host ">> Сервер Python:      [НЕ ЗАПУЩЕН]" -ForegroundColor Red
}

if ($cf) {
    Write-Host ">> Туннель Cloudflare: [АКТИВЕН] PID: $($cf.Id)" -ForegroundColor Green
} else {
    Write-Host ">> Туннель Cloudflare: [НЕ ЗАПУЩЕН]" -ForegroundColor Red
}

$urlPath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "tunnel_url.txt"
if (Test-Path $urlPath) {
    $url = (Get-Content $urlPath -Raw).Trim()
    Write-Host "`n>> Активная ссылка в Telegram: $url" -ForegroundColor Yellow
}

$startupPath = [System.IO.Path]::Combine($env:APPDATA, 'Microsoft\Windows\Start Menu\Programs\Startup\WaveMusic.lnk')
if (Test-Path $startupPath) {
    Write-Host ">> Автозапуск при старте Windows: [ВКЛЮЧЕН]" -ForegroundColor Green
} else {
    Write-Host ">> Автозапуск при старте Windows: [ОТКЛЮЧЕН]" -ForegroundColor DarkGray
}

Write-Host "========================================================" -ForegroundColor Cyan
