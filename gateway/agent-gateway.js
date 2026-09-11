"use strict";

const fs = require("fs");
const path = require("path");
const http = require("http");
const cp = require("child_process");

const ROOT = __dirname;
const CONFIG_PATH = path.join(ROOT, "gateway.config.json");
const CACHE_PATH = path.join(ROOT, "tool-cache.json");
const LOG_PATH = path.join(ROOT, "gateway.log");
const MCP_VERSION = "2025-06-18";

function now() { return new Date().toISOString(); }
function log(msg) {
  const line = `${now()} ${msg}\n`;
  try { fs.appendFileSync(LOG_PATH, line, "utf8"); } catch {}
  process.stderr.write(line);
}
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function readJson(file, fallback = {}) {
  try { return JSON.parse(fs.readFileSync(file, "utf8").replace(/^\uFEFF/, "")); }
  catch { return fallback; }
}
function writeJsonAtomic(file, value) {
  const tmp = file + ".tmp";
  fs.writeFileSync(tmp, JSON.stringify(value, null, 2), "utf8");
  fs.renameSync(tmp, file);
}

const defaultConfig = {
  host: "127.0.0.1",
  port: 8791,
  gateway_token: "",
  refresh_seconds: 300,
  backends: {
    master: { label: "Negin-Master", host: "127.0.0.1", port: 8766, prefix: "master" },
    code: { label: "Code-X", host: "127.0.0.1", port: 8777, prefix: "code" },
    ux: { label: "UX-X", host: "127.0.0.1", port: 8780, prefix: "ux" },
    data: { label: "Data-X", host: "127.0.0.1", port: 8781, prefix: "data" },
    automation: { label: "Automation-X", host: "127.0.0.1", port: 8782, prefix: "automation" }
  }
};

const config = Object.assign({}, defaultConfig, readJson(CONFIG_PATH, {}));
config.backends = Object.assign({}, defaultConfig.backends, config.backends || {});
if (!config.gateway_token) {
  log("FATAL gateway_token missing. Run install.ps1 first.");
  process.exit(2);
}

const tokenCache = new Map();

function envFileValue(file, keys) {
  try {
    const s = fs.readFileSync(file, "utf8");
    for (const line of s.split(/\r?\n/)) {
      const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);
      if (!m) continue;
      const key = m[1];
      let val = m[2].replace(/^['"]|['"]$/g, "");
      if (keys.includes(key) && val.length >= 16) return val;
    }
  } catch {}
  return null;
}

function tokenFromJson(file, envKeys) {
  const obj = readJson(file, null);
  if (!obj) return null;
  const queue = [obj];
  while (queue.length) {
    const cur = queue.shift();
    if (!cur || typeof cur !== "object") continue;
    for (const [k, v] of Object.entries(cur)) {
      if (v && typeof v === "object") queue.push(v);
      if (typeof v !== "string") continue;
      if (envKeys.includes(k) && v.length >= 16) return v;
      if (/^bearer[_-]?token$/i.test(k) && v.length >= 16) return v;
      if (/^token$/i.test(k) && v.length >= 24 && !/^[A-Za-z]:\\/.test(v)) return v;
      if (/token_env/i.test(k) && process.env[v]) return process.env[v];
    }
  }
  return null;
}

function boundedFiles(dir, maxDepth = 3, maxFiles = 250) {
  const out = [];
  function walk(d, depth) {
    if (depth > maxDepth || out.length >= maxFiles) return;
    let entries = [];
    try { entries = fs.readdirSync(d, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (out.length >= maxFiles) break;
      if (["node_modules", ".git", "runs", "backups", "dist", "build", "__pycache__"].includes(e.name)) continue;
      const full = path.join(d, e.name);
      if (e.isDirectory()) walk(full, depth + 1);
      else if (e.isFile()) {
        let st; try { st = fs.statSync(full); } catch { continue; }
        if (st.size > 512 * 1024) continue;
        if (/(\.json|\.env|runtime|config|private|settings)/i.test(e.name)) out.push(full);
      }
    }
  }
  walk(dir, 0);
  return out;
}

function masterTokenFromTailscale() {
  try {
    const s = cp.execFileSync("tailscale", ["serve", "status"], { encoding: "utf8", timeout: 30000 });
    const patterns = [
      /\/mcp\/([A-Za-z0-9._~-]{24,})\s+proxy\s+http:\/\/127\.0\.0\.1:8766\/mcp\//i,
      /\/mcp\/([A-Za-z0-9._~-]{24,})\s+proxy\s+http:\/\/127\.0\.0\.1:8766/i
    ];
    for (const p of patterns) {
      const m = s.match(p);
      if (m) return m[1];
    }
  } catch {}
  return null;
}

const TOKEN_SOURCES = {
  master: {
    env: ["ema_mcp_endpoint_token", "NEGIN_MCP_TOKEN", "NEGIN_MASTER_BEARER_TOKEN", "NEGIN_GATEWAY_API_KEY", "MASTER_BEARER_TOKEN"],
    roots: ["C:\\enterprise-master-agent"],
    files: [
      "C:\\enterprise-master-agent\\.env",
      "C:\\enterprise-master-agent\\gateway\\.env",
      "C:\\enterprise-master-agent\\bridge\\.env",
      "C:\\enterprise-master-agent\\bridge\\.runtime.json"
    ]
  },
  code: {
    env: ["CODE_X_BEARER_TOKEN", "CODEX_BEARER_TOKEN"],
    roots: ["C:\\code-x\\.code-x", "C:\\code-x\\code_x_agent"],
    files: ["C:\\code-x\\.env", "C:\\code-x\\.code-x\\.env"]
  },
  ux: {
    env: ["UX_X_BEARER_TOKEN"],
    roots: ["C:\\code-x\\agents\\ux-x"],
    files: [
      "C:\\code-x\\agents\\ux-x\\.runtime.json",
      "C:\\code-x\\agents\\ux-x\\.ux-x-private.json"
    ]
  },
  data: {
    env: ["DATA_X_BEARER_TOKEN"],
    roots: ["C:\\code-x\\agents\\specialist-host"],
    files: ["C:\\code-x\\agents\\specialist-host\\data-x.json"]
  },
  automation: {
    env: ["AUTOMATION_X_BEARER_TOKEN"],
    roots: ["C:\\code-x\\agents\\specialist-host"],
    files: ["C:\\code-x\\agents\\specialist-host\\automation-x.json"]
  }
};

function discoverToken(name, force = false) {
  const cached = tokenCache.get(name);
  if (!force && cached && (Date.now() - cached.ts) < 60000) return cached.value;

  const src = TOKEN_SOURCES[name] || { env: [], roots: [], files: [] };
  for (const k of src.env) {
    if (process.env[k] && process.env[k].length >= 16) {
      tokenCache.set(name, { ts: Date.now(), value: process.env[k] });
      return process.env[k];
    }
  }

  if (name === "master") {
    const t = masterTokenFromTailscale();
    if (t) {
      tokenCache.set(name, { ts: Date.now(), value: t });
      return t;
    }
  }

  const files = [...src.files];
  for (const r of src.roots) files.push(...boundedFiles(r));
  const seen = new Set();
  for (const f of files) {
    if (seen.has(f)) continue;
    seen.add(f);
    let t = null;
    if (/\.env$/i.test(f) || path.basename(f).toLowerCase().startsWith(".env")) {
      t = envFileValue(f, src.env);
    } else {
      t = tokenFromJson(f, src.env);
    }
    if (t) {
      tokenCache.set(name, { ts: Date.now(), value: t });
      return t;
    }
  }

  tokenCache.set(name, { ts: Date.now(), value: null });
  return null;
}

function httpJson({ host, port, method = "GET", pathname = "/", headers = {}, body = null, timeout = 8000 }) {
  return new Promise((resolve, reject) => {
    const data = body === null ? null : Buffer.from(JSON.stringify(body));
    const h = Object.assign({}, headers);
    if (data) {
      h["content-type"] = "application/json";
      h["content-length"] = data.length;
    }
    const req = http.request({ host, port, method, path: pathname, headers: h }, res => {
      let chunks = "";
      res.setEncoding("utf8");
      res.on("data", c => chunks += c);
      res.on("end", () => {
        let parsed = null;
        try { parsed = chunks ? JSON.parse(chunks) : null; } catch {}
        if (!parsed && chunks) {
          try {
            const payload = chunks
              .split(/\r?\n/)
              .filter(x => x.startsWith("data:"))
              .map(x => x.slice(5).trim())
              .filter(Boolean)
              .join("\n");
            if (payload) parsed = JSON.parse(payload);
          } catch {}
        }
        resolve({ status: res.statusCode || 0, headers: res.headers, text: chunks, json: parsed });
      });
    });
    req.setTimeout(timeout, () => req.destroy(new Error("timeout")));
    req.on("error", reject);
    if (data) req.write(data);
    req.end();
  });
}

async function backendHealth(name) {
  const b = config.backends[name];
  const paths = name === "master" ? ["/health", "/"] : ["/health"];
  for (const p of paths) {
    try {
      const r = await httpJson({ host: b.host, port: b.port, pathname: p, timeout: 3000 });
      if (r.status >= 200 && r.status < 500) {
        return { ok: r.status >= 200 && r.status < 300, status: r.status, body: r.json || r.text };
      }
    } catch (e) {}
  }
  return { ok: false, status: 0, error: "unreachable" };
}

async function callBackend(name, message, attempt = 0) {
  const b = config.backends[name];
  const token = discoverToken(name, attempt > 0);
  const headers = { "mcp-protocol-version": MCP_VERSION, "accept": "application/json, text/event-stream" };
  if (token) headers.authorization = `Bearer ${token}`;

  try {
    const r = await httpJson({
      host: b.host,
      port: b.port,
      method: "POST",
      pathname: (name === "master" && token) ? `/mcp/${token}` : "/mcp",
      headers,
      body: message,
      timeout: 15000
    });
    if (r.status === 401 && token) tokenCache.delete(name);
    if (r.status >= 200 && r.status < 300 && r.json) return r.json;
    throw new Error(`backend_${name}_http_${r.status}`);
  } catch (e) {
    const delays = [1500, 3500, 7000, 12000];
    if (attempt < delays.length) {
      await sleep(delays[attempt]);
      return callBackend(name, message, attempt + 1);
    }
    throw e;
  }
}

function prefixTools(name, tools) {
  const prefix = config.backends[name].prefix;
  return (tools || []).map(t => ({
    ...t,
    name: `${prefix}__${t.name}`,
    description: `[${config.backends[name].label}] ${t.description || ""}`.trim()
  }));
}

function loadCache() {
  return readJson(CACHE_PATH, { updated_at: null, agents: {} });
}
let cache = loadCache();

async function refreshTools() {
  const next = JSON.parse(JSON.stringify(cache || { updated_at: null, agents: {} }));
  next.agents = next.agents || {};
  for (const name of Object.keys(config.backends)) {
    try {
      const msg = { jsonrpc: "2.0", id: `tools-${name}-${Date.now()}`, method: "tools/list", params: {} };
      const r = await callBackend(name, msg);
      const tools = r && r.result && Array.isArray(r.result.tools) ? r.result.tools : null;
      if (!tools) throw new Error("tools_missing");
      next.agents[name] = {
        ok: true,
        label: config.backends[name].label,
        updated_at: now(),
        tools
      };
      log(`tool refresh ${name}: ${tools.length}`);
    } catch (e) {
      const prev = next.agents[name] || {};
      next.agents[name] = { ...prev, ok: false, last_error: String(e.message || e), failed_at: now() };
      log(`tool refresh failed ${name}: ${e.message || e}`);
    }
  }
  next.updated_at = now();
  cache = next;
  try { writeJsonAtomic(CACHE_PATH, cache); } catch (e) { log(`cache write failed: ${e.message}`); }
  return cache;
}

async function aggregateStatus() {
  const agents = {};
  for (const name of Object.keys(config.backends)) {
    agents[name] = await backendHealth(name);
    agents[name].token_discovered = !!discoverToken(name);
    agents[name].cached_tools = (((cache || {}).agents || {})[name] || {}).tools?.length || 0;
  }
  const healthy = Object.values(agents).filter(x => x.ok).length;
  return {
    ok: healthy === Object.keys(config.backends).length,
    healthy_agents: healthy,
    total_agents: Object.keys(config.backends).length,
    gateway: { host: config.host, port: config.port, cache_updated_at: cache.updated_at || null },
    agents
  };
}

function authorized(req) {
  const auth = String(req.headers.authorization || "");
  const pathname = String(req.url || "").split("?", 1)[0].replace(/\/+$/, "");
  return auth === `Bearer ${config.gateway_token}` || pathname === `/mcp/${config.gateway_token}`;
}

function sendJson(res, status, obj, extra = {}) {
  const s = JSON.stringify(obj);
  res.writeHead(status, {
    "content-type": "application/json",
    "content-length": Buffer.byteLength(s),
    "mcp-protocol-version": MCP_VERSION,
    ...extra
  });
  res.end(s);
}

function builtInTools() {
  return [
    {
      name: "gateway_status",
      description: "Return unified health/status for Negin-Master, Code-X, UX-X, Data-X and Automation-X.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false }
    },
    {
      name: "gateway_refresh_tools",
      description: "Refresh cached tool schemas from all five local agents without changing connectors.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false }
    }
  ];
}

function allTools() {
  const out = [...builtInTools()];
  for (const name of Object.keys(config.backends)) {
    const entry = (((cache || {}).agents || {})[name] || {});
    out.push(...prefixTools(name, entry.tools || []));
  }
  return out;
}

async function handleRpc(msg) {
  const id = msg.id;
  if (msg.method === "initialize") {
    return {
      jsonrpc: "2.0", id,
      result: {
        protocolVersion: MCP_VERSION,
        capabilities: { tools: { listChanged: true } },
        serverInfo: { name: "hagents-unified-gateway", version: "1.1.0" },
        instructions: "Stable unified gateway for Negin-Master, Code-X, UX-X, Data-X and Automation-X. Agent upgrades do not change this connector URL."
      }
    };
  }
  if (msg.method === "ping") return { jsonrpc: "2.0", id, result: {} };
  if (msg.method === "tools/list") {
    if (!cache.updated_at) await refreshTools();
    return { jsonrpc: "2.0", id, result: { tools: allTools() } };
  }
  if (msg.method === "tools/call") {
    const p = msg.params || {};
    const toolName = String(p.name || "");
    if (toolName === "gateway_status") {
      const status = await aggregateStatus();
      return { jsonrpc: "2.0", id, result: { isError: false, content: [{ type: "text", text: JSON.stringify(status) }], structuredContent: status } };
    }
    if (toolName === "gateway_refresh_tools") {
      const c = await refreshTools();
      const result = { ok: true, updated_at: c.updated_at, tool_count: allTools().length };
      return { jsonrpc: "2.0", id, result: { isError: false, content: [{ type: "text", text: JSON.stringify(result) }], structuredContent: result } };
    }

    const m = toolName.match(/^(master|code|ux|data|automation)__(.+)$/);
    if (!m) return { jsonrpc: "2.0", id, error: { code: -32601, message: "unknown_gateway_tool" } };

    const [, name, originalName] = m;
    const forwarded = {
      jsonrpc: "2.0",
      id,
      method: "tools/call",
      params: { name: originalName, arguments: p.arguments || {} }
    };
    try {
      return await callBackend(name, forwarded);
    } catch (e) {
      return { jsonrpc: "2.0", id, error: { code: -32000, message: `agent_unavailable:${name}:${e.message || e}` } };
    }
  }
  return { jsonrpc: "2.0", id, error: { code: -32601, message: "method_not_found" } };
}

const server = http.createServer(async (req, res) => {
  const pathname = String(req.url || "").split("?", 1)[0];

  if (req.method === "GET" && (pathname === "/health" || pathname === "/health/all")) {
    try { return sendJson(res, 200, await aggregateStatus()); }
    catch (e) { return sendJson(res, 503, { ok: false, error: String(e.message || e) }); }
  }

  if (req.method !== "POST" || !(pathname === "/" || pathname === "/mcp" || pathname.startsWith("/mcp/"))) {
    res.writeHead(404); return res.end();
  }
  if (!authorized(req)) {
    res.writeHead(401); return res.end();
  }

  let body = "";
  req.setEncoding("utf8");
  req.on("data", c => { if (body.length < 4_000_000) body += c; });
  req.on("end", async () => {
    let msg;
    try { msg = JSON.parse(body || "{}"); }
    catch { return sendJson(res, 400, { jsonrpc: "2.0", id: null, error: { code: -32700, message: "parse_error" } }); }

    if (msg.id === undefined) {
      res.writeHead(202); return res.end();
    }
    try {
      const out = await handleRpc(msg);
      return sendJson(res, 200, out, { "x-hagents-gateway": "1.1.0" });
    } catch (e) {
      return sendJson(res, 500, { jsonrpc: "2.0", id: msg.id ?? null, error: { code: -32000, message: String(e.message || e) } });
    }
  });
});

server.listen(Number(config.port || 8791), config.host || "127.0.0.1", async () => {
  log(`listening http://${config.host || "127.0.0.1"}:${config.port || 8791}/mcp`);
  try { await refreshTools(); } catch {}
});

setInterval(() => refreshTools().catch(() => {}), Math.max(60, Number(config.refresh_seconds || 300)) * 1000).unref();

