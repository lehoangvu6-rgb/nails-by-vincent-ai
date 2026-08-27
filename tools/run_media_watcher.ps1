$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$logPath = Join-Path $projectRoot "logs\media_watcher.log"

Set-Location -LiteralPath $projectRoot

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Project Python environment was not found."
}

& $pythonPath -m core.media_watcher *>> $logPath
