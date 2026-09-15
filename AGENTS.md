# Negin Agents — Base44 Dev Environment

## Architecture
Multi-agent MCP (Model Context Protocol) system with 5 backend agents behind a unified gateway:
- **Negin-Master** (Python/FastAPI, port 8765) — enterprise execution and intelligence runtime
- **MCP Bridge** (Node.js/Express, port 8766) — MCP transport layer for Negin-Master
- **Code-X** (Python, port 8777) — software engineering specialist agent
- **UX-X** (Node.js, port 8780) — UI/UX audit specialist agent
- **Data-X** (Node.js, port 8781) — read-only data specialist (via specialist-host)
- **Automation-X** (Node.js, port 8782) — automation specialist (via specialist-host)
- **Gateway** (Node.js, port 8791) — unified MCP gateway aggregating all 5 agents
- **Dashboard** (Node.js, port 3000) — web UI showing agent health and tool catalog

## Setup
All services run via `docker compose -f docker-compose.base44.yml up -d`.
Local infrastructure tokens are generated and stored in compose `environment:` sections.
No external service credentials are required.

## Config files (created for Base44 dev)
- `gateway/gateway.config.json` — gateway token and backend addresses (compose service names)
- `code-x/.code-x/config.json` — Code-X MCP config (host, port, bearer token)
- `data-x/data-x.config.json` — specialist-host config for Data-X
- `automation-x/automation-x.config.json` — specialist-host config for Automation-X
- `figma-x/server/index.js` — stub module (real figma-x not in repo; UX-X requires it)
- `shared/skills/AGENT_SKILL_ROUTING.json` — minimal skill routing file

## Key details
- Python services use `python:3.12-slim`; Node.js services use `node:22`
- All services bind `0.0.0.0` for inter-container communication
- `pyodbc` and `clickhouse-connect` are NOT installed (only used inside functions, not at import time)
- The MCP bridge requires `ema_mcp_endpoint_token` (64-char hex) env var
- The gateway discovers backend tokens from env vars (`ema_mcp_endpoint_token`, `CODE_X_BEARER_TOKEN`, etc.)
- Data-X and Automation-X are loaded via `shared/specialist-host/host.js` with a JSON config file
- `NEGINAI_SKILL_ROOT` env var must point to a directory with `AGENT_SKILL_ROUTING.json`

## Verification
- Dashboard at http://localhost:3000 shows agent health and tool catalog
- Gateway health at http://localhost:8791/health/all (no auth needed)
- Individual agent health at their respective /health endpoints
