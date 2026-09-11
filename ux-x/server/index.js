const fs = require("fs");
const path = require("path");
const http = require("http");
const VERSION = "0.6.1";
const advanced=require("./advanced");
const kits=require("./kits");
const researchSkills=require("./research-skills");
const figmaX=require("../../figma-x/server/index");
const FIGMA_X_LIVE_MCP_URL=process.env.UX_X_FIGMA_X_MCP_URL||"http://127.0.0.1:8784/mcp";
let figmaXRequestSeq=0;
function figmaXLiveCall(name,args={}){
  return new Promise((resolve,reject)=>{
    let u;
    try{u=new URL(FIGMA_X_LIVE_MCP_URL);}catch{return reject(new Error("figma_x_live_url_invalid"));}
    if(!["127.0.0.1","localhost","::1"].includes(u.hostname))return reject(new Error("figma_x_live_target_not_localhost"));
    const id="uxx-figmax-"+Date.now()+"-"+(++figmaXRequestSeq);
    const body=JSON.stringify({jsonrpc:"2.0",id,method:"tools/call",params:{name,arguments:args}});
    const headers={"content-type":"application/json","content-length":Buffer.byteLength(body)};
    const token=String(process.env.FIGMA_X_BEARER_TOKEN||"");
    if(token)headers.authorization="Bearer "+token;
    const req=http.request({protocol:u.protocol,hostname:u.hostname,port:u.port||80,path:u.pathname+(u.search||""),method:"POST",headers},res=>{
      let raw="";res.setEncoding("utf8");res.on("data",c=>{if(raw.length<2000000)raw+=c;});res.on("end",()=>{
        if(res.statusCode!==200)return reject(new Error("figma_x_live_http_"+res.statusCode));
        let msg;try{msg=JSON.parse(raw||"{}");}catch{return reject(new Error("figma_x_live_invalid_json"));}
        if(msg.error)return reject(new Error("figma_x_live_mcp_error:"+(msg.error.message||"unknown")));
        const r=msg.result||{};
        if(r.isError){const detail=r.structuredContent&&r.structuredContent.error||r.content&&r.content[0]&&r.content[0].text||"unknown";return reject(new Error("figma_x_live_tool_error:"+String(detail)));}
        if(r.structuredContent!==undefined)return resolve(r.structuredContent);
        const text=r.content&&r.content[0]&&r.content[0].text;
        if(typeof text==="string"){try{return resolve(JSON.parse(text));}catch{return resolve({ok:true,text});}}
        return resolve(r);
      });
    });
    req.setTimeout(20000,()=>req.destroy(new Error("figma_x_live_timeout")));
    req.on("error",e=>reject(new Error("figma_x_live_unavailable:"+String(e&&e.message||e))));
    req.write(body);req.end();
  });
}

const MCP_PROTOCOL_VERSION = "2025-06-18";
const DEFAULT_PORT = 8778;
const PRIVATE_CONFIG = path.join(__dirname, "..", ".runtime.json");
function loadPrivateConfig(){try{return JSON.parse(fs.readFileSync(PRIVATE_CONFIG,"utf8"));}catch{return {};}}
const privateConfig=loadPrivateConfig();
function roots(){const raw=process.env.UX_X_ALLOWED_ROOTS||privateConfig.allowed_roots||"C:\\code-x\\agents\\ux-x";const items=Array.isArray(raw)?raw:String(raw).split(";");return items.map(x=>path.resolve(String(x).trim())).filter(Boolean);}
function allowed(p){if(!p||typeof p!=="string")throw new Error("root_required");p=path.resolve(p);const ok=roots().some(r=>{const q=path.relative(r,p);return q===""||(!q.startsWith("..")&&!path.isAbsolute(q));});if(!ok)throw new Error("path_outside_allowlist");return p;}
function secret(n){const s=String(n).toLowerCase();return s===".env"||s.startsWith(".env.")||/(secret|token|password|credential|private[_-]?key|ux-x-private)/i.test(s);}
function files(root){root=allowed(root);const out=[],queue=[root];while(queue.length&&out.length<3000){const dir=queue.shift();let entries=[];try{entries=fs.readdirSync(dir,{withFileTypes:true});}catch{continue;}for(const e of entries){if(secret(e.name)||["node_modules",".git",".next","dist","build","coverage",".turbo",".cache"].includes(e.name))continue;const f=path.join(dir,e.name);if(e.isDirectory())queue.push(f);else if(e.isFile())out.push(f);if(out.length>=3000)break;}}return out;}
function text(f){try{const st=fs.statSync(f);return st.size<500000?fs.readFileSync(f,"utf8"):"";}catch{return "";}}
function packageObjects(list){return list.filter(f=>path.basename(f).toLowerCase()==="package.json").map(f=>{try{return JSON.parse(text(f));}catch{return {};}});}
function depExists(pkgs,name){return pkgs.some(p=>[p.dependencies,p.devDependencies,p.peerDependencies].some(d=>d&&Object.prototype.hasOwnProperty.call(d,name)));}
function depPrefix(pkgs,prefix){return pkgs.some(p=>[p.dependencies,p.devDependencies,p.peerDependencies].some(d=>d&&Object.keys(d).some(k=>k.startsWith(prefix))));}
function scan(root){
  root=allowed(root);
  const f=files(root);
  const rel=f.map(x=>path.relative(root,x).replace(/\\/g,"/"));
  const pkgs=packageObjects(f);
  const has=n=>rel.some(x=>x.toLowerCase().includes(n.toLowerCase()));
  return {ok:true,root,file_count:f.length,truncated:f.length>=3000,detected:{
    react:depExists(pkgs,"react"),
    nextjs:depExists(pkgs,"next")||has("next.config"),
    typescript:rel.some(x=>/\.(ts|tsx)$/i.test(x)),
    tailwind:depExists(pkgs,"tailwindcss")||has("tailwind.config"),
    shadcn:has("components.json"),
    base_ui:depExists(pkgs,"@base-ui-components/react"),
    radix_ui:depPrefix(pkgs,"@radix-ui/"),
    react_aria:depExists(pkgs,"react-aria-components"),
    mui:depExists(pkgs,"@mui/material"),
    ant_design:depExists(pkgs,"antd"),
    mantine:depExists(pkgs,"@mantine/core"),
    chakra:depExists(pkgs,"@chakra-ui/react"),
    floating_ui:depExists(pkgs,"@floating-ui/react"),
    lucide:depExists(pkgs,"lucide-react"),
    motion:depExists(pkgs,"motion")||depExists(pkgs,"framer-motion"),
    echarts:depExists(pkgs,"echarts"),
    tanstack_table:depExists(pkgs,"@tanstack/react-table"),
    react_hook_form:depExists(pkgs,"react-hook-form"),
    zod:depExists(pkgs,"zod"),
    style_dictionary:depExists(pkgs,"style-dictionary"),
    storybook:has(".storybook/")||pkgs.some(p=>Object.values(p.scripts||{}).some(v=>/storybook/i.test(String(v))))||depPrefix(pkgs,"@storybook/"),
    storybook_a11y:depExists(pkgs,"@storybook/addon-a11y"),
    playwright:depExists(pkgs,"@playwright/test")||has("playwright.config"),
    axe_core:depExists(pkgs,"axe-core")||depExists(pkgs,"@axe-core/playwright"),
    lighthouse:depExists(pkgs,"lighthouse")
  },files_sample:rel.slice(0,100)};
}
function audit(root){const s=scan(root),findings=[];const src=files(s.root).filter(x=>/\.(jsx?|tsx?|css|scss|html)$/i.test(x)).slice(0,700);for(const f of src){const t=text(f),lo=t.toLowerCase(),rel=path.relative(s.root,f).replace(/\\/g,"/");if(lo.includes("<img")&&!lo.includes("alt="))findings.push({severity:"high",rule:"img-alt",file:rel});if((t.includes("<div")||t.includes("<span"))&&/onClick\s*=/.test(t))findings.push({severity:"medium",rule:"nonsemantic-click-target",file:rel});if(/\b(?:width|min-width|max-width)\s*:\s*[\"']?\d{3,}px/i.test(t))findings.push({severity:"medium",rule:"large-fixed-width",file:rel});if(/outline\s*:\s*none/i.test(t))findings.push({severity:"medium",rule:"focus-outline-none",file:rel});}if(!s.detected.storybook)findings.push({severity:"info",rule:"storybook-not-detected"});if(!s.detected.playwright)findings.push({severity:"info",rule:"playwright-not-detected"});if(!s.detected.axe_core)findings.push({severity:"info",rule:"axe-not-detected"});return {ok:true,mode:"static-readonly",scan:s,findings,verification_limits:["Static heuristics do not prove visual correctness.","Runtime layout, touch behavior, browser rendering, Lighthouse scores and full accessibility conformance require runtime tests.","Preserve existing visual identity unless redesign is explicitly requested."]};}
function testPlan(root){const s=scan(root);return {ok:true,root:s.root,matrix:{viewports:["360x800","390x844","768x1024","1280x800","1440x900"],direction:["rtl","ltr"],input:["keyboard-only","touch","mouse"],states:["loading","empty","error","success","disabled","long-content"],accessibility:["focus-visible","semantic-controls","labels/names","contrast","touch-targets>=44px","axe-core"],layout:["panel-resize","zoom-200%","overflow","mobile-safe-area","orientation-change"],runtime:[s.detected.playwright?"playwright-cross-browser":"playwright-recommended",s.detected.storybook?"storybook-component-states":"storybook-recommended","lighthouse-performance-accessibility"]}};}
function safePatchPlan(root){const a=audit(root);return {ok:true,apply:false,checkpoint_required:true,files_to_write:[],proposed_changes:a.findings.filter(x=>x.severity==="high"||x.severity==="medium").map(x=>({rule:x.rule,file:x.file||null,action:"prepare_minimal_reversible_patch_after_owner_scope"})),message:"Plan only. UX-X made no repository changes."};}
function status(){return {ok:true,name:"UX-X",version:VERSION,mode:"audit-readonly",allowed_roots:roots(),network_outbound:false,sql:false,arbitrary_shell:false,tool_count:5,tools:["ux_status","ux_project_scan","ux_audit","ux_test_plan","ux_safe_patch_plan"]};}
function toolSchemas(){const rootSchema={type:"object",properties:{root:{type:"string"}},required:["root"],additionalProperties:false};return [{name:"ux_status",description:"Check UX-X runtime, security mode and capabilities.",inputSchema:{type:"object",properties:{},additionalProperties:false}},{name:"ux_project_scan",description:"Read-only scan of a frontend repository and detected UI stack.",inputSchema:rootSchema},{name:"ux_audit",description:"Static read-only UI/UX heuristic audit for responsiveness, accessibility and component quality.",inputSchema:rootSchema},{name:"ux_test_plan",description:"Generate a deterministic responsive/accessibility/interaction test matrix.",inputSchema:rootSchema},{name:"ux_safe_patch_plan",description:"Return a reversible patch plan only. Never writes repository files.",inputSchema:rootSchema}];}
function callTool(name,args={}){switch(name){case "ux_status":return status();case "ux_project_scan":return scan(args.root);case "ux_audit":return audit(args.root);case "ux_test_plan":return testPlan(args.root);case "ux_safe_patch_plan":return safePatchPlan(args.root);default:throw new Error("unknown_tool");}}
async function mcpHandle(message){if(!message||message.id===undefined)return null;const id=message.id;if(message.method==="initialize")return {jsonrpc:"2.0",id,result:{protocolVersion:MCP_PROTOCOL_VERSION,capabilities:{tools:{listChanged:true}},serverInfo:{name:"ux-x",version:VERSION},instructions:"UX-X is a read-only UI/UX specialist. Preserve existing visual identity unless redesign is explicitly requested. Use ux_project_scan and ux_audit before proposing changes. Negin Agent v4 owns orchestration/business/safety; Code-X owns coding/refactoring; UX-X owns UI/UX audit, design-system consistency, responsiveness and accessibility."}};if(message.method==="ping")return {jsonrpc:"2.0",id,result:{}};if(message.method==="tools/list")return {jsonrpc:"2.0",id,result:{tools:toolSchemas()}};if(message.method==="tools/call"){const p=message.params||{};try{const data=await callTool(String(p.name||""),p.arguments||{});return {jsonrpc:"2.0",id,result:{isError:false,content:[{type:"text",text:JSON.stringify(data)}],structuredContent:data}};}catch(e){return {jsonrpc:"2.0",id,result:{isError:true,content:[{type:"text",text:JSON.stringify({ok:false,error:String(e.message||e)})}]}};}}return {jsonrpc:"2.0",id,error:{code:-32601,message:"method_not_found"}};}
function authorized(req){const token=String(process.env.UX_X_BEARER_TOKEN||privateConfig.bearer_token||"");if(!token)return false;const auth=req.headers.authorization||"";const pathname=req.url.split("?",1)[0].replace(/\/+$/,"");return auth===`Bearer ${token}`||pathname===`/mcp/${token}`;}
function serveHttp(){const host=process.env.UX_X_HOST||privateConfig.host||"127.0.0.1";const port=Number(process.env.UX_X_PORT||privateConfig.port||DEFAULT_PORT);const server=http.createServer((req,res)=>{const pathname=req.url.split("?",1)[0];if(req.method==="GET"&&pathname==="/health"){const body=JSON.stringify({ok:true,name:"ux-x",version:VERSION});res.writeHead(200,{"content-type":"application/json","content-length":Buffer.byteLength(body)});return res.end(body);}if(req.method!=="POST"||(!["/","/mcp"].includes(pathname)&&!pathname.startsWith("/mcp/"))){res.writeHead(404);return res.end();}if(!authorized(req)){res.writeHead(401);return res.end();}let body="";req.setEncoding("utf8");req.on("data",c=>{if(body.length<2000000)body+=c;});req.on("end",async()=>{try{const response=await mcpHandle(JSON.parse(body||"{}"));if(response===null){res.writeHead(202);return res.end();}const out=JSON.stringify(response);res.writeHead(200,{"content-type":"application/json","mcp-protocol-version":MCP_PROTOCOL_VERSION,"content-length":Buffer.byteLength(out)});res.end(out);}catch{const out=JSON.stringify({jsonrpc:"2.0",id:null,error:{code:-32700,message:"parse_error"}});res.writeHead(400,{"content-type":"application/json","content-length":Buffer.byteLength(out)});res.end(out);}});});server.listen(port,host,()=>process.stderr.write(`ux-x mcp listening on http://${host}:${port}/mcp\n`));return server;}
function serveStdio(){process.stdin.setEncoding("utf8");let buf="";process.stdin.on("data",async chunk=>{buf+=chunk;let i;while((i=buf.indexOf("\n"))>=0){const line=buf.slice(0,i).trim();buf=buf.slice(i+1);if(!line)continue;let response;try{response=await mcpHandle(JSON.parse(line));}catch{response={jsonrpc:"2.0",id:null,error:{code:-32700,message:"parse_error"}};}if(response)process.stdout.write(JSON.stringify(response)+"\n");}});}
if(require.main===module){const mode=(process.argv[2]||"stdio").toLowerCase();if(mode==="http")serveHttp();else serveStdio();}
module.exports={allowed,secret,scan,audit,testPlan,safePatchPlan,plan:safePatchPlan,tests:testPlan,status,toolSchemas,callTool,mcpHandle,serveHttp,serveStdio,_files:files,advanced};





function advancedApi(){return {allowed,scan,audit,_files:files};}
function status(){
  const toolNames=["ux_status","ux_project_scan","ux_project_manifest","ux_component_inventory","ux_design_system_audit","ux_audit","ux_runtime_preflight","ux_runtime_audit","ux_test_plan","ux_quality_gate","ux_change_spec","ux_safe_patch_plan","ux_kit_catalog","ux_kit_recommend","ux_research_skill_catalog","ux_research_skill_get","ux_research_skill_resolve",...figmaX.toolSchemas().map(t=>t.name)];
  return {ok:true,name:"UX-X",version:VERSION,mode:"design-authority",allowed_roots:roots(),network_outbound:"allowlisted-runtime-hosts-only",sql:false,arbitrary_shell:false,tool_count:toolNames.length,tools:toolNames,design_authority:true,profile_mode:"dynamic",default_project_profile:"generic"};
}
function toolSchemas(){
  const rootSchema={type:"object",properties:{root:{type:"string"}},required:["root"],additionalProperties:false};
  const runtimeSchema={type:"object",properties:{root:{type:"string"},url:{type:"string"}},required:["root","url"],additionalProperties:false};
  const optionalRuntimeSchema={type:"object",properties:{root:{type:"string"},url:{type:"string"}},required:["root"],additionalProperties:false};
  return [
    {name:"ux_status",description:"Check UX-X design-authority runtime, security mode and capabilities.",inputSchema:{type:"object",properties:{},additionalProperties:false}},
    {name:"ux_project_scan",description:"Read-only scan of a frontend repository and detected UI stack.",inputSchema:rootSchema},
    {name:"ux_project_manifest",description:"Read package scripts, dependency inventory and UI entry hints without modifying the repository.",inputSchema:rootSchema},
    {name:"ux_component_inventory",description:"Inventory UI files and detectable component families across legacy and component-based frontends.",inputSchema:rootSchema},
    {name:"ux_design_system_audit",description:"Audit CSS tokenization, color/spacing/radius/font literals, breakpoints, focus-visible, RTL and reduced-motion signals.",inputSchema:rootSchema},
    {name:"ux_audit",description:"Static read-only UI/UX heuristic audit for responsiveness, accessibility and component quality.",inputSchema:rootSchema},
    {name:"ux_runtime_preflight",description:"Check whether the project has the local Playwright/axe prerequisites for rendered QA.",inputSchema:rootSchema},
    {name:"ux_runtime_audit",description:"Run allowlisted rendered Playwright QA on mobile and desktop, capturing overflow, console errors, axe findings and screenshots outside the project.",inputSchema:runtimeSchema},
    {name:"ux_test_plan",description:"Generate the deterministic responsive/accessibility/interaction test matrix.",inputSchema:rootSchema},
    {name:"ux_quality_gate",description:"Apply UX-X release gates. Without a runtime URL, rendered gates are BLOCKED rather than falsely passing.",inputSchema:optionalRuntimeSchema},
    {name:"ux_change_spec",description:"Generate a prioritized P0/P1 change specification for Code-X, preserving the target project visual identity unless redesign is explicit.",inputSchema:optionalRuntimeSchema},
    {name:"ux_kit_catalog",description:"Return UX-X's curated professional UI/UX kit catalog. Advisory only; never installs packages.",inputSchema:{type:"object",properties:{},additionalProperties:false}},
    {name:"ux_kit_recommend",description:"Recommend compatible UI/UX kits for a scanned project while preserving the existing component system. Read-only.",inputSchema:{type:"object",properties:{root:{type:"string"},context:{type:"string"}},required:["root"],additionalProperties:false}},    {name:"ux_research_skill_catalog",description:"List UX-X external design-research skills (Dribbble, Mobbin, Behance) and their guardrails.",inputSchema:{type:"object",properties:{},additionalProperties:false}},
    {name:"ux_research_skill_get",description:"Get one UX-X external design-research skill by id.",inputSchema:{type:"object",properties:{id:{type:"string",enum:["dribbble","mobbin","behance"]}},required:["id"],additionalProperties:false}},
    {name:"ux_research_skill_resolve",description:"Rank UX-X external design-research skills for a design-research context.",inputSchema:{type:"object",properties:{context:{type:"string"}},required:["context"],additionalProperties:false}},
    {name:"ux_safe_patch_plan",description:"Return a reversible patch plan only. Never writes repository files.",inputSchema:rootSchema},
    ...figmaX.toolSchemas()
  ];
}
function callTool(name,args={}){
  const api=advancedApi();
  switch(name){
    case "ux_status": return status();
    case "ux_project_scan": return scan(args.root);
    case "ux_project_manifest": return advanced.manifest(args.root,api);
    case "ux_component_inventory": return advanced.inventory(args.root,api);
    case "ux_design_system_audit": return advanced.designSystemAudit(args.root,api);
    case "ux_audit": return audit(args.root);
    case "ux_runtime_preflight": return advanced.runtimePreflight(args.root,api);
    case "ux_runtime_audit": return advanced.runtimeAudit(args.root,args.url,api);
    case "ux_test_plan": return testPlan(args.root);
    case "ux_quality_gate": return advanced.qualityGate(args.root,args.url||null,api);
    case "ux_change_spec": return advanced.changeSpec(args.root,args.url||null,api);
    case "ux_kit_catalog": return kits.catalog();
    case "ux_kit_recommend": return kits.recommend(scan(args.root),args.context||"");    case "ux_research_skill_catalog": return researchSkills.catalog();
    case "ux_research_skill_get": return researchSkills.get(args.id);
    case "ux_research_skill_resolve": return researchSkills.resolve(args.context||"");
    case "ux_safe_patch_plan": return safePatchPlan(args.root);
    default: if(String(name).startsWith("figma_x_")) return figmaXLiveCall(name,args); throw new Error("unknown_tool");
  }
}






