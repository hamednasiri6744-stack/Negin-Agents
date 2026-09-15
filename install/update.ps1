param(
    [string]$MasterRoot = 'C:\enterprise-master-agent',
    [string]$CodeRoot = 'C:\code-x',
    [switch]$NoPull,
    [switch]$SkipDependencies
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$BackupRoot = Join-Path $CodeRoot "agent-backups\$stamp"
function Write-Step([string]$Text) { Write-Host "[Negin-Agents] $Text" }
function Backup-Path([string]$Source, [string]$RelativeName) {
    if (-not (Test-Path $Source)) { return }
    $dest = Join-Path $BackupRoot $RelativeName
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
    Copy-Item -LiteralPath $Source -Destination $dest -Recurse -Force
}

if (-not $NoPull) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'git is required for update; use -NoPull if the repository was updated externally' }
    Write-Step 'Pull latest canonical source'
    Push-Location $RepoRoot
    try {
        git pull --ff-only
        if ($LASTEXITCODE -ne 0) { throw 'git pull --ff-only failed' }
    } finally { Pop-Location }
}

Write-Step "Create source backup: $BackupRoot"
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
Backup-Path (Join-Path $MasterRoot 'src') 'negin-master\src'
Backup-Path (Join-Path $MasterRoot '.agents') 'negin-master\.agents'
Backup-Path (Join-Path $CodeRoot 'code_x_agent') 'code-x\code_x_agent'
Backup-Path (Join-Path $CodeRoot 'skills') 'code-x\skills'
Backup-Path (Join-Path $CodeRoot 'agents\ux-x\server') 'ux-x\server'
Backup-Path (Join-Path $CodeRoot 'agents\ux-x\skills') 'ux-x\skills'
Backup-Path (Join-Path $CodeRoot 'agents\ux-x\profiles') 'ux-x\profiles'
Backup-Path (Join-Path $CodeRoot 'agents\shared\neginai-skill-router.js') 'shared\neginai-skill-router.js'
Backup-Path (Join-Path $CodeRoot 'agents\specialist-host\host.js') 'specialist-host\host.js'
Backup-Path (Join-Path $CodeRoot 'agents\specialist-host\data-x.js') 'specialist-host\data-x.js'
Backup-Path (Join-Path $CodeRoot 'agents\specialist-host\automation-x.js') 'specialist-host\automation-x.js'
Backup-Path (Join-Path $CodeRoot 'ops\agent-gateway\agent-gateway.js') 'gateway\agent-gateway.js'
Backup-Path (Join-Path $CodeRoot 'ops\agent-gateway\run-gateway.ps1') 'gateway\run-gateway.ps1'

try {
    Write-Step 'Apply canonical source while preserving local secrets/runtime configs'
    $args = @{ MasterRoot=$MasterRoot; CodeRoot=$CodeRoot; SkipStart=$true }
    if ($SkipDependencies) { $args.SkipDependencies=$true }
    & (Join-Path $PSScriptRoot 'install.ps1') @args
    Write-Step 'Reconnect and verify 5/5'
    & (Join-Path $PSScriptRoot 'reconnect.ps1') -MasterRoot $MasterRoot -CodeRoot $CodeRoot
} catch {
    Write-Host "UPDATE FAILED: $($_.Exception.Message)"
    Write-Host "Backup retained at: $BackupRoot"
    throw
}

Write-Step 'UPDATE COMPLETE'
Write-Host "Backup=$BackupRoot"
