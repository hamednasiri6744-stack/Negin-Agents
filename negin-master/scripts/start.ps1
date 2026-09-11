$ErrorActionPreference = "Stop"
$root = split-path -parent $PSScriptRoot
set-location $root

$python = "$root\.venv\Scripts\python.exe"
if (-not (test-path $python)) { throw "run scripts\install.ps1 first" }

$core = start-process -filepath $python -argumentlist "-m","enterprise_master_agent.main" -workingdirectory $root -passthru
start-sleep -seconds 2

$node = (get-command node).source
$bridge = start-process -filepath $node -argumentlist "$root\bridge\src\server.mjs" -workingdirectory "$root\bridge" -passthru

@{
  core_pid = $core.id
  bridge_pid = $bridge.id
  started = (get-date).tostring("o")
} | convertto-json | set-content "$root\state\runtime.json"

write-host "core: http://127.0.0.1:8765/health"
write-host "mcp:  http://127.0.0.1:8766/mcp"
