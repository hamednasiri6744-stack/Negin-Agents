const fs=require("fs"),path=require("path");

const DEFAULT_ROOT=process.env.NEGINAI_SKILL_ROOT||"D:\\Projects\\NeginAI\\skills";
const ROUTING_FILE="AGENT_SKILL_ROUTING.json";

function root(){ return path.resolve(DEFAULT_ROOT); }
function routing(){
  const file=path.join(root(),ROUTING_FILE);
  const data=JSON.parse(fs.readFileSync(file,"utf8").replace(/^\uFEFF/,""));
  if(!data||!data.agents) throw new Error("invalid_agent_skill_routing");
  return data;
}
function agentConfig(agent){
  const cfg=routing().agents[String(agent||"")];
  if(!cfg) throw new Error("unknown_agent_skill_route");
  return cfg;
}
function frontmatter(text){
  const m=String(text||"").match(/^---\s*\n([\s\S]*?)\n---/);
  const out={};
  if(!m) return out;
  for(const line of m[1].split(/\r?\n/)){
    const i=line.indexOf(":"); if(i<0) continue;
    const k=line.slice(0,i).trim(),v=line.slice(i+1).trim().replace(/^["']|["']$/g,"");
    out[k]=v;
  }
  return out;
}
function readSkill(name){
  if(!/^[a-z0-9][a-z0-9-]*$/i.test(String(name||""))) throw new Error("invalid_skill_name");
  const file=path.join(root(),String(name),"SKILL.md");
  const rel=path.relative(root(),file);
  if(rel.startsWith("..")||path.isAbsolute(rel)) throw new Error("skill_path_outside_root");
  const text=fs.readFileSync(file,"utf8");
  const fm=frontmatter(text);
  return {name:fm.name||String(name),path:file,description:fm.description||"",license:fm.license||null,skill:text};
}
function allowedNames(agent){ return [...new Set(agentConfig(agent).skills||[])]; }
function catalog(agent,query=""){
  const q=String(query||"").trim().toLocaleLowerCase();
  const rows=[];
  for(const name of allowedNames(agent)){
    try{
      const s=readSkill(name),hay=`${s.name} ${s.description}`.toLocaleLowerCase();
      if(q&&!hay.includes(q)) continue;
      rows.push({name:s.name,path:s.path,description:s.description,license:s.license});
    }catch{}
  }
  return {ok:true,agent,role:agentConfig(agent).role,primary:agentConfig(agent).primary||[],skills:rows};
}
function get(agent,name){
  if(!allowedNames(agent).includes(String(name))) throw new Error("skill_not_routed_to_agent");
  return {ok:true,agent,...readSkill(name)};
}
function terms(text){
  return [...new Set(String(text||"").toLocaleLowerCase().match(/[\p{L}\p{N}_+-]{2,}/gu)||[])];
}
function resolve(agent,task,limit=5){
  const cfg=agentConfig(agent),data=routing(),ts=terms(task),primary=new Set(cfg.primary||[]);
  const scored=[];
  for(const name of allowedNames(agent)){
    let s; try{s=readSkill(name)}catch{continue}
    const keywords=(data.skill_keywords&&data.skill_keywords[name])||[];
    const hay=`${name} ${s.description} ${keywords.join(" ")}`.toLocaleLowerCase();
    let score=primary.has(name)?2:0;
    for(const t of ts){
      if(name.toLocaleLowerCase().includes(t)) score+=5;
      else if(keywords.some(k=>String(k).toLocaleLowerCase()===t)) score+=4;
      else if(hay.includes(t)) score+=1;
    }
    if(score>0) scored.push({name:s.name,path:s.path,description:s.description,score,primary:primary.has(name)});
  }
  scored.sort((a,b)=>b.score-a.score||Number(b.primary)-Number(a.primary)||a.name.localeCompare(b.name));
  return {ok:true,agent,role:cfg.role,task:String(task||""),matches:scored.slice(0,Math.min(Math.max(Number(limit)||5,1),10))};
}
function matrix(){ const r=routing(); return {ok:true,schema:r.schema,version:r.version,canonical_root:r.canonical_root,agents:r.agents}; }

module.exports={root,routing,agentConfig,catalog,get,resolve,matrix};
