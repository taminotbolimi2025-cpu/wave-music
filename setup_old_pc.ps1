# Setup Wave Music 24/7 on an Old PC / Laptop
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "     НАСТРОЙКА WAVE MUSIC 24/7 НА СТАРОМ КОМПЬЮТЕРЕ     " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Check Python
$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyCmd) {
    Write-Host "[!] Python не найден в системе!" -ForegroundColor Red
    Write-Host "Пожалуйста, скачайте Python с официального сайта: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "ВАЖНО: При установке ОБЯЗАТЕЛЬНО поставьте галочку 'Add python.exe to PATH'!" -ForegroundColor Yellow
    Read-Host "Нажмите Enter после установки Python..."
}

# 2. Download cloudflared.exe if missing
$cfExe = Join-Path $scriptDir "cloudflared.exe"
if (-not (Test-Path $cfExe)) {
    Write-Host "`n>> Скачивание Cloudflare Tunnel (cloudflared.exe)..." -ForegroundColor Cyan
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile $cfExe -UseBasicParsing
        Write-Host ">> Cloudflare Tunnel успешно скачан!" -ForegroundColor Green
    } catch {
        Write-Host "[!] Не удалось автоматически скачать cloudflared: $_" -ForegroundColor Yellow
    }
}

# 3. Virtualenv & Dependencies
$venvDir = Join-Path $scriptDir ".venv"
$venvPy = Join-Path $venvDir "Scripts\python.exe"

if (-not (Test-Path $venvPy)) {
    Write-Host "`n>> Создание окружения Python (.venv)..." -ForegroundColor Cyan
    python -m venv $venvDir
}

Write-Host "`n>> Установка зависимостей (yt-dlp, telebot, aiohttp)..." -ForegroundColor Cyan
& $venvPy -m pip install --upgrade pip --quiet
& $venvPy -m pip install -r (Join-Path $scriptDir "requirements.txt") --quiet

# 4. Install Autostart into Windows Startup
Write-Host "`n>> Настройка автозапуска при включении Windows..." -ForegroundColor Cyan
& (Join-Path $scriptDir "install_autostart.ps1")

# 5. Start the server silently in background
Write-Host "`n>> Запуск сервера в фоновом режиме..." -ForegroundColor Cyan
& (Join-Path $scriptDir "start_background.ps1")

Start-Sleep -Seconds 4

# 6. Check Status
& (Join-Path $scriptDir "status.ps1")

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "   ПОЗДРАВЛЯЕМ! СЕРВЕР УСПЕШНО НАСТРОЕН И ЗАПУЩЕН!      " -ForegroundColor Green
Write-Host "   Теперь этот компьютер работает как ваш сервер 24/7.  " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
