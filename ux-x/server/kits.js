const CATALOG = [
  {
    id: "modern-source-owned",
    label: "Modern source-owned UI",
    purpose: "Greenfield or custom-brand React interfaces where the team should own component source and styling.",
    stack: ["shadcn/ui", "Base UI", "Tailwind CSS", "Lucide"],
    package_hints: ["@base-ui-components/react", "tailwindcss", "lucide-react"],
    strengths: ["source-owned components", "high visual control", "design-token friendly", "good fit for custom brand systems"],
    cautions: ["Base UI is preferred for new shadcn projects; keep Radix when an existing project already uses it", "do not migrate an established component system just for fashion"],
    full_component_library: false
  },
  {
    id: "accessible-headless",
    label: "Accessibility-first headless",
    purpose: "Custom design systems that need robust semantics, keyboard/touch behavior, i18n and composable primitives.",
    stack: ["React Aria Components", "Base UI", "Radix UI", "Floating UI"],
    package_hints: ["react-aria-components", "@base-ui-components/react", "@radix-ui/*", "@floating-ui/react"],
    strengths: ["accessibility-first", "unstyled/composable", "interaction primitives", "internationalization/RTL-friendly choices"],
    cautions: ["choose one primary primitive family per component domain where possible", "verify focus management and overlay behavior in runtime tests"],
    full_component_library: false
  },
  {
    id: "enterprise-material",
    label: "Material UI",
    purpose: "Mature React applications and enterprise products already aligned with Material UI.",
    stack: ["Material UI (MUI)"],
    package_hints: ["@mui/material"],
    strengths: ["mature component coverage", "production-ready defaults", "large ecosystem", "design-kit support"],
    cautions: ["preserve an existing custom identity; do not impose Material styling on a non-Material product without explicit redesign scope"],
    full_component_library: true
  },
  {
    id: "enterprise-dense",
    label: "Ant Design",
    purpose: "Dense enterprise/admin applications that benefit from a broad integrated component system.",
    stack: ["Ant Design"],
    package_hints: ["antd"],
    strengths: ["enterprise-oriented patterns", "broad component set", "internationalization", "theme customization"],
    cautions: ["avoid mixing with another full component library", "do not introduce solely to modernize appearance"],
    full_component_library: true
  },
  {
    id: "product-app",
    label: "Mantine",
    purpose: "Product applications needing a broad React component set plus high-value hooks.",
    stack: ["Mantine"],
    package_hints: ["@mantine/core", "@mantine/hooks"],
    strengths: ["broad component coverage", "large hooks collection", "fast application assembly"],
    cautions: ["avoid parallel full-library adoption when MUI, Ant or Chakra already owns the UI layer"],
    full_component_library: true
  },
  {
    id: "chakra-compat",
    label: "Chakra UI compatibility",
    purpose: "Preserve and improve projects already built on Chakra UI.",
    stack: ["Chakra UI"],
    package_hints: ["@chakra-ui/react"],
    strengths: ["component primitives", "theming system", "existing-project compatibility"],
    cautions: ["compatibility awareness, not UX-X's default migration target"],
    full_component_library: true
  },
  {
    id: "motion-interaction",
    label: "Motion & micro-interactions",
    purpose: "Production-grade motion, gestures, layout transitions and micro-interactions.",
    stack: ["Motion for React"],
    package_hints: ["motion", "framer-motion"],
    strengths: ["layout animation", "gestures", "scroll animation", "agent-oriented Motion AI Kit exists upstream"],
    cautions: ["respect prefers-reduced-motion", "animation must clarify state or hierarchy rather than add noise"],
    full_component_library: false
  },
  {
    id: "data-ui",
    label: "Data-heavy UI",
    purpose: "Analytics, BI, dashboards and complex tabular interfaces.",
    stack: ["TanStack Table v9", "Apache ECharts 6.x"],
    package_hints: ["@tanstack/react-table", "echarts"],
    strengths: ["headless table control", "large/complex table behaviors", "rich interactive visualization", "responsive data exploration"],
    cautions: ["charts still require semantic summaries and accessible interaction paths", "virtualization or progressive rendering should be evidence-driven"],
    full_component_library: false
  },
  {
    id: "forms-validation",
    label: "Form UX & validation",
    purpose: "Complex forms requiring predictable validation, error states and accessible field behavior.",
    stack: ["React Hook Form", "Zod"],
    package_hints: ["react-hook-form", "zod"],
    strengths: ["form state efficiency", "schema-driven validation", "clear error-state architecture"],
    cautions: ["validation architecture does not replace accessible labels, descriptions and focus-on-error behavior"],
    full_component_library: false
  },
  {
    id: "quality-a11y",
    label: "Component QA & accessibility",
    purpose: "Universal UI quality gates for component states, rendered interaction and accessibility.",
    stack: ["Storybook", "@storybook/addon-a11y", "Playwright", "axe-core", "Lighthouse"],
    package_hints: ["@storybook/*", "@storybook/addon-a11y", "@playwright/test", "axe-core", "@axe-core/playwright", "lighthouse"],
    strengths: ["component-state documentation", "automated accessibility checks", "cross-browser interaction testing", "performance/accessibility audits"],
    cautions: ["automated accessibility checks do not prove full WCAG conformance", "real-device/manual review remains necessary"],
    full_component_library: false
  },
  {
    id: "design-tokens",
    label: "Design tokens",
    purpose: "Keep color, spacing, typography, radius and motion decisions consistent across platforms.",
    stack: ["Style Dictionary", "CSS custom properties"],
    package_hints: ["style-dictionary"],
    strengths: ["platform-neutral tokens", "systematic theming", "design/dev consistency"],
    cautions: ["do not replace an established token pipeline without a migration plan"],
    full_component_library: false
  },
  {
    id: "visual-neumorphism",
    label: "Neumorphism / Soft UI",
    purpose: "Selective soft-depth visual language using paired highlights/shadows, tactile surfaces and restrained low-contrast elevation.",
    stack: ["CSS custom properties", "box-shadow", "inset shadows", "design tokens"],
    package_hints: [],
    strengths: ["distinct tactile depth", "soft premium appearance", "works well for focused controls and compact branded surfaces"],
    cautions: ["low-contrast edges can fail accessibility", "never rely on shadow alone for state or affordance", "provide visible focus, borders or contrast fallback", "avoid broad use in dense enterprise/data-heavy screens"],
    full_component_library: false,
    visual_language_only: true,
    accessibility_requirements: ["WCAG-aware text/control contrast", "visible focus indicators", "non-shadow state cues", "clear disabled/pressed states"]
  },
  {
    id: "visual-glassmorphism",
    label: "Glassmorphism",
    purpose: "Layered translucent surfaces with background blur, controlled transparency and luminous depth for modern premium interfaces.",
    stack: ["CSS backdrop-filter", "semi-transparent surfaces", "CSS custom properties", "progressive enhancement"],
    package_hints: [],
    strengths: ["strong visual hierarchy", "modern layered depth", "effective for overlays, cards, navigation and hero surfaces"],
    cautions: ["maintain text/control contrast over variable backgrounds", "provide fallback when backdrop-filter is unavailable", "blur and transparency can increase GPU/compositing cost", "avoid excessive nested glass layers or decorative noise"],
    full_component_library: false,
    visual_language_only: true,
    accessibility_requirements: ["contrast-safe foregrounds", "opaque/fallback surface path", "reduced-transparency friendly design", "runtime performance verification"]
  },
  {
    id: "design-reference",
    label: "Design/reference integrations",
    purpose: "Use design files and high-quality product references as research inputs.",
    stack: ["Figma", "Penpot", "Mobbin", "Dribbble", "Behance"],
    package_hints: [],
    strengths: ["design-source inspection", "reference pattern research", "designer/developer alignment"],
    cautions: ["external reference integrations are not runtime dependencies", "never copy a reference blindly; preserve product identity and requirements"],
    full_component_library: false,
    external_reference_only: true
  },
  {
    id: "research-dribbble",
    label: "Dribbble Pattern Research",
    purpose: "External visual and UI pattern research; synthesis only, never pixel-copying.",
    stack: ["Dribbble"],
    package_hints: [],
    strengths: ["visual inspiration","component treatment research","micro-interaction ideas","source-linked synthesis"],
    cautions: ["do not copy shots or proprietary assets","respect access controls and source terms","NeginAI canonical identity remains authoritative"],
    full_component_library: false,
    external_reference_only: true
  },
  {
    id: "research-mobbin",
    label: "Mobbin Product Pattern Research",
    purpose: "External real-product flow and interaction-pattern research for mobile/web UX.",
    stack: ["Mobbin"],
    package_hints: [],
    strengths: ["real product flows","navigation patterns","state patterns","screen-flow comparison"],
    cautions: ["never bypass login/paywalls","do not clone proprietary screens","adapt patterns to NeginAI semantics"],
    full_component_library: false,
    external_reference_only: true
  },
  {
    id: "research-behance",
    label: "Behance Case Study Research",
    purpose: "External design-system, case-study, branding and motion research.",
    stack: ["Behance"],
    package_hints: [],
    strengths: ["long-form rationale","design-system inspiration","motion/brand exploration","case-study synthesis"],
    cautions: ["do not copy case studies/assets","separate presentation polish from production UX","preserve NeginAI authority"],
    full_component_library: false,
    external_reference_only: true
  }
];

const byId = id => CATALOG.find(x => x.id === id);
const detectedFull = d => [
  ["enterprise-material", d.mui],
  ["enterprise-dense", d.ant_design],
  ["product-app", d.mantine],
  ["chakra-compat", d.chakra]
].filter(([,v]) => !!v).map(([id]) => id);

function catalog(){
  return {
    ok: true,
    version: "0.5.2",
    policy: {
      target_repository_mutation: false,
      package_installation: false,
      preserve_visual_identity: true,
      migration_requires_explicit_scope: true,
      avoid_overlapping_full_component_libraries: true
    },
    kits: CATALOG
  };
}

function recommend(scan, context=""){
  const d = (scan && scan.detected) || {};
  const ctx = String(context || "").toLowerCase();
  const recs = [];
  const conflicts = [];
  const non_actions = [
    "Do not install packages or write to the target repository.",
    "Do not replace an established component system without explicit migration/redesign scope.",
    "Do not combine multiple full component libraries for the same UI layer.",
    "Do not change brand colors, visual identity or conceptual skin unless redesign is explicitly requested."
  ];
  const push = (id, score, reason, role="recommended") => {
    if (recs.some(x => x.id === id)) return;
    const kit = byId(id);
    if (kit) recs.push({id, label:kit.label, score, role, reason, cautions:kit.cautions});
  };

  const full = detectedFull(d);
  if (full.length > 1) {
    conflicts.push({
      type: "overlapping-full-component-libraries",
      detected: full,
      action: "preserve current architecture; investigate ownership by surface before any consolidation proposal"
    });
  }
  if (full.length) {
    for (const id of full) push(id, 100, "Already detected in the project; UX-X should preserve and improve the existing component system.", "preserve-existing");
  } else if (d.react) {
    if (d.shadcn || d.base_ui || d.tailwind || d.lucide) {
      push("modern-source-owned", 96, "The project already contains source-owned/Tailwind-oriented signals; continue the existing direction.");
    } else if (d.react_aria || d.radix_ui || d.floating_ui) {
      push("accessible-headless", 96, "The project already uses headless/accessibility primitives; preserve that architecture.");
    } else {
      push("modern-source-owned", 88, "Greenfield React default: strong control over branding with source-owned components.");
      push("accessible-headless", 80, "Greenfield alternative when accessibility primitives and custom design-system composition are the priority.", "alternative");
    }
  }

  push("quality-a11y", 95, "Universal quality layer for component states, accessibility and rendered interaction verification.");

  const dataHeavy = /\\b(data|dashboard|analytics|bi|report|table|grid|chart|visuali[sz]ation|kpi)\\b/.test(ctx) || d.tanstack_table || d.echarts;
  if (dataHeavy) push("data-ui", d.tanstack_table || d.echarts ? 94 : 84, "Data-heavy context or existing table/chart tooling detected.");

  const motionNeeded = /\\b(motion|animation|micro[- ]?interaction|gesture|transition)\\b/.test(ctx) || d.motion;
  if (motionNeeded) push("motion-interaction", d.motion ? 92 : 78, "Motion is present or requested; require reduced-motion handling and purposeful interaction feedback.");

  const formHeavy = /\\b(form|validation|wizard|checkout|onboarding|input)\\b/.test(ctx) || d.react_hook_form || d.zod;
  if (formHeavy) push("forms-validation", d.react_hook_form || d.zod ? 90 : 76, "Form-heavy context or existing validation tooling detected.");

  const tokenHeavy = /\\b(design system|design-system|token|theme|theming|multi[- ]?platform)\\b/.test(ctx) || d.style_dictionary;
  if (tokenHeavy) push("design-tokens", d.style_dictionary ? 90 : 78, "Design-system/theming context benefits from explicit token governance.");

  const wantsNeumorphism = ["neumorphism","neumorphic","soft ui","soft-ui","soft surface","soft-surface"].some(x=>ctx.includes(x));
  if (wantsNeumorphism) push("visual-neumorphism", 74, "Neumorphic/Soft UI styling requested; use selectively with explicit contrast, focus and non-shadow state cues.");

  const wantsGlassmorphism = ["glassmorphism","glassmorphic","glass ui","glass-ui","frosted glass","frosted-glass","backdrop blur","backdrop-blur"].some(x=>ctx.includes(x));
  if (wantsGlassmorphism) push("visual-glassmorphism", 78, "Glassmorphism requested; apply as a visual language with contrast-safe translucent surfaces, progressive fallback and runtime performance checks.");

  const wantsReference = /\\b(figma|penpot|mobbin|dribbble|behance|reference|benchmark|redesign|prototype|inspiration|case study)\\b/.test(ctx);
  if (wantsReference) push("design-reference", 72, "Reference/design-source context requested; treat these as external inputs, never project dependencies.");
  if (ctx.includes("dribbble")) push("research-dribbble", 94, "Dribbble explicitly requested as a visual-pattern research source.");
  if (ctx.includes("mobbin")) push("research-mobbin", 96, "Mobbin explicitly requested as a real-product flow/pattern research source.");
  if (ctx.includes("behance")) push("research-behance", 94, "Behance explicitly requested as a design-system/case-study research source.");

  const enterpriseCtx = /\\b(enterprise|admin|erp|backoffice|back-office|dense|operations|crm)\\b/.test(ctx);
  if (enterpriseCtx && !full.length) {
    recs.push({
      id: "enterprise-choice",
      label: "Enterprise full-library choice",
      score: 60,
      role: "conditional",
      reason: "For a true greenfield dense enterprise/admin product, evaluate MUI versus Ant Design versus Mantine, but select only one after visual-identity and interaction requirements are known.",
      cautions: ["Do not add all three.", "This is conditional guidance, not an installation recommendation."]
    });
  }

  recs.sort((a,b)=>b.score-a.score);
  return {
    ok: true,
    root: scan && scan.root ? scan.root : null,
    context: context || null,
    detected: d,
    detected_full_component_libraries: full,
    recommendations: recs,
    conflicts,
    non_actions,
    policy: catalog().policy
  };
}

module.exports = { catalog, recommend, CATALOG };





