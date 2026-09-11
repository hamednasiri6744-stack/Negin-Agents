const SKILLS = [
  {
    id: "dribbble",
    label: "Dribbble Pattern Research",
    source: "https://dribbble.com/",
    purpose: "Visual inspiration and focused UI pattern research for layout, component composition, interaction cues, visual hierarchy and micro-interactions.",
    outputs: ["pattern insights","IA/component observations","interaction patterns","visual-token ideas","anti-patterns","source links"],
    guardrails: [
      "Do not copy shots pixel-for-pixel or extract proprietary assets.",
      "Respect authentication, access controls, robots, rate limits and source terms.",
      "Use references as inspiration only; NeginAI canonical product and visual constraints remain authoritative.",
      "Prefer synthesis across multiple references over imitation of one design."
    ]
  },
  {
    id: "mobbin",
    label: "Mobbin Product Pattern Research",
    source: "https://mobbin.com/",
    purpose: "Product-flow and interaction-pattern research across real mobile and web products, especially navigation, onboarding, search, forms, commerce, dashboards and states.",
    outputs: ["flow comparison","screen/pattern matrix","navigation patterns","state behavior","component patterns","source links"],
    guardrails: [
      "Never bypass login, paywalls or access restrictions.",
      "Do not reproduce proprietary screens or assets as implementation targets.",
      "Extract reusable product principles and compare multiple products where possible.",
      "Preserve NeginAI feature semantics, RTL, accessibility and mobile-first constraints."
    ]
  },
  {
    id: "behance",
    label: "Behance Case Study Research",
    source: "https://www.behance.net/",
    purpose: "Long-form design-system, product case-study, branding, motion and interaction research for higher-order design rationale and visual-system exploration.",
    outputs: ["case-study principles","design-system observations","layout/motion ideas","brand-system ideas","anti-patterns","source links"],
    guardrails: [
      "Do not copy case studies, illustrations, mockups or branded assets.",
      "Respect source access rules and attribution requirements.",
      "Separate presentation polish from production-realistic UX.",
      "NeginAI canonical constraints override external visual references."
    ]
  }
];

function catalog(){
  return {ok:true, skills:SKILLS};
}
function get(id){
  const skill=SKILLS.find(x=>x.id===String(id||"").toLowerCase());
  if(!skill) throw new Error("research_skill_not_found");
  return {ok:true, skill};
}
function resolve(context=""){
  const c=String(context||"").toLowerCase();
  const scored=SKILLS.map(skill=>{
    let score=40;
    if(c.includes(skill.id)) score=100;
    if(skill.id==="mobbin" && /\b(flow|journey|mobile|app|navigation|onboarding|pattern|screen)\b/.test(c)) score=Math.max(score,92);
    if(skill.id==="dribbble" && /\b(visual|ui|card|microinteraction|animation|dashboard|aesthetic|inspiration)\b/.test(c)) score=Math.max(score,86);
    if(skill.id==="behance" && /\b(case study|branding|design system|presentation|motion|concept|identity)\b/.test(c)) score=Math.max(score,88);
    return {...skill,score};
  }).sort((a,b)=>b.score-a.score);
  return {ok:true,context,ranked:scored};
}
module.exports={SKILLS,catalog,get,resolve};
