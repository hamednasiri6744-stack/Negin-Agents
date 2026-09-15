param(
    [string]$MasterRoot = 'C:\enterprise-master-agent',
    [string]$CodeRoot = 'C:\code-x',
    [switch]$SkipDependencies,
    [switch]$SkipStart,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot

function Write-Step([string]$Text) { Write-Host "[Negin-Agents] $Text" }
function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) { throw "Required command not found: $Name" }
}
function New-RandomToken {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+','-').Replace('/','_')
}
function Ensure-Directory([string]$Path) {
    if ($DryRun) { Write-Step "DRY RUN mkdir $Path"; return }
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}
function Copy-SourceTree([string]$Source, [string]$Destination) {
    if (-not (Test-Path $Source)) { throw "Source missing: $Source" }
    if ($DryRun) { Write-Step "DRY RUN copy $Source -> $Destination"; return }
    Ensure-Directory $Destination
    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $Destination -Recurse -Force
    }
}
function Write-JsonIfMissing([string]$Path, [hashtable]$Value) {
    if (Test-Path $Path) { Write-Step "Preserve local runtime config: $Path"; return }
    if ($DryRun) { Write-Step "DRY RUN create local runtime config $Path"; return }
    $Value | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $Path -Encoding UTF8
}
function Ensure-MasterEnv {
    $envPath = Join-Path $MasterRoot '.env'
    if (Test-Path $envPath) { Write-Step 'Preserve existing Negin-Master .env'; return }
    if ($DryRun) { Write-Step "DRY RUN create $envPath from .env.example plus local MCP token"; return }
    Copy-Item (Join-Path $MasterRoot '.env.example') $envPath -Force
    Add-Content -LiteralPath $envPath -Value ("`nNEGIN_MCP_TOKEN=" + (New-RandomToken)) -Encoding UTF8
}

Write-Step "Repository: $RepoRoot"
Require-Command powershell
Require-Command python
Require-Command node
if (-not $SkipDependencies) { Require-Command npm }

Write-Step 'Install Negin-Master source'
Copy-SourceTree (Join-Path $RepoRoot 'negin-master') $MasterRoot
Ensure-MasterEnv

Write-Step 'Install Code-X source'
Ensure-Directory $CodeRoot
Copy-SourceTree (Join-Path $RepoRoot 'code-x\code_x_agent') (Join-Path $CodeRoot 'code_x_agent')
Copy-SourceTree (Join-Path $RepoRoot 'code-x\skills') (Join-Path $CodeRoot 'skills')
foreach ($file in @('code-x.py','code-x.ps1','code-x.cmd','README_CODE_X.md','CODE_X_ARCHITECTURE.md','CODE_X_MANIFEST.txt','CODE_X_NOTICE.md','CODE_X_VERIFICATION.md')) {
    $src = Join-Path $RepoRoot "code-x\$file"
    if (Test-Path $src) {
        if ($DryRun) { Write-Step "DRY RUN copy $src -> $CodeRoot" } else { Copy-Item $src $CodeRoot -Force }
    }
}

$UxRoot = Join-Path $CodeRoot 'agents\ux-x'
Write-Step 'Install UX-X source'
Copy-SourceTree (Join-Path $RepoRoot 'ux-x\server') (Join-Path $UxRoot 'server')
Copy-SourceTree (Join-Path $RepoRoot 'ux-x\skills') (Join-Path $UxRoot 'skills')
Copy-SourceTree (Join-Path $RepoRoot 'ux-x\profiles') (Join-Path $UxRoot 'profiles')
Copy-SourceTree (Join-Path $RepoRoot 'ux-x\tests') (Join-Path $UxRoot 'tests')
if ((Test-Path (Join-Path $RepoRoot 'ux-x\README.md')) -and -not $DryRun) {
    Copy-Item (Join-Path $RepoRoot 'ux-x\README.md') $UxRoot -Force
}
Write-JsonIfMissing (Join-Path $UxRoot '.runtime.json') @{
    host='127.0.0.1'; port=8780; bearer_token=(New-RandomToken); runtime_mode='hot-reload-reconnect-safe'
}

$AgentSharedRoot = Join-Path $CodeRoot 'agents\shared'
Ensure-Directory $AgentSharedRoot
$skillRouter = Join-Path $RepoRoot 'shared\neginai-skill-router.js'
if (-not (Test-Path $skillRouter)) { throw "Missing shared NeginAI skill router: $skillRouter" }
if ($DryRun) { Write-Step "DRY RUN copy $skillRouter -> $AgentSharedRoot" } else { Copy-Item $skillRouter (Join-Path $AgentSharedRoot 'neginai-skill-router.js') -Force }

$SpecialistRoot = Join-Path $CodeRoot 'agents\specialist-host'
Write-Step 'Install Data-X and Automation-X source'
Ensure-Directory $SpecialistRoot
$sharedHost = Join-Path $RepoRoot 'shared\specialist-host\host.js'
if (-not (Test-Path $sharedHost)) { throw "Missing shared specialist host: $sharedHost" }
if ($DryRun) {
    Write-Step "DRY RUN copy specialist host and modules -> $SpecialistRoot"
} else {
    Copy-Item $sharedHost (Join-Path $SpecialistRoot 'host.js') -Force
    Copy-Item (Join-Path $RepoRoot 'data-x\data-x.js') (Join-Path $SpecialistRoot 'data-x.js') -Force
    Copy-Item (Join-Path $RepoRoot 'automation-x\automation-x.js') (Join-Path $SpecialistRoot 'automation-x.js') -Force
}

$allowedRoots = @($CodeRoot, 'D:\Projects', "$env:USERPROFILE\Documents")
Write-JsonIfMissing (Join-Path $SpecialistRoot 'data-x.json') @{
    name='Data-X'; id='data-x'; prefix='data_x'; kind='data'; version='0.3.0'; mode='analytics-live-readonly';
    host='127.0.0.1'; port=8781; token_env='DATA_X_BEARER_TOKEN'; bearer_token=(New-RandomToken);
    allowed_roots=$allowedRoots;
    instructions='Data-X analytics specialist. Production data access is strict read-only; canonical KPI semantics remain governed by Negin-Master.';
    module='.\data-x.js'; runtime_mode='hot-reload-reconnect-safe'
}
Write-JsonIfMissing (Join-Path $SpecialistRoot 'automation-x.json') @{
    name='Automation-X'; id='automation-x'; prefix='automation_x'; kind='automation'; version='0.3.0'; mode='workflow-operational-guarded';
    host='127.0.0.1'; port=8782; token_env='AUTOMATION_X_BEARER_TOKEN'; bearer_token=(New-RandomToken);
    allowed_roots=@($CodeRoot,'D:\Projects','D:\negin-airflow',$MasterRoot,"$env:USERPROFILE\Documents");
    instructions='Automation-X workflow specialist. Mutating actions require explicit approval gates; production SQL and credential exposure are forbidden.';
    module='.\automation-x.js'; runtime_mode='hot-reload-reconnect-safe'
}

$GatewayRoot = Join-Path $CodeRoot 'ops\agent-gateway'
Write-Step 'Install Unified Gateway source'
Copy-SourceTree (Join-Path $RepoRoot 'gateway') $GatewayRoot
Write-JsonIfMissing (Join-Path $GatewayRoot 'gateway.config.json') @{
    host='127.0.0.1'; port=8792; gateway_token=(New-RandomToken); refresh_seconds=300
}

if (-not $SkipDependencies) {
    if ($DryRun) {
        Write-Step 'DRY RUN dependency bootstrap: Negin-Master Python/Node and Code-X Python capability pack'
    } else {
        Write-Step 'Install Negin-Master dependencies'
        & (Join-Path $MasterRoot 'scripts\install.ps1')
        Write-Step 'Create Code-X virtual environment'
        $codeVenv = Join-Path $CodeRoot '.venv'
        if (-not (Test-Path (Join-Path $codeVenv 'Scripts\python.exe'))) { python -m venv $codeVenv }
        $codePython = Join-Path $codeVenv 'Scripts\python.exe'
        & $codePython -m pip install --upgrade pip packaging
        & $codePython (Join-Path $CodeRoot 'code-x.py') bootstrap
        if ($LASTEXITCODE -ne 0) { throw 'Code-X capability bootstrap failed' }
        & $codePython (Join-Path $CodeRoot 'code-x.py') endpoint | Out-Null
    }
}

if (-not $SkipStart) {
    if ($DryRun) { Write-Step 'DRY RUN reconnect all agents and gateway' }
    else { & (Join-Path $PSScriptRoot 'reconnect.ps1') -MasterRoot $MasterRoot -CodeRoot $CodeRoot }
}

Write-Step 'INSTALL COMPLETE'
Write-Host "MasterRoot=$MasterRoot"
Write-Host "CodeRoot=$CodeRoot"
Write-Host 'Secrets/runtime state remain local and are not sourced from GitHub.'
