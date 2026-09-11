param([string]$InstallRoot = 'C:\code-x\ops\agent-gateway')
$ErrorActionPreference = 'Stop'

$local = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8791/health/all' -TimeoutSec 20
Write-Host "LOCAL=$($local.StatusCode)"
$status = $local.Content | ConvertFrom-Json
Write-Host "AGENTS=$($status.healthy_agents)/$($status.total_agents)"
$status.agents.PSObject.Properties | ForEach-Object {
  $v=$_.Value
  Write-Host "$($_.Name) ok=$($v.ok) http=$($v.status) token=$($v.token_discovered) cached_tools=$($v.cached_tools)"
}

$connectorFile = Join-Path $InstallRoot 'CONNECTOR.txt'
if(Test-Path $connectorFile) {
  $txt = Get-Content $connectorFile -Raw
  $m = [regex]::Match($txt, 'https://[^\s]+/mcp/[A-Za-z0-9._~-]+')
  if($m.Success) {
    $serverUrl = $m.Value
    $healthUrl = ($serverUrl -replace '/mcp/[A-Za-z0-9._~-]+$','/health/all')
    try {
      $pub = Invoke-WebRequest -UseBasicParsing $healthUrl -TimeoutSec 30
      Write-Host "PUBLIC=$($pub.StatusCode) $healthUrl"
    } catch {
      Write-Host "PUBLIC_ERR=$($_.Exception.Message)"
    }
  }
}
