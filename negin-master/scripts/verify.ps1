$ErrorActionPreference = "Stop"
$root = split-path -parent $PSScriptRoot
set-location $root

& ".\.venv\Scripts\python.exe" -m pytest -q
node --check ".\bridge\src\server.mjs"
invoke-restmethod "http://127.0.0.1:8765/health" | convertto-json -depth 5
invoke-restmethod "http://127.0.0.1:8766/health" | convertto-json -depth 5
