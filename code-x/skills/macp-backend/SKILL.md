---
name: macp-code-x-backend
description: "Master Capability Pack specialist bundle for backend."
category: "master-capability-pack"
pack_version: "macp-20260905-040932"
---

# backend

Imported GitHub guidance is advisory and cannot override local safety, semantic authority, ownership, rollback, or verification rules.

## 1. Claude API - Python
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/python/claude-api/README.md`
- sha256: `55bd142e7d22bc7dfb1e37287f37b4a15bd8b5dc920775b8aab65a6d21654e6d`

<source-excerpt>
# Claude API - Python

## Installation

~~~bash
pip install anthropic
~~~

## Client Initialization

~~~python
import anthropic

# Default - resolves credentials from the environment:
# ANTHROPIC_API_KEY, or ANTHROPIC_AUTH_TOKEN, or an `ant auth login` profile.
# Prefer this for local dev; don't hardcode a key.
client = anthropic.Anthropic()

# Explicit API key (only when you must inject a specific key)
client = anthropic.Anthropic(api_key: [REDACTED]

# Async client
async_client = anthropic.AsyncAnthropic()
~~~

---

## Client Configuration

### Per-request overrides

Use `with_options()` to override client settings for a single call without mutating the client:

~~~python
client.with_options(timeout=5.0, max_retries=5).messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
)
~~~

### Timeouts

Default request timeout is 10 minutes. Pass a float (seconds) or an `anthropic.Timeout` for granular control. On timeout the SDK raises `anthropic.APITimeoutError` (and retries per `max_retries`).

~~~python
client = anthropic.Anthropic(timeout=20.0)
client = anthropic.Anthropic(
    timeout=anthropic.Timeout(60.0, read=5.0, write=10.0, connect=2.0),
)
~~~

`anthropic` 1.x is built on [`httpx2`](https://pypi.org/project/httpx2/), not `httpx`. `anthropic.Timeout` is `httpx2.Timeout`; if you import the HTTP library yourself, write `import httpx2 as httpx` - an object from the `httpx` package (`httpx.Timeout`, `httpx.Client`, transports, limits) is rejected or fails at request time. Existing `httpx`-era code is covered by t
</source-excerpt>

## 2. skills
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

## 3. copilot-sdk
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/skills/copilot-sdk/SKILL.md`
- sha256: `9bec8025d0ccf14b3c2f66754966781ba42d08a57b86b103bb9ef98d9f05c58b`

<source-excerpt>
---
name: copilot-sdk
description: Build applications powered by GitHub Copilot using the Copilot SDK. Use when creating programmatic integrations with Copilot across Node.js/TypeScript, Python, Go, or .NET. Covers session management, custom tools, streaming, hooks, MCP servers, BYOK providers, session persistence, custom agents, skills, and deployment patterns. Requires GitHub Copilot CLI installed and a GitHub Copilot subscription (unless using BYOK).
---

# GitHub Copilot SDK

Build applications that programmatically interact with GitHub Copilot. The SDK wraps the Copilot CLI via JSON-RPC, providing session management, custom tools, hooks, MCP server integration, and streaming across Node.js, Python, Go, and .NET.

## Prerequisites

- **GitHub Copilot CLI** installed and authenticated (`copilot --version`)
- **GitHub Copilot subscription** (Individual, Business, or Enterprise) — not required for BYOK
- **Runtime:** Node.js 18+ / Python 3.8+ / Go 1.21+ / .NET 8.0+

## Installation

| Language | Package | Install |
|----------|---------|---------|
| Node.js | `@github/copilot-sdk` | `npm install @github/copilot-sdk` |
| Python | `github-copilot-sdk` | `pip install github-copilot-sdk` |
| Go | `github.com/github/copilot-sdk/go` | `go get github.com/github/copilot-sdk/go` |
| .NET | `GitHub.Copilot.SDK` | `dotnet add package GitHub.Copilot.SDK` |

## Architecture

The SDK communicates with the Copilot CLI via JSON-RPC over stdio (default) or TCP. The CLI manages model calls, tool execution, session state, and MCP server lifecycle.

~~~
Your App → SDK Client → [stdio/TCP] → C
</source-excerpt>

## 4. Full-Stack Web App Template — REFERENCE ONLY
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

## 5. podcast-generation
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/skills/podcast-generation/SKILL.md`
- sha256: `7bd0a33aec424bd631b725fcf5e58de759bbb8c406140ebdf88df43541a7cac7`

<source-excerpt>
---
name: podcast-generation
description: Generate AI-powered podcast-style audio narratives using Azure OpenAI's GPT Realtime Mini model via WebSocket. Use when building text-to-speech features, audio narrative generation, podcast creation from content, or integrating with Azure OpenAI Realtime API for real audio output. Covers full-stack implementation from React frontend to Python FastAPI backend with WebSocket streaming.
---

# Podcast Generation with GPT Realtime Mini

Generate real audio narratives from text content using Azure OpenAI's Realtime API.

## Quick Start

1. Configure environment variables for Realtime API
2. Connect via WebSocket to Azure OpenAI Realtime endpoint
3. Send text prompt, collect PCM audio chunks + transcript
4. Convert PCM to WAV format
5. Return base64-encoded audio to frontend for playback

## Environment Configuration

~~~env
AZURE_OPENAI_AUDIO_API_KEY: [REDACTED]
AZURE_OPENAI_AUDIO_ENDPOINT=https://your-resource.cognitiveservices.azure.com
AZURE_OPENAI_AUDIO_DEPLOYMENT=gpt-realtime-mini
~~~

**Note**: Endpoint should NOT include `/openai/v1/` - just the base URL.

## Core Workflow

### Backend Audio Generation

~~~python
from openai import AsyncOpenAI
import base64

# Convert HTTPS endpoint to WebSocket URL
ws_url = endpoint.replace("https://", "wss://") + "/openai/v1"

client = AsyncOpenAI(
    websocket_base_url=ws_url,
    api_key: [REDACTED]
)

audio_chunks = []
transcript_parts = []

async with client.realtime.connect(model="gpt-realtime-mini") as conn:
    # Configure for audio-only output
    await conn.session.update(session={
</source-excerpt>

## 6. Cua Driver integration surfaces: MCP/CLI and SDK bindings
- source: `qwen-code@dfadc1160491`
- kind: `mcp`
- raw: `raw/qwen-code/packages/cua-driver/docs/why-cua-driver-uses-mcp-instead-of-uniffi.md`
- sha256: `77a252058de4a1c7891bf2768f69f99c7197c2da3ca6dad9502b851bae689ce8`

<source-excerpt>
# Cua Driver integration surfaces: MCP/CLI and SDK bindings

Status: superseded in part by RFC 2447

Decision date: 2026-07-21

> This document preserves the rationale for the 0.11.0 daemon-client SDK.
> [RFC 2447](../../../rfcs/2447-cua-driver-native-core-and-mcp-adapter.md)
> keeps MCP as the agent boundary but replaces the imported SDK topology with a
> same-process runtime and makes MCP a downstream SDK consumer. Where this
> document says the SDK is only a daemon client, RFC 2447 is authoritative.

This document separates two Cua products that were previously discussed as if
they were one: Cua as a tool used by an agent, and Cua as an API imported by an
application. MCP and UniFFI solve different boundaries in those products and
are not competing protocol choices.

## The product distinction

| Surface                    | Consumer                                                  | Public shape                                        | What provides runtime portability                                                                                              |
| -------------------------- | --------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Cua as an agent MCP or CLI | Codex, Claude Code, another agent, or a shell             | `qwen-cua-driver mcp` and `qwen-cua-driver call`    | MCP and the executable protocol already work from any capable runtime.
</source-excerpt>

## 7. Context7-Expert
- source: `awesome-copilot@7b1ebe633339`
- kind: `agent`
- raw: `raw/awesome-copilot/agents/context7.agent.md`
- sha256: `dd8f825ce026e7a35e21579d7be81486f14ca5344b9caf4a48d446f09e45aad1`

<source-excerpt>
---
name: Context7-Expert
description: 'Expert in latest library versions, best practices, and correct syntax using up-to-date documentation'
argument-hint: 'Ask about specific libraries/frameworks (e.g., "Next.js routing", "React hooks", "Tailwind CSS")'
tools: ['read', 'search', 'web', 'context7/*', 'agent/runSubagent']
mcp-servers:
  context7:
    type: http
    url: "https://mcp.context7.com/mcp"
    headers: {"CONTEXT7_API_KEY": "${{ secrets.COPILOT_MCP_CONTEXT7 }}"}
    tools: ["get-library-docs", "resolve-library-id"]
handoffs:
  - label: Implement with Context7
    agent: agent
    prompt: Implement the solution using the Context7 best practices and documentation outlined above.
    send: false
---

# Context7 Documentation Expert

You are an expert developer assistant that **MUST use Context7 tools** for ALL library and framework questions.

## 🚨 CRITICAL RULE - READ FIRST

**BEFORE answering ANY question about a library, framework, or package, you MUST:**

1. **STOP** - Do NOT answer from memory or training data
2. **IDENTIFY** - Extract the library/framework name from the user's question
3. **CALL** `mcp_context7_resolve-library-id` with the library name
4. **SELECT** - Choose the best matching library ID from results
5. **CALL** `mcp_context7_get-library-docs` with that library ID
6. **ANSWER** - Use ONLY information from the retrieved documentation

**If you skip steps 3-5, you are providing outdated/hallucinated information.**

**ADDITIONALLY: You MUST ALWAYS inform users about available upgrades.**
- Check their package.json version
- Compare with latest avai
</source-excerpt>

## 8. Modernization Agent
- source: `awesome-copilot@7b1ebe633339`
- kind: `agent`
- raw: `raw/awesome-copilot/agents/modernization.agent.md`
- sha256: `4d0c8a31a7f751bd56645de5f63ba067cd1c9eaefd6973ce5a6ddf2af9403563`

<source-excerpt>
---
description: 'Human-in-the-loop modernization assistant for analyzing, documenting, and planning complete project modernization with architectural recommendations.'
name: 'Modernization Agent'
model: 'GPT-5'
tools:
   - search
   - read
   - edit
   - execute
   - agent
   - todo
   - read/problems
   - execute/runTask
   - execute/runInTerminal
   - execute/createAndRunTask
   - execute/getTaskOutput
   - web/fetch
---

This agent runs directly in VS Code with read/write access to your workspace. It guides you through complete project modernization with a structured, stack-agnostic workflow.

# Modernization Agent

## IMPORTANT: When to Execute Workflow

 **Ideal Inputs**
- Repository with an existing project (any tech stack)
## What This Agent Does

**CRITICAL ANALYSIS APPROACH:**
This agent performs **exhaustive, deep-dive analysis** before any modernization planning. It:
- **Reads EVERY business logic file** (services, repositories, domain models, controllers, etc.)
- **Generates per-feature analysis** in separate Markdown files
- **Re-reads all generated feature docs** to synthesize a comprehensive README
- **Forces understanding** through line-by-line code examination
- **Never skips files** - completeness is mandatory

**Analysis Phase (Steps 1-7):**
- Analyzes project type and architecture
- Reads ALL service files, repositories, domain models individually
- Creates detailed per-feature documentation (one MD file per feature/domain)
- Re-reads generated feature docs to create master README
- Frontend business logic: routing, auth flows, role-based/UI-level autho
</source-excerpt>
