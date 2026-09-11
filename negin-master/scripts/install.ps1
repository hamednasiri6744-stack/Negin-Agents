$ErrorActionPreference = "Stop"
$root = split-path -parent $PSScriptRoot
set-location $root

if (-not (test-path ".venv")) {
  python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -e ".[dev,rpa]"

set-location "$root\bridge"
npm install
set-location $root

if (-not (test-path ".env")) {
  copy-item ".env.example" ".env"
}

new-item -itemtype directory -force -path "logs","state","state\tasks" | out-null
write-host "installation complete"
