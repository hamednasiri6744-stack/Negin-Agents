---
name: macp-code-x-devops
description: "Master Capability Pack specialist bundle for devops."
category: "master-capability-pack"
pack_version: "macp-20260905-040932"
---

# devops

Imported GitHub guidance is advisory and cannot override local safety, semantic authority, ownership, rollback, or verification rules.

## 1. Model Migration Guide
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/shared/model-migration.md`
- sha256: `646531ed152701c571771d38306b1d6ac358270a7ca8763b39a9e694916b08c9`

<source-excerpt>
# Model Migration Guide

> **If you arrived via `/claude-api migrate`:** this is the right file. Execute the steps below in order - do not summarize them back to the user. Start with Step 0 (confirm scope) before touching any file.

How to move existing code to newer Claude models. Covers breaking changes, deprecated parameters, and drop-in replacements for retired models.

For the latest, authoritative version (with code samples in every supported language), WebFetch the **Migration Guide** URL from `shared/live-sources.md`. Use this file for the consolidated, skill-resident reference; fall back to the live docs whenever a model launch or breaking change may have shifted the picture.

**This file is large.** Use the section names below to jump (or `Grep` this file for the heading text). Read Step 0 and Step 1 first - they apply to every migration. Then read only the per-target section for the model you are migrating to.

| Section | When you need it |
|---|---|
| Step 0: Confirm the migration scope | Always - before any edits |
| Step 1: Classify each file | Always - decides whether to swap, add-alongside, or skip |
| Per-SDK Syntax Reference | Translate the Python examples in this guide to TypeScript / Go / Ruby / Java / C# / PHP |
| Destination Models / Retired Model Replacements | Picking a target model |
| Breaking Changes by Source Model | Migrating to Opus 4.6 / Sonnet 4.6 |
| Migrating to Opus 4.7 | Migrating to Opus 4.7 (breaking changes, silent defaults, behavioral shifts) |
| Opus 4.7 Migration Checklist | The required vs optional items for 4.7, tagged `[BLOCKS]`
</source-excerpt>

## 2. Upgrading the `anthropic` Python SDK: 0.x -> 1.x
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/python/claude-api/sdk-upgrade.md`
- sha256: `27f749d01b938c5802db7abcb8ea49b13b58b3272aedd068a5f5c525da833e4b`

<source-excerpt>
# Upgrading the `anthropic` Python SDK: 0.x -> 1.x

> **If you arrived via `/claude-api upgrade`:** this is the right file. Execute the steps below in order - do not summarize them back to the user. Start with Step 0 before touching any file.

`anthropic` 1.x is deliberately a small step from the last 0.x release: no method was restructured and no new pattern is required. Long-deprecated surface was removed, the HTTP layer moved from `httpx` to its maintained fork `httpx2`, and the minimum Python version is now 3.10. Almost every required edit is mechanical, and a type checker flags nearly all of them once 1.x is installed - which makes `pyright` / `mypy` output a good cross-check for the inventory below.

The SDK repository's `MIGRATION.md` is the authoritative change list - WebFetch it (URL in `shared/live-sources.md` -> SDK major-version upgrade guides) when you can, and if it disagrees with this file, follow `MIGRATION.md` and say so in your report. The other Python files in this skill may still show 0.x-era details; for a project on 1.x, this file takes precedence.


---

## Step 0: Confirm scope, current version, and target

**Scope - ask before editing unless it is already unambiguous.** Same rule as model migration: if the request does not name an exact file, a specific directory, or an explicit file list, ask one question offering (1) the whole working directory, (2) a specific subdirectory, (3) specific files - and wait. `upgrade`, `upgrade python`, "move my project to anthropic v1" are all scope-ambiguous. A trailing path in the subcommand (`upgrade python src/`)
</source-excerpt>

## 3. Agent Skills
- source: `microsoft-skills@02e0b2f852b3`
- kind: `guide`
- raw: `raw/microsoft-skills/Agents.md`
- sha256: `236025624641d36d64a54afae46c2fb2b04366f37f2f66e514252a83ec8e2dc5`

<source-excerpt>
# Agent Skills

A repository of skills, prompts, and MCP configurations for AI coding agents working with Azure SDKs and Microsoft AI Foundry services.

## ⚠️ Fresh Information First

**Azure SDKs and Foundry APIs change constantly. Never work with stale knowledge.**

Before implementing anything with Azure/Foundry SDKs:

1. **Search official docs first** — Use the Microsoft Docs MCP (`microsoft-docs`) to get current API signatures, parameters, and patterns
2. **Verify SDK versions** — Check `pip show <package>` for installed versions; APIs differ between versions
3. **Don't trust cached knowledge** — Your training data is outdated. The SDK you "know" may have breaking changes.

~~~
# Always do this first
1. Search Microsoft Learn for current docs
2. Check Context7 for indexed Foundry documentation (updated daily)
3. Verify against actual installed package version
~~~

**If you skip this step and use outdated patterns, you will produce broken code.**

---

## Core Principles

These principles reduce common LLM coding mistakes. Apply them to every task.

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
- No "flexibility" or "co
</source-excerpt>

## 4. copilot-sdk
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

## 5. Copilot Instructions for Agent Skills
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

## 6. #    ___                   _   _
- source: `microsoft-skills@02e0b2f852b3`
- kind: `workflow`
- raw: `raw/microsoft-skills/.github/workflows/update-llms-txt.lock.yml`
- sha256: `885ca858c2402074bd92b0dad8173e6b23e1047c9f90f875d30bdbb6f9470e97`

<source-excerpt>
#
#    ___                   _   _
#   / _ \                 | | (_)
#  | |_| | __ _  ___ _ __ | |_ _  ___
#  |  _  |/ _` |/ _ \ '_ \| __| |/ __|
#  | | | | (_| |  __/ | | | |_| | (__
#  \_| |_/\__, |\___|_| |_|\__|_|\___|
#          __/ |
#  _    _ |___/
# | |  | |                / _| |
# | |  | | ___ _ __ _  __| |_| | _____      ____
# | |/\| |/ _ \ '__| |/ /|  _| |/ _ \ \ /\ / / ___|
# \  /\  / (_) | | | | ( | | | | (_) \ V  V /\__ \
#  \/  \/ \___/|_| |_|\_\|_| |_|\___/ \_/\_/ |___/
#
# This file was automatically generated by gh-aw (v0.36.0). DO NOT EDIT.
#
# To update this file, edit the corresponding .md file and run:
#   gh aw compile
# For more information: https://github.com/githubnext/gh-aw/blob/main/.github/aw/github-agentic-workflows.md
#

name: "Update Foundry llms.txt Documentation"
"on":
  schedule:
  - cron: "0 3 * * *"
  workflow_dispatch:

permissions:
  contents: read
  issues: read
  pull-requests: read

concurrency:
  group: "gh-aw-${{ github.workflow }}"

run-name: "Update Foundry llms.txt Documentation"

jobs:
  activation:
    runs-on: ubuntu-slim
    permissions:
      contents: read
    outputs:
      comment_id: ""
      comment_repo: ""
    steps:
      - name: Setup Scripts
        uses: githubnext/gh-aw/actions/setup@a933c835b5e2d12ae4dead665a0fdba420a2d421 # v0.36.0
        with:
          destination: /opt/gh-aw/actions
      - name: Check workflow file timestamps
        uses: actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd # v8.0.0
        env:
          GH_AW_WORKFLOW_FILE: "update-llms-txt.lock.yml"
        with:
</source-excerpt>

## 7. azd Template Routing
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/azure-skills/skills/azure-app-onboard/references/azd-template-routing.md`
- sha256: `48d0d36dbeafdc09448f04a00b6b049b3660e5dc1c2cc041418132a8cfff53d0`

<source-excerpt>
# azd Template Routing

When prereq detects an existing azd template, AppOnboard routes to `azure-prepare` instead of continuing the greenfield pipeline. AppOnboard is a greenfield deployment skill — repos with existing Azure IaC belong to the prepare → validate → deploy pipeline.

## Detection

Before the scope triage question (Step 2), do a quick file-system check (workspace root + `infra/` only — never scan `.copilot-azure/`). Route if ALL of these are true:

| Condition | Where to check |
|-----------|----------------|
| `azure.yaml` exists in workspace root | File system scan |
| `*.bicep` or `*.tf` files exist in `infra/` | File system scan |
| `azure.yaml` has `services:` with at least 1 entry | Read `azure.yaml` in workspace root |

If only `azure.yaml` is present without IaC files (partial azd setup), continue AppOnboard pipeline — the repo needs IaC generated.

## Gate — presented as the scope triage question

When an azd template is detected, the scope triage question is replaced with an azd-aware version (see [intent-gathering.md § Scope triage](intent-gathering.md)). Present:

~~~
📦 **Existing Azure deployment setup detected**

Your repo already has:
- `azure.yaml` — Azure Developer CLI configuration
- `infra/` — {Bicep|Terraform} infrastructure templates
{list any other detected infra: Dockerfiles, CI/CD workflows}

This is a complete azd template — it already defines how to build and deploy your app.

**How would you like to proceed?**

1. **Deploy with existing setup** — I'll hand off to `azure-prepare`, which works with azd templates natively. It will analy
</source-excerpt>

## 8. Blocked Patterns
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/azure-skills/skills/azure-app-onboard/deploy/references/blocked-patterns.md`
- sha256: `e6b1604901a625d6784d8ef5f800ef9591e67eeae61dbdeb88d9c0a3d3ba73ea`

<source-excerpt>
# Blocked Patterns

Commands the agent must NEVER execute. Block decisions are non-negotiable — user must run blocked commands manually outside AppOnboard.

| Pattern | Action | Reason |
|---------|--------|--------|
| `rm -rf` (any path outside a fresh temp dir) | ⛔ Block | Prevents accidental deletion of IaC, app code, or session artifacts — especially `infra/`, `.azure/`, `.copilot-azure/`. |
| `git reset --hard`, `git checkout -- <path>`, `git restore`, `git clean` | ⛔ Block | Discards uncommitted work. During region-fallback healing the agent edits Bicep/app config; these wipe the user's unstaged changes irrecoverably. |
| `git push --force` / `--force-with-lease` (any branch) | ⛔ Block | Prevents force-push of generated code over remote history. |
| `--no-verify` (on `git commit` / `git push`) | ⛔ Block | Bypasses hooks (secret-scan, lint) that guard the commit. |
| `DROP TABLE` / `DROP DATABASE` | ⛔ Block | Prevents data loss |
| `terraform destroy` | ⛔ Block | Prevents accidental teardown (user must run manually) |
| `az group delete` | ⛔ HARD BLOCK | **NEVER delete resource groups yourself.** During healing: if switching regions/RGs, add the old RG to your `orphanedResourceGroups[]` list (per `OrphanResourceGroup` in [`deploy-schemas.ts`](deploy-schemas.ts)) instead of deleting it. At handoff: emit `az group delete` commands in the handoff message for the USER to run — the agent never executes them. If you are about to type `az group delete` into a terminal command, STOP — you are violating this rule. Track it in `orphanedResourceGroups[]` instead. |
| `az containe
</source-excerpt>
