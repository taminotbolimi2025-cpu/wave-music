# Windows Background Launcher for Wave Music MiniApp
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# 1. Kill any existing instances of run_app.py to prevent conflicts
Get-CimInstance Win32_Process -Filter "Name = 'python.exe' or Name = 'pythonw.exe'" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*run_app.py*" -and $_.ProcessId -ne $PID
} | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

# 2. Kill any orphaned cloudflared process
Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 1

# 3. Locate Python executable (.venv preferred)
$pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python.exe"
}

# 4. Start hiddenly and redirect logs
$stdoutLog = Join-Path $scriptDir "server_out.log"
$stderrLog = Join-Path $scriptDir "server_err.log"

Start-Process -FilePath $pythonExe -ArgumentList "run_app.py" -WorkingDirectory $scriptDir -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
