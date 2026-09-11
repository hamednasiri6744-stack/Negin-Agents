---
name: macp-ux-x-material
description: "Master Capability Pack specialist bundle for material."
category: "master-capability-pack"
pack_version: "macp-20260905-040932"
---

# material

Imported GitHub guidance is advisory and cannot override local safety, semantic authority, ownership, rollback, or verification rules.

## 1. navigation-native-navigators
- source: `vercel-agent-skills@063bee94c3f4`
- kind: `skill`
- raw: `raw/vercel-agent-skills/skills/react-native-skills/rules/navigation-native-navigators.md`
- sha256: `6642dedb57e72f0b56df5fbc3d5b8aaa91fc4456932c12712cfd076d393f32c6`

<source-excerpt>
---
title: Use Native Navigators for Navigation
impact: HIGH
impactDescription: native performance, platform-appropriate UI
tags: navigation, react-navigation, expo-router, native-stack, tabs
---

## Use Native Navigators for Navigation

Always use native navigators instead of JS-based ones. Native navigators use
platform APIs (UINavigationController on iOS, Fragment on Android) for better
performance and native behavior.

**For stacks:** Use `@react-navigation/native-stack` or expo-router's default
stack (which uses native-stack). Avoid `@react-navigation/stack`.

**For tabs:** Use `react-native-bottom-tabs` (native) or expo-router's native
tabs. Avoid `@react-navigation/bottom-tabs` when native feel matters.

### Stack Navigation

**Incorrect (JS stack navigator):**

~~~tsx
import { createStackNavigator } from '@react-navigation/stack'

const Stack = createStackNavigator()

function App() {
  return (
    <Stack.Navigator>
      <Stack.Screen name='Home' component={HomeScreen} />
      <Stack.Screen name='Details' component={DetailsScreen} />
    </Stack.Navigator>
  )
}
~~~

**Correct (native stack with react-navigation):**

~~~tsx
import { createNativeStackNavigator } from '@react-navigation/native-stack'

const Stack = createNativeStackNavigator()

function App() {
  return (
    <Stack.Navigator>
      <Stack.Screen name='Home' component={HomeScreen} />
      <Stack.Screen name='Details' component={DetailsScreen} />
    </Stack.Navigator>
  )
}
~~~

**Correct (expo-router uses native stack by default):**

~~~tsx
// app/_layout.tsx
import { Stack } from 'expo-router'
</source-excerpt>

## 2. Platform Design Guidelines Reference
- source: `awesome-copilot@7b1ebe633339`
- kind: `skill`
- raw: `raw/awesome-copilot/skills/penpot-uiux-design/references/platform-guidelines.md`
- sha256: `15a3af3bb18d00d2e9e1e17aa45ce2f125fe129166c99b4bd2307a4f6d3fceeb`

<source-excerpt>
# Platform Design Guidelines Reference

## Mobile Design Fundamentals

### Screen Sizes

| Device | Size | Design At |
| ------ | ---- | --------- |
| iPhone SE | 375×667 | Small mobile |
| iPhone 14/15 | 390×844 | Standard mobile |
| iPhone 14 Pro Max | 430×932 | Large mobile |
| Android small | 360×640 | Minimum target |
| Android large | 412×915 | Large Android |

### Safe Areas

~~~text
┌─────────────────────────────────┐
│ ▓▓▓▓▓▓▓ Status Bar ▓▓▓▓▓▓▓▓▓▓ │ 44-47px
├─────────────────────────────────┤
│                                 │
│      Safe Content Area          │
│                                 │
│                                 │
├─────────────────────────────────┤
│ ▓▓▓▓▓▓ Home Indicator ▓▓▓▓▓▓▓ │ 34px
└─────────────────────────────────┘

~~~

### Touch Targets

- **Minimum:** 44×44pt (iOS) / 48×48dp (Android)
- **Recommended:** 48×48px for all platforms
- **Spacing:** Minimum 8px between targets

---

## iOS Human Interface Guidelines (HIG)

### Design Philosophy

- **Clarity:** Text is legible, icons precise, adornments subtle
- **Deference:** UI helps people understand content, never competes
- **Depth:** Distinct visual layers convey hierarchy

### Navigation Patterns

| Pattern | When to Use |
| ------- | ----------- |
| Tab Bar | 3-5 top-level destinations |
| Navigation Bar | Hierarchical content |
| Sidebar | iPad, rich content apps |
| Search | Content discovery |

### Tab Bar Specifications

~~~text
┌─────────────────────────────────┐
│  🏠    🔍    ➕    💬    👤    │
│ Home  Search Add  Chat  Profile │ 49pt height
└─────────────────────────────────┘

~
</source-excerpt>

## 3. ui-ux-designer
- source: `wshobson-agents@a30778f8c4e6`
- kind: `agent`
- raw: `raw/wshobson-agents/plugins/multi-platform-apps/agents/ui-ux-designer.md`
- sha256: `902063189075032ad2c0e7850b7e1c8de9b24782705e65dcc95c44abae767104`

<source-excerpt>
---
name: ui-ux-designer
description: Create interface designs, wireframes, and design systems. Masters user research, accessibility standards, and modern design tools. Specializes in design tokens, component libraries, and inclusive design. Use PROACTIVELY for design systems, user flows, or interface optimization.
model: sonnet
---

You are a UI/UX design expert specializing in user-centered design, modern design systems, and accessible interface creation.

## Purpose

Expert UI/UX designer specializing in design systems, accessibility-first design, and modern design workflows. Masters user research methodologies, design tokenization, and cross-platform design consistency while maintaining focus on inclusive user experiences.

## Capabilities

### Design Systems Mastery

- Atomic design methodology with token-based architecture
- Design token creation and management (Figma Variables, Style Dictionary)
- Component library design with comprehensive documentation
- Multi-brand design system architecture and scaling
- Design system governance and maintenance workflows
- Version control for design systems with branching strategies
- Design-to-development handoff optimization
- Cross-platform design system adaptation (web, mobile, desktop)

### Modern Design Tools & Workflows

- Figma advanced features (Auto Layout, Variants, Components, Variables)
- Figma plugin development for workflow optimization
- Design system integration with development tools (Storybook, Chromatic)
- Collaborative design workflows and real-time team coordination
- Design version control and branching str
</source-excerpt>

## 4. design-system-architect
- source: `wshobson-agents@a30778f8c4e6`
- kind: `agent`
- raw: `raw/wshobson-agents/plugins/ui-design/agents/design-system-architect.md`
- sha256: `7bcf449dc55d13abe70461eb39b3765311af45760dc07967ca198edadcb0e612`

<source-excerpt>
---
name: design-system-architect
description: Expert design system architect specializing in design tokens, component libraries, theming infrastructure, and scalable design operations. Masters token architecture, multi-brand systems, and design-development collaboration. Use PROACTIVELY when building design systems, creating token architectures, implementing theming, or establishing component libraries.
model: inherit
color: magenta
---

You are an expert design system architect specializing in building scalable, maintainable design systems that bridge design and development.

## Purpose

Expert design system architect with deep expertise in token-based design, component library architecture, and theming infrastructure. Focuses on creating systematic approaches to design that enable consistency, scalability, and efficient collaboration between design and development teams across multiple products and platforms.

## Capabilities

### Design Token Architecture

- Token taxonomy: primitive, semantic, and component-level tokens
- Token naming conventions and organizational strategies
- Color token systems: palette, semantic (success, warning, error), component-specific
- Typography tokens: font families, sizes, weights, line heights, letter spacing
- Spacing tokens: consistent scale systems (4px, 8px base units)
- Shadow and elevation token systems
- Border radius and shape tokens
- Animation and timing tokens (duration, easing)
- Breakpoint and responsive tokens
- Token aliasing and referencing strategies

### Token Tooling & Transformation

- Style Dictionary configuration a
</source-excerpt>

## 5. mobile-android-design
- source: `wshobson-agents@a30778f8c4e6`
- kind: `skill`
- raw: `raw/wshobson-agents/plugins/ui-design/skills/mobile-android-design/SKILL.md`
- sha256: `0a209a1c45585ce0056548cc2f0fd352b7fde5980a3b5dd397a9daf5dff19fe7`

<source-excerpt>
---
name: mobile-android-design
description: Master Material Design 3 and Jetpack Compose patterns for building native Android apps. Use when designing Android interfaces, implementing Compose UI, or following Google's Material Design guidelines.
---

# Android Mobile Design

Master Material Design 3 (Material You) and Jetpack Compose to build modern, adaptive Android applications that integrate seamlessly with the Android ecosystem.

## When to Use This Skill

- Designing Android app interfaces following Material Design 3
- Building Jetpack Compose UI and layouts
- Implementing Android navigation patterns (Navigation Compose)
- Creating adaptive layouts for phones, tablets, and foldables
- Using Material 3 theming with dynamic colors
- Building accessible Android interfaces
- Implementing Android-specific gestures and interactions
- Designing for different screen configurations

## Detailed section: Core Concepts

Originally a 9201-byte section in this SKILL.md. Moved to `references/details.md` to fit Codex's 8 KB skill body cap.

## Quick Start Component

~~~kotlin
@Composable
fun ItemListCard(
    item: Item,
    onItemClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        onClick = onItemClick,
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(48.dp)
</source-excerpt>

## 6. Mobile Accessibility
- source: `wshobson-agents@a30778f8c4e6`
- kind: `skill`
- raw: `raw/wshobson-agents/plugins/ui-design/skills/accessibility-compliance/references/mobile-accessibility.md`
- sha256: `b293d6c2b0a44c7f6ebb4848f7fe09d33713e91bbb1b97d88a561e7360b90201`

<source-excerpt>
# Mobile Accessibility

## Overview

Mobile accessibility ensures apps work for users with disabilities on iOS and Android devices. This includes support for screen readers (VoiceOver, TalkBack), motor impairments, and various visual disabilities.

## Touch Target Sizing

### Minimum Sizes

~~~css
/* WCAG 2.2 Level AA: 24x24px minimum */
.interactive-element {
  min-width: 24px;
  min-height: 24px;
}

/* WCAG 2.2 Level AAA / Apple HIG / Material Design: 44x44dp */
.touch-target {
  min-width: 44px;
  min-height: 44px;
}

/* Android Material Design: 48x48dp recommended */
.android-touch-target {
  min-width: 48px;
  min-height: 48px;
}
~~~

### Touch Target Spacing

~~~tsx
// Ensure adequate spacing between touch targets
function ButtonGroup({ buttons }) {
  return (
    <div className="flex gap-3">
      {" "}
      {/* 12px minimum gap */}
      {buttons.map((btn) => (
        <button key={btn.id} className="min-w-[44px] min-h-[44px] px-4 py-2">
          {btn.label}
        </button>
      ))}
    </div>
  );
}

// Expanding hit area without changing visual size
function IconButton({ icon, label, onClick }) {
  return (
    <button
      onClick={onClick}
      aria-label={label}
      className="relative p-3" // Creates 44x44 touch area
    >
      <span className="block w-5 h-5">{icon}</span>
    </button>
  );
}
~~~

## iOS VoiceOver

### React Native Accessibility Props

~~~tsx
import { View, Text, TouchableOpacity, AccessibilityInfo } from "react-native";

// Basic accessible button
function AccessibleButton({ onPress, title, hint }) {
  return (
    <TouchableOpacit
</source-excerpt>

## 7. mobile-android-design — detailed sections
- source: `wshobson-agents@a30778f8c4e6`
- kind: `skill`
- raw: `raw/wshobson-agents/plugins/ui-design/skills/mobile-android-design/references/details.md`
- sha256: `854f692ebe2b6adbf42f1406d0e7e1f7bc895ee34baa4ceff1ef1afc9f2dd962`

<source-excerpt>
# mobile-android-design — detailed sections

## Core Concepts

### 1. Material Design 3 Principles

**Personalization**: Dynamic color adapts UI to user's wallpaper
**Accessibility**: Tonal palettes ensure sufficient color contrast
**Large Screens**: Responsive layouts for tablets and foldables

**Material Components:**

- Cards, Buttons, FABs, Chips
- Navigation (rail, drawer, bottom nav)
- Text fields, Dialogs, Sheets
- Lists, Menus, Progress indicators

### 2. Jetpack Compose Layout System

**Column and Row:**

~~~kotlin
// Vertical arrangement with alignment
Column(
    modifier = Modifier.padding(16.dp),
    verticalArrangement = Arrangement.spacedBy(12.dp),
    horizontalAlignment = Alignment.Start
) {
    Text(
        text = "Title",
        style = MaterialTheme.typography.headlineSmall
    )
    Text(
        text = "Subtitle",
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant
    )
}

// Horizontal arrangement with weight
Row(
    modifier = Modifier.fillMaxWidth(),
    horizontalArrangement = Arrangement.SpaceBetween,
    verticalAlignment = Alignment.CenterVertically
) {
    Icon(Icons.Default.Star, contentDescription = null)
    Text("Featured")
    Spacer(modifier = Modifier.weight(1f))
    TextButton(onClick = {}) {
        Text("View All")
    }
}
~~~

**Lazy Lists and Grids:**

~~~kotlin
// Lazy column with sticky headers
LazyColumn {
    items.groupBy { it.category }.forEach { (category, categoryItems) ->
        stickyHeader {
            Text(
                text = category,
</source-excerpt>

## 8. Material Design 3 Theming
- source: `wshobson-agents@a30778f8c4e6`
- kind: `skill`
- raw: `raw/wshobson-agents/plugins/ui-design/skills/mobile-android-design/references/material3-theming.md`
- sha256: `72ba4c1ef77fba5740b039b3f8b3676902967495141e3f40e0b800df3e85da7c`

<source-excerpt>
# Material Design 3 Theming

## Color System

### Dynamic Color (Material You)

~~~kotlin
@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context)
            else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        shapes = AppShapes,
        content = content
    )
}
~~~

### Custom Color Scheme

~~~kotlin
// Define color palette
val md_theme_light_primary = Color(0xFF6750A4)
val md_theme_light_onPrimary = Color(0xFFFFFFFF)
val md_theme_light_primaryContainer = Color(0xFFEADDFF)
val md_theme_light_onPrimaryContainer = Color(0xFF21005D)
val md_theme_light_secondary = Color(0xFF625B71)
val md_theme_light_onSecondary = Color(0xFFFFFFFF)
val md_theme_light_secondaryContainer = Color(0xFFE8DEF8)
val md_theme_light_onSecondaryContainer = Color(0xFF1D192B)
val md_theme_light_tertiary = Color(0xFF7D5260)
val md_theme_light_onTertiary = Color(0xFFFFFFFF)
val md_theme_light_tertiaryContainer = Color(0xFFFFD8E4)
val md_theme_light_onTertiaryContainer = Color(0xFF31111D)
val md_theme_light_error = Color(0xFFB3261E)
val md_theme_light_onError = Color(0xFFFFFFFF)
val md_theme_light_errorContainer = Color(0xFFF9DEDC)
val md_the
</source-excerpt>
