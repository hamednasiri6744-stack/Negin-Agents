$ErrorActionPreference = "Stop"
invoke-restmethod "http://127.0.0.1:8765/health" | convertto-json -depth 5
invoke-restmethod "http://127.0.0.1:8766/health" | convertto-json -depth 5
