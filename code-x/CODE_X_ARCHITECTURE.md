# Code-X Architecture

## Objective

Code-X is an independently callable software-engineering agent layered on the preserved Codex source tree. It is intentionally complementary to **Negin Agent v4**, not a duplicate of it.

## Capability ownership

### Code-X — software-engineering specialist

Code-X owns:
- repository inspection and source reasoning
- implementation and refactoring inside approved roots
- unit, integration, and regression testing
- build/debug and code review
- Git/PR engineering
- software architecture
- MCP and agent implementation code

### Negin Agent v4 — enterprise orchestrator and safety boundary

Negin owns:
- enterprise semantics and business rules
- production SQL/data access and governance
- RPA and n8n/workflow operations
- workstation/server/network operations
- owner approvals
- enterprise knowledge and observability
- independent final verification for mixed/enterprise work

## Collaboration contract

Code-only work:

`Code-X -> implement/test/verify`

Enterprise-only work:

`Code-X -> structured handoff -> Negin Agent v4`

Mixed work:

`Negin decomposes/approves -> Code-X implements bounded repo changes -> Negin independently verifies`

The routing contract lives in `code_x_agent/routing.py` and is exposed through:
- `code_x_complementarity`
- `code_x_route_task`
- `code_x_handoff_to_negin`

`code_x_handoff_to_negin` creates a structured host-readable handoff packet only. It does not contain a Negin secret and does not call Negin over the network.

## Layers

1. **Upstream Codex engine** — `codex-rs/`, SDK, CLI, app-server, MCP components, sandboxing and agent roles. Preserved.
2. **Code-X control plane** — `code_x_agent/`. Policy, capability truth, routing, skills, bounded repository tools, checked execution, verification and MCP exposure.
3. **Client/host surface** — CLI or MCP client. ChatGPT/host reasoning may route between Code-X and Negin Agent v4.
4. **State** — `.code-x/config.json` and local job state.

## Trust boundaries

- MCP HTTP remains authenticated.
- Shell execution stays restricted to configured allowed roots.
- Secret-like environment variables are scrubbed from child processes.
- Repository reads reject traversal outside the source root.
- Code-X must not bypass Negin-owned production or enterprise boundaries through shell or direct networking.
- A successful Code-X command is not sufficient completion evidence for mixed/enterprise work; Negin performs independent final verification.

## Why Codex identifiers remain internal

The upstream snapshot contains a large Rust workspace with tightly coupled package and crate identifiers. Mass renaming would create a fragile fork and make upstream merges expensive. Code-X is therefore the product/control-plane identity while Codex remains the preserved engine namespace internally.
