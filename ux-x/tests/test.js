const a=require("assert"),fs=require("fs"),os=require("os"),path=require("path");
let t=fs.mkdtempSync(path.join(os.tmpdir(),"uxx-"));process.env.UX_X_ALLOWED_ROOTS=t;
let u=require("../server/index.js");
a.throws(()=>u.allowed(path.resolve(t,"..")),/path_outside_allowlist/);a(u.secret(".env"));

function mk(name,deps={},devDeps={},extra={}){
  const p=path.join(t,name);fs.mkdirSync(p);
  fs.writeFileSync(path.join(p,"package.json"),JSON.stringify({dependencies:deps,devDependencies:devDeps}));
  for(const [n,v] of Object.entries(extra)) fs.writeFileSync(path.join(p,n),v);
  return p;
}

let p=mk("p",
  {react:"x","@mui/material":"x",antd:"x","react-aria-components":"x","@mantine/core":"x",motion:"x","@tanstack/react-table":"x",echarts:"x"},
  {"@playwright/test":"x","axe-core":"x","@storybook/addon-a11y":"x",lighthouse:"x"},
  {"components.json":"{}","a.jsx":"<div onClick={()=>0}><img src=x /></div>",".env":"secret=x"}
);
let s=u.scan(p);
a(s.detected.react&&s.detected.shadcn&&s.detected.playwright&&s.detected.axe_core);
a(s.detected.mui&&s.detected.ant_design&&s.detected.react_aria&&s.detected.mantine);
a(s.detected.motion&&s.detected.tanstack_table&&s.detected.echarts&&s.detected.storybook_a11y&&s.detected.lighthouse);
a(!s.files_sample.some(x=>x.includes(".env")));

let q=u.audit(p);a(q.findings.some(x=>x.rule==="img-alt"));a(q.findings.some(x=>x.rule==="nonsemantic-click-target"));
let z=u.plan(p);a(z.apply===false&&z.files_to_write.length===0);

const adv=require("../server/advanced.js");
let gp=adv.profile(p);a.strictEqual(gp.project,"generic");a.strictEqual(path.resolve(gp.root),path.resolve(p));a.notStrictEqual(gp.project,"NeginAI");a.strictEqual(gp.profile_source,"default");
let np=adv.profile("D:\\Projects\\NeginAI");a.strictEqual(np.project,"NeginAI");a.strictEqual(np.profile_source,"neginai");

let st=u.status();a.strictEqual(st.version,"0.5.2");a.strictEqual(st.profile_mode,"dynamic");a.strictEqual(st.default_project_profile,"generic");
a(st.tools.includes("ux_kit_catalog")&&st.tools.includes("ux_kit_recommend")&&st.tools.includes("figma_x_status"));a.strictEqual(st.tool_count,25);

const catalog=u.callTool("ux_kit_catalog",{});
a(catalog.ok&&catalog.kits.some(k=>k.id==="modern-source-owned")&&catalog.kits.some(k=>k.id==="quality-a11y"));
a(catalog.kits.some(k=>k.id==="visual-neumorphism")&&catalog.kits.some(k=>k.id==="visual-glassmorphism"));

let muiOnly=mk("mui-only",{react:"x","@mui/material":"x"});
const before=fs.readFileSync(path.join(muiOnly,"package.json"),"utf8");
let r1=u.callTool("ux_kit_recommend",{root:muiOnly,context:"enterprise admin dashboard"});
a(r1.recommendations.some(x=>x.id==="enterprise-material"&&x.role==="preserve-existing"));
a(!r1.recommendations.some(x=>["enterprise-dense","product-app","chakra-compat"].includes(x.id)));
a(r1.recommendations.some(x=>x.id==="quality-a11y"));
a.strictEqual(fs.readFileSync(path.join(muiOnly,"package.json"),"utf8"),before);

let green=mk("green",{react:"x"});
let r2=u.callTool("ux_kit_recommend",{root:green,context:"new customer-facing product"});
a(r2.recommendations.some(x=>x.id==="modern-source-owned"||x.id==="accessible-headless"));
a(r2.recommendations.some(x=>x.id==="quality-a11y"));
a(r2.non_actions.some(x=>/Do not install packages/i.test(x)));

let r3=u.callTool("ux_kit_recommend",{root:green,context:"premium glassmorphism with frosted glass"});
a(r3.recommendations.some(x=>x.id==="visual-glassmorphism"));
let r4=u.callTool("ux_kit_recommend",{root:green,context:"neumorphic soft ui controls"});
a(r4.recommendations.some(x=>x.id==="visual-neumorphism"));

console.log("ux-x tests passed");


