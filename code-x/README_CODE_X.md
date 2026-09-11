# Code-X

**Code-X** is a secure, chat-first coding-agent control plane built on the full Codex source snapshot contained in this repository. It deliberately keeps upstream `codex-*` crate names and architecture intact so the engine remains maintainable and updateable, while adding an agent layer comparable in operating model to Negin Agent v4.

## What was added

- `code-x.py`, `code-x.cmd`, `code-x.ps1`: user-facing launchers.
- `code_x_agent/`: local agent control plane.
- Guarded checked shell with allowed-root enforcement, command deny rules, timeouts, output bounds, and secret-bearing environment scrubbing.
- Skill catalog, resolver and loader over both Code-X and bundled Codex skills.
- Bounded repository search/read tools.
- Explicit task verifier with evidence assertions.
- MCP server over stdio and loopback HTTP, exposing narrow `code_x_*` tools.
- Optional delegation to the bundled/installed Codex CLI using the user's existing Codex/ChatGPT login.
- Durable SQLite job registry for explicitly supported background-safe job types.

## Run

Windows:

```powershell
.\code-x.ps1 status
.\code-x.ps1 capabilities
.\code-x.ps1 skills
.\code-x.ps1 mcp --transport http
```

Portable:

```bash
python code-x.py status
python code-x.py capabilities
python code-x.py mcp --transport stdio
```

The first run creates `.code-x/config.json` with a random MCP bearer token. The default HTTP listener is `127.0.0.1:8777`; it is intentionally not exposed to the LAN or internet by default.

## MCP contract

Core tools:

- `code_x_status`
- `code_x_capabilities`
- `code_x_skill_catalog`
- `code_x_skill_resolve`
- `code_x_skill_get`
- `code_x_repo_search`
- `code_x_repo_read`
- `code_x_shell_checked_sequence`
- `code_x_verify`
- `code_x_coding_task`
- `code_x_job_submit`
- `code_x_jobs`
- `code_x_job_status`

For specialist work, clients should call `code_x_skill_resolve`, load the smallest relevant skill set with `code_x_skill_get`, execute, then verify explicit postconditions with `code_x_verify`.

## Relationship to Codex

This is a derivative integration layer, not a claim of independent authorship of the upstream engine. The original Apache-2.0 `LICENSE` and `NOTICE` are preserved. Internal Codex crate/package identifiers are intentionally left intact to avoid dependency breakage and to preserve the ability to merge upstream updates.

## Verification policy

Code-X considers a task complete only when the requested artifact/change exists and relevant checks have passed, or when unavailable checks are explicitly reported. A successful last command is not sufficient evidence if prior required steps failed.

## Python Capability Pack v1

Code-X keeps its advanced Python engineering dependencies in `code_x_agent/python_capability_pack.json`.
The synchronized runtime state is stored at `.code-x/python-capability-pack-state.json`.

Upgrade semantics are reconnect-driven: when the manifest fingerprint or required package state changes,
an MCP `initialize` (a normal client reconnect) performs one serialized, bounded sync. If everything is
already compliant, reconnect is a fast no-op and does not invoke pip. Fresh process startup performs the
same bootstrap before the HTTP MCP server starts.

The core pack covers typed schemas, async HTTP, retry policy, rich CLI diagnostics, multi-language parsing,
lossless Python refactoring, graph analysis, property-based testing, coverage, static typing, process
inspection, fast JSON, file watching, schema validation, Git automation, pytest and Ruff. Heavy data,
security and profiling packages remain optional/on-demand metadata rather than permanent core dependencies.

A failed or timed-out dependency sync does not take down MCP. Code-X starts/initializes in degraded mode,
records only non-secret status metadata, and retries on a later reconnect. Manual inspection is available
with `python code-x.py capability-pack`; explicit manual synchronization is `python code-x.py bootstrap`.

Rollback snapshot for this rollout: `.code-x/backups/python-capability-pack-v1-20260905/`.

