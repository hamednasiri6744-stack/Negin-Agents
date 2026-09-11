const path=require('path');
const T=(n,d,p={},r=[])=>({name:n,description:d,inputSchema:{type:'object',properties:p,required:r,additionalProperties:false}});
const CORE=process.env.EMA_CORE_URL||'http://127.0.0.1:8765';

async function coreJson(route,options={}){
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),Number(options.timeout_ms||30000));
  try{
    const res=await fetch(`${CORE}${route}`,{
      method:options.method||'GET',
      headers:{'content-type':'application/json',...(options.headers||{})},
      body:options.body===undefined?undefined:JSON.stringify(options.body),
      signal:controller.signal
    });
    const text=await res.text();
    let data={};
    try{data=text?JSON.parse(text):{}}catch{data={raw:text.slice(0,4000)}}
    if(!res.ok) throw Error(`core_http_${res.status}:${JSON.stringify(data).slice(0,1500)}`);
    return data;
  } finally { clearTimeout(timer); }
}

function assertReadOnlySql(sql){
  const raw=String(sql||'').trim();
  if(!raw||raw.length>20000) throw Error('sql length must be 1..20000');
  const low=raw.toLowerCase().replace(/\s+/g,' ');
  if(!/^(select|with)\b/.test(low)) throw Error('SELECT/CTE only');
  if(/--|\/\*|\*\/|;/.test(raw)) throw Error('comments and multi-statements are forbidden');
  const forbidden=[
    'insert','update','delete','merge','drop','alter','create','truncate','exec','execute',
    'grant','revoke','deny','use','into','dbcc','backup','restore','bulk','openrowset',
    'openquery','opendatasource','waitfor','kill','shutdown'
  ];
  for(const w of forbidden){ if(new RegExp(`\\b${w}\\b`,'i').test(raw)) throw Error(`forbidden sql token: ${w}`); }
  return raw;
}

function rows(h,a){
  const t=h.readText(a.path),e=path.extname(a.path).toLowerCase(),m=Math.min(Math.max(+a.max_rows||1000,1),5000);
  if(e==='.json'){
    const v=JSON.parse(t),x=Array.isArray(v)?v:(Array.isArray(v.rows)?v.rows:[]);
    return x.slice(0,m).filter(z=>z&&typeof z==='object'&&!Array.isArray(z));
  }
  if(e!=='.csv')throw Error('supported_formats: csv,json');
  const ls=t.split(/\r?\n/).filter(Boolean);if(!ls.length)return[];
  const split=l=>{const o=[];let c='',q=false;for(let i=0;i<l.length;i++){const x=l[i];if(x==='"'){if(q&&l[i+1]==='"'){c+='"';i++}else q=!q}else if(x===','&&!q){o.push(c);c=''}else c+=x}o.push(c);return o};
  const hd=split(ls[0]);
  return ls.slice(1,m+1).map(l=>{const v=split(l),o={};hd.forEach((k,i)=>o[k||`col_${i+1}`]=v[i]??'');return o});
}
function prof(rs){
  const ks=[...new Set(rs.flatMap(Object.keys))],cols={};
  for(const k of ks){
    const vs=rs.map(r=>r[k]),p=vs.filter(v=>v!==null&&v!==undefined&&v!==''),
      nums=p.map(Number).filter(Number.isFinite);
    cols[k]={missing:vs.length-p.length,missing_rate:vs.length?(vs.length-p.length)/vs.length:0,distinct:new Set(p.map(String)).size,type:nums.length===p.length&&p.length?'numeric':'text'};
  }
  return{rows:rs.length,column_count:ks.length,columns:cols};
}

function tools(){return[
T('data_x_status','Runtime, safety boundaries and operational live-data mode.'),
T('data_x_contract','Ownership/routing contract.'),
T('data_x_capabilities','List analytical and live read-only capabilities.'),
T('data_x_quality_gate','Evaluate evidence readiness.',{evidence:{type:'array',items:{type:'string'}}}),
T('data_x_handoff','Create bounded handoff.',{to:{type:'string',enum:['Negin-Master','Code-X']},task:{type:'string'},reason:{type:'string'}},['to','task']),
T('data_x_live_health','Check Enterprise Core and strict read-only SQL health.'),
T('data_x_semantic_resolve','Resolve organizational/business language against the canonical semantic source before KPI work.',{text:{type:'string'}},['text']),
T('data_x_sql_readonly_health','Verify live SQL connectivity and strict read-only identity.'),
T('data_x_varanegar_schema_search','Search live Varanegar SQL catalog by terms without scanning business data.',{terms:{type:'array',items:{type:'string'},minItems:1,maxItems:12},max_rows:{type:'integer',minimum:1,maximum:2000}},['terms']),
T('data_x_sql_readonly_query','Run one bounded live SELECT/CTE through Negin_Report_ReadOnly with a second local firewall.',{sql:{type:'string'},max_rows:{type:'integer',minimum:1,maximum:5000}},['sql']),
T('data_x_dataset_profile','Profile local CSV/JSON read-only.',{path:{type:'string'},max_rows:{type:'integer'}},['path']),
T('data_x_schema_infer','Infer local dataset schema.',{path:{type:'string'},max_rows:{type:'integer'}},['path']),
T('data_x_data_quality_audit','Audit local data quality.',{path:{type:'string'},max_rows:{type:'integer'}},['path']),
T('data_x_dataset_compare','Compare two local datasets.',{left_path:{type:'string'},right_path:{type:'string'},max_rows:{type:'integer'}},['left_path','right_path']),
T('data_x_analysis_plan','Design analysis.',{objective:{type:'string'}},['objective']),
T('data_x_anomaly_plan','Design layered anomaly detection.',{fields:{type:'array',items:{type:'string'}}}),
T('data_x_forecast_plan','Design forecast/backtest.',{target:{type:'string'},time_field:{type:'string'},horizon:{}},['target','time_field','horizon']),
T('data_x_time_series_health','Design time-series health checks.',{time_field:{type:'string'},value_field:{type:'string'}},['time_field','value_field']),
T('data_x_kpi_validation_spec','Validate candidate KPI against supplied canonical definition.',{canonical_definition:{type:'string'},candidate_formula:{type:'string'}},['canonical_definition','candidate_formula']),
T('data_x_kpi_reconciliation_plan','Plan KPI reconciliation.',{canonical_definition:{type:'string'},candidate_definition:{type:'string'}},['canonical_definition','candidate_definition'])
]}

async function call(c,n,a,h){
  if(n==='data_x_status')return{
    ok:true,name:c.name,version:c.version,operational_version:'0.3.0',mode:'analytics-live-readonly',
    tool_count:tools().length,allowed_roots:h.roots(),production_sql:'strict-readonly-only',arbitrary_shell:false,
    statuses:['FACT','INFERRED','NEEDS_VALIDATION'],canonical_semantics_owner:'Negin-Master',
    guarantees:['SELECT/CTE only','bounded rows','no DDL/DML/EXEC','canonical semantics required for enterprise KPI claims'],contract:c.contract
  };
  if(n==='data_x_contract')return{ok:true,...c.contract,operational_extensions:['live strict-readonly SQL','live Varanegar schema discovery','canonical semantic resolution']};
  if(n==='data_x_capabilities')return{ok:true,capabilities:tools().map(x=>x.name),canonical_semantics_owner:'Negin-Master',live_readonly_sql:true};
  if(n==='data_x_quality_gate'){
    const e=a.evidence||[];return{ok:e.length>0,status:e.length?'REVIEWABLE':'BLOCKED',
      gates:['canonical definition supplied when enterprise KPI involved','source/grain documented','quality checks complete','uncertainty stated','live SQL remains strict read-only']};
  }
  if(n==='data_x_handoff')return{ok:true,from:c.name,to:a.to,task:a.task,reason:a.reason||'capability boundary'};
  if(n==='data_x_live_health'){
    const [core,sql]=await Promise.all([coreJson('/health'),coreJson('/sql/readonly/health')]);
    return{ok:!!core.ok&&!!sql.ok,operational_version:'0.3.0',core,sql};
  }
  if(n==='data_x_semantic_resolve'){
    const text=String(a.text||'').trim(); if(!text)throw Error('text required');
    return await coreJson('/semantic/resolve',{method:'POST',body:{text}});
  }
  if(n==='data_x_sql_readonly_health')return await coreJson('/sql/readonly/health');
  if(n==='data_x_varanegar_schema_search'){
    const terms=(a.terms||[]).map(x=>String(x).trim()).filter(Boolean).slice(0,12);
    if(!terms.length)throw Error('at least one term required');
    return await coreJson('/varanegar/schema/search',{method:'POST',body:{terms,max_rows:Math.min(Math.max(+a.max_rows||500,1),2000)}});
  }
  if(n==='data_x_sql_readonly_query'){
    const sql=assertReadOnlySql(a.sql);
    return await coreJson('/sql/readonly/query',{method:'POST',body:{sql,max_rows:Math.min(Math.max(+a.max_rows||1000,1),5000)},timeout_ms:45000});
  }
  if(n==='data_x_dataset_profile'){const r=rows(h,a);return{ok:true,mode:'local-readonly',file:h.allowed(a.path),...prof(r),limitations:['Canonical KPI meaning belongs to Negin-Master.']}}
  if(n==='data_x_schema_infer'){const p=prof(rows(h,a));return{ok:true,status:'INFERRED',schema:Object.fromEntries(Object.entries(p.columns).map(([k,v])=>[k,{type:v.type,nullable:v.missing>0}]))}}
  if(n==='data_x_data_quality_audit'){const p=prof(rows(h,a)),f=[];for(const[k,v]of Object.entries(p.columns)){if(v.missing_rate>0.2)f.push({severity:'review',field:k,rule:'high_missing_rate',value:v.missing_rate});if(v.distinct===1&&p.rows>1)f.push({severity:'review',field:k,rule:'constant_column'})}return{ok:true,status:'FACT',rows:p.rows,findings:f}}
  if(n==='data_x_dataset_compare'){const l=prof(rows(h,{path:a.left_path,max_rows:a.max_rows})),r=prof(rows(h,{path:a.right_path,max_rows:a.max_rows})),lk=Object.keys(l.columns),rk=Object.keys(r.columns);return{ok:true,status:'FACT',left_rows:l.rows,right_rows:r.rows,only_left:lk.filter(x=>!rk.includes(x)),only_right:rk.filter(x=>!lk.includes(x)),shared:lk.filter(x=>rk.includes(x))}}
  if(n==='data_x_analysis_plan')return{ok:true,apply:false,objective:a.objective,sequence:['confirm semantics if enterprise KPI','profile quality/leakage','baseline','robust validation','uncertainty/business impact']};
  if(n==='data_x_anomaly_plan')return{ok:true,apply:false,fields:a.fields||[],layers:['canonical rule','history/seasonality','peer-group','multivariate if justified'],statuses:['FACT','INFERRED','NEEDS_VALIDATION']};
  if(n==='data_x_forecast_plan')return{ok:true,apply:false,target:a.target,time_field:a.time_field,horizon:a.horizon,stages:['continuity check','seasonal-naive baseline','rolling-origin backtest','candidate models','prediction intervals','bias review'],metrics:['MAE','WAPE','bias']};
  if(n==='data_x_time_series_health')return{ok:true,apply:false,checks:['duplicate timestamps','missing periods','irregular cadence','outliers','structural breaks','seasonality drift']};
  if(n==='data_x_kpi_validation_spec')return{ok:true,status:String(a.canonical_definition||'').trim()?'comparable':'BLOCKED',checks:['grain','filters','signs','time basis','exclusions','rounding'],rule:'Never invent or replace canonical Varanegar semantics.'};
  if(n==='data_x_kpi_reconciliation_plan')return{ok:true,apply:false,status:'NEEDS_VALIDATION',steps:['freeze both definitions','align grain/filter/time basis','build row-level bridge','quantify delta by cause','validate against Golden Case','only then version canonical source']};
  throw Error('unknown_tool');
}
module.exports={tools,call};
