$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$node = (Get-Command node.exe -ErrorAction Stop).Source
Set-Location $root

$config = Get-Content (Join-Path $root 'gateway.config.json') -Raw | ConvertFrom-Json
$port = [int]$config.port
$listener = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listener) { exit 0 }

Start-Process -FilePath $node `
    -ArgumentList @("$root\agent-gateway.js") `
    -WorkingDirectory $root `
    -WindowStyle Hidden
