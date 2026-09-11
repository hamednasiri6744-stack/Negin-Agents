---
name: macp-code-x-react-nextjs
description: "Master Capability Pack specialist bundle for react-nextjs."
category: "master-capability-pack"
pack_version: "macp-20260905-040932"
---

# react-nextjs

Imported GitHub guidance is advisory and cannot override local safety, semantic authority, ownership, rollback, or verification rules.

## 1. metadata
- source: `vercel-agent-skills@063bee94c3f4`
- kind: `skill`
- raw: `raw/vercel-agent-skills/skills/react-best-practices/metadata.json`
- sha256: `c4e18bac3290fbe1b471a605867d4df68b03144ea26b8befdbe8f9d8fd124354`

<source-excerpt>
{
  "version": "1.0.0",
  "organization": "Vercel Engineering",
  "date": "January 2026",
  "abstract": "Comprehensive performance optimization guide for React and Next.js applications, designed for AI agents and LLMs. Contains 40+ rules across 8 categories, prioritized by impact from critical (eliminating waterfalls, reducing bundle size) to incremental (advanced patterns). Each rule includes detailed explanations, real-world examples comparing incorrect vs. correct implementations, and specific impact metrics to guide automated refactoring and code generation.",
  "references": [
    "https://react.dev",
    "https://nextjs.org",
    "https://swr.vercel.app",
    "https://github.com/shuding/better-all",
    "https://github.com/isaacs/node-lru-cache",
    "https://vercel.com/blog/how-we-optimized-package-imports-in-next-js",
    "https://vercel.com/blog/how-we-made-the-vercel-dashboard-twice-as-fast"
  ]
}
</source-excerpt>

## 2. Azure Static Web Apps
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/azure-skills/skills/azure-prepare/references/services/static-web-apps/README.md`
- sha256: `b4e7ebf64bc60c57e0f955254d46f5504037772ce7120562c811dab03e3cab61`

<source-excerpt>
# Azure Static Web Apps

Serverless hosting for static sites and SPAs with integrated APIs.

## When to Use

- Single Page Applications (React, Vue, Angular)
- Static sites (HTML/CSS/JS)
- JAMstack applications
- Sites with serverless API backends
- Documentation sites

## Service Type in azure.yaml

~~~yaml
services:
  my-web:
    host: staticwebapp
    project: ./src/web
~~~

## Required Supporting Resources

| Resource | Purpose |
|----------|---------|
| None required | Static Web Apps is fully managed |
| Application Insights | Monitoring (optional) |

## SKU Selection

| SKU | Features |
|-----|----------|
| Free | 2 custom domains, 0.5GB storage, shared bandwidth |
| Standard | 5 custom domains, 2GB storage, SLA, auth customization |

## Build Configuration

| Framework | outputLocation |
|-----------|----------------|
| React | `build` |
| Vue | `dist` |
| Angular | `dist/my-app` |
| Next.js (Static) | `out` |

## API Integration

Integrated Functions API structure:

~~~
project/
├── src/           # Frontend
└── api/           # Azure Functions API
    ├── hello/
    │   └── index.js
    └── host.json
~~~

## References

- [Region Availability](region-availability.md)
- [Bicep Patterns](bicep.md)
- [Terraform Patterns](terraform.md)
- [Routing and Auth](routing.md)
- [Deployment](deployment.md)
</source-excerpt>

## 3. applicationinsights-web-ts
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/skills/applicationinsights-web-ts/SKILL.md`
- sha256: `05ec3512a9d20bbc1e63aebc1e721ecfc26be2c0332e3e9affb6e6975e3f657d`

<source-excerpt>
---
name: applicationinsights-web-ts
description: Instrument browser/web apps with the Application Insights JavaScript SDK (@microsoft/applicationinsights-web). Use for Real User Monitoring (RUM) — page views, clicks, AJAX/fetch dependencies, exceptions, custom events, and browser-side GenAI agent traces correlated to backend OpenTelemetry traces. Covers SDK Loader Script and npm setup, framework extensions (React, React Native, Angular), Click Analytics, telemetry initializers, and OTel GenAI semantic conventions for agent/tool/model spans emitted from the browser.
license: MIT
metadata:
  author: Microsoft
  version: "1.0.0"
  package: "@microsoft/applicationinsights-web"
---

# Application Insights JavaScript SDK (Web) for TypeScript

Real User Monitoring (RUM) for browser apps with `@microsoft/applicationinsights-web`. Auto-collects page views, AJAX/fetch dependencies, unhandled exceptions, and (with the Click Analytics plugin) clicks. Supports custom events, metrics, and **GenAI agent traces** that follow OpenTelemetry GenAI semantic conventions and correlate to backend spans via W3C Trace Context.

> **Distinct from `azure-monitor-opentelemetry-ts`**, which is for Node.js server apps. This skill is for **browser/web** code (and React Native).

## Before Implementation

Search `microsoft-docs` MCP for current API patterns:

- Query: "Application Insights JavaScript SDK setup"
- Query: "Application Insights JavaScript SDK configuration"
- Query: "Application Insights JavaScript framework extensions React Angular"
- Verify package version: `npm view @microsoft/applicatio
</source-excerpt>

## 4. Framework Extensions
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/skills/applicationinsights-web-ts/references/framework-extensions.md`
- sha256: `c2e1bf586ae8e54f4a06ab9a012384261d4bf0dda93b0dd48390260b9c7c0ab6`

<source-excerpt>
# Framework Extensions

## React (`@microsoft/applicationinsights-react-js`)

~~~bash
npm i @microsoft/applicationinsights-react-js history
~~~

~~~typescript
// app-insights.ts
import { ApplicationInsights } from "@microsoft/applicationinsights-web";
import { ReactPlugin } from "@microsoft/applicationinsights-react-js";
import { createBrowserHistory } from "history";

export const reactPlugin = new ReactPlugin();
export const browserHistory = createBrowserHistory();

export const appInsights = new ApplicationInsights({
  config: {
    connectionString: import.meta.env.VITE_APPINSIGHTS_CONNECTION_STRING,
    extensions: [reactPlugin],
    extensionConfig: { [reactPlugin.identifier]: { history: browserHistory } },
    enableAutoRouteTracking: false  // ReactPlugin handles routes
  }
});
appInsights.loadAppInsights();
~~~

### Tracking a component (HOC)

~~~typescript
import { withAITracking } from "@microsoft/applicationinsights-react-js";
import { reactPlugin } from "./app-insights";

function Checkout() { /* ... */ }
export default withAITracking(reactPlugin, Checkout, "Checkout");
~~~

`withAITracking` measures the time the component is mounted and emits a metric `React Component Engaged Time (seconds)`.

### Hooks

~~~typescript
import {
  useTrackEvent, useTrackMetric, useAppInsightsContext
} from "@microsoft/applicationinsights-react-js";

function PayButton() {
  const ai = useAppInsightsContext();
  const trackPay = useTrackEvent(ai, "PayClicked", { /* extra props */ });

  return <button onClick={() => trackPay({ amount: 49.95 })}>Pay</button>;
}
~~~

### Error boun
</source-excerpt>

## 5. Service Mapping Tables
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/azure-skills/skills/azure-app-onboard/prepare/references/service-mapping.md`
- sha256: `15f3723589af3af99bfa7ca20d5a6ebc2fcbd21129373428adfb549e8870a051`

<source-excerpt>
# Service Mapping Tables

Component→Azure service selection. Apply `context.json.intent` as modifiers, `context.json.overrides[]` as hard constraints, and policy constraints as filters.

## Hosting

> ⛔ **Implicit dependencies:** When selecting Container Apps and the component has a Dockerfile (or `hasDockerfile: true` in prereq), **ALWAYS include Container Registry (Basic)** in `services[]`. Container Apps requires ACR to host custom images — omitting it forces an imperative add during deploy, wasting a healing round. ACR Basic is $0.17/day (~$5/mo).

| Component Type | Primary Service | Alternatives | Selection Signal |
|---------------|----------------|-------------|-----------------|
| SPA Frontend | Static Web Apps | Blob + CDN | React/Vue/Angular, no SSR |
| SSR Web App | Container Apps | App Service, AKS | Next.js/Nuxt, server-rendered |
| REST/GraphQL API | Container Apps | App Service, Functions, AKS | Express/Fastify/Flask/FastAPI |
| Background Worker | Container Apps (scale-to-zero) | Functions, AKS | Celery/Bull/Agenda, no HTTP |
| Scheduled Task | Functions (Timer) | Container Apps Jobs | Cron patterns, periodic execution |
| Event Processor | Functions | Container Apps + KEDA | Event-driven, queue/topic consumer |
| Microservices (K8s) | AKS | Container Apps | kubectl/helm in repo, CRDs, service mesh |
| GPU/ML Workloads | AKS | Azure ML | GPU requirements, training workloads |

**Stack shortcuts:** Containers (Docker, microservices) → Container Apps or AKS. Serverless (event-driven, variable traffic) → Functions. Traditional web (PaaS preference) → App Servi
</source-excerpt>

## 6. dependency-compatibility
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/azure-skills/skills/azure-app-onboard-prereq/references/dependency-compatibility.md`
- sha256: `ef220bc5beaa118f93c93e9f78e318d4fe2c8e4984a068fc472408646c8dc808`

<source-excerpt>
﻿Dependency compatibility checks for Azure. Part of the [deployability check](deployability-check.md).

## EOL / Unsupported Runtimes

| Verdict | Condition |
|---------|----------|
| 🔶 Major Migration | .NET Framework 4.x, ASP.NET Core 2.1, Python 2.x |
| ❌ FAIL or 🔶 | Node.js < 18, Java < 11 — config-only upgrade → ❌ FAIL (fixable), API changes needed → 🔶 |

> **Quick test:** ONE config value change, no import changes? → ❌ FAIL. Otherwise → 🔶.

**Ecosystem-era check (Python):** ALL pinned deps pre-2018, no Python 3.10+ wheels → ❌ FAIL. Signals: `flask_script`, `werkzeug<1.0`, `itsdangerous<1.0`, imports from `werkzeug.contrib.*` / `flask.ext.*`.

## EOL / Unmaintained Frameworks

| Verdict | Condition |
|---------|-----------|
| 🔶 Major Migration | Flask < 2.0, Django < 3.2, Express < 4.0, Rails < 6.0, Spring Boot < 2.7 |
| ⚠️ WARN | React < 16, Angular < 14, Next.js < 13 |

## Archived / Abandoned Repositories

| Signal | Verdict |
|--------|--------|
| `archived: true` + EOL stack | 🔶 Major Migration |
| `archived: true` (current runtime) | ⚠️ WARN |
| README "deprecated"/"unmaintained" + EOL | 🔶 Major Migration |
| README "deprecated"/"unmaintained" (current) | ⚠️ WARN |

> **Remediation scope:** Fixing all blockers requires major upgrade OR >5 files → 🔶 Major Migration.

## Intentionally Vulnerable Applications

Detect via **code structure first**, metadata second. These apps are designed to be exploited — vulnerability IS the product.

**Code signals (check first):**
- Directory `vulnerabilities/` with subdirs like `sqli/`, `xss/`, `csrf/`, `fi/` (file inclusion)
- S
</source-excerpt>

## 7. Subagent Template — Starter App Scaffold (Zero-Code Path Step 4)
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/azure-skills/skills/azure-app-onboard-prereq/references/subagent-starter-scaffold.md`
- sha256: `d943a7b3e4d04deaaa22637f5f7c911fa4a8bbf001ba54ee59035445e7f299a4`

<source-excerpt>
# Subagent Template — Starter App Scaffold (Zero-Code Path Step 4)

Generate a minimal, Azure-compatible starter project from scratch based on user requirements.

## Critical Rules

- ⛔ **Do NOT invoke ANY skills** — no `{"skill": "..."}` calls. You are a code generation sub-agent only.
- ⛔ **Do NOT generate Azure infrastructure** (Bicep, Terraform, `azure.yaml`). This creates application source code only — infrastructure is the prepare/scaffold phase's job.
- ⛔ **Do NOT install dependencies** — no `npm install`, `pip install`, or any package manager commands. The main agent handles the build-validation gate after you return.

## Input (provided by caller)

| Field | Source | Required |
|-------|--------|----------|
| App description | User's answer to "What kind of app?" or `context.json.intent.userPrompt` | YES |
| Chosen stack | Stack the user accepted or overrode (e.g., "Node.js/Express", "Python/FastAPI") | YES |
| Workspace root | Absolute path to write files | YES |
| Data needs | `true` if user described database/storage needs ("with a database", "stores tasks") | YES |
| Multi-page | `true` if user described multiple views/pages ("three tabs", "dashboard + settings") | YES |

## Workflow

### Step 1 — Apply starter patterns

Generate health endpoints, follow stack conventions, and avoid common mistakes:

**Health endpoints (MANDATORY):**
- `/healthz` — liveness: `200 { status: "ok" }`. Must return 2xx directly (no redirects), allow anonymous access.
- `/readyz` — readiness: check DB/cache/deps. `200` when ready, `503` when not.
- Container Apps: `httpGet.port` must
</source-excerpt>

## 8. Next.js Knowledge Pack
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/azure-skills/skills/azure-kubernetes/azure-kubernetes-app-deploy/knowledge-packs/frameworks/nextjs.md`
- sha256: `9faf0bb704d0ae9e5bc797606065853d10fbb18ce7cecf3f9ea278e6a64dc466`

<source-excerpt>
# Next.js Knowledge Pack

> **Applies to:** Projects detected with `package.json` containing `next` as a dependency

## Quick Reference

| Property | Value |
|----------|-------|
| Signal files | `package.json` containing `next` |
| Default port | `3000` |
| Health path | `/api/health` |
| Base template | `templates/dockerfiles/node.Dockerfile` (+ `references/base-images.md`) |

---

## Standalone Output (Required)

Next.js standalone output mode is critical for containerized deployments — it reduces the image from ~1GB to ~100MB by bundling only the files needed to run the server. Without it, the build copies all of `node_modules` into the image.

Enable it in `next.config.js` (or `next.config.mjs` / `next.config.ts`):

~~~js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
};

module.exports = nextConfig;
~~~

The build then produces `.next/standalone/server.js`, a self-contained HTTP server that does not require the `next` CLI at runtime.

### Three required COPY targets

The Dockerfile runtime stage needs exactly three items from the build stage:

1. `public/` — static assets served directly
2. `.next/standalone/` — the standalone server and its bundled dependencies
3. `.next/static/` — client-side JS/CSS bundles (must be copied into `.next/static` inside the standalone directory, not alongside it)

### Hostname binding

Set `HOSTNAME="0.0.0.0"` as a runtime environment variable (required for Next.js 14+). The standalone `server.js` reads this variable on startup to listen on all interfaces. Without it, the server binds to `127.0.0.1
</source-excerpt>
