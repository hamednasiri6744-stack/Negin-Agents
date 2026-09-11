---
name: negin-code-x-delegation
description: "Delegate coding and software-engineering work to the local Code-X agent built from the full Codex source, while preserving Negin Agent v4 as the orchestration and safety boundary."
compatibility: "Negin Agent v4 on the local Windows workstation. Requires C:\\code-x and an approved Code-X allowed root."
metadata:
  bundle: "negin-agents-specialist-skills"
  version: "1.0.0"
  category: "engineering"
---

# Purpose

Use Code-X as a specialist coding engine for repository-scoped engineering tasks while Negin Agent v4 remains the orchestration, approval, and verification layer.

# When to use

Use this skill when the owner explicitly asks to use `code-x`, asks Negin Agent v4 to collaborate with Code-X, or when a coding task would materially benefit from delegated Codex-engine execution.

# Preconditions

1. Verify `C:\code-x\code-x.ps1 status` succeeds.
2. Verify the requested working directory exists and is present in `C:\code-x\.code-x\config.json` under `security.allowed_roots`.
3. Inspect repository status before any modifying task.
4. Preserve unrelated uncommitted work.

# Execution

For a bounded Code-X task, invoke:

`powershell.exe -noprofile -executionpolicy bypass -file C:\code-x\code-x.ps1 codex --cwd "<approved-repo-root>" --timeout 120 "<task-prompt>"`

For health/capability checks use:

`powershell.exe -noprofile -executionpolicy bypass -file C:\code-x\code-x.ps1 status`

`powershell.exe -noprofile -executionpolicy bypass -file C:\code-x\code-x.ps1 capabilities`

# Guardrails

- Never delegate a cwd outside Code-X `security.allowed_roots`.
- Do not expand allowed roots to an entire drive or Windows/system directories.
- Do not move, rename, merge, delete, or relocate project files without explicit owner approval.
- Do not overwrite unrelated user changes.
- Production SQL remains read-only and must use Negin Agent v4's governed SQL tools, not Code-X shell execution.
- Do not expose the Code-X MCP bearer token in chat, logs, prompts, or source files.
- Prefer inspection, tests, and minimal reversible patches.
- A successful Code-X command is not completion evidence by itself; verify postconditions independently with Negin Agent v4.
- Do not modify or restart Negin Agent v4, n8n, Tailscale routes, or other services as a side effect of a coding task unless separately approved.

# Collaboration model

Negin Agent v4 owns:
- task decomposition
- owner approvals
- enterprise/business context
- production safety
- independent verification

Code-X owns:
- repository inspection
- coding
- refactoring
- local test execution
- implementation-level reasoning

# Completion rule

Report completion only after Code-X output is independently checked against explicit postconditions and the final repository state is reviewed.
