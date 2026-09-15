"use strict";
const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = 3000;
const GATEWAY_HOST = process.env.GATEWAY_HOST || "gateway";
const GATEWAY_PORT = Number(process.env.GATEWAY_PORT || 8791);
const GATEWAY_TOKEN = process.env.GATEWAY_TOKEN || "";

const HTML_PATH = path.join(__dirname, "index.html");

function gatewayRequest(p, method = "GET", body = null) {
  return new Promise((resolve) => {
    const data = body ? Buffer.from(JSON.stringify(body)) : null;
    const headers = { "accept": "application/json" };
    if (data) {
      headers["content-type"] = "application/json";
      headers["content-length"] = data.length;
    }
    if (GATEWAY_TOKEN) headers.authorization = `Bearer ${GATEWAY_TOKEN}`;
    const req = http.request(
      { host: GATEWAY_HOST, port: GATEWAY_PORT, method, path: p, headers, timeout: 8000 },
      (res) => {
        let raw = "";
        res.setEncoding("utf8");
        res.on("data", (c) => (raw += c));
        res.on("end", () => {
          let json = null;
          try { json = raw ? JSON.parse(raw) : null; } catch {}
          resolve({ status: res.statusCode, json, text: raw });
        });
      }
    );
    req.on("error", () => resolve({ status: 0, json: null, text: "" }));
    req.on("timeout", () => req.destroy(new Error("timeout")));
    if (data) req.write(data);
    req.end();
  });
}

const server = http.createServer(async (req, res) => {
  const url = req.url.split("?")[0];

  if (url === "/" || url === "/index.html") {
    try {
      const html = fs.readFileSync(HTML_PATH, "utf8");
      res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
      return res.end(html);
    } catch {
      res.writeHead(500);
      return res.end("dashboard html not found");
    }
  }

  if (url === "/api/status") {
    const r = await gatewayRequest("/health/all");
    if (r.json) {
      res.writeHead(200, { "content-type": "application/json" });
      return res.end(JSON.stringify(r.json));
    }
    res.writeHead(502, { "content-type": "application/json" });
    return res.end(JSON.stringify({ ok: false, error: "gateway_unreachable", status: r.status }));
  }

  if (url === "/api/tools") {
    const r = await gatewayRequest("/mcp", "POST", {
      jsonrpc: "2.0",
      id: `dashboard-${Date.now()}`,
      method: "tools/list",
      params: {},
    });
    if (r.json) {
      res.writeHead(200, { "content-type": "application/json" });
      return res.end(JSON.stringify(r.json));
    }
    res.writeHead(502, { "content-type": "application/json" });
    return res.end(JSON.stringify({ ok: false, error: "gateway_unreachable" }));
  }

  if (url === "/api/refresh") {
    const r = await gatewayRequest("/mcp", "POST", {
      jsonrpc: "2.0",
      id: `dashboard-refresh-${Date.now()}`,
      method: "tools/call",
      params: { name: "gateway_refresh_tools", arguments: {} },
    });
    if (r.json) {
      res.writeHead(200, { "content-type": "application/json" });
      return res.end(JSON.stringify(r.json));
    }
    res.writeHead(502, { "content-type": "application/json" });
    return res.end(JSON.stringify({ ok: false, error: "gateway_unreachable" }));
  }

  res.writeHead(404);
  res.end();
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`dashboard listening on http://0.0.0.0:${PORT}`);
});
