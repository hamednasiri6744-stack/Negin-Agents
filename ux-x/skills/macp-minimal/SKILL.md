---
name: macp-ux-x-minimal
description: "Master Capability Pack specialist bundle for minimal."
category: "master-capability-pack"
pack_version: "macp-20260905-040932"
---

# minimal

Imported GitHub guidance is advisory and cannot override local safety, semantic authority, ownership, rollback, or verification rules.

## 1. frontend-design
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/frontend-design/SKILL.md`
- sha256: `d91970639e9f5c37682ac7ab60094d35f1c7c1f38d731bd56396563aee10c1d3`

<source-excerpt>
---
name: frontend-design
description: Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one. Helps with aesthetic direction, typography, and making choices that don't read as templated defaults.
license: Complete terms in LICENSE.txt
---

# Frontend Design

Approach this as the design lead at a design studio known for giving every client a distinct visual identity that is not mistaken for anyone else's. This client has already rejected proposals that felt cliché or templated, and is paying for a distinctive point of view: make deliberate, opinionated choices about palette, typography, and layout that are specific to this brief, and take aesthetic risk if justified.

## Ground your designs in the subject matter

If the brief does not identify what the product or subject matter is, identify it yourself before designing, and confirm with the client. You can come up with one concrete subject, the design's audience, and the design's primary job, as a proposal. If there's any information in your memory about the client's preferences or context about what they're building, use that as a hint. The subject's industry, subject matter, materials, and vernacular are where distinctive visual choices come from — a design for a toy for girls aged 8–11 will be very aesthetically different from a dashboard for financial analysts. Build with the brief's real content and subject matter throughout.

## Design principles

For web designs, the hero is the first thing viewers will see. Open with the most characteristic thing in the subject's world,
</source-excerpt>

## 2. algorithmic-art
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/algorithmic-art/SKILL.md`
- sha256: `c7b82d7256e936e1e0b31499156b0a1b8d8cd4ac837c81b2ccb48524c700b405`

<source-excerpt>
---
name: algorithmic-art
description: Creating algorithmic art using p5.js with seeded randomness and interactive parameter exploration. Use this when users request creating art using code, generative art, algorithmic art, flow fields, or particle systems. Create original algorithmic art rather than copying existing artists' work to avoid copyright violations.
license: Complete terms in LICENSE.txt
---

Algorithmic philosophies are computational aesthetic movements that are then expressed through code. Output .md files (philosophy), .html files (interactive viewer), and .js files (generative algorithms).

This happens in two steps:
1. Algorithmic Philosophy Creation (.md file)
2. Express by creating p5.js generative art (.html + .js files)

First, undertake this task:

## ALGORITHMIC PHILOSOPHY CREATION

To begin, create an ALGORITHMIC PHILOSOPHY (not static images or templates) that will be interpreted through:
- Computational processes, emergent behavior, mathematical beauty
- Seeded randomness, noise fields, organic systems
- Particles, flows, fields, forces
- Parametric variation and controlled chaos

### THE CRITICAL UNDERSTANDING
- What is received: Some subtle input or instructions by the user to take into account, but use as a foundation; it should not constrain creative freedom.
- What is created: An algorithmic philosophy/generative aesthetic movement.
- What happens next: The same version receives the philosophy and EXPRESSES IT IN CODE - creating p5.js sketches that are 90% algorithmic generation, 10% essential parameters.

Consider this approach:
- Write a man
</source-excerpt>

## 3. Check SKILL.md exists
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/skill-creator/scripts/quick_validate.py`
- sha256: `faf8532dbfa0cb55780a126213ce0017a6790afe26667ccd5b33a12a742e183e`

<source-excerpt>
#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
"""

import sys
import os
import re
import yaml
from pathlib import Path

def validate_skill(skill_path):
    """Basic validation of a skill"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text()
    if not content.startswith('---'):
        return False, "No YAML frontmatter found"

    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter_text = match.group(1)

    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    # Define allowed properties
    ALLOWED_PROPERTIES = {'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility'}

    # Check for unexpected properties (excluding nested keys under metadata)
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed properties are: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    # Check required fields
</source-excerpt>

## 4. Azure Web PubSub Java SDK - Examples
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/azure-sdk-java/skills/azure-messaging-webpubsub-java/references/examples.md`
- sha256: `e0c19cec089a61aed1720821f3ab52d664c2c8233e234c8252ad191940493d04`

<source-excerpt>
# Azure Web PubSub Java SDK - Examples

Comprehensive code examples for the Azure Web PubSub SDK for Java.

## Table of Contents
- [Maven Dependency](#maven-dependency)
- [Client Creation](#client-creation)
- [Send Messages](#send-messages)
- [Group Management](#group-management)
- [Connection Management](#connection-management)
- [Client Access Tokens](#client-access-tokens)
- [Permissions](#permissions)
- [Async Operations](#async-operations)
- [Complete Application Example](#complete-application-example)

## Maven Dependency

~~~xml
<dependency>
    <groupId>com.azure</groupId>
    <artifactId>azure-messaging-webpubsub</artifactId>
    <version>1.5.0</version>
</dependency>
~~~

## Client Creation

### With Connection String

~~~java
import com.azure.messaging.webpubsub.WebPubSubServiceClient;
import com.azure.messaging.webpubsub.WebPubSubServiceClientBuilder;

WebPubSubServiceClient client = new WebPubSubServiceClientBuilder()
    .connectionString(System.getenv("WEB_PUBSUB_CONNECTION_STRING"))
    .hub("chat")
    .buildClient();
~~~

### With DefaultAzureCredential

~~~java
import com.azure.identity.DefaultAzureCredentialBuilder;

WebPubSubServiceClient client = new WebPubSubServiceClientBuilder()
    .credential(new DefaultAzureCredentialBuilder().build())
    .endpoint(System.getenv("WEB_PUBSUB_ENDPOINT"))
    .hub("chat")
    .buildClient();
~~~

### With Access Key

~~~java
import com.azure.core.credential.AzureKeyCredential;

WebPubSubServiceClient client = new WebPubSubServiceClientBuilder()
    .credential(new AzureKeyCredential("<access-key>"))
    .endpoint("
</source-excerpt>

## 5. Checkpointing Reference
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/azure-sdk-typescript/skills/azure-eventhub-ts/references/checkpointing.md`
- sha256: `fcb3cc87352b1bbb32e477a180a755728b812ff15df9713d62eb215f5b92accd`

<source-excerpt>
# Checkpointing Reference

Persistent checkpointing with BlobCheckpointStore for Azure Event Hubs consumer applications.

## Overview

Checkpointing tracks the last successfully processed event position per partition. This enables:
- **Resumption** — Continue from where you left off after restart
- **Load balancing** — Distribute partitions across multiple consumers
- **Exactly-once processing** — When combined with idempotent downstream operations

## Installation

~~~bash
npm install @azure/event-hubs @azure/eventhubs-checkpointstore-blob @azure/storage-blob @azure/identity
~~~

## Key Interfaces

~~~typescript
import { CheckpointStore, Checkpoint, PartitionOwnership } from "@azure/event-hubs";

// CheckpointStore interface (implemented by BlobCheckpointStore)
interface CheckpointStore {
  listCheckpoints(
    fullyQualifiedNamespace: string,
    eventHubName: string,
    consumerGroup: string
  ): Promise<Checkpoint[]>;

  updateCheckpoint(checkpoint: Checkpoint): Promise<void>;

  listOwnership(
    fullyQualifiedNamespace: string,
    eventHubName: string,
    consumerGroup: string
  ): Promise<PartitionOwnership[]>;

  claimOwnership(
    partitionOwnership: PartitionOwnership[]
  ): Promise<PartitionOwnership[]>;
}

// Checkpoint structure
interface Checkpoint {
  fullyQualifiedNamespace: string;
  eventHubName: string;
  consumerGroup: string;
  partitionId: string;
  sequenceNumber: number;
  offset: string;
}

// Partition ownership (for load balancing)
interface PartitionOwnership {
  fullyQualifiedNamespace: string;
  eventHubName: string;
  consumerGroup: strin
</source-excerpt>

## 6. Example: evaluate a non-ATK project
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/microsoft-365-agents-toolkit/skills/m365-agent-evaluator/examples/not-atk-project.md`
- sha256: `561b687faeba871bcad879e2d57340be2b665cbc29c2b5bcdeea5d4e5b8e480b`

<source-excerpt>
# Example: evaluate a non-ATK project

User intent: "I do not have an Agents Toolkit project. Can I still evaluate a deployed agent?"

Yes. Use an explicit deployed agent ID through `M365_AGENT_ID` or `--m365-agent-id`.

## Suggested layout

~~~text
evals\evals.json
env\.env.dev
.evals\
~~~

Example `env\.env.dev` values:

~~~text
TENANT_ID=<tenant-guid>
M365_AGENT_ID=<deployed-agent-id>
AZURE_AI_OPENAI_ENDPOINT=<foundry-models-endpoint>
AZURE_AI_API_KEY: [REDACTED]
AZURE_AI_API_VERSION=2024-12-01-preview
AZURE_AI_MODEL_NAME=gpt-4o-mini
~~~

Do not print or commit this file if it contains secrets.

## Commands

~~~powershell
npx -y --package @microsoft/m365-copilot-eval@latest runevals --init-only --env dev
~~~

~~~powershell
npx -y --package @microsoft/m365-copilot-eval@latest runevals --prompts-file evals\evals.json --env dev --output .evals\non-atk.json
~~~

Explicit override:

~~~powershell
npx -y --package @microsoft/m365-copilot-eval@latest runevals --prompts-file evals\evals.json --m365-agent-id <agent-id> --env dev --output .evals\non-atk.json
~~~

## Minimal dataset

~~~json
{
  "schemaVersion": "1.2.0",
  "default_evaluators": {
    "Relevance": {},
    "Coherence": {}
  },
  "items": [
    {
      "prompt": "What can this agent help me with?",
      "expected_response": "The agent describes its supported scope."
    }
  ]
}
~~~

If auth, tenant consent, or model setup fails, resolve that before evaluating agent quality.
</source-excerpt>

## 7. shortcuts-extensions-ts
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/microsoft-365-agents-toolkit/skills/teams-app-developer/experts/bridge/shortcuts-extensions-ts.md`
- sha256: `b5cee52913a0f0befb258d67920b49fe7dd982110ce4775ca048ffe9693d6b0a`

<source-excerpt>
# shortcuts-extensions-ts

## purpose

Bridges Slack shortcuts (global and message) and Teams message extensions / compose extensions for cross-platform bots targeting Slack, Teams, or both.

## rules

1. **Slack global shortcuts → Teams action-based compose extensions with `context: ['compose', 'commandBox']`.** Slack global shortcuts appear in the lightning bolt menu and don't reference a specific message. In Teams, the equivalent is a compose extension with `fetchTask: true` and action context targeting the compose box and command bar. [learn.microsoft.com -- Action-based extensions](https://learn.microsoft.com/en-us/microsoftteams/platform/messaging-extensions/how-to/action-commands/define-action-command)
2. **Slack message shortcuts → Teams action-based extensions with `context: ['message']`.** Slack message shortcuts appear in the message context menu (⋮ → More actions). In Teams, action-based extensions with `context: ['message']` appear in the message overflow menu (... → More actions). The target message content is available in the invoke payload. [learn.microsoft.com -- Message context](https://learn.microsoft.com/en-us/microsoftteams/platform/messaging-extensions/how-to/action-commands/define-action-command#choose-action-command-invoke-locations)
3. **Slack `trigger_id` + `views.open()` → Teams `fetchTask: true` + task module.** Slack shortcuts use the `trigger_id` to open a modal. Teams action-based extensions use `fetchTask: true` in the manifest, which causes Teams to invoke the bot's `message.ext.open` handler to fetch the task module (dialog) content. No tri
</source-excerpt>

## 8. teams-dotnet
- source: `microsoft-skills@02e0b2f852b3`
- kind: `skill`
- raw: `raw/microsoft-skills/.github/plugins/microsoft-365-agents-toolkit/skills/teams-app-developer/experts/teams/teams-dotnet.md`
- sha256: `2da355f36160877441c9cd8412e94df19c6ef0a0dca3886719c7c821563ede14`

<source-excerpt>
# teams-dotnet

## purpose

Microsoft Teams SDK for .NET (C#) patterns — app initialization, activity handling, AI integration, and Adaptive Cards for Tier 3 C# projects.

## rules

1. Add the NuGet packages: `Microsoft.Teams.Apps`, `Microsoft.Teams.AI`, `Microsoft.Teams.AI.Models.OpenAI`, and `Microsoft.Teams.Plugins.AspNetCore`. The SDK targets **.NET 8+** and uses the modern minimal API pattern. [teams.net source: Libraries/]
2. Initialize with ASP.NET Core dependency injection: `builder.AddTeams()` registers core Teams services, then `app.UseTeams()` returns the `App` instance for handler registration. When no ClientId is configured, pass `skipAuth: true` to disable auth validation: `builder.AddTeams(skipAuth: true)`. This replaces the TS `Application.create()` pattern. [teams.net source: HostApplicationBuilder.cs]
3. Register activity handlers using fluent methods: `teams.OnMessage(async (context, ct) => { ... })`. Supports pattern matching: `teams.OnMessage(@"^hi$", async (context, ct) => { ... })`. Handlers are checked in registration order — first match wins. [teams.net source: App.cs]
4. All handlers receive `IContext<TActivity>` and `CancellationToken`. Access the activity via `context.Activity`, the API client via `context.Api`, storage via `context.Storage`, and logger via `context.Log`. This replaces the TS `TurnContext` pattern. [teams.net source: Context.cs]
5. Send messages with `await context.Send("text", ct)` or `await context.Reply("reply", ct)`. The `Send` method accepts strings, `ActivityParams`, or `AdaptiveCard` objects. For typing indicators, use `aw
</source-excerpt>
