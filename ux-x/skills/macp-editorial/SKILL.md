---
name: macp-ux-x-editorial
description: "Master Capability Pack specialist bundle for editorial."
category: "master-capability-pack"
pack_version: "macp-20260905-040932"
---

# editorial

Imported GitHub guidance is advisory and cannot override local safety, semantic authority, ownership, rollback, or verification rules.

## 1. LICENSE
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/claude-api/LICENSE.txt`
- sha256: `35f751188ae17bca4d5ff6523b1c589414433ecdac49e36d2d587b202e1bdaac`

<source-excerpt>
Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether
</source-excerpt>

## 2. premium-frontend-ui
- source: `awesome-copilot@7b1ebe633339`
- kind: `skill`
- raw: `raw/awesome-copilot/skills/premium-frontend-ui/SKILL.md`
- sha256: `7c256bc86b193d75e4c7e97ba35b66acbbeaa547acef2cfca2844bf9e73eaaff`

<source-excerpt>
---
name: premium-frontend-ui
description: 'A comprehensive guide for GitHub Copilot to craft immersive, high-performance web experiences with advanced motion, typography, and architectural craftsmanship.'
metadata:
  author: 'Utkarsh Patrikar'
  author_url: 'https://github.com/utkarsh232005'
---

# Immersive Frontend UI Craftsmanship

As an AI engineering assistant, your role when building premium frontend experiences goes beyond outputting functional HTML and CSS. You must architect **immersive digital environments**. This skill provides the blueprint for generating highly intentional, award-level web applications that prioritize aesthetic quality, deep interactivity, and flawless performance.

When a user requests a high-end landing page, an interactive portfolio, or a specialized component that requires top-tier visual polish, apply the following rigorous standards to every line of code you generate.

---

## 1. Establishing the Creative Foundation

Before generating layout code, ensure you understand the core emotional resonance the UI should deliver. Do not default to generic, unopinionated code.

Commit to a strong visual identity in your CSS and component structure:
- **Editorial Brutalism**: High-contrast monochromatic palettes, oversized typography, sharp rectangular edges, and raw grid structures.
- **Organic Fluidity**: Soft gradients, deeply rounded corners, glassmorphism overlays, and bouncy spring-based physics.
- **Cyber / Technical**: Dark mode dominance, glowing neon accents, monospaced typography, and rapid, staggered reveal animations.
- **Cinematic Paci
</source-excerpt>

## 3. Stitch Architecture Reference
- source: `wshobson-agents@a30778f8c4e6`
- kind: `skill`
- raw: `raw/wshobson-agents/plugins/brand-landingpage/skills/brand-landingpage/references/stitch-architecture.md`
- sha256: `ce5adc9d142721f5962e8a20d6da32674fe2e97f9cc1252db5e43dd0a6c59dfa`

<source-excerpt>
# Stitch Architecture Reference

Stable patterns for working with Stitch. This file covers concepts and taxonomies that remain consistent across SDK versions. For the current API surface (parameter names, return shapes, enum values), the authoritative source is the SDK repository linked in the Stitch Documentation section of SKILL.md.

---

## Stitch Conceptual Model

- **Project**: Top-level container. One project per landing page engagement. Contains screens and a design system.
- **Screen**: A single generated UI design. Has associated HTML and a screenshot, both available as download URLs. Edits produce new screen versions; originals are preserved and can be revisited.
- **Design System**: Project-wide visual tokens (colors, fonts, shapes, spacing). Applies consistently to all screens. Described in semantic language, not CSS.
- **Generation is asynchronous**: Screen generation can take 1-3 minutes. Do NOT retry a generation call if it seems slow. Use `get_screen` or `list_screens` to check completion status.
- **Assets are URLs**: Both `getHtml()` and `getImage()` return download URLs, not inline content. Download the files using whatever tools are available.
- **Namespace varies**: Stitch MCP tool names may be prefixed differently depending on the server configuration. Always discover the prefix via `list_tools` at startup.

---

## Font Personality Guide

Stitch supports 28 font enums. Use this guide to select fonts based on the brand personality established during the interview. Always select both a headline font and a body font.

### Modern / Clean Sans-Serif
For br
</source-excerpt>

## 4. Design Profile Guidance
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

## 5. seo-authority-builder
- source: `wshobson-agents@a30778f8c4e6`
- kind: `agent`
- raw: `raw/wshobson-agents/plugins/seo-analysis-monitoring/agents/seo-authority-builder.md`
- sha256: `fe33633ac96e76cf567f10abfbaf32eaf886e8e1a606c3e214ee10dee08fcf19`

<source-excerpt>
---
name: seo-authority-builder
description: Analyzes content for E-E-A-T signals and suggests improvements to build authority and trust. Identifies missing credibility elements. Use PROACTIVELY for YMYL topics.
model: sonnet
---

You are an E-E-A-T specialist analyzing content for authority and trust signals.

## Focus Areas

- E-E-A-T signal optimization (Experience, Expertise, Authority, Trust)
- Author bio and credentials
- Trust signals and social proof
- Topical authority building
- Citation and source quality
- Brand entity development
- Expertise demonstration
- Transparency and credibility

## E-E-A-T Framework

**Experience Signals:**

- First-hand experience indicators
- Case studies and examples
- Original research/data
- Behind-the-scenes content
- Process documentation

**Expertise Signals:**

- Author credentials display
- Technical depth and accuracy
- Industry-specific terminology
- Comprehensive topic coverage
- Expert quotes and interviews

**Authority Signals:**

- Authoritative external links
- Brand mentions and citations
- Industry recognition
- Speaking engagements
- Published research

**Trust Signals:**

- Contact information
- Privacy policy/terms
- SSL certificates
- Reviews/testimonials
- Security badges
- Editorial guidelines

## Approach

1. Analyze content for existing E-E-A-T signals
2. Identify missing authority indicators
3. Suggest author credential additions
4. Recommend trust elements
5. Assess topical coverage depth
6. Propose expertise demonstrations
7. Recommend appropriate schema

## Output

**E-E-A-T Enhancement Plan:**

~~~
Curren
</source-excerpt>
