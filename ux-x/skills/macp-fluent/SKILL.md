---
name: macp-ux-x-fluent
description: "Master Capability Pack specialist bundle for fluent."
category: "master-capability-pack"
pack_version: "macp-20260905-040932"
---

# fluent

Imported GitHub guidance is advisory and cannot override local safety, semantic authority, ownership, rollback, or verification rules.

## 1. teams-dotnet
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

## 2. fluentui-blazor
- source: `awesome-copilot@7b1ebe633339`
- kind: `skill`
- raw: `raw/awesome-copilot/skills/fluentui-blazor/SKILL.md`
- sha256: `d23fbc5dfb9a1580f930652bdfbf8c891edbaaa3bf162fb4904de9cba74f01b0`

<source-excerpt>
---
name: fluentui-blazor
description: >
  Guide for using the Microsoft Fluent UI Blazor component library
  (Microsoft.FluentUI.AspNetCore.Components NuGet package) in Blazor applications.
  Use this when the user is building a Blazor app with Fluent UI components,
  setting up the library, using FluentUI components like FluentButton, FluentDataGrid,
  FluentDialog, FluentToast, FluentNavMenu, FluentTextField, FluentSelect,
  FluentAutocomplete, FluentDesignTheme, or any component prefixed with "Fluent".
  Also use when troubleshooting missing providers, JS interop issues, or theming.
---

# Fluent UI Blazor — Consumer Usage Guide

This skill teaches how to correctly use the **Microsoft.FluentUI.AspNetCore.Components** (version 4) NuGet package in Blazor applications.

## Critical Rules

### 1. No manual `<script>` or `<link>` tags needed

The library auto-loads all CSS and JS via Blazor's static web assets and JS initializers. **Never tell users to add `<script>` or `<link>` tags for the core library.**

### 2. Providers are mandatory for service-based components

These provider components **MUST** be added to the root layout (e.g. `MainLayout.razor`) for their corresponding services to work. Without them, service calls **fail silently** (no error, no UI).

~~~razor
<FluentToastProvider />
<FluentDialogProvider />
<FluentMessageBarProvider />
<FluentTooltipProvider />
<FluentKeyCodeProvider />
~~~

### 3. Service registration in Program.cs

~~~csharp
builder.Services.AddFluentUIComponents();

// Or with configuration:
builder.Services.AddFluentUIComponents(options =>
{
</source-excerpt>

## 3. EF Core Model Extraction
- source: `awesome-copilot@7b1ebe633339`
- kind: `skill`
- raw: `raw/awesome-copilot/skills/efcore-d2-db-diagram/references/efcore-model-extraction.md`
- sha256: `68605a8487c4c56c01924a23ba2b1df37f5d02bebe6e1799e42f98b818d0fe17`

<source-excerpt>
# EF Core Model Extraction

## Files to inspect

Inspect, in this order:

1. `DbContext` classes.
2. `DbSet<T>` declarations.
3. `OnModelCreating`.
4. `IEntityTypeConfiguration<T>` classes.
5. Entity classes.
6. Migrations and model snapshot.
7. Data annotations.

## Mapping priority

When sources conflict, use:

1. Latest migration / model snapshot.
2. Fluent API.
3. Data annotations.
4. EF Core conventions.
5. C# shape.

## Important EF Core APIs

Look for:

- `ToTable`
- `HasKey`
- `HasAlternateKey`
- `HasIndex`
- `IsUnique`
- `Property`
- `HasColumnName`
- `HasColumnType`
- `IsRequired`
- `HasMaxLength`
- `HasConversion`
- `HasOne`
- `WithMany`
- `WithOne`
- `HasForeignKey`
- `OnDelete`
- `OwnsOne`
- `OwnsMany`
- `UsingEntity`
- `Ignore`

## Migrations

Use migrations to detect:

- Actual table names.
- Join tables.
- Shadow FK columns.
- Indexes.
- Composite keys.
- Delete behaviors.
- Migration-only tables.
</source-excerpt>

## 4. Quality Gate
- source: `awesome-copilot@7b1ebe633339`
- kind: `skill`
- raw: `raw/awesome-copilot/skills/efcore-d2-db-diagram/references/quality-gate.md`
- sha256: `6827076597373e65ed459d4f583219f7ec6f2dbcf3c9d18c2d59b0acd7105b06`

<source-excerpt>
# Quality Gate

Before delivery:

- Confirm the selected DbContext.
- Confirm source files inspected.
- Validate table names against Fluent API and migrations.
- Include primary keys.
- Include foreign keys.
- Include cardinalities.
- Include join tables unless hidden by user choice.
- Include owned types according to user choice.
- Hide technical tables only if configured and list them in the summary.
- Run `d2 fmt` when available.
- Use full dot-notation for edges inside containers.
- Provide render command.
</source-excerpt>

## 5. Design Profile Guidance
- source: `wshobson-agents@a30778f8c4e6`
- kind: `skill`
- raw: `raw/wshobson-agents/plugins/pptx-deck-creation/skills/pptx-deck-context/references/design-profiles.md`
- sha256: `84fe61ef59bc853556650f5a6d8165ed6d1e731248a7c8a9e8046e8dae5686f1`

<source-excerpt>
# Design Profile Guidance

Use a profile as design evidence, then lock its palette, typography, spacing, and signature element in `summary.design_context` before coordinate authoring.

| Profile | Best for | Signals |
| --- | --- | --- |
| `fluent-ui-design-tokens` | enterprise and Microsoft-aligned decks | restrained neutrals, clear hierarchy, token-based spacing, modest radii |
| `primer-primitives` | GitHub and developer-focused decks | crisp surfaces, strong text contrast, functional accents, compact labels |
| `editorial-minimal` | executive narrative and research decks | generous whitespace, high-contrast type, limited palette, one visual motif |

## Rules

- Prefer an explicit user brand guide. Otherwise use read-only reference-deck evidence, then a documented profile.
- Record profile ID, source URL when applicable, license information when known, and the resulting style lock.
- Use public design signals for inspiration only. Do not copy proprietary images, logos, fonts, screenshots, or slide content.
- Translate the lock into explicit `layout_tree` colors, fills, typography, rules, card shells, and bboxes.
</source-excerpt>
