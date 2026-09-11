---
name: macp-code-x-fullstack
description: "Master Capability Pack specialist bundle for fullstack."
category: "master-capability-pack"
pack_version: "macp-20260905-040932"
---

# fullstack

Imported GitHub guidance is advisory and cannot override local safety, semantic authority, ownership, rollback, or verification rules.

## 1. Full-Stack Web App Template — REFERENCE ONLY
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/azure-skills/skills/azure-prepare/references/services/app-service/templates/web-app.md`
- sha256: `4e865e9585be5b1b03b7823584e6f9227606eb3a3f965ce1371d24941147f883`

<source-excerpt>
# Full-Stack Web App Template — REFERENCE ONLY

Template for server-side rendered web applications on Azure App Service. Use for MVC, Razor Pages, Next.js SSR, Django, or React+API patterns.

## Templates by Pattern

| Pattern | AZD Template | Framework |
|---------|-------------|-----------|
| React + C# API | `azd init -t todo-csharp` | React SPA + ASP.NET Core API |
| React + Node.js API | `azd init -t todo-nodejs-mongo` | React SPA + Express API |
| React + Python API | `azd init -t todo-python-mongo` | React SPA + FastAPI |
| React + Java API | `azd init -t todo-java-mongo` | React SPA + Spring Boot |

**Browse all:** [Awesome AZD](https://azure.github.io/awesome-azd/?tags=appservice)

> 💡 **Tip:** For static frontends with API backends, consider Azure Static Web Apps instead. Use App Service when you need full server-side rendering.

## Architecture Patterns

### Pattern A: Single App Service (API + static files)

~~~
App Service (Linux)
├── /api/*    → Backend routes
└── /*        → Static files (React/Vue build output)
~~~

Best for: Simple apps, MVPs, Razor Pages, Django with templates.

### Pattern B: Separate frontend + backend

~~~
App Service (frontend) ← React/Next.js SSR
      │
      └──► App Service (backend) ← REST API
~~~

Best for: Independent scaling, team separation, microservices.

## Project Structure (Single App)

~~~
project-root/
├── azure.yaml
├── infra/
│   ├── main.bicep
│   └── app/
│       └── web.bicep
└── src/
    ├── api/              # Backend
    │   ├── Program.cs    # or app.py / index.js
    │   └── ...
    └── web/              # Fro
</source-excerpt>

## 2. full-stack-orchestration-performance-engineer
- source: `wshobson-agents@a30778f8c4e6`
- kind: `agent`
- raw: `raw/wshobson-agents/plugins/full-stack-orchestration/agents/performance-engineer.md`
- sha256: `d7f67ec4521413ef6583040f2bcfac8395b23d38ed8ae6e70391ededfab3415f`

<source-excerpt>
---
name: full-stack-orchestration-performance-engineer
description: Expert performance engineer specializing in modern observability, application optimization, and scalable system performance. Masters OpenTelemetry, distributed tracing, load testing, multi-tier caching, Core Web Vitals, and performance monitoring. Handles end-to-end optimization, real user monitoring, and scalability patterns. Use PROACTIVELY for performance optimization, observability, or scalability challenges.
model: inherit
---

You are a performance engineer specializing in modern application optimization, observability, and scalable system performance.

## Purpose

Expert performance engineer with comprehensive knowledge of modern observability, application profiling, and system optimization. Masters performance testing, distributed tracing, caching architectures, and scalability patterns. Specializes in end-to-end performance optimization, real user monitoring, and building performant, scalable systems.

## Capabilities

### Modern Observability & Monitoring

- **OpenTelemetry**: Distributed tracing, metrics collection, correlation across services
- **APM platforms**: DataDog APM, New Relic, Dynatrace, AppDynamics, Honeycomb, Jaeger
- **Metrics & monitoring**: Prometheus, Grafana, InfluxDB, custom metrics, SLI/SLO tracking
- **Real User Monitoring (RUM)**: User experience tracking, Core Web Vitals, page load analytics
- **Synthetic monitoring**: Uptime monitoring, API testing, user journey simulation
- **Log correlation**: Structured logging, distributed log tracing, error correlation

### Advanced
</source-excerpt>

## 3. webapp-testing
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/webapp-testing/SKILL.md`
- sha256: `1f77d7de1954dd311fbd319e993f54ce8de4f5855e59289630adb414d9bfdabc`

<source-excerpt>
---
name: webapp-testing
description: Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs.
license: Complete terms in LICENSE.txt
---

# Web Application Testing

To test local web applications, write native Python Playwright scripts.

**Helper Scripts Available**:
- `scripts/with_server.py` - Manages server lifecycle (supports multiple servers)

**Always run scripts with `--help` first** to see usage. DO NOT read the source until you try running the script first and find that a customized solution is abslutely necessary. These scripts can be very large and thus pollute your context window. They exist to be called directly as black-box scripts rather than ingested into your context window.

## Decision Tree: Choosing Your Approach

~~~
User task → Is it static HTML?
    ├─ Yes → Read HTML file directly to identify selectors
    │         ├─ Success → Write Playwright script using selectors
    │         └─ Fails/Incomplete → Treat as dynamic (below)
    │
    └─ No (dynamic webapp) → Is the server already running?
        ├─ No → Run: python scripts/with_server.py --help
        │        Then use the helper + write simplified Playwright script
        │
        └─ Yes → Reconnaissance-then-action:
            1. Navigate and wait for networkidle
            2. Take screenshot or inspect DOM
            3. Identify selectors from rendered state
            4. Execute actions with discovered selectors
~~~

## Example: Using wit
</source-excerpt>

## 4. Single server
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/webapp-testing/scripts/with_server.py`
- sha256: `c558ba21a3cea020cdf9c059e9c1e3119e01c23509227ee23fb4ae4f556e1373`

<source-excerpt>
#!/usr/bin/env python3
"""
Start one or more servers, wait for them to be ready, run a command, then clean up.

Usage:
    # Single server
    python scripts/with_server.py --server "npm run dev" --port 5173 -- python automation.py
    python scripts/with_server.py --server "npm start" --port 3000 -- python test.py

    # Multiple servers
    python scripts/with_server.py \
      --server "cd backend && python server.py" --port 3000 \
      --server "cd frontend && npm run dev" --port 5173 \
      -- python test.py
"""

import subprocess
import socket
import time
import sys
import argparse

def is_server_ready(port, timeout=30):
    """Wait for server to be ready by polling the port."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(('localhost', port), timeout=1):
                return True
        except (socket.error, ConnectionRefusedError):
            time.sleep(0.5)
    return False


def main():
    parser = argparse.ArgumentParser(description='Run command with one or more servers')
    parser.add_argument('--server', action='append', dest='servers', required=True, help='Server command (can be repeated)')
    parser.add_argument('--port', action='append', dest='ports', type=int, required=True, help='Port for each server (must match --server count)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds per server (default: 30)')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='Command to run after server(s) ready')

    args = parser.pa
</source-excerpt>

## 5. skills
- source: `microsoft-skills@02e0b2f852b3`
- kind: `guide`
- raw: `raw/microsoft-skills/docs-site/src/data/skills.json`
- sha256: `0f25d58d3ece3557614002aeca3f1616443056ebd9e00167ac337d8e0d695b3f`

<source-excerpt>
[
  {
    "name": "agent-framework-azure-ai-py",
    "description": "Build Azure AI Foundry agents using the Microsoft Agent Framework Python SDK (agent-framework-azure-ai). Use when creating persistent agents with AzureAIAgentsProvider, using hosted tools (code interpreter, file search, web search), integrating MCP servers, managing conversation threads, or implementing streaming responses. Covers function tools, structured outputs, and multi-tool agents.",
    "lang": "py",
    "category": "foundry",
    "path": ".github/plugins/azure-sdk-python/skills/agent-framework-azure-ai-py"
  },
  {
    "name": "airunway-aks-setup",
    "description": "Set up AI Runway on AKS — from bare cluster to running model. Covers cluster verification, controller install, GPU assessment, provider setup, and first deployment. WHEN: \"setup AI Runway\", \"onboard AKS cluster\", \"install AI Runway\", \"airunway setup\", \"deploy model to AKS\", \"GPU inference on AKS\", \"KAITO setup on AKS\", \"run LLM on AKS\", \"vLLM on AKS\", \"set up model serving on AKS\", \"AI Runway controller\".",
    "lang": "core",
    "category": "compute",
    "path": ".github/plugins/azure-skills/skills/airunway-aks-setup"
  },
  {
    "name": "appinsights-instrumentation",
    "description": "Guidance for instrumenting webapps with Azure Application Insights. Provides telemetry patterns, SDK setup, and configuration references. WHEN: how to instrument app, App Insights SDK, telemetry patterns, what is App Insights, Application Insights guidance, instrumentation examples, APM best practices.",
    "lang": "core",
</source-excerpt>

## 6. agents
- source: `microsoft-skills@02e0b2f852b3`
- kind: `guide`
- raw: `raw/microsoft-skills/docs-site/src/data/agents.json`
- sha256: `eabcce5114e1a883fa2dff2d8f985dd0487388a876fa25f4785687f364cb7a9c`

<source-excerpt>
[
  {
    "id": "backend",
    "name": "Backend Agent",
    "emoji": "⚙️",
    "description": "FastAPI, Pydantic, Cosmos DB, Azure services",
    "skills": ["FastAPI routers", "Pydantic models", "Cosmos DB", "Azure SDKs", "async patterns"],
    "file": "backend.agent.md"
  },
  {
    "id": "frontend",
    "name": "Frontend Agent",
    "emoji": "🎨",
    "description": "React, TypeScript, React Flow, Zustand, Tailwind",
    "skills": ["React components", "TypeScript", "React Flow nodes", "Zustand stores", "Tailwind CSS"],
    "file": "frontend.agent.md"
  },
  {
    "id": "infrastructure",
    "name": "Infrastructure Agent",
    "emoji": "🏗️",
    "description": "Bicep, Azure CLI, Container Apps, networking",
    "skills": ["Bicep templates", "Azure CLI", "Container Apps", "Networking", "azd deployment"],
    "file": "infrastructure.agent.md"
  },
  {
    "id": "planner",
    "name": "Planner Agent",
    "emoji": "📋",
    "description": "Task decomposition, architecture decisions",
    "skills": ["Task breakdown", "Architecture", "Tech decisions", "Dependency analysis", "Scope definition"],
    "file": "planner.agent.md"
  },
  {
    "id": "presenter",
    "name": "Presenter Agent",
    "emoji": "🎤",
    "description": "Documentation, demos, technical writing",
    "skills": ["Documentation", "README files", "Demo scripts", "Technical writing", "API docs"],
    "file": "presenter.agent.md"
  },
  {
    "id": "scaffolder",
    "name": "Scaffolder Agent",
    "emoji": "🏭",
    "description": "Full-stack Microsoft Foundry app scaffolding",
    "skills": ["Project setup", "Vite +
</source-excerpt>

## 7. Azure Static Web Apps
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/azure-skills/skills/azure-prepare/references/services/static-web-apps/README.md`
- sha256: `b4e7ebf64bc60c57e0f955254d46f5504037772ce7120562c811dab03e3cab61`

<source-excerpt>
# Azure Static Web Apps

Serverless hosting for static sites and SPAs with integrated APIs.

## When to Use

- Single Page Applications (React, Vue, Angular)
- Static sites (HTML/CSS/JS)
- JAMstack applications
- Sites with serverless API backends
- Documentation sites

## Service Type in azure.yaml

~~~yaml
services:
  my-web:
    host: staticwebapp
    project: ./src/web
~~~

## Required Supporting Resources

| Resource | Purpose |
|----------|---------|
| None required | Static Web Apps is fully managed |
| Application Insights | Monitoring (optional) |

## SKU Selection

| SKU | Features |
|-----|----------|
| Free | 2 custom domains, 0.5GB storage, shared bandwidth |
| Standard | 5 custom domains, 2GB storage, SLA, auth customization |

## Build Configuration

| Framework | outputLocation |
|-----------|----------------|
| React | `build` |
| Vue | `dist` |
| Angular | `dist/my-app` |
| Next.js (Static) | `out` |

## API Integration

Integrated Functions API structure:

~~~
project/
├── src/           # Frontend
└── api/           # Azure Functions API
    ├── hello/
    │   └── index.js
    └── host.json
~~~

## References

- [Region Availability](region-availability.md)
- [Bicep Patterns](bicep.md)
- [Terraform Patterns](terraform.md)
- [Routing and Auth](routing.md)
- [Deployment](deployment.md)
</source-excerpt>

## 8. Project Scaffolder
- source: `microsoft-skills@02e0b2f852b3`
- kind: `agent`
- raw: `raw/microsoft-skills/.github/agents/scaffolder.agent.md`
- sha256: `e90ddab15a264f4856c54171f820b8a2ce0e208346fbbaef7db2ade388138f43`

<source-excerpt>
---
name: Project Scaffolder
description: Full-stack Azure AI Foundry application scaffolder for React + FastAPI + azd projects
tools: ["read", "edit", "search", "execute"]
---

You are a **Project Scaffolder** for Azure AI Foundry applications. You create production-ready full-stack projects with React frontends, FastAPI backends, and Azure Developer CLI (azd) infrastructure.

## Tech Stack

### Frontend
- **Vite + React + TypeScript** with pnpm
- **Fluent UI v9** dark theme design system
- **Framer Motion** for animations
- **Tailwind CSS** for utility styles

### Backend
- **FastAPI** with async/await patterns
- **Pydantic v2** models (Base, Create, Update, Response, InDB)
- **pytest** with TDD approach
- **Ruff** for linting
- **uv** for package management

### Infrastructure
- **Azure Developer CLI (azd)** with `remoteBuild: true`
- **Bicep** templates for Container Apps
- **Managed Identity** for authentication
- **Azure Container Registry** for images

## Skills Reference

Load these skills for domain expertise:

| Skill | Purpose |
|-------|---------|
| `frontend-ui-dark-ts` | Dark theme patterns with Tailwind CSS, Framer Motion, glassmorphism |
| `fastapi-router-py` | FastAPI routers with CRUD, auth dependencies |
| `pydantic-models-py` | Pydantic v2 multi-model pattern (Base, Create, Update, Response, InDB) |

## Prompts Reference

Use these prompts for common scaffolding tasks:

| Prompt | Purpose |
|--------|---------|
| `scaffold-foundry-app.prompt.md` | Complete full-stack project scaffolding |

## Directory Structure

~~~
${PROJECT_NAME}/
├── azure.yaml
</source-excerpt>
