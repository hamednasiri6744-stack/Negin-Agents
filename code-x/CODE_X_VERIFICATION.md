# Code-X Verification Report

## Source

- Input archive: `codex-main.zip`
- Input SHA-256: `b54c51ac058ff8c65e7430d5eec41e8b5bdb1b639db8ed46ba69800863c4f1cd`
- Snapshot contains the full supplied Codex source tree, including `codex-rs`, CLI, SDK, skills, sandboxing, app-server and MCP components.

## Implemented Code-X layer

- User-facing product name: `code-x`
- Control plane: `code_x_agent/`
- MCP tools: 13
- MCP transports: stdio + loopback HTTP
- HTTP authentication: path token or Bearer token
- Guarded shell: allowed-root enforcement, deny rules, timeout, output bounds, secret-like environment scrubbing
- Skills: bundled Codex skills plus `code-x-core`
- Verification: explicit assertion-based task verifier
- Durable state: SQLite job registry and worker for supported read-only planning/audit jobs
- Codex engine delegation: uses an available authenticated Codex CLI; bundled Rust source is preserved

## Executed verification

1. Python compile check: PASS (all `code_x_agent/*.py`).
2. Agent unit/integration tests: PASS, 9/9.
3. MCP HTTP health: PASS.
4. MCP initialize negotiation: PASS; server name `code-x`.
5. MCP tools/list: PASS; 13 tools returned.
6. MCP tool call `code_x_status`: PASS.
7. Runtime state cleanup: generated bearer token and SQLite test state excluded from the deliverable.

## Not verified in this environment

The container does not contain `cargo`/`rustc`, so a complete Rust build of the upstream `codex-rs` workspace could not be executed here. This is reported as an explicit verification gap, not treated as a passing build. The supplied Rust source was preserved rather than mechanically mass-renamed.

## Python Capability Pack v1 rollout

- Manifest: `code_x_agent/python_capability_pack.json`
- Runtime sync/state implementation: `code_x_agent/capability_pack.py`
- State: `.code-x/python-capability-pack-state.json`
- Reconnect hook: MCP `initialize` performs idempotent manifest/package synchronization.
- Startup hook: `scripts/start-code-x.ps1` runs `code-x.py bootstrap` before serving MCP.
- Failure contract: dependency-sync failure is fail-open/degraded for MCP; explicit CLI bootstrap returns non-zero.
- Concurrency contract: in-process and cross-process locking prevent duplicate pip synchronization.
- Rollback snapshot: `.code-x/backups/python-capability-pack-v1-20260905/`

