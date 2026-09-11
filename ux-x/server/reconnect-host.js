const fs = require("fs");
const path = require("path");
const http = require("http");

const MCP_PROTOCOL_VERSION = "2025-06-18";
const ROOT = path.resolve(__dirname, "..");
const DEFAULT_ENTRY = path.join(__dirname, "index.js");
const RUNTIME_CONFIG = path.join(ROOT, ".runtime.json");
const PRIVATE_CONFIG = path.join(ROOT, ".ux-x-private.json");

function readJson(file) {
  try { return JSON.parse(fs.readFileSync(file, "utf8")); } catch { return {}; }
}

function resolvedEntry() {
  return path.resolve(process.env.UX_X_ENTRY || DEFAULT_ENTRY);
}

function sourceFingerprint(entry) {
  const dir = path.dirname(entry);
  const files = [];
  const queue = [dir];
  while (queue.length) {
    const current = queue.shift();
    let entries = [];
    try { entries = fs.readdirSync(current, { withFileTypes: true }); } catch { continue; }
    for (const item of entries) {
      const full = path.join(current, item.name);
      if (item.isDirectory()) queue.push(full);
      else if (item.isFile() && /\.(?:js|json)$/i.test(item.name)) {
        try {
          const st = fs.statSync(full);
          files.push(`${full}:${st.size}:${st.mtimeMs}`);
        } catch {}
      }
    }
  }
  return files.sort().join("|");
}

function clearServerCache(entry) {
  const dir = path.dirname(entry) + path.sep;
  for (const key of Object.keys(require.cache)) {
    if (key === entry || key.startsWith(dir)) delete require.cache[key];
  }
}

function validateModule(mod) {
  if (!mod || typeof mod.status !== "function" || typeof mod.toolSchemas !== "function" || typeof mod.mcpHandle !== "function") {
    throw new Error("invalid_ux_x_module_exports");
  }
  const status = mod.status();
  const schemas = mod.toolSchemas();
  if (!status || status.ok !== true || !status.version) throw new Error("invalid_ux_x_status");
  if (!Array.isArray(schemas) || schemas.length < 1) throw new Error("invalid_ux_x_tool_schemas");
  if (status.tool_count !== schemas.length) throw new Error("ux_x_tool_count_mismatch");  const names = new Set(schemas.map(x => String(x && x.name || "")));
  const required = [
    "ux_status","ux_project_scan","ux_kit_catalog","ux_kit_recommend",
    "ux_research_skill_catalog","ux_research_skill_get","ux_research_skill_resolve",
    "figma_x_status","figma_x_capabilities","figma_x_auth_status","figma_x_file_get",
    "figma_x_nodes_get","figma_x_images_get","figma_x_bridge_status",
    "figma_x_checkpoint_create","figma_x_apply_operations","figma_x_operation_status","figma_x_rollback"
  ];
  for (const name of required) {
    if (!names.has(name)) throw new Error(`ux_x_required_tool_missing:${name}`);
  }
  return { status, schemas };
}

function createReloader(entry = resolvedEntry()) {
  let active = null;
  let fingerprint = null;
  let lastError = null;
  let reloadCount = 0;

  function load(force = false) {
    const nextFingerprint = sourceFingerprint(entry);
    if (!force && active && nextFingerprint === fingerprint) {
      return { changed: false, active, status: active.status(), reloadCount, lastError };
    }

    try {
      clearServerCache(entry);
      const candidate = require(entry);
      const verified = validateModule(candidate);
      active = candidate;
      fingerprint = nextFingerprint;
      lastError = null;
      reloadCount += 1;
      return { changed: true, active, status: verified.status, reloadCount, lastError: null };
    } catch (error) {
      lastError = String(error && error.message ? error.message : error);
      if (!active) throw error;
      return { changed: false, active, status: active.status(), reloadCount, lastError };
    }
  }

  return {
    load,
    state() {
      const loaded = load(false);
      return {
        ok: !!loaded.active,
        active_version: loaded.status && loaded.status.version || null,
        tool_count: loaded.status && loaded.status.tool_count || null,
        reload_count: loaded.reloadCount,
        last_reload_error: loaded.lastError || null,
        source_changed_on_last_check: loaded.changed
      };
    }
  };
}

function bearerToken() {
  const runtime = readJson(RUNTIME_CONFIG);
  const privateCfg = readJson(PRIVATE_CONFIG);
  return String(process.env.UX_X_BEARER_TOKEN || runtime.bearer_token || privateCfg.bearer_token || "");
}

function authorized(req) {
  const token = bearerToken();
  if (!token) return false;
  const auth = String(req.headers.authorization || "");
  const pathname = req.url.split("?", 1)[0].replace(/\/+$/, "");
  return auth === `Bearer ${token}` || pathname === `/mcp/${token}`;
}

function createHttpServer(options = {}) {
  const reloader = options.reloader || createReloader();
  const config = readJson(RUNTIME_CONFIG);
  const host = options.host || process.env.UX_X_HOST || config.host || "127.0.0.1";
  const port = Number(options.port || process.env.UX_X_PORT || 8780);

  return http.createServer((req, res) => {
    const pathname = req.url.split("?", 1)[0];

    if (req.method === "GET" && pathname === "/health") {
      let state;
      try { state = reloader.state(); }
      catch (error) {
        const body = JSON.stringify({ ok: false, name: "ux-x-reconnect-host", error: String(error.message || error) });
        res.writeHead(503, { "content-type": "application/json", "content-length": Buffer.byteLength(body) });
        return res.end(body);
      }
      const body = JSON.stringify({ ok: true, name: "ux-x-reconnect-host", ...state });
      res.writeHead(200, { "content-type": "application/json", "content-length": Buffer.byteLength(body) });
      return res.end(body);
    }

    if (req.method !== "POST" || (!["/", "/mcp"].includes(pathname) && !pathname.startsWith("/mcp/"))) {
      res.writeHead(404);
      return res.end();
    }
    if (!authorized(req)) {
      res.writeHead(401);
      return res.end();
    }

    let body = "";
    req.setEncoding("utf8");
    req.on("data", chunk => { if (body.length < 2000000) body += chunk; });
    req.on("end", async () => {
      try {
        const message = JSON.parse(body || "{}");
        const loaded = reloader.load(false);
        const response = await loaded.active.mcpHandle(message);
        if (response === null) {
          res.writeHead(202);
          return res.end();
        }
        const out = JSON.stringify(response);
        res.writeHead(200, {
          "content-type": "application/json",
          "mcp-protocol-version": MCP_PROTOCOL_VERSION,
          "x-ux-x-version": loaded.status.version,
          "x-ux-x-reload-count": String(loaded.reloadCount),
          "content-length": Buffer.byteLength(out)
        });
        return res.end(out);
      } catch {
        const out = JSON.stringify({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "parse_or_reload_error" } });
        res.writeHead(400, { "content-type": "application/json", "content-length": Buffer.byteLength(out) });
        return res.end(out);
      }
    });
  }).on("listening", () => {
    process.stderr.write(`ux-x reconnect host listening on http://${host}:${port}/mcp\n`);
  });
}

function serveHttp() {
  const config = readJson(RUNTIME_CONFIG);
  const host = process.env.UX_X_HOST || config.host || "127.0.0.1";
  const port = Number(process.env.UX_X_PORT || 8780);
  const server = createHttpServer({ host, port });
  server.listen(port, host);
  return server;
}

function serveStdio() {
  const reloader = createReloader();
  process.stdin.setEncoding("utf8");
  let buffer = "";
  process.stdin.on("data", async chunk => {
    buffer += chunk;
    let index;
    while ((index = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, index).trim();
      buffer = buffer.slice(index + 1);
      if (!line) continue;
      let response;
      try {
        const message = JSON.parse(line);
        const loaded = reloader.load(false);
        response = await loaded.active.mcpHandle(message);
      } catch {
        response = { jsonrpc: "2.0", id: null, error: { code: -32700, message: "parse_or_reload_error" } };
      }
      if (response) process.stdout.write(JSON.stringify(response) + "\n");
    }
  });
}

if (require.main === module) {
  const mode = String(process.argv[2] || "stdio").toLowerCase();
  if (mode === "http") serveHttp();
  else serveStdio();
}

module.exports = {
  createReloader,
  createHttpServer,
  serveHttp,
  serveStdio,
  validateModule,
  sourceFingerprint,
  clearServerCache
};

