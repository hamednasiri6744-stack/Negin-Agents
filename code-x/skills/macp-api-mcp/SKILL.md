---
name: macp-code-x-api-mcp
description: "Master Capability Pack specialist bundle for api-mcp."
category: "master-capability-pack"
pack_version: "macp-20260905-040932"
---

# api-mcp

Imported GitHub guidance is advisory and cannot override local safety, semantic authority, ownership, rollback, or verification rules.

## 1. claude-api
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/SKILL.md`
- sha256: `001abd67b06d9aa18f7f7c1a221200a51394f2cfb45cb583f4931bf77fd4b70f`

<source-excerpt>
---
name: claude-api
description: |-
  Reference for the Claude API / Anthropic SDK — model ids, pricing, params, streaming, tool use, MCP, agents, caching, token counting, model migration.
  TRIGGER — read BEFORE opening the target file; don't skip because it "looks like a one-liner" — whenever: the prompt names Claude/Anthropic in any form (Claude, Anthropic, Fable, Opus, Sonnet, Haiku, `anthropic`, `@anthropic-ai`, `claude-*`, `us.anthropic.*`, `[1m]`); the user asks about an LLM (pricing/model choice/limits/caching) — never answer from memory; OR the task is LLM-shaped with provider unstated (agent/MCP/tool-definition/multi-agent/RAG/LLM-judge/computer-use; generate/summarize/extract/classify/rewrite/converse over NL; debugging refusals/cutoffs/streaming/tool-calls/tokens).
  SKIP only when another provider is being worked on (overrides all triggers): OpenAI/GPT/Gemini/Llama/Mistral/Cohere/Ollama named in the query; OR `grep -rE 'openai|langchain_openai|google.generativeai|genai|mistralai|cohere|ollama'` over the project hits (run this grep FIRST if no provider named — don't Read the file).
license: Complete terms in LICENSE.txt
---

# Building LLM-Powered Applications with Claude

This skill helps you build LLM-powered applications with Claude. Choose the right surface based on your needs, detect the project language, then read the relevant language-specific documentation.

## Before You Start

Scan the target file (or, if no target file, the prompt and project) for non-Anthropic provider markers - `import openai`, `from openai`, `langchain_openai`, `OpenAI(`, `gpt-4`,
</source-excerpt>

## 2. doc-coauthoring
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/doc-coauthoring/SKILL.md`
- sha256: `2e47d78846faeea4a56e9809c52700087a15a2155a3f293a3efbaded81398ef4`

<source-excerpt>
---
name: doc-coauthoring
description: Guide users through a structured workflow for co-authoring documentation. Use when user wants to write documentation, proposals, technical specs, decision docs, or similar structured content. This workflow helps users efficiently transfer context, refine content through iteration, and verify the doc works for readers. Trigger when user mentions writing docs, creating proposals, drafting specs, or similar documentation tasks.
---

# Doc Co-Authoring Workflow

This skill provides a structured workflow for guiding users through collaborative document creation. Act as an active guide, walking users through three stages: Context Gathering, Refinement & Structure, and Reader Testing.

## When to Offer This Workflow

**Trigger conditions:**
- User mentions writing documentation: "write a doc", "draft a proposal", "create a spec", "write up"
- User mentions specific doc types: "PRD", "design doc", "decision doc", "RFC"
- User seems to be starting a substantial writing task

**Initial offer:**
Offer the user a structured workflow for co-authoring the document. Explain the three stages:

1. **Context Gathering**: User provides all relevant context while Claude asks clarifying questions
2. **Refinement & Structure**: Iteratively build each section through brainstorming and editing
3. **Reader Testing**: Test the doc with a fresh Claude (no context) to catch blind spots before others read it

Explain that this approach helps ensure the doc works well when others read it (including when they paste it into Claude). Ask if they want to try this workf
</source-excerpt>

## 3. mcp-builder
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/mcp-builder/SKILL.md`
- sha256: `0f4592dcb53cf2b5d6b7febee6b4152018b565551a1c29e3c612f57b218ab295`

<source-excerpt>
---
name: mcp-builder
description: Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).
license: Complete terms in LICENSE.txt
---

# MCP Server Development Guide

## Overview

Create MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. The quality of an MCP server is measured by how well it enables LLMs to accomplish real-world tasks.

---

# Process

## 🚀 High-Level Workflow

Creating a high-quality MCP server involves four main phases:

### Phase 1: Deep Research and Planning

#### 1.1 Understand Modern MCP Design

**API Coverage vs. Workflow Tools:**
Balance comprehensive API endpoint coverage with specialized workflow tools. Workflow tools can be more convenient for specific tasks, while comprehensive coverage gives agents flexibility to compose operations. Performance varies by client—some clients benefit from code execution that combines basic tools, while others work better with higher-level workflows. When uncertain, prioritize comprehensive API coverage.

**Tool Naming and Discoverability:**
Clear, descriptive tool names help agents find the right tools quickly. Use consistent prefixes (e.g., `github_create_issue`, `github_list_repos`) and action-oriented naming.

**Context Management:**
Agents benefit from concise tool descriptions and the ability to filter/paginate results. Des
</source-excerpt>

## 4. Managed Agents - cURL / Raw HTTP
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/curl/managed-agents.md`
- sha256: `e1fe01c98f270e08544b200d660c25fc6efb9b7caf3c321b29bab02d2ed01dc5`

<source-excerpt>
# Managed Agents - cURL / Raw HTTP

Use these examples when the user needs raw HTTP requests or is working without an SDK.

## Setup

~~~bash
export ANTHROPIC_API_KEY: [REDACTED]

# Common headers
HEADERS=(
  -H "Content-Type: application/json"
  -H "x-api-key: [REDACTED]
  -H "anthropic-version: 2023-06-01"
  -H "anthropic-beta: managed-agents-2026-04-01"
)
~~~

---

## Create an Environment

~~~bash
curl -X POST https://api.anthropic.com/v1/environments \
  "${HEADERS[@]}" \
  -d '{
    "name": "my-dev-env",
    "config": {
      "type": "cloud",
      "networking": { "type": "unrestricted" }
    }
  }'
~~~

### With restricted networking

~~~bash
curl -X POST https://api.anthropic.com/v1/environments \
  "${HEADERS[@]}" \
  -d '{
    "name": "restricted-env",
    "config": {
      "type": "cloud",
      "networking": {
        "type": "limited",
        "allow_package_managers": true,
        "allow_mcp_servers": true,
        "allowed_hosts": ["api.example.com"]
      }
    }
  }'
~~~

---

## Create an Agent (required first step)

> Warning: **There is no inline agent config.** Under `managed-agents-2026-04-01`, `model`/`system`/`tools` are top-level fields on `POST /v1/agents`, not on the session. Always create the agent first - the session only takes `"agent": {"type": "agent", "id": "..."}`.

### Minimal

~~~bash
# 1. Create the agent
curl -X POST https://api.anthropic.com/v1/agents \
  "${HEADERS[@]}" \
  -d '{
    "name": "Coding Assistant",
    "model": "claude-opus-5",
    "tools": [{ "type": "agent_toolset_20260401" }]
  }'
# -> { "id": "agent_abc123", ... }

#
</source-excerpt>

## 5. Live Documentation Sources
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/shared/live-sources.md`
- sha256: `c2c6b9c517d36f2101bf8a7bf8718cb7ae2f274c59ae36c2207a3aa10281a69b`

<source-excerpt>
# Live Documentation Sources

This file contains WebFetch URLs for fetching current information from platform.claude.com and Agent SDK repositories. Use these when users need the latest data that may have changed since the cached content was last updated.

## When to Use WebFetch

- User explicitly asks for "latest" or "current" information
- Cached data seems incorrect
- User asks about features not covered in cached content
- User needs specific API details or examples

## Claude API Documentation URLs

### Models & Pricing

| Topic           | URL                                                                          | Extraction Prompt                                                               |
| --------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Models Overview | `https://platform.claude.com/docs/en/about-claude/models/overview.md`        | "Extract current model IDs, context windows, and pricing for all Claude models" |
| Migration Guide | `https://platform.claude.com/docs/en/about-claude/models/migration-guide.md` | "Extract breaking changes, deprecated parameters, and per-model migration steps when moving to a newer Claude model" |
| Introducing Claude Fable 5 | `https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5.md` | "Extract capabilities, API changes, and availability stages for Claude Fable 5 and Claude Mythos 5" |
| Pricing         | `https://platform.claude.com/docs/en/pricing.md`
</source-excerpt>

## 6. Managed Agents - Endpoint Reference
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/shared/managed-agents-api-reference.md`
- sha256: `abb04671f430a4542012d8d25bc8b3932704142302a1eeb4c4d7a33d46314595`

<source-excerpt>
# Managed Agents - Endpoint Reference

All endpoints require `x-api-key` and `anthropic-version: 2023-06-01` headers. Managed Agents endpoints additionally require the `anthropic-beta` header.

> Most users should define agents and environments as version-controlled YAML applied with the `ant` CLI - see `shared/anthropic-cli.md`. The endpoints below are the underlying API that the CLI and SDKs drive.

## Beta Headers

~~~
anthropic-beta: managed-agents-2026-04-01
~~~

The SDK adds this header automatically for all `client.beta.{agents,environments,sessions,vaults,memory_stores,deployments,deployment_runs}.*` calls. Skills endpoints use `skills-2025-10-02`; Files endpoints use `files-api-2025-04-14`.

---

## SDK Method Reference

All resources are under the `beta` namespace. Python and TypeScript share identical method names.

| Resource | Python / TypeScript (`client.beta.*`) | Go (`client.Beta.*`) |
| --- | --- | --- |
| Agents | `agents.create` / `retrieve` / `update` / `list` / `archive` | `Agents.New` / `Get` / `Update` / `List` / `Archive` |
| Agent Versions | `agents.versions.list` | `Agents.Versions.List` |
| Environments | `environments.create` / `retrieve` / `update` / `list` / `delete` / `archive` | `Environments.New` / `Get` / `Update` / `List` / `Delete` / `Archive` |
| Environment Work (self-hosted) | `environments.work.poller` / `stats` / `stop` | See `shared/managed-agents-self-hosted-sandboxes.md` |
| Sessions | `sessions.create` / `retrieve` / `update` / `list` / `delete` / `archive` | `Sessions.New` / `Get` / `Update` / `List` / `Delete` / `Archive` |
| S
</source-excerpt>

## 7. Managed Agents - Core Concepts
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/shared/managed-agents-core.md`
- sha256: `2ed62fb4ee32dfa077c052bcefff289df63c65e843f2191ab8b33a1c04e33d7c`

<source-excerpt>
# Managed Agents - Core Concepts

## Architecture

Managed Agents is built around four core concepts:

| Concept | Endpoint | What it is |
|---|---|---|
| **Agent** | `/v1/agents` | A persisted, versioned object defining the agent's capabilities and persona: model, system prompt, tools, MCP servers, skills. **Must be created before starting a session.** See the Agents section below. |
| **Session** | `/v1/sessions` | A stateful interaction with an agent. References a pre-created agent by ID + an environment + initial instructions. Produces an event stream. |
| **Environment** | `/v1/environments` | A template defining the configuration for container provisioning. |
| **Container** | N/A | An isolated compute instance where the agent's **tools** execute (bash, file ops, code). The agent loop does not run here - it runs on Anthropic's orchestration layer and acts on the container via tool calls. |

~~~
                       +-------------------------------------+
                       |  Anthropic orchestration layer      |
Agent (config) ------->|  (agent loop: Claude + tool calls)  |
                       +--------------+----------------------+
                                      | tool calls
                                      v
Environment (template) --> Container (tool execution workspace)
                                 |
                         Session -+
                                 +-- Resources (files, repos, memory stores - attached at startup)
                                 +-- Vault IDs (MCP credential references)
                                 +
</source-excerpt>

## 8. Managed Agents - Environments & Resources
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/shared/managed-agents-environments.md`
- sha256: `faa3bb1a55a8bfc308d7884329ed2ed9fa2b9f64f39696bb51aeb3c69b86b264`

<source-excerpt>
# Managed Agents - Environments & Resources

## Environments

Creating a session requires an `environment_id`. Environments are **reusable configuration templates** for spinning up containers in Anthropic's infrastructure - you might create different environments for different use cases (e.g. data visualization vs web development, with different package sets). Anthropic handles scaling, container lifecycle, and work orchestration.

**Environment names must be unique.** Creating an environment with an existing name returns 409.

### Networking

| Network Policy   | Description                                                   |
| ---------------- | ------------------------------------------------------------- |
| `unrestricted`   | Full egress (except legal blocklist)                          |
| `limited`        | Deny-by-default; opt in via `allowed_hosts` / `allow_package_managers` / `allow_mcp_servers` |

~~~json
{
  "networking": {
    "type": "limited",
    "allow_package_managers": true,
    "allow_mcp_servers": true,
    "allowed_hosts": ["api.example.com"]
  }
}
~~~

All three `limited` fields are optional. `allow_package_managers` (default `false`) permits PyPI/npm/etc.; `allow_mcp_servers` (default `false`) permits the agent's configured MCP server endpoints without listing them in `allowed_hosts`.

**MCP caveat:** Under `limited` networking, either set `allow_mcp_servers: true` or add each MCP server domain to `allowed_hosts`. Otherwise the container can't reach them and tools silently fail.

**Packages caveat:** Under `limited` networking, `packages` requires `a
</source-excerpt>
