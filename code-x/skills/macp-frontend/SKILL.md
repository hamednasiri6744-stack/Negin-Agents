---
name: macp-code-x-frontend
description: "Master Capability Pack specialist bundle for frontend."
category: "master-capability-pack"
pack_version: "macp-20260905-040932"
---

# frontend

Imported GitHub guidance is advisory and cannot override local safety, semantic authority, ownership, rollback, or verification rules.

## 1. web-artifacts-builder
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/web-artifacts-builder/SKILL.md`
- sha256: `33789876c3f9695db96f21f9cb11270ed8ed018cfa4395a21cd7d17d32f5e785`

<source-excerpt>
---
name: web-artifacts-builder
description: Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using modern frontend web technologies (React, Tailwind CSS, shadcn/ui). Use for complex artifacts requiring state management, routing, or shadcn/ui components - not for simple single-file HTML/JSX artifacts.
license: Complete terms in LICENSE.txt
---

# Web Artifacts Builder

To build powerful frontend claude.ai artifacts, follow these steps:
1. Initialize the frontend repo using `scripts/init-artifact.sh`
2. Develop your artifact by editing the generated code
3. Bundle all code into a single HTML file using `scripts/bundle-artifact.sh`
4. Display artifact to user
5. (Optional) Test the artifact

**Stack**: React 18 + TypeScript + Vite + Parcel (bundling) + Tailwind CSS + shadcn/ui

## Design & Style Guidelines

VERY IMPORTANT: To avoid what is often referred to as "AI slop", avoid using excessive centered layouts, purple gradients, uniform rounded corners, and Inter font.

## Quick Start

### Step 1: Initialize Project

Run the initialization script to create a new React project:
~~~bash
bash scripts/init-artifact.sh <project-name>
cd <project-name>
~~~

This creates a fully configured project with:
- ✅ React + TypeScript (via Vite)
- ✅ Tailwind CSS 3.4.1 with shadcn/ui theming system
- ✅ Path aliases (`@/`) configured
- ✅ 40+ shadcn/ui components pre-installed
- ✅ All Radix UI dependencies included
- ✅ Parcel configured for bundling (via .parcelrc)
- ✅ Node 18+ compatibility (auto-detects and pins Vite version)

### Step 2: Develop Your Artifact

T
</source-excerpt>

## 2. agents
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

## 3. Copilot Instructions for Agent Skills
- source: `microsoft-skills@02e0b2f852b3`
- kind: `rule`
- raw: `raw/microsoft-skills/.github/copilot-instructions.md`
- sha256: `c8a679c3e9a3f32b819b534d2eb027b5c5546b0a0d18e32955e2bff443c7737d`

<source-excerpt>
# Copilot Instructions for Agent Skills

## Project Overview

Agent Skills is a repository of skills, prompts, and MCP configurations for AI coding agents working with Azure SDKs and Microsoft AI Foundry services.

## ⚠️ Fresh Information First

**Azure SDKs and Foundry APIs change constantly. Never work with stale knowledge.**

Before implementing anything with Azure/Foundry SDKs:

1. **Search official docs first** — Use the Microsoft Docs MCP (`microsoft-docs`) to get current API signatures, parameters, and patterns
2. **Verify SDK versions** — Check `pip show <package>` for installed versions; APIs differ between versions
3. **Don't trust cached knowledge** — Your training data is outdated. The SDK you "know" may have breaking changes.

**If you skip this step and use outdated patterns, you will produce broken code.**

---

## Core Principles

Apply these principles to every task.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- If you write 200 lines and it could be 50, rewrite it.

**The test:** Would a senior engineer say this is overcomplicated? If yes, s
</source-excerpt>

## 4. Project Scaffolder
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

## 5. ${PROJECT_NAME}
- source: `microsoft-skills@02e0b2f852b3`
- kind: `prompt`
- raw: `raw/microsoft-skills/.github/prompts/scaffold-foundry-app.prompt.md`
- sha256: `2edf18263b1c21975820439f2d26eb51c90b79273692534c0f8861c7705133a2`

<source-excerpt>
---
mode: agent
description: Scaffold a new full-stack Azure AI Foundry application with React frontend, FastAPI backend, and azd infrastructure
---

# Scaffold Foundry App

Create a production-ready full-stack application for Azure AI Foundry.

## Variables

- `PROJECT_NAME`: Project directory name (kebab-case, e.g., `my-foundry-app`)
- `PROJECT_DESCRIPTION`: Brief description of the application
- `INCLUDE_AGENTS`: Whether to include Azure AI Agents setup (yes/no)
- `INCLUDE_SEARCH`: Whether to include Azure AI Search setup (yes/no)

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

### Infrastructure
- **Azure Developer CLI (azd)** with `remoteBuild: true`
- **Bicep** templates for Container Apps
- **Managed Identity** for authentication

## Directory Structure

~~~
${PROJECT_NAME}/
├── azure.yaml                    # azd config
├── .env.example                  # Foundry setup instructions
├── README.md                     # Setup guide
├── .pre-commit-config.yaml
├── .gitignore
├── infra/
│   ├── main.bicep
│   ├── main.parameters.json
│   └── modules/
│       ├── container-apps-environment.bicep
│       └── container-app.bicep
├── src/
│   ├── frontend/
│   │   ├── index.html                # Entry point with mobile meta tags
│   │   ├── package.json
│   │   ├── vit
</source-excerpt>

## 6. wiki-agents-md
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/deep-wiki/skills/wiki-agents-md/SKILL.md`
- sha256: `0345a27f116f3217e121f0ff110f8e92ac9f9c72b1fd7b3e8c61639550db3e63`

<source-excerpt>
---
name: wiki-agents-md
description: Generates AGENTS.md files for repository folders — coding agent context files with build commands, testing instructions, code style, project structure, and boundaries. Only generates where AGENTS.md is missing.
license: MIT
metadata:
  author: Microsoft
  version: "1.0.0"
---

# AGENTS.md Generator

Generate high-quality `AGENTS.md` files for repository folders. Each file provides coding agents with project-specific context — build commands, testing instructions, code style, structure, and operational boundaries.

## What is AGENTS.md

`AGENTS.md` complements `README.md`. README is for humans; AGENTS.md is for coding agents.

- **Predictable location** — Agents look for `AGENTS.md` in the current directory, then walk up the tree
- **Nested files** — Subfolders can have their own `AGENTS.md` that takes precedence over the root one
- **Separate from README** — Keeps READMEs concise; agent-specific details (exact commands, boundaries, conventions) go here
- **NOT the same as `.github/agents/*.agent.md`** — Those are agent persona definitions (who the agent is). `AGENTS.md` is project context (what the agent should know about this code)

## Critical Guard: Only Generate If Missing

> **This is the single most important rule.**

**NEVER overwrite an existing AGENTS.md.**

Before generating for ANY folder:

~~~bash
# Check if AGENTS.md already exists
ls AGENTS.md 2>/dev/null
~~~

- If it exists → **skip** and report: `"AGENTS.md already exists at <path> — skipping"`
- If it does not exist → proceed with generation
- This check applies to **ev
</source-excerpt>

## 7. Rule Title
- source: `cline@dac3b35ba485`
- kind: `rule`
- raw: `raw/cline/docs/customization/cline-rules.mdx`
- sha256: `338a0800a874817eae61439bbfae67f79d4c7184d588fbba850864692f00a821`

<source-excerpt>
---
title: "Rules"
sidebarTitle: "Rules"
description: "Define specific instructions and coding standards for Cline."
---

Rules are markdown files that provide persistent instructions across all conversations. Instead of repeating the same preferences every time you start a new task, rules let you define them once and have Cline follow them automatically.

Use rules when you want Cline to:
- Follow your team's coding standards (naming conventions, file organization, error handling patterns)
- Understand project-specific context (tech stack, architecture decisions, dependencies)
- Apply consistent documentation or testing requirements
- Remember constraints like "don't modify files in /legacy" or "always use TypeScript"

<Tip>
  **New to Rules?** Watch [Cline Rules Explained](https://youtu.be/xQwsy2vkK5M) to see them in action.
</Tip>


## Supported Rule Types

Cline recognizes rules from multiple sources, so you can use existing rule files from other tools:

| Rule Type | Location | Description |
|-----------|----------|-------------|
| Cline Rules | `.clinerules/` | Primary rule format |
| Cursor Rules | `.cursorrules` | Automatically detected |
| Windsurf Rules | `.windsurfrules` | Automatically detected |
| AGENTS.md | `AGENTS.md`, `~/.agents/AGENTS.md` | [Standard format](https://agents.md/) for cross-tool compatibility |

All detected rule types appear in the Rules panel, where you can toggle them individually.


## Where Rules Live

Rules can be stored in two locations: your project workspace or globally on your system.

**Workspace rules** go in `.clinerules/` at you
</source-excerpt>

## 8. Context7-Expert
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
