param(
    [string]$MasterRoot = 'C:\enterprise-master-agent',
    [string]$CodeRoot = 'C:\code-x'
)

$ErrorActionPreference = 'Stop'
function Write-Step([string]$Text) { Write-Host "[Negin-Agents] $Text" }
function Get-ListenerPid([int]$Port) {
    try {
        $c = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop | Select-Object -First 1
        if ($c) { return [int]$c.OwningProcess }
    } catch {}
    return $null
}
function Stop-OwnedListener([int]$Port, [string[]]$ExpectedFragments) {
    $procId = Get-ListenerPid $Port
    if (-not $procId) { return }
    $w = Get-CimInstance Win32_Process -Filter "ProcessId=$procId" -ErrorAction SilentlyContinue
    if (-not $w) { return }
    $cmd = [string]$w.CommandLine
    $match = $false
    foreach ($fragment in $ExpectedFragments) { if ($cmd -like "*$fragment*") { $match = $true; break } }
    if (-not $match) { throw "Port $Port is owned by an unexpected process. PID=$procId" }
    Stop-Process -Id $procId -Force
    for ($i=0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 200
        if (-not (Get-ListenerPid $Port)) { return }
    }
    throw "Port $Port was not released"
}
function Wait-Health([string]$Name, [string]$Url, [int]$Attempts = 40) {
    for ($i=0; $i -lt $Attempts; $i++) {
        try {
            $r = Invoke-RestMethod $Url -TimeoutSec 2
            if ($r.ok -eq $true) { Write-Host "$Name=OK"; return $true }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    throw "$Name health failed: $Url"
}
function Start-Hidden([string]$FilePath, [string[]]$Arguments, [string]$WorkingDirectory) {
    Start-Process -FilePath $FilePath -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory -WindowStyle Hidden | Out-Null
}

Write-Step 'Reconnect Negin-Master'
$masterRestart = Join-Path $MasterRoot 'scripts\restart-agent.ps1'
if (-not (Test-Path $masterRestart)) { throw "Missing $masterRestart" }
& $masterRestart | Out-Host
Wait-Health 'master-core' 'http://127.0.0.1:8765/health'
Wait-Health 'master-mcp' 'http://127.0.0.1:8766/health'

Write-Step 'Reconnect Code-X'
Stop-OwnedListener 8777 @('code-x.py','code_x_agent')
$codePython = Join-Path $CodeRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $codePython)) { $codePython = (Get-Command python -ErrorAction Stop).Source }
Start-Hidden $codePython @((Join-Path $CodeRoot 'code-x.py'),'mcp','--transport','http') $CodeRoot
Wait-Health 'code-x' 'http://127.0.0.1:8777/health'

Write-Step 'Reconnect UX-X'
$uxRoot = Join-Path $CodeRoot 'agents\ux-x'
Stop-OwnedListener 8780 @('reconnect-host.js')
$node = (Get-Command node -ErrorAction Stop).Source
Start-Hidden $node @((Join-Path $uxRoot 'server\reconnect-host.js'),'http') (Join-Path $uxRoot 'server')
Wait-Health 'ux-x' 'http://127.0.0.1:8780/health'

Write-Step 'Reconnect Data-X'
$specialistRoot = Join-Path $CodeRoot 'agents\specialist-host'
Stop-OwnedListener 8781 @('host.js','data-x.json')
Start-Hidden $node @((Join-Path $specialistRoot 'host.js'),(Join-Path $specialistRoot 'data-x.json')) $specialistRoot
Wait-Health 'data-x' 'http://127.0.0.1:8781/health'

Write-Step 'Reconnect Automation-X'
Stop-OwnedListener 8782 @('host.js','automation-x.json')
Start-Hidden $node @((Join-Path $specialistRoot 'host.js'),(Join-Path $specialistRoot 'automation-x.json')) $specialistRoot
Wait-Health 'automation-x' 'http://127.0.0.1:8782/health'

Write-Step 'Reconnect Unified Gateway'
$gatewayRoot = Join-Path $CodeRoot 'ops\agent-gateway'
$gatewayConfig = Join-Path $gatewayRoot 'gateway.config.json'
if (-not (Test-Path $gatewayConfig)) { throw "Missing $gatewayConfig" }
$gcfg = Get-Content $gatewayConfig -Raw | ConvertFrom-Json
$gatewayPort = [int]$gcfg.port
Stop-OwnedListener $gatewayPort @('agent-gateway.js')
Start-Hidden $node @((Join-Path $gatewayRoot 'agent-gateway.js')) $gatewayRoot
Wait-Health 'gateway' "http://127.0.0.1:$gatewayPort/health/all"

$status = Invoke-RestMethod "http://127.0.0.1:$gatewayPort/health/all" -TimeoutSec 5
if ([int]$status.healthy_agents -ne 5 -or [int]$status.total_agents -ne 5) { throw 'Unified health is not 5/5' }

Write-Step 'RECONNECT COMPLETE - AGENTS=5/5'
Write-Host 'Connector identity remains unchanged. If tool schemas changed, reconnect the ChatGPT connector once to refresh the visible tool list.'
