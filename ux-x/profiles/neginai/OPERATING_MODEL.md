# UX-X / Code-X Operating Model

## Roles

**UX-X**
- product UI/UX authority;
- audits, concepts, design-system decisions, change specifications;
- runtime/visual/accessibility verification;
- final UI acceptance.

**Code-X**
- implementation worker;
- bounded refactoring and frontend code changes;
- build/lint/test execution;
- no independent visual-direction changes.

**Negin Agent v4**
- orchestration, system/network operations, business context and independent safety verification when available.

## Change Protocol

`UX-X inspect -> UX-X spec -> checkpoint -> Code-X implement -> Code-X tests -> UX-X rendered QA -> UX-X gate -> accept/reject`

If UX-X rejects a change, Code-X receives a repair specification and the loop repeats.

## Priority Order

P0: broken layout, inaccessible primary controls, runtime errors, mobile blockers, security-sensitive UI mistakes.
P1: inconsistent information architecture, state handling, responsive behavior, design-system fragmentation.
P2: typography, spacing, visual rhythm, motion, perceived quality.
P3: optional flourish and delight.

No P2/P3 polish should hide unresolved P0/P1 defects.
