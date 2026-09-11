# UX-X World-Class Quality Gates

These gates are the release contract for NeginAI UI/UX.

| Gate | Requirement |
|---|---|
| Render | Target page loads, meaningful content is visible, no framework/runtime overlay |
| Responsive | 360x800, 390x844, 768x1024, 1280x800 and 1440x900 have no accidental horizontal overflow |
| Direction | Primary flows verified in RTL and LTR where applicable |
| Accessibility | WCAG 2.2 AA target; zero serious/critical automated axe findings unless explicitly waived |
| Keyboard | Primary controls reachable and operable; visible focus treatment |
| Touch | Primary touch controls target >=44px where practical |
| States | Loading, empty, error, success, disabled and long-content behavior are intentional |
| Console | Zero relevant application console errors |
| Typography | Deliberate hierarchy for content and app chrome; no browser-default control typography |
| Design System | Repeated colors, spacing, radii, typography and controls use shared tokens/primitives where feasible |
| Motion | Purposeful; reduced-motion path present for non-essential animation |
| Visual QA | Material changes have before/after screenshot evidence at desktop + mobile |
| Interaction | At least one primary target flow is exercised after each material change |
| Performance | Lighthouse targets: Performance >=90, Accessibility >=95, Best Practices >=95 when environment is representative |
| Stability | CLS target <=0.1; LCP target <=2.5s in representative conditions |
| Regression | Existing high-value flows and established visual baselines remain intact |
| Reversibility | Any code-changing batch has a checkpoint and bounded rollback path |

A gate is `BLOCKED`, not `PASS`, when required evidence cannot be collected.
