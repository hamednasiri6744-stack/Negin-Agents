
const fs = require("fs");
const path = require("path");
const cp = require("child_process");

function readJson(p){ try { return JSON.parse(fs.readFileSync(p,"utf8")); } catch { return null; } }
function readText(p, max=600000){ try { const s=fs.statSync(p); return s.size<=max ? fs.readFileSync(p,"utf8") : ""; } catch { return ""; } }
function top(map,n=20){ return [...map.entries()].sort((a,b)=>b[1]-a[1]).slice(0,n).map(([value,count])=>({value,count})); }
function inc(map,k){ if(!k)return; map.set(k,(map.get(k)||0)+1); }

function profile(root){
  const profilesDir = path.join(__dirname,"..","profiles");
  const target = root ? path.resolve(root) : null;
  const entries = [];
  try {
    for (const dir of fs.readdirSync(profilesDir,{withFileTypes:true})) {
      if (!dir.isDirectory()) continue;
      const cfg = readJson(path.join(profilesDir,dir.name,"profile.json"));
      if (cfg) entries.push({name:dir.name,cfg});
    }
  } catch {}
  const samePath=(a,b)=>process.platform==="win32"?path.resolve(a).toLowerCase()===path.resolve(b).toLowerCase():path.resolve(a)===path.resolve(b);
  if (target) {
    const exact = entries.find(x=>x.cfg.root && samePath(x.cfg.root,target));
    if (exact) return {...exact.cfg,root:target,profile_source:exact.name};
  }
  const fallback = entries.find(x=>x.name.toLowerCase()==="default") || {name:"builtin",cfg:{project:"generic",preserve_visual_identity:true,redesign_requires_explicit_owner_request:true,required_directions:["rtl","ltr"]}};
  return {...fallback.cfg,root:target || fallback.cfg.root || null,profile_source:fallback.name};
}
function manifest(root, api){
  root = api.allowed(root);
  const pkg = readJson(path.join(root,"package.json")) || {};
  const deps = {...(pkg.dependencies||{}), ...(pkg.devDependencies||{}), ...(pkg.peerDependencies||{})};
  const files = api.scan(root).files_sample || [];
  return {
    ok:true, root,
    package_manager: fs.existsSync(path.join(root,"pnpm-lock.yaml"))?"pnpm":fs.existsSync(path.join(root,"yarn.lock"))?"yarn":fs.existsSync(path.join(root,"package-lock.json"))?"npm":"unknown",
    scripts: pkg.scripts||{},
    dependency_names: Object.keys(deps).sort(),
    has_playwright: !!(deps["@playwright/test"]||deps.playwright),
    has_axe: !!(deps["axe-core"]||deps["@axe-core/playwright"]),
    has_lighthouse: !!deps.lighthouse,
    ui_hints: files.filter(x=>/\.(html|css|jsx?|tsx?)$/i.test(x)).slice(0,120)
  };
}
function inventory(root, api){
  root=api.allowed(root);
  const all=api._files(root);
  const cats={html:[],css:[],js:[],ts:[],tsx:[],jsx:[],templates:[],other_ui:[]};
  const components=[];
  for(const f of all){
    const rel=path.relative(root,f).replace(/\\/g,"/");
    const ext=path.extname(f).toLowerCase();
    if(ext===".html")cats.html.push(rel);
    else if(ext===".css"||ext===".scss")cats.css.push(rel);
    else if(ext===".js")cats.js.push(rel);
    else if(ext===".ts")cats.ts.push(rel);
    else if(ext===".tsx")cats.tsx.push(rel);
    else if(ext===".jsx")cats.jsx.push(rel);
    if(/template/i.test(rel)) cats.templates.push(rel);
    if([".js",".ts",".tsx",".jsx"].includes(ext)){
      const t=readText(f);
      const rx=/(?:function|class)\s+([A-Z][A-Za-z0-9_]*)|(?:const|let)\s+([A-Z][A-Za-z0-9_]*)\s*=/g;
      let m; while((m=rx.exec(t)) && components.length<500){ components.push({name:m[1]||m[2],file:rel}); }
    }
  }
  return {ok:true,root,counts:Object.fromEntries(Object.entries(cats).map(([k,v])=>[k,v.length])),files:Object.fromEntries(Object.entries(cats).map(([k,v])=>[k,v.slice(0,150)])),components:components.slice(0,300)};
}
function designSystemAudit(root, api){
  root=api.allowed(root);
  const cssFiles=api._files(root).filter(f=>/\.(css|scss)$/i.test(f)).slice(0,500);
  const colors=new Map(), spacing=new Map(), radii=new Map(), fonts=new Map(), fontSizes=new Map(), breakpoints=new Map();
  const customProps=new Set();
  let focusVisible=0, focusRules=0, reducedMotion=0, rtlSignals=0, importantCount=0, filesRead=0;
  for(const f of cssFiles){
    const t=readText(f); if(!t)continue; filesRead++;
    for(const m of t.matchAll(/--([a-z0-9-_]+)\s*:/gi)) customProps.add("--"+m[1]);
    for(const m of t.matchAll(/#[0-9a-f]{3,8}\b|rgba?\([^)]+\)|hsla?\([^)]+\)/gi)) inc(colors,m[0].toLowerCase());
    for(const m of t.matchAll(/\b(?:margin|padding|gap|inset|top|right|bottom|left)(?:-[a-z]+)?\s*:\s*(-?\d+(?:\.\d+)?(?:px|rem|em))/gi)) inc(spacing,m[1].toLowerCase());
    for(const m of t.matchAll(/border-radius\s*:\s*([^;}{]+)/gi)) inc(radii,m[1].trim().toLowerCase());
    for(const m of t.matchAll(/font-family\s*:\s*([^;}{]+)/gi)) inc(fonts,m[1].trim());
    for(const m of t.matchAll(/font-size\s*:\s*([^;}{]+)/gi)) inc(fontSizes,m[1].trim().toLowerCase());
    for(const m of t.matchAll(/@media[^{]*(?:min|max)-width\s*:\s*([^)]+)/gi)) inc(breakpoints,m[1].trim().toLowerCase());
    focusVisible += (t.match(/:focus-visible/gi)||[]).length;
    focusRules += (t.match(/:focus\b/gi)||[]).length;
    reducedMotion += (t.match(/prefers-reduced-motion/gi)||[]).length;
    rtlSignals += (t.match(/\[dir\s*=\s*["']?rtl|direction\s*:\s*rtl|:dir\(rtl\)/gi)||[]).length;
    importantCount += (t.match(/!important/gi)||[]).length;
  }
  const findings=[];
  if(customProps.size<10) findings.push({severity:"medium",rule:"weak-token-layer",evidence:{custom_property_count:customProps.size}});
  if(colors.size>40) findings.push({severity:"medium",rule:"color-literal-fragmentation",evidence:{unique_color_literals:colors.size}});
  if(focusVisible===0) findings.push({severity:"high",rule:"focus-visible-system-missing"});
  if(reducedMotion===0) findings.push({severity:"medium",rule:"reduced-motion-path-missing"});
  if(rtlSignals===0) findings.push({severity:"high",rule:"rtl-system-signal-missing"});
  if(importantCount>50) findings.push({severity:"medium",rule:"important-density",evidence:{count:importantCount}});
  return {ok:true,root,css_files_read:filesRead,metrics:{custom_property_count:customProps.size,unique_color_literals:colors.size,focus_visible_rules:focusVisible,focus_rules:focusRules,reduced_motion_rules:reducedMotion,rtl_signals:rtlSignals,important_count:importantCount},top_literals:{colors:top(colors),spacing:top(spacing),radii:top(radii),fonts:top(fonts),font_sizes:top(fontSizes),breakpoints:top(breakpoints)},findings};
}
function playwrightModule(root){
  const candidates=[
    path.join(root,"node_modules","playwright"),
    path.join(root,"node_modules","@playwright","test")
  ];
  for(const p of candidates){ if(fs.existsSync(p)) return p; }
  return null;
}
function axeModule(root){
  const p=path.join(root,"node_modules","axe-core");
  return fs.existsSync(p)?p:null;
}
function systemBrowser(){
  const candidates=[
    path.join(process.env.PROGRAMFILES||"C:\\Program Files","Google","Chrome","Application","chrome.exe"),
    path.join(process.env["PROGRAMFILES(X86)"]||"C:\\Program Files (x86)","Microsoft","Edge","Application","msedge.exe"),
    path.join(process.env.LOCALAPPDATA||"","Google","Chrome","Application","chrome.exe")
  ];
  for(const p of candidates){ if(p && fs.existsSync(p)) return p; }
  return null;
}
function runtimePreflight(root,api){
  root=api.allowed(root);
  const p=profile(root);
  const pw=playwrightModule(root), axe=axeModule(root), sysBrowser=systemBrowser();
  const browserCache=path.join(process.env.LOCALAPPDATA||"","ms-playwright");
  const cachePresent=!!browserCache&&fs.existsSync(browserCache);
  return {ok:true,root,profile:p,playwright_module:pw?pw:null,axe_module:axe?axe:null,system_browser:sysBrowser,browser_cache_present:cachePresent,ready:!!pw && (!!sysBrowser || cachePresent)};
}
function validateUrl(url,root){
  const u=new URL(url);
  if(!["http:","https:"].includes(u.protocol)) throw new Error("unsupported_url_protocol");
  const p=profile(root), hosts=p.allowed_runtime_hosts||["127.0.0.1","localhost"];
  if(!hosts.includes(u.hostname)) throw new Error("runtime_host_not_allowlisted");
  return u.toString();
}
function runtimeAudit(root,url,api){
  root=api.allowed(root); url=validateUrl(url,root);
  const pre=runtimePreflight(root,api);
  if(!pre.ready) return {ok:false,error:"playwright_not_available",preflight:pre};
  const runDir=path.join(__dirname,"..","runs",new Date().toISOString().replace(/[:.]/g,"-"));
  fs.mkdirSync(runDir,{recursive:true});
  const script=path.join(runDir,"audit-runner.js");
  const outFile=path.join(runDir,"result.json");
  const viewports=(profile(root).viewports||[]).filter(v=>["mobile-primary","desktop-primary"].includes(v.name));
  const source=`
const fs=require("fs");
const pw=require(${JSON.stringify(pre.playwright_module)});
const axePath=${JSON.stringify(pre.axe_module)};
const systemBrowser=${JSON.stringify(pre.system_browser)};
const target=process.env.UX_TARGET_URL;
const outFile=process.env.UX_OUT_FILE;
const viewports=JSON.parse(process.env.UX_VIEWPORTS||"[]");
(async()=>{
 const chromium=pw.chromium || (pw.default&&pw.default.chromium);
 if(!chromium) throw new Error("chromium_api_missing");
 const browser=await chromium.launch({headless:true,...(systemBrowser?{executablePath:systemBrowser}:{})});
 const out={ok:true,target,viewports:[],started_at:new Date().toISOString()};
 for(const vp of viewports){
  const ctx=await browser.newContext({viewport:{width:vp.width,height:vp.height}});
  const page=await ctx.newPage();
  const consoleErrors=[]; const consoleWarnings=[];
  page.on("console",m=>{ if(m.type()==="error")consoleErrors.push(m.text()); else if(m.type()==="warning")consoleWarnings.push(m.text()); });
  page.on("pageerror",e=>consoleErrors.push("pageerror: "+e.message));
  let navError=null;
  try{await page.goto(target,{waitUntil:"domcontentloaded",timeout:20000});}catch(e){navError=e.message;}
  await page.waitForTimeout(600);
  const metrics=await page.evaluate(()=>({title:document.title,url:location.href,dir:getComputedStyle(document.documentElement).direction,bodyText:(document.body&&document.body.innerText||"").trim().length,scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,scrollHeight:document.documentElement.scrollHeight,clientHeight:document.documentElement.clientHeight,activeTag:document.activeElement&&document.activeElement.tagName}));
  const screenshot=require("path").join(${JSON.stringify(runDir)},vp.name+".png");
  await page.screenshot({path:screenshot,fullPage:false});
  let axe=null;
  if(axePath){ try{ const axeSource=fs.readFileSync(require("path").join(axePath,"axe.min.js"),"utf8"); await page.addScriptTag({content:axeSource}); axe=await page.evaluate(async()=>{const r=await axe.run();return {violations:r.violations.map(v=>({id:v.id,impact:v.impact,description:v.description,nodes:v.nodes.length}))};}); }catch(e){axe={error:e.message};} }
  out.viewports.push({name:vp.name,width:vp.width,height:vp.height,nav_error:navError,metrics,horizontal_overflow:metrics.scrollWidth>metrics.clientWidth,console_errors:consoleErrors.slice(0,50),console_warnings:consoleWarnings.slice(0,50),axe,screenshot});
  await ctx.close();
 }
 await browser.close(); out.finished_at=new Date().toISOString(); fs.writeFileSync(outFile,JSON.stringify(out,null,2));
})().catch(e=>{fs.writeFileSync(outFile,JSON.stringify({ok:false,error:e.stack||e.message},null,2));process.exitCode=1;});
`;
  fs.writeFileSync(script,source,"utf8");
  const r=cp.spawnSync(process.execPath,[script],{cwd:root,env:{...process.env,UX_TARGET_URL:url,UX_OUT_FILE:outFile,UX_VIEWPORTS:JSON.stringify(viewports)},encoding:"utf8",timeout:90000,windowsHide:true});
  const result=readJson(outFile)||{ok:false,error:"runtime_result_missing",stderr:(r.stderr||"").slice(-3000)};
  result.runner={exit_code:r.status,timed_out:!!r.error&&/timed out/i.test(String(r.error)),run_dir:runDir};
  return result;
}
function qualityGate(root,url,api){
  root=api.allowed(root);
  const stat=api.audit(root), ds=designSystemAudit(root,api);
  const runtime=url?runtimeAudit(root,url,api):null;
  const gates=[];
  const add=(name,status,evidence)=>gates.push({name,status,evidence});
  add("static-critical-findings",stat.findings.some(x=>x.severity==="high")?"FAIL":"PASS",stat.findings.filter(x=>x.severity==="high"));
  add("design-system-critical-findings",ds.findings.some(x=>x.severity==="high")?"FAIL":"PASS",ds.findings.filter(x=>x.severity==="high"));
  if(!runtime) add("rendered-runtime","BLOCKED","runtime URL not supplied");
  else if(!runtime.ok) add("rendered-runtime","FAIL",runtime.error||runtime);
  else {
    add("rendered-runtime",runtime.viewports.every(v=>!v.nav_error&&v.metrics.bodyText>0)?"PASS":"FAIL",runtime.viewports.map(v=>({name:v.name,nav_error:v.nav_error,bodyText:v.metrics.bodyText})));
    add("responsive-overflow",runtime.viewports.every(v=>!v.horizontal_overflow)?"PASS":"FAIL",runtime.viewports.map(v=>({name:v.name,horizontal_overflow:v.horizontal_overflow,scrollWidth:v.metrics.scrollWidth,clientWidth:v.metrics.clientWidth})));
    add("console-errors",runtime.viewports.every(v=>v.console_errors.length===0)?"PASS":"FAIL",runtime.viewports.map(v=>({name:v.name,count:v.console_errors.length,errors:v.console_errors.slice(0,5)})));
    const serious=[]; for(const v of runtime.viewports){ for(const x of ((v.axe&&v.axe.violations)||[])){ if(["serious","critical"].includes(x.impact)) serious.push({viewport:v.name,...x}); } }
    add("axe-serious-critical",serious.length===0?"PASS":"FAIL",serious.slice(0,30));
  }
  const overall=gates.some(g=>g.status==="FAIL")?"FAIL":gates.some(g=>g.status==="BLOCKED")?"BLOCKED":"PASS";
  return {ok:true,root,overall,gates,static_audit:stat,design_system:ds,runtime};
}
function changeSpec(root,url,api){
  const gate=qualityGate(root,url,api);
  const actions=[];
  for(const f of gate.static_audit.findings) if(["high","medium"].includes(f.severity)) actions.push({priority:f.severity==="high"?"P0":"P1",source:"static",rule:f.rule,file:f.file||null});
  for(const f of gate.design_system.findings) if(["high","medium"].includes(f.severity)) actions.push({priority:f.severity==="high"?"P0":"P1",source:"design-system",rule:f.rule,evidence:f.evidence||null});
  if(gate.runtime&&gate.runtime.ok){
    for(const v of gate.runtime.viewports){
      if(v.horizontal_overflow) actions.push({priority:"P0",source:"runtime",rule:"horizontal-overflow",viewport:v.name});
      if(v.console_errors.length) actions.push({priority:"P0",source:"runtime",rule:"console-errors",viewport:v.name,evidence:v.console_errors.slice(0,5)});
    }
  }
  const rank={P0:0,P1:1,P2:2,P3:3}; actions.sort((a,b)=>rank[a.priority]-rank[b.priority]);
  return {ok:true,root:gate.root,design_authority:"UX-X",implementation_owner:"Code-X",gate_status:gate.overall,actions,required_verification:["same runtime URL","mobile-primary 390x844","desktop-primary 1440x900","RTL/LTR where applicable","axe serious/critical = 0","relevant console errors = 0","before/after screenshots for material visual work"],note:"Code-X must not invent a new visual direction; preserve the target project identity unless the owner explicitly requests redesign."};
}

module.exports={manifest,inventory,designSystemAudit,runtimePreflight,runtimeAudit,qualityGate,changeSpec,profile,systemBrowser};
