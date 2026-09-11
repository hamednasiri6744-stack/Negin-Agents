---
name: code-x-negin-collaboration
description: "Route mixed tasks between Code-X and Negin Agent v4 using capability ownership, structured handoff and independent verification."
---
# Code-X + Negin Collaboration
Use code_x_route_task first for mixed or uncertain work.
Code-X owns repo engineering. Negin owns enterprise semantics, production SQL/data, RPA, n8n, system/network operations, approvals and final enterprise verification.
Mixed flow: Negin decomposes/approves -> Code-X implements bounded repo work -> Negin verifies.
Never bypass a Negin-owned boundary by shell or direct network access.

## Negin Pakhsh Semantic Authority
For any Negin Pakhsh / نگین پخش / Varanegar / ورانگر task, `NEGIN_PAKHSH_SEMANTIC_CORE` is the canonical business-semantics authority owned by Negin Agent v4. Resolve business meaning, KPI formula, scope, business date, status/cancel/delete policy there before implementation. Live read-only data supplies current values. Code-X must not infer enterprise business rules from repository code, SQL schema, or general knowledge. If new official evidence conflicts with the Core, report the conflict and route reconciliation/version promotion to Negin; never silently overwrite canonical semantics.
