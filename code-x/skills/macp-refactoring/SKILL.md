---
name: macp-code-x-refactoring
description: "Master Capability Pack specialist bundle for refactoring."
category: "master-capability-pack"
pack_version: "macp-20260905-040932"
---

# refactoring

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

## 2. Prompt Audit - Finding and Removing Dated Prompting Patterns
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/shared/prompt-audit.md`
- sha256: `571b08c181a8f3f0906a99045ff0bca88ca728d5a2d01afabb620b270c8048a2`

<source-excerpt>
# Prompt Audit - Finding and Removing Dated Prompting Patterns

> **If you arrived via `/claude-api prompt-audit`:** this is the right file. Execute the steps below in order - do not summarize them back to the user. Start with Step 0 (establish scope and target model), and finish by producing both deliverables: the audit report (Step 5) and the proposed diff (Step 6).

Prompts, skills, and tool descriptions accumulate instructions tuned to older models: emphasis added because an old model under-triggered, step-by-step scripts added because an old model planned poorly, format scaffolds written before the API had structured outputs. Current Claude models follow instructions more closely and more literally than the models much of this text was written for, so the leftover text is not just wasted tokens - specific outdated instructions actively degrade behavior (over-triggering, over-planning, rigid responses in gray areas), while merely irrelevant text is comparatively harmless. The audit's job is therefore to find **specific dated instructions**, not to make prompts shorter. "Every token earns its place" is the frame; "make it short" is not.

**The audit produces two artifacts - both, always:**

1. **An audit report**: every finding with its location (`file:line`), the pattern it matches, why it is obsolete for the target model, and a confidence level.
2. **A proposed diff**: concrete edits for the findings that warrant them. Propose - never apply edits without the user's consent.

**Prime directive: distinguish cruft from load-bearing content.** A finding you cannot tie to a
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

## 4. Copilot Instructions for Agent Skills
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

## 5. Azure SDK Migration Guidelines
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/azure-skills/skills/azure-upgrade/references/languages/java/INSTRUCTION.md`
- sha256: `5613629285530244a4b172988da800eaed5d91639e26d2dae09774ca5c7c05d2`

<source-excerpt>
# Azure SDK Migration Guidelines

## Context

The application is identified using legacy Azure SDKs for Java (`com.microsoft.azure.*`). These libraries reached end of support in 2023. They are not recommended for use in production, should be migrated to the latest Azure SDKs with the latest security patches and new capabilities support.

Follow these steps:

- **Inventory legacy dependencies**: Use tools such as `mvn dependency:tree` or `gradlew dependencies` to find every `com.microsoft.azure.*` SDK and map each one to its modern counterpart under `com.azure.*`. Do **not** rely solely on the root reactor — also grep the entire repository for legacy coordinates so you catch build files that aren't reachable from the root project. Run from the repo root:

  ~~~bash
  # Find every file referencing legacy groupIds/artifacts, including CI, samples, parent poms, buildSrc, version catalogs, Dockerfiles, and docs.
  grep -RIn --exclude-dir={.git,target,build,node_modules,out} \
    -E 'com\.microsoft\.azure(\.|:)|microsoft-azure-|azure-eventhubs-eph|azure-keyvault(:|["'\''])' .
  ~~~

  PowerShell equivalent (run from repo root):

  ~~~powershell
  Get-ChildItem -Path . -Recurse -File |
    Where-Object { $_.FullName -notmatch '(\\|/)(\.git|target|build|node_modules|out)(\\|/)' } |
    Select-String -Pattern 'com\.microsoft\.azure(\.|:)|microsoft-azure-|azure-eventhubs-eph|azure-keyvault(:|["''])'
  ~~~

  Commonly overlooked locations:`.ci/**/pom.xml`, `ci/**`, parent/BOM poms, `buildSrc/`, `gradle/libs.versions.toml`, `settings.gradle(.kts)`, `archetype-resources/`, sample sub-m
</source-excerpt>

## 6. Deep Wiki: Changelog Generation
- source: `microsoft-skills@02e0b2f852b3`
- kind: `command`
- raw: `raw/microsoft-skills/.github/plugins/deep-wiki/commands/changelog.md`
- sha256: `43d7a01289aa57a43a5725f49c2035708480fb8a924128b68b1ba4beed9ebcea`

<source-excerpt>
---
description: Generate a structured changelog from recent git commits, categorized by change type
---

# Deep Wiki: Changelog Generation

Analyze the git commit history of this repository and generate a structured changelog.

## Source Repository Resolution (MUST DO FIRST)

Before generating any changelog, resolve the source repository context:

1. **Check for git remote**: Run `git remote get-url origin`
2. **Ask the user**: _"Is this a local-only repository, or do you have a source repository URL?"_
   - Remote URL → store as `REPO_URL`, link commit hashes: `[abc1234](REPO_URL/commit/abc1234)`
   - Local → use plain commit hashes
3. **Do NOT proceed** until resolved

## Process

1. Examine recent git commits (messages, dates, authors)
2. Group by date: daily for last 7 days, aggregated weekly for older
3. Classify each commit into categories
4. Generate concise, user-facing descriptions using project terminology from README

## Categories

| Emoji | Category | Signal Keywords |
|-------|----------|----------------|
| 🆕 | New Features | `feat`, `add`, `new`, `implement`, `introduce` |
| 🐛 | Bug Fixes | `fix`, `bug`, `patch`, `resolve`, `hotfix` |
| 🔄 | Refactoring | `refactor`, `restructure`, `reorganize`, `clean` |
| 📝 | Documentation | `docs`, `readme`, `comment`, `jsdoc`, `docstring` |
| 🔧 | Configuration | `config`, `env`, `setting`, `ci`, `build` |
| 📦 | Dependencies | `deps`, `upgrade`, `bump`, `package`, `lock` |
| ⚠️ | Breaking Changes | `breaking`, `BREAKING`, `migrate`, `deprecate` |

## Output

For each time period, output:

~~~markdown
## [Date or Date Range
</source-excerpt>

## 7. wiki-changelog
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/deep-wiki/skills/wiki-changelog/SKILL.md`
- sha256: `c2c5da0e585855d44f831859a163ef1fa931df56ec3fb9d6d86ff6929f0a4e9a`

<source-excerpt>
---
name: wiki-changelog
description: Analyzes git commit history and generates structured changelogs categorized by change type. Use when the user asks about recent changes, wants a changelog, or needs to understand what changed in the repository.
license: MIT
metadata:
  author: Microsoft
  version: "1.0.0"
---

# Wiki Changelog

Generate structured changelogs from git history.

## Source Repository Resolution (MUST DO FIRST)

Before generating any changelog, you MUST determine the source repository context:

1. **Check for git remote**: Run `git remote get-url origin` to detect if a remote exists
2. **Ask the user**: _"Is this a local-only repository, or do you have a source repository URL (e.g., GitHub, Azure DevOps)?"_
   - Remote URL provided → store as `REPO_URL`, use **linked citations** for commit hashes and file references
   - Local-only → use plain commit hashes and file references
3. **Do NOT proceed** until source repo context is resolved

## When to Activate

- User asks "what changed recently", "generate a changelog", "summarize commits"
- User wants to understand recent development activity

## Procedure

1. Examine git log (commits, dates, authors, messages)
2. Group by time period: daily (last 7 days), weekly (older)
3. Classify each commit: Features (🆕), Fixes (🐛), Refactoring (🔄), Docs (📝), Config (🔧), Dependencies (📦), Breaking (⚠️)
4. Generate concise user-facing descriptions using project terminology

## Constraints

- Focus on user-facing changes
- Merge related commits into coherent descriptions
- Use project terminology from README
- Highlight bre
</source-excerpt>

## 8. frontend-design-review
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/skills/frontend-design-review/SKILL.md`
- sha256: `639b68cdc6f9b4cdd66a111851555afee2eb82d4de37bf9cbad3be845bb00c2d`

<source-excerpt>
---
name: frontend-design-review
description: >
  Review and create distinctive, production-grade frontend interfaces with high design quality and design system compliance.
  Evaluates using three pillars: frictionless insight-to-action, quality craft, and trustworthy building.
  USE FOR: PR reviews, design reviews, accessibility audits, design system compliance checks, creative frontend design,
  UI code review, component reviews, responsive design checks, theme testing, and creating memorable UI.
  DO NOT USE FOR: Backend API reviews, database schema reviews, infrastructure or DevOps work, pure business logic
  without UI, or non-frontend code.
acknowledgments: |
  Design review principles and quality pillar framework created by @Quirinevwm (https://github.com/Quirinevwm).
  Creative frontend guidance inspired by Anthropic's frontend-design skill
  (https://github.com/anthropics/skills/tree/main/skills/frontend-design). Licensed under respective terms.
---

# Frontend Design Review

Review UI implementations against design quality standards and your design system **OR** create distinctive, production-grade frontend interfaces from scratch.

## Two Modes

### Mode 1: Design Review
Evaluate existing UI for design system compliance, three quality pillars (Frictionless, Quality Craft, Trustworthy), accessibility, and code quality.

### Mode 2: Creative Frontend Design
Create distinctive interfaces that avoid generic "AI slop" aesthetics, have clear conceptual direction, and execute with precision.

---

## Creative Frontend Design

Before coding, commit to an aesthetic direct
</source-excerpt>
