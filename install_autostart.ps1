$ws = New-Object -ComObject WScript.Shell
$startupPath = [System.IO.Path]::Combine($env:APPDATA, 'Microsoft\Windows\Start Menu\Programs\Startup\WaveMusic.lnk')
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$vbsPath = [System.IO.Path]::Combine($scriptDir, 'start_silent.vbs')

$shortcut = $ws.CreateShortcut($startupPath)
$shortcut.TargetPath = "wscript.exe"
$shortcut.Arguments = "`"$vbsPath`""
$shortcut.WorkingDirectory = $scriptDir
$shortcut.IconLocation = "shell32.dll,138"
$shortcut.Save()

if (Test-Path $startupPath) {
    Write-Host "SUCCESS: Auto-start shortcut created at $startupPath" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to create shortcut" -ForegroundColor Red
}
