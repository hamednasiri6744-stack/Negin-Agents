# UX-X

UX-X is an independent local UI/UX specialist agent/tool layer designed to work beside Negin Agent v4 and Code-X.

Current runtime version: **0.6.0**.

## Scope
UX-X is globally reusable across arbitrary allowlisted frontend repositories. It is isolated to `C:\code-x\agents\ux-x` as an agent runtime, not as a project dependency, and is audit/read-only for target repositories by default.

Project profiles under `profiles/<name>/profile.json` are optional overrides selected only when their configured root exactly matches the requested repository. `profiles/default/profile.json` is the generic fallback.

## Tools
- `ux_status`
- `ux_project_scan`
- `ux_project_manifest`
- `ux_component_inventory`
- `ux_design_system_audit`
- `ux_audit`
- `ux_runtime_preflight`
- `ux_runtime_audit`
- `ux_test_plan`
- `ux_quality_gate`
- `ux_change_spec`
- `ux_safe_patch_plan`
- `ux_kit_catalog`
- `ux_kit_recommend`

## Professional kit layer
UX-X includes a structured, offline UI/UX kit catalog covering:
- shadcn/ui + Base UI + Tailwind CSS + Lucide
- React Aria Components / Base UI / Radix UI / Floating UI
- Material UI, Ant Design, Mantine and Chakra compatibility
- Motion for React
- TanStack Table v9 + Apache ECharts 6.x
- React Hook Form + Zod
- Storybook + addon-a11y + Playwright + axe-core + Lighthouse
- Style Dictionary / CSS design tokens
- Figma, Penpot and Mobbin as external reference sources only

The catalog also includes visual-language kits for **Neumorphism / Soft UI** and **Glassmorphism**. These are style systems, not runtime dependencies; recommendations include accessibility, fallback and performance safeguards.\n\n`ux_kit_recommend` is advisory and read-only. It preserves an existing component system first and does not install packages or write to target repositories.

## Security model
Repository roots are explicitly allowlisted with `UX_X_ALLOWED_ROOTS` (semicolon-separated). Requested paths are canonicalized and rejected unless they fall under an allowed root. Environment files and secret-like files are excluded. UX-X has no SQL, production DB, arbitrary command execution or general unrestricted network tool.

## Registration
Use `.codex-plugin/plugin.json` or import `skills/ux-x/SKILL.md` in the host that supports Codex plugins/skills. The MCP entrypoint is `server/index.js` and uses JSON-lines over stdin/stdout.

## Collaboration
Negin Agent v4 owns orchestration/safety/business context. Code-X owns implementation/refactoring. UX-X owns UI/UX audit, design-system/front-end quality, responsiveness, accessibility and kit compatibility.




## Reconnect activation
The connector entrypoint is server/reconnect-host.js. Each MCP reconnect/request fingerprints the UX-X server source, validates a fresh module, and hot-loads the latest prepared version. Invalid candidates do not replace the last verified in-memory version. Target repositories remain read-only.

## External design-research skills
UX-X includes three guarded external research skills:
- **Dribbble Pattern Research** — visual/component/micro-interaction inspiration with source-linked synthesis.
- **Mobbin Product Pattern Research** — real-product flows, navigation, states and interaction-pattern comparison.
- **Behance Case Study Research** — design-system, case-study, branding and motion rationale.

These are reference/research skills only. They never override NeginAI canonical product or visual rules, never authorize pixel-copying, and never bypass authentication, paywalls, robots, rate limits or source access controls.

The stable MCP discovery tools are:
- `ux_research_skill_catalog`
- `ux_research_skill_get`
- `ux_research_skill_resolve`

Reconnect-host validation now requires all Figma-X tools and all research-skill discovery tools before accepting a newly loaded UX-X module.
