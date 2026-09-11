const fs=require('fs'),path=require('path'),http=require('http');
const MCP='2025-06-18',RUNTIME='0.3.0',cfgPath=process.argv[2]; if(!cfgPath) throw Error('config_path_required');
let cfg,cfgM=0,mod,modM=0;
const readJson=f=>JSON.parse(fs.readFileSync(f,'utf8').replace(/^\uFEFF/,''));
function roots(){return (cfg.allowed_roots||[]).map(x=>path.resolve(x))}
function allowed(p){const a=path.resolve(p);if(!roots().some(r=>{const q=path.relative(r,a);return q===''||(!q.startsWith('..')&&!path.isAbsolute(q))}))throw Error('path_outside_allowlist');return a}
function secret(n){const s=String(n).toLowerCase();return s==='.env'||s.startsWith('.env.')||/(secret|token|password|credential|private[_-]?key)/i.test(s)}
function readText(p,max=1500000){p=allowed(p);if(secret(path.basename(p)))throw Error('secret_file_blocked');const st=fs.statSync(p);if(!st.isFile())throw Error('file_required');if(st.size>max)throw Error('file_too_large');return fs.readFileSync(p,'utf8')}
function walk(root,limit=2500){root=allowed(root);const out=[],q=[root];while(q.length&&out.length<limit){let es=[];const d=q.shift();try{es=fs.readdirSync(d,{withFileTypes:true})}catch{continue}for(const e of es){if(secret(e.name)||['node_modules','.git','.venv','venv','dist','build','__pycache__','.cache','checkpoints'].includes(e.name))continue;const f=path.join(d,e.name);if(e.isDirectory())q.push(f);else if(e.isFile())out.push(f);if(out.length>=limit)break}}return out}
function load(){const s=fs.statSync(cfgPath).mtimeMs;if(!cfg||s!==cfgM){cfg=readJson(cfgPath);cfgM=s}const mp=path.resolve(path.dirname(cfgPath),cfg.module);const m=fs.statSync(mp).mtimeMs;if(!mod||m!==modM){delete require.cache[require.resolve(mp)];mod=require(mp);modM=m;if(typeof mod.tools!=='function'||typeof mod.call!=='function')throw Error('invalid_agent_module')}}
const helpers=()=>({fs,path,allowed,readText,walk,roots});
function send(res,o){const s=JSON.stringify(o);res.writeHead(200,{'content-type':'application/json','mcp-protocol-version':MCP,'content-length':Buffer.byteLength(s)});res.end(s)}
load();
http.createServer((req,res)=>{try{load()}catch(e){res.writeHead(500);return res.end(String(e.message||e))}
 const u=req.url.split('?',1)[0];
 if(req.method==='GET'&&u==='/health'){const b=JSON.stringify({ok:true,name:cfg.name,version:cfg.version,tool_count:mod.tools(cfg).length,runtime_version:RUNTIME,runtime_mode:cfg.runtime_mode});res.writeHead(200,{'content-type':'application/json','content-length':Buffer.byteLength(b)});return res.end(b)}
 const token=String(process.env[cfg.token_env]||cfg.bearer_token||''),auth=String(req.headers.authorization||'');
 if(req.method!=='POST'||(!['/','/mcp'].includes(u)&&!u.startsWith('/mcp/'))){res.writeHead(404);return res.end()}
 if(!token||(auth!==`Bearer ${token}`&&u.replace(/\/+$/,'')!==`/mcp/${token}`)){res.writeHead(401);return res.end()}
 let b='';req.setEncoding('utf8');req.on('data',c=>{if(b.length<2000000)b+=c});req.on('end',async()=>{let out;try{load();const m=JSON.parse(b||'{}'),id=m.id;if(id===undefined)return res.end();
 if(m.method==='initialize')out={jsonrpc:'2.0',id,result:{protocolVersion:MCP,capabilities:{tools:{listChanged:false}},serverInfo:{name:cfg.id,version:cfg.version},instructions:cfg.instructions}};
 else if(m.method==='ping')out={jsonrpc:'2.0',id,result:{}};
 else if(m.method==='tools/list')out={jsonrpc:'2.0',id,result:{tools:mod.tools(cfg)}};
 else if(m.method==='tools/call'){const p=m.params||{},d=await Promise.resolve(mod.call(cfg,String(p.name||''),p.arguments||{},helpers()));out={jsonrpc:'2.0',id,result:{isError:false,content:[{type:'text',text:JSON.stringify(d)}],structuredContent:d}}}
 else out={jsonrpc:'2.0',id,error:{code:-32601,message:'method_not_found'}}}catch(e){out={jsonrpc:'2.0',id:null,error:{code:-32000,message:String(e.message||e)}}}send(res,out)})}).listen(cfg.port,cfg.host||'127.0.0.1',()=>console.error(`${cfg.name} listening on ${cfg.host||'127.0.0.1'}:${cfg.port}`));
