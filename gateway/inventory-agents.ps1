param(
  [string]$OutputRoot = 'C:\code-x\ops\agent-gateway\inventory'
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

$canonical = @(
  'C:\code-x',
  'C:\code-x\code_x_agent',
  'C:\code-x\agents\ux-x',
  'C:\code-x\agents\figma-x',
  'C:\code-x\agents\specialist-host',
  'C:\enterprise-master-agent',
  'C:\code-x\ops\agent-reliability',
  'C:\code-x\ops\agent-gateway'
)

$roots = @('C:\','D:\')
$patterns = '(?i)(agent|code-x|ux-x|ui-x|data-x|automation-x|figma-x|master-agent|mcp)'
$dirs = New-Object System.Collections.Generic.List[object]

$procText = (Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | ForEach-Object { "$($_.CommandLine)" }) -join "`n"
$taskText = (Get-ScheduledTask -ErrorAction SilentlyContinue | ForEach-Object {
  ($_.Actions | ForEach-Object { "$($_.Execute) $($_.Arguments)" }) -join ' '
}) -join "`n"

foreach($root in $roots) {
  if(-not (Test-Path $root)) { continue }
  Get-ChildItem -Path $root -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match $patterns } |
    ForEach-Object {
      $p=$_.FullName
      $isCanonical = $canonical -contains $p
      $procRef = $procText -like "*$p*"
      $taskRef = $taskText -like "*$p*"
      $classification = if($isCanonical -or $procRef -or $taskRef) {'KEEP'} else {'REVIEW'}
      $dirs.Add([pscustomobject]@{
        path=$p
        name=$_.Name
        last_write=$_.LastWriteTime
        process_reference=$procRef
        scheduled_task_reference=$taskRef
        canonical=$isCanonical
        classification=$classification
      })
    }
}

# Important nested areas where legacy agent copies have existed.
$nestedRoots = @('C:\code-x\agents','C:\code-x\.code-x\backups','C:\code-x')
foreach($nr in $nestedRoots) {
  if(-not (Test-Path $nr)) { continue }
  Get-ChildItem -Path $nr -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match $patterns -or $_.Name -match '(?i)(staging|backup)' } |
    ForEach-Object {
      if($dirs.path -contains $_.FullName) { return }
      $p=$_.FullName
      $isCanonical = $canonical -contains $p
      $procRef = $procText -like "*$p*"
      $taskRef = $taskText -like "*$p*"
      $classification = if($isCanonical -or $procRef -or $taskRef) {'KEEP'} else {'REVIEW'}
      $dirs.Add([pscustomobject]@{
        path=$p
        name=$_.Name
        last_write=$_.LastWriteTime
        process_reference=$procRef
        scheduled_task_reference=$taskRef
        canonical=$isCanonical
        classification=$classification
      })
    }
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$json = Join-Path $OutputRoot "agent-folder-inventory-$stamp.json"
$csv = Join-Path $OutputRoot "agent-folder-inventory-$stamp.csv"
$dirs | Sort-Object classification,path | ConvertTo-Json -Depth 5 | Set-Content $json -Encoding UTF8
$dirs | Sort-Object classification,path | Export-Csv $csv -NoTypeInformation -Encoding UTF8

Write-Host "JSON=$json"
Write-Host "CSV=$csv"
Write-Host ''
$dirs | Sort-Object classification,path | Format-Table classification,canonical,process_reference,scheduled_task_reference,path -AutoSize
Write-Host ''
Write-Host 'No folder was deleted. REVIEW only means candidate for manual reconciliation.'
