---
name: code-x-core
description: "Core Code-X workflow for safe repository engineering, bounded execution, specialist skill routing, and evidence-based completion."
---

# Code-X Core

Use this skill for non-trivial engineering tasks in the Code-X source tree.

## Workflow
1. Inspect the target repository and current git state before edits.
2. Resolve and load the smallest relevant specialist skill set.
3. State explicit postconditions for the requested change.
4. Make focused edits that preserve unrelated work and upstream Codex compatibility.
5. Run the narrowest relevant formatter/linter/test first.
6. Use `code_x_verify` with explicit assertions before claiming completion.

## Guardrails
- Never expose secrets or credential values.
- Never run destructive host/OS commands through the coding shell.
- Keep file operations inside configured allowed roots.
- Preserve Apache-2.0 LICENSE and NOTICE from upstream Codex.
- Treat upstream Codex internals as an engine dependency; avoid mass renaming internal crates.
- Do not report COMPLETE when build/test evidence is unavailable or failing.
