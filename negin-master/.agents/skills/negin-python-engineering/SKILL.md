---
name: negin-python-engineering
description: "Engineer, debug and maintain Python systems. Use for Python services, FastAPI, async code, packaging, data utilities, tests and performance work."
compatibility: "Agent Skills compatible clients, including ChatGPT/Codex where Skills are enabled. May use approved MCP/app tools when available."
metadata:
  bundle: "negin-agents-specialist-skills"
  version: "1.0.0"
  category: "engineering"
---

# Purpose

Specialist workflow for production-quality Python engineering.

# Inputs

- Repository/system context
- Requested behavior or failure
- Runtime/version constraints
- Available tests, logs or acceptance criteria

# Workflow

1. Inspect project and dependency management.
2. Reproduce behavior or define acceptance criteria.
3. Implement the smallest coherent change.
4. Handle types, errors and resource lifecycle explicitly.
5. Run focused tests and review the diff.

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
