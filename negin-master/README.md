# Enterprise Master Agent

Provider-free enterprise execution and intelligence runtime.

## Core rules
- No LLM/model provider inside the agent.
- No paid API dependency and no Codex Work API dependency.
- ChatGPT or another AI client is an external reasoning/control surface only.
- Production SQL is read-only and last-resort.
- Heavy analytics must run outside production, primarily on ClickHouse/cache/preaggregates.
- Direct command execution on the production server is forbidden.
- Wake-on-LAN for server use is script-generation only.
- Network shares and server-connected paths are protected by default.
- Sub-agents/external agents cannot bypass policy.
- Only the Master Agent returns the final answer.
- Missing capabilities are checkpointed and can be added at runtime.
- Multi-endpoint design is enabled; initial active endpoint is the local workstation.

## Local ports
- core HTTP: `127.0.0.1:8765`
- MCP bridge: `127.0.0.1:8766/mcp`

## Windows first run
```powershell
cd c:\enterprise-master-agent
powershell -executionpolicy bypass -file .\scripts\install.ps1
powershell -executionpolicy bypass -file .\scripts\start.ps1
powershell -executionpolicy bypass -file .\scripts\health.ps1
```

See `docs/capability-map.md`.
