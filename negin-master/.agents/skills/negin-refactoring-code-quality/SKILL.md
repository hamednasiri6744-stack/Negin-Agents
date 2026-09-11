---
name: negin-refactoring-code-quality
description: "Improve maintainability without unintended behavior change. Use for modularization, duplication removal, dependency cleanup, naming, complexity reduction and technical debt."
compatibility: "Agent Skills compatible clients, including ChatGPT/Codex where Skills are enabled. May use approved MCP/app tools when available."
metadata:
  bundle: "negin-agents-specialist-skills"
  version: "1.0.0"
  category: "engineering"
---

# Purpose

Specialist workflow for safe refactoring with preserved behavior.

# Inputs

- Repository/system context
- Requested behavior or failure
- Runtime/version constraints
- Available tests, logs or acceptance criteria

# Workflow

1. Define invariants that must not change.
2. Separate refactor from feature work.
3. Make incremental edits.
4. Run tests after meaningful steps.
5. Review the diff for semantic drift.

# Guardrails

- Inspect before modifying and prefer minimal, reversible changes.
- Preserve unrelated work, existing structure and public contracts unless change is intentional.
- Do not expose secrets, credentials or sensitive configuration in output or logs.
- Do not claim success without verification evidence when verification is available.
- Treat destructive, production or security-sensitive operations as separately governed actions.

# Output contract

Return the implementation/diagnosis summary, files or components affected, verification evidence, important risks and the next action if anything remains.

# Final checks

- Run the narrowest relevant verification first.
- Review the final diff/state.
- Check error/failure paths.
- Report anything not verified.

# Completion rule

Do not report completion until the requested result is produced and the relevant checks have been performed or explicitly identified as unavailable.
