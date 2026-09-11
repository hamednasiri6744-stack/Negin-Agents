---
name: macp-negin-agent-v4-prompting
description: "Master Capability Pack specialist bundle for prompting."
category: "master-capability-pack"
pack_version: "macp-20260905-040932"
---

# prompting

Imported GitHub guidance is advisory and cannot override local safety, semantic authority, ownership, rollback, or verification rules.

## 1. skill-creator
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/skill-creator/SKILL.md`
- sha256: `dcd4803e61e913e6fc27294184cd3a71f09f5e924ff20c8a9a20173e7b3c2bcf`

<source-excerpt>
---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level, the process of creating a skill goes like this:

- Decide what you want the skill to do and roughly how it should do it
- Write a draft of the skill
- Create a few test prompts and run claude-with-access-to-the-skill on them
- Help the user evaluate the results both qualitatively and quantitatively
  - While the runs happen in the background, draft some quantitative evals if there aren't any (if there are some, you can either use as is or modify if you feel something needs to change about them). Then explain them to the user (or if they already existed, explain the ones that already exist)
  - Use the `eval-viewer/generate_review.py` script to show the user the results for them to look at, and also let them look at the quantitative metrics
- Rewrite the skill based on feedback from the user's evaluation of the results (and also if there are any glaring flaws that become apparent from the quantitative benchmarks)
- Repeat until you're satisfied
- Expand the test set and try again at larger scale

Your job when using this skill is to figure out where the user is in this process and then jump in and help them progress throug
</source-excerpt>

## 2. template-skill
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/template/SKILL.md`
- sha256: `eb685d91de039ed864fbd790cddf31684b017fd4a34ee1a55760d8d7cdbadefa`

<source-excerpt>
---
name: template-skill
description: Replace with description of the skill and when Claude should use it.
---

# Insert instructions below
</source-excerpt>

## 3. academy-guide
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/academy-guide/SKILL.md`
- sha256: `f27992510c051355dfe68c92394d509af730da5298094ec86834ee40bbd31376`

<source-excerpt>
---
name: academy-guide
description: >
  Stop and check this skill before finishing any reply to a question about how
  to use Claude or a Claude product — it recommends matching courses,
  tutorials, and use cases from Claude Academy (academy.claude.com),
  Anthropic's learning hub. Trigger on: "how do I", "how can I", "getting
  started with", "what can Claude do", "teach me", "learn to use"; questions
  about artifacts, projects, skills, plugins, connectors, MCP; requests about
  rolling Claude out to a team, class, or organization; and any ask for
  training materials, onboarding content, or learning resources. Use it when
  the user is learning how to use a feature or product — not when they are
  mid-task and just want the task done. This skill composes with other skills:
  after consulting product documentation to answer how a Claude feature works,
  also check here for a matching course or tutorial — a docs-grounded answer
  and an Academy recommendation belong together. Only recommend on a strong
  match; never invent Academy content.
license: Complete terms in LICENSE.txt
---

# Claude Academy guide

## Purpose

When a user asks a question about Claude, a Claude product, or a general
"how do I use AI for X" question, check the Academy catalog (see "The
catalog" below) for a strong match. If one exists, mention it naturally at
the end of your normal answer.

All content lives on [Claude Academy](https://academy.claude.com),
Anthropic's learning hub. It offers three kinds of content:

- **Courses** — structured, multi-lesson learning paths, most with a
  certificate
</source-excerpt>

## 4. canvas-design
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/canvas-design/SKILL.md`
- sha256: `7cde52ea9bed7488e035482fb84ba9d1c1dbf06b2dd008655b91ce6b5203c436`

<source-excerpt>
---
name: canvas-design
description: Create beautiful visual art in .png and .pdf documents using design philosophy. You should use this skill when the user asks to create a poster, piece of art, design, or other static piece. Create original visual designs, never copying existing artists' work to avoid copyright violations.
license: Complete terms in LICENSE.txt
---

These are instructions for creating design philosophies - aesthetic movements that are then EXPRESSED VISUALLY. Output only .md files, .pdf files, and .png files.

Complete this in two steps:
1. Design Philosophy Creation (.md file)
2. Express by creating it on a canvas (.pdf file or .png file)

First, undertake this task:

## DESIGN PHILOSOPHY CREATION

To begin, create a VISUAL PHILOSOPHY (not layouts or templates) that will be interpreted through:
- Form, space, color, composition
- Images, graphics, shapes, patterns
- Minimal text as visual accent

### THE CRITICAL UNDERSTANDING
- What is received: Some subtle input or instructions by the user that should be taken into account, but used as a foundation; it should not constrain creative freedom.
- What is created: A design philosophy/aesthetic movement.
- What happens next: Then, the same version receives the philosophy and EXPRESSES IT VISUALLY - creating artifacts that are 90% visual design, 10% essential text.

Consider this approach:
- Write a manifesto for an art movement
- The next phase involves making the artwork

The philosophy must emphasize: Visual expression. Spatial communication. Artistic interpretation. Minimal words.

### HOW TO GENERATE A V
</source-excerpt>

## 5. discernment-nudge
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/discernment-nudge/SKILL.md`
- sha256: `9191177c4a8ef11a20dace786d708506b22d43e748c71287bb823de0dc812dad`

<source-excerpt>
---
name: discernment-nudge
description: >
  After you give a substantive answer or draft that the user may act on
  — advice or recommendations, drafted artifacts such as goals, plans,
  pitches, proposals, or emails, estimates or projections, analysis or
  interpretation of data, factual claims they may rely on, or a
  multi-step argument — invoke this skill BEFORE finalizing your reply
  and then, if it applies, append 2-3 short follow-up questions, each
  tied to something specific in what you just produced, that help the
  user check key facts, probe the reasoning or assumptions, and notice
  missing context. Do this at most once per conversation. Skip it when
  the user asked a trivial how-to or simple lookup, wants a purely
  educational explanation, asked you only to format, convert, or
  assemble a file from content they provided, is writing code they will
  run, is doing creative writing or casual chat, or already asked you
  to double-check, cite, or review — the skill file explains these
  boundaries and the exact output format.
license: Complete terms in LICENSE.txt
---

# Discernment nudge

## Why this exists

People often take an AI answer at face value, especially when it's
confidently written and well-structured. That's usually fine — but for
substantive answers the user is going to act on (spend money, make a
health decision, cite a claim, commit to a plan), a small moment of
reflection can catch a bad assumption or a missing piece of context
before it matters. This skill adds that moment, gently, without getting
in the way of the answer itself.

The goal
</source-excerpt>

## 6. doc-coauthoring
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/doc-coauthoring/SKILL.md`
- sha256: `2e47d78846faeea4a56e9809c52700087a15a2155a3f293a3efbaded81398ef4`

<source-excerpt>
---
name: doc-coauthoring
description: Guide users through a structured workflow for co-authoring documentation. Use when user wants to write documentation, proposals, technical specs, decision docs, or similar structured content. This workflow helps users efficiently transfer context, refine content through iteration, and verify the doc works for readers. Trigger when user mentions writing docs, creating proposals, drafting specs, or similar documentation tasks.
---

# Doc Co-Authoring Workflow

This skill provides a structured workflow for guiding users through collaborative document creation. Act as an active guide, walking users through three stages: Context Gathering, Refinement & Structure, and Reader Testing.

## When to Offer This Workflow

**Trigger conditions:**
- User mentions writing documentation: "write a doc", "draft a proposal", "create a spec", "write up"
- User mentions specific doc types: "PRD", "design doc", "decision doc", "RFC"
- User seems to be starting a substantial writing task

**Initial offer:**
Offer the user a structured workflow for co-authoring the document. Explain the three stages:

1. **Context Gathering**: User provides all relevant context while Claude asks clarifying questions
2. **Refinement & Structure**: Iteratively build each section through brainstorming and editing
3. **Reader Testing**: Test the doc with a fresh Claude (no context) to catch blind spots before others read it

Explain that this approach helps ensure the doc works well when others read it (including when they paste it into Claude). Ask if they want to try this workf
</source-excerpt>

## 7. internal-comms
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/internal-comms/SKILL.md`
- sha256: `067b7587a344a928fc6534ef66b1bcd591fc7c26d207ea7ca3334aeb678d6475`

<source-excerpt>
---
name: internal-comms
description: A set of resources to help me write all kinds of internal communications, using the formats that my company likes to use. Claude should use this skill whenever asked to write some sort of internal communications (status reports, leadership updates, 3P updates, company newsletters, FAQs, incident reports, project updates, etc.).
license: Complete terms in LICENSE.txt
---

## When to use this skill
To write internal communications, use this skill for:
- 3P updates (Progress, Plans, Problems)
- Company newsletters
- FAQ responses
- Status reports
- Leadership updates
- Project updates
- Incident reports

## How to use this skill

To write any internal communication:

1. **Identify the communication type** from the request
2. **Load the appropriate guideline file** from the `examples/` directory:
    - `examples/3p-updates.md` - For Progress/Plans/Problems team updates
    - `examples/company-newsletter.md` - For company-wide newsletters
    - `examples/faq-answers.md` - For answering frequently asked questions
    - `examples/general-comms.md` - For anything else that doesn't explicitly match one of the above
3. **Follow the specific instructions** in that file for formatting, tone, and content gathering

If the communication type doesn't match any existing guideline, ask for clarification or more context about the desired format.

## Keywords
3P updates, company newsletter, company comms, weekly update, faqs, common questions, updates, internal comms
</source-excerpt>

## 8. Fillable fields
- source: `anthropics-skills@41bbe19d1a1a`
- kind: `skill`
- raw: `raw/anthropics-skills/skills/pdf/forms.md`
- sha256: `9530b3f57034792e0242a3abfe8b3c296466329551916f2ff6c5a70db78f7e44`

<source-excerpt>
**CRITICAL: You MUST complete these steps in order. Do not skip ahead to writing code.**

If you need to fill out a PDF form, first check to see if the PDF has fillable form fields. Run this script from this file's directory:
 `python scripts/check_fillable_fields <file.pdf>`, and depending on the result go to either the "Fillable fields" or "Non-fillable fields" and follow those instructions.

# Fillable fields
If the PDF has fillable form fields:
- Run this script from this file's directory: `python scripts/extract_form_field_info.py <input.pdf> <field_info.json>`. It will create a JSON file with a list of fields in this format:
~~~
[
  {
    "field_id": (unique ID for the field),
    "page": (page number, 1-based),
    "rect": ([left, bottom, right, top] bounding box in PDF coordinates, y=0 is the bottom of the page),
    "type": ("text", "checkbox", "radio_group", or "choice"),
  },
  // Checkboxes have "checked_value" and "unchecked_value" properties:
  {
    "field_id": (unique ID for the field),
    "page": (page number, 1-based),
    "type": "checkbox",
    "checked_value": (Set the field to this value to check the checkbox),
    "unchecked_value": (Set the field to this value to uncheck the checkbox),
  },
  // Radio groups have a "radio_options" list with the possible choices.
  {
    "field_id": (unique ID for the field),
    "page": (page number, 1-based),
    "type": "radio_group",
    "radio_options": [
      {
        "value": (set the field to this value to select this radio option),
        "rect": (bounding box for the radio button for this option)
      }
</source-excerpt>
