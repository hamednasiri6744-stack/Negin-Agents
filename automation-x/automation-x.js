const path=require('path');
const T=(n,d,p={},r=[])=>({name:n,description:d,inputSchema:{type:'object',properties:p,required:r,additionalProperties:false}});
const CORE=process.env.EMA_CORE_URL||'http://127.0.0.1:8765';
const AIRFLOW=(process.env.AIRFLOW_BASE_URL||'http://127.0.0.1:8080').replace(/\/+$/,'');

async function httpJson(url,options={}){
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),Number(options.timeout_ms||20000));
  try{
    const headers={'content-type':'application/json',...(options.headers||{})};
    const token=process.env.AIRFLOW_API_TOKEN||process.env.AIRFLOW_BEARER_TOKEN||'';
    const user=process.env.AIRFLOW_API_USERNAME||'';
    const pass=process.env.AIRFLOW_API_PASSWORD||'';
    if(options.airflow_auth!==false){
      if(token) headers.authorization=`Bearer ${token}`;
      else if(user&&pass) headers.authorization=`Basic ${Buffer.from(`${user}:${pass}`).toString('base64')}`;
    }
    const res=await fetch(url,{
      method:options.method||'GET',
      headers,
      body:options.body===undefined?undefined:JSON.stringify(options.body),
      signal:controller.signal
    });
    const text=await res.text();
    let data={};
    try{data=text?JSON.parse(text):{}}catch{data={raw:text.slice(0,4000)}}
    if(!res.ok){
      const e=new Error(`http_${res.status}`);
      e.status=res.status;e.data=data;throw e;
    }
    return data;
  } finally { clearTimeout(timer); }
}
async function coreJson(route,options={}){
  return httpJson(`${CORE}${route}`,{...options,airflow_auth:false,timeout_ms:options.timeout_ms||30000});
}
async function safe(fn){
  try{return await fn()}catch(e){
    return{ok:false,error:String(e&&e.message||e),status:e&&e.status||null,detail:e&&e.data||null};
  }
}
function requireApproval(a,action){
  if(!a||a.owner_approved!==true) throw Error(`${action} requires owner_approved=true`);
}
async function airflowAny(paths,options={}){
  let last=null;
  for(const p of paths){
    try{return await httpJson(`${AIRFLOW}${p}`,options)}
    catch(e){last=e;if(![404,405].includes(Number(e.status||0)))throw e}
  }
  throw last||Error('airflow_endpoint_unavailable');
}

function tools(){return[
T('automation_x_status','Runtime, safety boundaries and operational workflow mode.'),
T('automation_x_contract','Ownership/routing contract.'),
T('automation_x_capabilities','List automation capabilities.'),
T('automation_x_quality_gate','Evaluate workflow readiness.',{evidence:{type:'array',items:{type:'string'}}}),
T('automation_x_handoff','Create bounded handoff.',{to:{type:'string',enum:['Negin-Master','Code-X']},task:{type:'string'},reason:{type:'string'}},['to','task']),
T('automation_x_live_health','Check Enterprise Core, n8n and Airflow local runtime health.'),
T('automation_x_n8n_list','List live n8n workflows through the guarded Enterprise Core.',{limit:{type:'integer',minimum:1,maximum:100},cursor:{type:'string'},include_credential_refs:{type:'boolean'}}),
T('automation_x_n8n_get','Read one live n8n workflow through the guarded Enterprise Core.',{workflow_id:{type:'string'},include_credential_refs:{type:'boolean'}},['workflow_id']),
T('automation_x_n8n_validate','Validate an inline or existing n8n workflow before mutation.',{workflow_id:{type:'string'},workflow:{type:'object'},allow_risky_nodes:{type:'boolean'}}),
T('automation_x_n8n_manage','Create/update/activate/deactivate/import/delete a local n8n workflow through safety gates. owner_approved=true is mandatory; delete also requires confirm_destructive=true.',{
  action:{type:'string',enum:['create','update','activate','deactivate','delete','import']},
  workflow_id:{type:'string'},workflow:{type:'object'},allow_risky_nodes:{type:'boolean'},
  confirm_destructive:{type:'boolean'},owner_approved:{type:'boolean'}
},['action','owner_approved']),
T('automation_x_n8n_webhook','Execute a local n8n webhook. owner_approved=true is mandatory because the workflow may have side effects.',{
  path:{type:'string'},method:{type:'string',enum:['GET','POST']},payload:{type:'object'},owner_approved:{type:'boolean'}
},['path','owner_approved']),
T('automation_x_airflow_health','Check the local Airflow API without changing DAG state.'),
T('automation_x_airflow_dags_list','List Airflow DAGs read-only.',{limit:{type:'integer',minimum:1,maximum:200},offset:{type:'integer',minimum:0}}),
T('automation_x_airflow_dag_get','Read one Airflow DAG read-only.',{dag_id:{type:'string'}},['dag_id']),
T('automation_x_airflow_dag_trigger','Trigger one local Airflow DAG run. owner_approved=true is mandatory.',{dag_id:{type:'string'},conf:{type:'object'},owner_approved:{type:'boolean'}},['dag_id','owner_approved']),
T('automation_x_airflow_dag_pause','Pause or unpause one local Airflow DAG. owner_approved=true is mandatory.',{dag_id:{type:'string'},is_paused:{type:'boolean'},owner_approved:{type:'boolean'}},['dag_id','is_paused','owner_approved']),
T('automation_x_project_scan','Scan automation artifacts read-only.',{root:{type:'string'}},['root']),
T('automation_x_n8n_audit','Audit exported n8n workflow JSON read-only.',{path:{type:'string'}},['path']),
T('automation_x_airflow_audit','Audit Airflow DAG source read-only.',{path:{type:'string'}},['path']),
T('automation_x_integration_plan','Design reliable workflow.',{goal:{type:'string'},systems:{type:'array',items:{type:'string'}}},['goal']),
T('automation_x_api_contract_review','Review API/webhook reliability.',{endpoints:{type:'array',items:{type:'string'}}}),
T('automation_x_idempotency_review','Review idempotency design.',{strategy:{type:'string'},side_effects:{type:'array',items:{type:'string'}}}),
T('automation_x_retry_policy_review','Review retry/backoff policy.',{policy:{type:'string'}}),
T('automation_x_observability_plan','Design workflow observability.',{workflow:{type:'string'}},['workflow']),
T('automation_x_workflow_risk_matrix','Create workflow risk matrix.',{steps:{type:'array',items:{type:'string'}}}),
T('automation_x_runbook_plan','Create operator runbook plan.',{workflow:{type:'string'}},['workflow'])
]}

function scan(a,h){
  const root=h.allowed(a.root),fs=h.walk(root),rel=fs.map(f=>path.relative(root,f).replace(/\\/g,'/'));
  return{ok:true,mode:'static-readonly',root,file_count:fs.length,detected:{
    n8n:rel.filter(x=>/\.json$/i.test(x)&&/(n8n|workflow)/i.test(x)).slice(0,100),
    airflow:rel.filter(x=>/\.py$/i.test(x)&&/(dag|airflow)/i.test(x)).slice(0,100),
    openapi:rel.filter(x=>/(openapi|swagger).*\.(json|ya?ml)$/i.test(x)).slice(0,60),
    compose:rel.filter(x=>/compose.*\.ya?ml$/i.test(x)).slice(0,60)
  }};
}

async function call(c,n,a,h){
  if(n==='automation_x_status')return{
    ok:true,name:c.name,version:c.version,operational_version:'0.3.0',mode:'workflow-operational-guarded',
    tool_count:tools().length,allowed_roots:h.roots(),arbitrary_shell:false,
    live_n8n:true,live_airflow:true,mutation_policy:'explicit-owner-approval',
    guarantees:['no credential exposure','destructive delete requires double confirmation','local targets only','static audits remain read-only'],
    contract:c.contract
  };
  if(n==='automation_x_contract')return{ok:true,...c.contract,operational_extensions:['live n8n read/manage','guarded n8n webhook execution','live Airflow read/trigger/pause']};
  if(n==='automation_x_capabilities')return{ok:true,capabilities:tools().map(x=>x.name),mutation_owner:'owner-approved Automation-X via guarded local APIs'};
  if(n==='automation_x_quality_gate'){
    const e=a.evidence||[];
    return{ok:e.length>0,status:e.length?'REVIEWABLE':'BLOCKED',gates:[
      'no plaintext secrets','retry/idempotency defined','failure route defined',
      'side effects require explicit owner approval','rollback/compensation documented','runtime verification before activation'
    ]};
  }
  if(n==='automation_x_handoff')return{ok:true,from:c.name,to:a.to,task:a.task,reason:a.reason||'capability boundary'};
  if(n==='automation_x_live_health'){
    const core=await safe(()=>coreJson('/health'));
    const n8n=await safe(()=>coreJson('/n8n/workflows/manage',{method:'POST',body:{action:'auth_health'}}));
    const airflow=await safe(()=>airflowAny(['/api/v2/monitor/health','/api/v1/health','/health']));
    return{ok:!!core.ok,operational_version:'0.3.0',core,n8n,airflow};
  }
  if(n==='automation_x_n8n_list'){
    return await coreJson('/n8n/workflows/manage',{method:'POST',body:{
      action:'list',limit:Math.min(Math.max(+a.limit||20,1),100),cursor:a.cursor||null,
      include_credential_refs:a.include_credential_refs===true
    }});
  }
  if(n==='automation_x_n8n_get'){
    return await coreJson('/n8n/workflows/manage',{method:'POST',body:{
      action:'get',workflow_id:String(a.workflow_id),include_credential_refs:a.include_credential_refs===true
    }});
  }
  if(n==='automation_x_n8n_validate'){
    return await coreJson('/n8n/workflows/manage',{method:'POST',body:{
      action:'validate',workflow_id:a.workflow_id||null,workflow:a.workflow||null,allow_risky_nodes:a.allow_risky_nodes===true
    }});
  }
  if(n==='automation_x_n8n_manage'){
    requireApproval(a,`n8n ${a.action}`);
    if(a.action==='delete'&&a.confirm_destructive!==true)throw Error('n8n delete requires confirm_destructive=true');
    return await coreJson('/n8n/workflows/manage',{method:'POST',body:{
      action:a.action,workflow_id:a.workflow_id||null,workflow:a.workflow||null,
      allow_risky_nodes:a.allow_risky_nodes===true,confirm_destructive:a.confirm_destructive===true,
      include_credential_refs:false
    },timeout_ms:45000});
  }
  if(n==='automation_x_n8n_webhook'){
    requireApproval(a,'n8n webhook execution');
    return await coreJson('/n8n/webhook',{method:'POST',body:{
      path:String(a.path||''),method:a.method||'POST',payload:a.payload||{}
    },timeout_ms:45000});
  }
  if(n==='automation_x_airflow_health')return await safe(()=>airflowAny(['/api/v2/monitor/health','/api/v1/health','/health']));
  if(n==='automation_x_airflow_dags_list'){
    const limit=Math.min(Math.max(+a.limit||50,1),200),offset=Math.max(+a.offset||0,0);
    return await airflowAny([`/api/v2/dags?limit=${limit}&offset=${offset}`,`/api/v1/dags?limit=${limit}&offset=${offset}`]);
  }
  if(n==='automation_x_airflow_dag_get'){
    const id=encodeURIComponent(String(a.dag_id||''));
    if(!id)throw Error('dag_id required');
    return await airflowAny([`/api/v2/dags/${id}`,`/api/v1/dags/${id}`]);
  }
  if(n==='automation_x_airflow_dag_trigger'){
    requireApproval(a,'airflow dag trigger');
    const id=encodeURIComponent(String(a.dag_id||''));
    if(!id)throw Error('dag_id required');
    return await airflowAny([`/api/v2/dags/${id}/dagRuns`,`/api/v1/dags/${id}/dagRuns`],{
      method:'POST',body:{conf:a.conf||{}},timeout_ms:45000
    });
  }
  if(n==='automation_x_airflow_dag_pause'){
    requireApproval(a,'airflow dag pause state change');
    const id=encodeURIComponent(String(a.dag_id||''));
    if(!id)throw Error('dag_id required');
    return await airflowAny([`/api/v2/dags/${id}`,`/api/v1/dags/${id}`],{
      method:'PATCH',body:{is_paused:a.is_paused===true},timeout_ms:30000
    });
  }
  if(n==='automation_x_project_scan')return scan(a,h);
  if(n==='automation_x_n8n_audit'){
    const raw=JSON.parse(h.readText(a.path)),w=raw.workflow||raw,ns=Array.isArray(w.nodes)?w.nodes:[],f=[];
    for(const x of ns){
      const t=String(x.type||''),nm=String(x.name||'');
      if(/executecommand|ssh|ftp|sftp|postgres|mysql|mssql|httprequest/i.test(t))
        f.push({severity:'review',rule:'side_effect_or_external_node',node:nm,type:t});
      if(x.credentials)f.push({severity:'info',rule:'credential_reference_present',node:nm,types:Object.keys(x.credentials)});
    }
    return{ok:true,mode:'static-readonly',workflow_name:w.name||null,node_count:ns.length,active:!!w.active,findings:f,activation_policy:'owner approval required'};
  }
  if(n==='automation_x_airflow_audit'){
    const p=h.allowed(a.path),files=h.fs.statSync(p).isDirectory()?h.walk(p).filter(f=>f.endsWith('.py')):[p],f=[];
    for(const x of files.slice(0,200)){
      let t='';try{t=h.readText(x)}catch{continue}
      if(!/(DAG\(|@dag\b|airflow)/i.test(t))continue;
      if(!/retries\s*=|default_args/i.test(t))f.push({severity:'medium',rule:'retry_policy_not_obvious',file:path.basename(x)});
      if(/catchup\s*=\s*True/i.test(t))f.push({severity:'review',rule:'catchup_enabled',file:path.basename(x)});
      if(/password|token|api[_-]?key/i.test(t)&&/=\s*["'][^"']+["']/i.test(t))f.push({severity:'high',rule:'possible_inline_secret',file:path.basename(x)});
    }
    return{ok:true,mode:'static-readonly',files_checked:Math.min(files.length,200),findings:f};
  }
  if(n==='automation_x_integration_plan')return{ok:true,apply:false,goal:a.goal,systems:a.systems||[],design:[
    'trigger/input/output/idempotency key','separate validation from side effects','bounded retry/backoff + failure route',
    'checkpoint long-running work','correlation id/observability','rollback/compensation','explicit owner approval for side effects'
  ]};
  if(n==='automation_x_api_contract_review')return{ok:true,apply:false,endpoint_count:(a.endpoints||[]).length,checks:[
    'auth without credential exposure','timeouts/retries','idempotency','rate limits','pagination',
    'webhook verification/replay protection','error schema/observability'
  ]};
  if(n==='automation_x_idempotency_review')return{ok:true,apply:false,status:String(a.strategy||'').trim()?'REVIEWABLE':'NEEDS_VALIDATION',checks:[
    'stable idempotency key','dedupe store/window','replay behavior','side-effect classification','compensation'
  ]};
  if(n==='automation_x_retry_policy_review')return{ok:true,apply:false,status:String(a.policy||'').trim()?'REVIEWABLE':'NEEDS_VALIDATION',checks:[
    'bounded attempts','exponential backoff','jitter','retryable error classes','dead-letter/failure route','timeout budget'
  ]};
  if(n==='automation_x_observability_plan')return{ok:true,apply:false,workflow:a.workflow,telemetry:[
    'correlation_id','run_id','step status','latency','retry_count','external response class','business outcome'
  ],alerts:['stuck runs','retry exhaustion','error-rate spike','latency breach']};
  if(n==='automation_x_workflow_risk_matrix')return{ok:true,apply:false,rows:(a.steps||[]).map((s,i)=>({
    step:i+1,name:s,risk:'NEEDS_VALIDATION',questions:['side effect?','idempotent?','retry safe?','rollback?','credential boundary?']
  }))};
  if(n==='automation_x_runbook_plan')return{ok:true,apply:false,workflow:a.workflow,sections:[
    'purpose/owners','dependencies','normal operation','failure signatures','safe retry','rollback/compensation','escalation','post-incident evidence'
  ]};
  throw Error('unknown_tool');
}
module.exports={tools,call};

// --- NeginAI project-local skill routing adapter (hot-reload/reconnect-safe) ---
const neginaiProjectSkills = require("../shared/neginai-skill-router");
const _neginaiAutomationBaseTools = tools;
const _neginaiAutomationBaseCall = call;
function _neginaiAutomationSkillTools(){
  return [
    T("automation_x_skill_catalog","List project-local NeginAI skills routed to Automation-X.",{query:{type:"string"}}),
    T("automation_x_skill_get","Load one exact project-local NeginAI skill routed to Automation-X.",{name:{type:"string"}},["name"]),
    T("automation_x_skill_resolve","Resolve an Automation-X task to the most relevant project-local NeginAI skills.",{task:{type:"string"},limit:{type:"integer",minimum:1,maximum:10}},["task"])
  ];
}
function _neginaiAutomationTools(){ return [..._neginaiAutomationBaseTools(),..._neginaiAutomationSkillTools()]; }
async function _neginaiAutomationCall(c,n,a,h){
  if(n==="automation_x_skill_catalog") return neginaiProjectSkills.catalog("Automation-X",a.query||"");
  if(n==="automation_x_skill_get") return neginaiProjectSkills.get("Automation-X",a.name);
  if(n==="automation_x_skill_resolve") return neginaiProjectSkills.resolve("Automation-X",a.task||"",a.limit||5);
  if(n==="automation_x_status"){
    const r=await _neginaiAutomationBaseCall(c,n,a,h);
    return {...r,tool_count:_neginaiAutomationTools().length,project_skill_routing:true,skill_root:neginaiProjectSkills.root()};
  }
  if(n==="automation_x_capabilities"){
    const r=await _neginaiAutomationBaseCall(c,n,a,h);
    return {...r,capabilities:_neginaiAutomationTools().map(x=>x.name),project_skill_routing:true};
  }
  return _neginaiAutomationBaseCall(c,n,a,h);
}
module.exports={tools:_neginaiAutomationTools,call:_neginaiAutomationCall};
