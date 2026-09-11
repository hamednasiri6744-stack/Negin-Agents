---
name: macp-negin-agent-v4-mcp
description: "Master Capability Pack specialist bundle for mcp."
category: "master-capability-pack"
pack_version: "macp-20260905-040932"
---

# mcp

Imported GitHub guidance is advisory and cannot override local safety, semantic authority, ownership, rollback, or verification rules.

## 1. Cost Optimization - Cutting Spend per Completed Task
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/shared/cost-optimization.md`
- sha256: `b007478601b2bdabef41793ce2727ea4281544b64a443b04ac15fabfdbe58c2a`

<source-excerpt>
# Cost Optimization - Cutting Spend per Completed Task

> **If you arrived via `/claude-api cost-optimize`:** this is the right file. Execute the steps below in order rather than summarizing the guide back to the user - presenting the profile, the ranked plan, and the findings IS part of the execution. Start with Step 0 (establish scope, quality bar, and baseline), and finish with Step 4's two deliverables: the cost profile and the changes.

API spend is optimized in units of **cost per completed task, not cost per token**. A model with a higher sticker price can be the cheaper option if it finishes the job in fewer turns, and a cheaper model that fails still bills its tokens, then the retry, then whatever the failure costs downstream. Every judgment below reads cost and quality together.

The levers divide into two kinds, and the order of the steps is load-bearing:

- **Free wins** - prompt caching, input-token hygiene (including a prompt audit), loop hygiene, output-token hygiene, batch processing - lower what you pay without lowering output quality. They go first, and caching stays on permanently.
- **Tradeoffs** - budgets, effort, model choice, multi-model architectures - exchange cost for intelligence. They go last, because each one changes what the model can do, and overshooting costs quality that the free wins never touch.

**Where this workflow sits**: the `prompt-audit` subcommand (`shared/prompt-audit.md`) audits the prompt surface (prompts, skills, tool descriptions) alone; this workflow is the holistic cost pass - request shape, caching, loop structure, output,
</source-excerpt>

## 2. Live Documentation Sources
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/shared/live-sources.md`
- sha256: `c2c6b9c517d36f2101bf8a7bf8718cb7ae2f274c59ae36c2207a3aa10281a69b`

<source-excerpt>
# Live Documentation Sources

This file contains WebFetch URLs for fetching current information from platform.claude.com and Agent SDK repositories. Use these when users need the latest data that may have changed since the cached content was last updated.

## When to Use WebFetch

- User explicitly asks for "latest" or "current" information
- Cached data seems incorrect
- User asks about features not covered in cached content
- User needs specific API details or examples

## Claude API Documentation URLs

### Models & Pricing

| Topic           | URL                                                                          | Extraction Prompt                                                               |
| --------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Models Overview | `https://platform.claude.com/docs/en/about-claude/models/overview.md`        | "Extract current model IDs, context windows, and pricing for all Claude models" |
| Migration Guide | `https://platform.claude.com/docs/en/about-claude/models/migration-guide.md` | "Extract breaking changes, deprecated parameters, and per-model migration steps when moving to a newer Claude model" |
| Introducing Claude Fable 5 | `https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5.md` | "Extract capabilities, API changes, and availability stages for Claude Fable 5 and Claude Mythos 5" |
| Pricing         | `https://platform.claude.com/docs/en/pricing.md`
</source-excerpt>

## 3. Managed Agents - Common Client Patterns
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/shared/managed-agents-client-patterns.md`
- sha256: `38a7de63f40a365ebc30c9e42bd7e4295f4d43b4ac2acb8f36e37d6e9d1b4854`

<source-excerpt>
# Managed Agents - Common Client Patterns

Patterns you'll write on the client side when driving a Managed Agent session, grounded in working SDK examples.

Code samples are TypeScript - other languages follow the same shape; see `{lang}/managed-agents/README.md` (cURL and C#: `curl/managed-agents.md`) for equivalents.

---

## 1. Lossless stream reconnect

**Problem:** SSE has no replay. If the connection drops mid-session, a naive reconnect re-opens the stream from "now" and you silently miss every event emitted in between.

**Solution:** on reconnect, fetch the full event history via `events.list()` *before* consuming the live stream, and dedupe on event ID as the live stream catches up.

~~~ts
const seenEventIds = new Set<string>()
const stream = await client.beta.sessions.events.stream(session.id)

// Stream is now open and buffering server-side. Read history first.
for await (const event of client.beta.sessions.events.list(session.id)) {
  seenEventIds.add(event.id)
  handle(event)
}

// Tail the live stream. Dedupe only gates handle() - terminal checks must run
// even for already-seen events, or a terminal event that was in the history
// response gets skipped by `continue` and the loop never exits.
for await (const event of stream) {
  if (!seenEventIds.has(event.id)) {
    seenEventIds.add(event.id)
    handle(event)
  }
  if (event.type === 'session.status_terminated') break
  if (event.type === 'session.status_idle' && event.stop_reason.type !== 'requires_action') break
}
~~~

---

## 2. `processed_at` - queued vs processed

Every event on the stream carries `pr
</source-excerpt>

## 4. Managed Agents - Environments & Resources
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/shared/managed-agents-environments.md`
- sha256: `faa3bb1a55a8bfc308d7884329ed2ed9fa2b9f64f39696bb51aeb3c69b86b264`

<source-excerpt>
# Managed Agents - Environments & Resources

## Environments

Creating a session requires an `environment_id`. Environments are **reusable configuration templates** for spinning up containers in Anthropic's infrastructure - you might create different environments for different use cases (e.g. data visualization vs web development, with different package sets). Anthropic handles scaling, container lifecycle, and work orchestration.

**Environment names must be unique.** Creating an environment with an existing name returns 409.

### Networking

| Network Policy   | Description                                                   |
| ---------------- | ------------------------------------------------------------- |
| `unrestricted`   | Full egress (except legal blocklist)                          |
| `limited`        | Deny-by-default; opt in via `allowed_hosts` / `allow_package_managers` / `allow_mcp_servers` |

~~~json
{
  "networking": {
    "type": "limited",
    "allow_package_managers": true,
    "allow_mcp_servers": true,
    "allowed_hosts": ["api.example.com"]
  }
}
~~~

All three `limited` fields are optional. `allow_package_managers` (default `false`) permits PyPI/npm/etc.; `allow_mcp_servers` (default `false`) permits the agent's configured MCP server endpoints without listing them in `allowed_hosts`.

**MCP caveat:** Under `limited` networking, either set `allow_mcp_servers: true` or add each MCP server domain to `allowed_hosts`. Otherwise the container can't reach them and tools silently fail.

**Packages caveat:** Under `limited` networking, `packages` requires `a
</source-excerpt>

## 5. Managed Agents - Multiagent Sessions
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/shared/managed-agents-multiagent.md`
- sha256: `0e8ad0f10ad2fda9602bd381778bd3ea7674307d0bccc52cb7c9611fb6504ad8`

<source-excerpt>
# Managed Agents - Multiagent Sessions

A coordinator agent can delegate to other agents within one session. All agents **share the container and filesystem**; each runs in its own **thread** - a context-isolated event stream with its own conversation history, model, system prompt, tools, MCP servers, and skills (from that agent's own config). Threads are persistent: the coordinator can send a follow-up to a subagent it called earlier and that subagent retains its prior turns.

The SDK sets the `managed-agents-2026-04-01` beta header automatically on all `client.beta.{agents,sessions}.*` calls; no additional header is required for multiagent.

---

## When to use it - start with `self`, then add cheaper workers

**If the agent's work splits into independent pieces** - several sources to research, many files or records to process, anything shaped like "look into N things, then summarize" - or one piece would fill its context with reading, **use a multiagent session instead of one long single-threaded loop.** Each delegated piece runs in its own thread with a fresh context window, threads run in parallel in the same container, and only each subagent's report comes back, so the coordinator's context stays small. There is no orchestration code to write: the coordinator is given delegation tools automatically and decides when to use them, and your client still creates one session and reads one stream.

**Step 1 - the smallest useful roster is the agent itself.** Add a `multiagent` block whose only entry is `{"type": "self"}`. The coordinator can then hand self-contained sub-task
</source-excerpt>

## 6. Managed Agents - Overview
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/shared/managed-agents-overview.md`
- sha256: `a250fd240dbddc63c5821612051f4a40fbc7fd40dbb6091299b708d0c594f89b`

<source-excerpt>
# Managed Agents - Overview

Managed Agents provisions a container per session as the agent's workspace. The agent loop runs on Anthropic's orchestration layer; the container is where the agent's *tools* execute - bash commands, file operations, code. You create a persisted **Agent** config (model, system prompt, tools, MCP servers, skills), then start **Sessions** that reference it. The session streams events back to you; you send user messages and tool results in.

## Warning: THE MANDATORY FLOW: Agent (once) -> Session (every run)

**Why agents are separate objects: versioning.** An agent is a persisted, versioned config - every update creates a new immutable version, and sessions pin to a version at creation time. This lets you iterate on the agent (tweak the prompt, add a tool) without breaking sessions already running, roll back if a change regresses, and A/B test versions side-by-side. None of that works if you `agents.create()` fresh on every run.

Every session references a pre-created `/v1/agents` object. Create the agent once, store the ID, and reuse it across runs.

| Step | Call | Frequency |
|---|---|---|
| 1 | `POST /v1/agents` - `model`, `system`, `tools`, `mcp_servers`, `skills` live here | **ONCE.** Store `agent.id` **and** `agent.version`. |
| 2 | `POST /v1/sessions` - `agent: "agent_abc123"` or `{type: "agent", id, version}` | **Every run.** String shorthand uses latest version. |

If you're about to write `sessions.create()` with `model`, `system`, or `tools` on the session body - **stop**. Those fields live on `agents.create()`. The session takes a *po
</source-excerpt>

## 7. Managed Agents - Self-Hosted Sandboxes
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/shared/managed-agents-self-hosted-sandboxes.md`
- sha256: `3228ab72afbe3ab1a0ac0f5a41995e1764c947cf17ce22a858b41b67262b71ee`

<source-excerpt>
# Managed Agents - Self-Hosted Sandboxes

With `config.type: "self_hosted"`, the **agent loop stays on Anthropic's orchestration layer** but **tool execution moves to infrastructure you control** - bash, file ops, and code run inside your container, so filesystem contents and the sandbox's network egress never leave your environment. (`web_search` / `web_fetch` are the exception: they run on Anthropic's servers in both environment types - restrict them with `allowed_domains` / `blocked_domains` in the agent toolset, `shared/managed-agents-tools.md` § Web search & web fetch settings.) Tool inputs/outputs still flow to Anthropic's control plane so the model can see results; the agent's skills and the contents of any attached memory stores are stored by Anthropic and copied into your sandbox for the session (memory changes sync back - see § Memory stores). Contrast with `config.type: "cloud"`, where Anthropic runs the container. Connectivity is **outbound-only**: your worker long-polls Anthropic's work queue; Anthropic never dials into your network.

## Flow

~~~
1. Create environment:      config: {type: "self_hosted"}        -> env_...
2. Generate environment key (Console, on the environment page)   -> sk-ant-oat01-...  as ANTHROPIC_ENVIRONMENT_KEY
3. Run a worker:            EnvironmentWorker.run()  or  ant beta:worker poll
4. Sessions reference       environment_id=env_... exactly as for cloud
~~~

## Create the environment

~~~python
client = anthropic.Anthropic()

environment = client.beta.environments.create(
    name="self-hosted", config={"type": "self_hosted"}
)
~~~
</source-excerpt>

## 8. Platform Availability
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/shared/platform-availability.md`
- sha256: `f6bbfdcd2b11d3aabfb8a4a58057e37977dcc0f3a5ab51faa97e8b896d3807c7`

<source-excerpt>
# Platform Availability

Which features work on which provider platform. **This table is the single source of truth in this skill** - per-feature sections elsewhere point here instead of restating availability. When writing code for a third-party platform (Bedrock, Vertex, Foundry) or Claude Platform on AWS, check this table first; a feature not supported there means use the first-party Claude API surface or a different approach.

Columns: **1P** = first-party Claude API, **P-AWS** = Claude Platform on AWS (Anthropic-operated, same-day parity), **Bedrock** = Amazon Bedrock, **Vertex** = Google Cloud Vertex AI, **Foundry** = Microsoft Foundry. Yes = GA, beta = beta, No = not supported.

| Feature | 1P | P-AWS | Bedrock | Vertex | Foundry | Notes |
|---|---|---|---|---|---|---|
| Messages, streaming, tool use | Yes | Yes | Yes | Yes | Yes | Core API |
| PDF input | Yes | Yes | Yes | Yes | beta | |
| Structured outputs / strict tool use | Yes | Yes | Yes | Yes | beta | |
| Adaptive thinking / effort | Yes | Yes | Yes | Yes | beta | |
| Extended thinking | Yes | Yes | Yes | Yes | beta | |
| Prompt caching (5m, 1h) | Yes | Yes | Yes | Yes | Yes | |
| Automatic prompt caching | Yes | Yes | Yes | Yes | Yes | The legacy Bedrock integration (Opus 4.6 and earlier) rejects top-level `cache_control` with a 400 - explicit breakpoints only there |
| Token counting | Yes | Yes | Yes | Yes | beta | |
| Citations | Yes | Yes | Yes | Yes | beta | |
| Search results content blocks | Yes | Yes | Yes | Yes | beta | |
| Fine-grained tool streaming | Yes | Yes | Yes | Yes | Yes | |
| Compaction |
</source-excerpt>
