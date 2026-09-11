import express from "express";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";

const here = path.dirname(fileURLToPath(import.meta.url));
const databases = ["NeginPakhsh", "Cloud", "grs"];
const defaultHost = "127.0.0.1";
const defaultPort = 8770;
const helperTimeoutMs = 20_000;
const helperMaxBytes = 2 * 1024 * 1024;

function normalizeSql(sql) {
  return ` ${String(sql || "").trim().replace(/\s+/g, " ").toLowerCase()} `;
}

export function assertReadOnlySql(sql) {
  const raw = String(sql || "");
  if (raw.length < 1 || raw.length > 20_000) throw new Error("sql length must be 1..20000");
  const s = normalizeSql(raw);
  const start = raw.trimStart().toLowerCase();
  if (!(start.startsWith("select ") || start.startsWith("select\n") || start.startsWith("select\t") ||
        start.startsWith("with ") || start.startsWith("with\n") || start.startsWith("with\t"))) {
    throw new Error("SELECT/CTE only");
  }

  const literalBlocks = [";", "--", "/*", "*/"];
  for (const token of literalBlocks) {
    if (raw.includes(token)) throw new Error(`forbidden sql token: ${token}`);
  }

  const blockedWords = [
    "insert", "update", "delete", "merge", "drop", "alter", "create", "truncate",
    "exec", "execute", "dbcc", "into", "use", "grant", "revoke", "deny",
    "backup", "restore", "reconfigure", "shutdown", "kill", "waitfor", "bulk",
    "openrowset", "openquery", "opendatasource"
  ];
  for (const word of blockedWords) {
    const rx = new RegExp(`\\b${word}\\b`, "i");
    if (rx.test(raw)) throw new Error(`forbidden sql token: ${word}`);
  }

  if (/\bnext\s+value\s+for\b/i.test(raw)) throw new Error("sequences are not allowed");
  if (/\bxp_[a-z0-9_]*\b/i.test(raw) || /\bsp_oa[a-z0-9_]*\b/i.test(raw)) {
    throw new Error("extended procedures are not allowed");
  }

  // Prevent bypassing the selected database with explicit three-part names.
  const threePart = /(?:\[[^\]]+\]|[a-z_][\w$]*)\s*\.\s*(?:\[[^\]]+\]|[a-z_][\w$]*)\s*\.\s*(?:\[[^\]]+\]|[a-z_][\w$]*)/i;
  if (threePart.test(raw)) throw new Error("cross-database three-part identifiers are not allowed");

  return true;
}

function clamp(value, min, max, fallback) {
  const n = Number.isFinite(Number(value)) ? Math.trunc(Number(value)) : fallback;
  return Math.max(min, Math.min(max, n));
}

function pythonExe() {
  if (process.env.varanegar_python_exe) return process.env.varanegar_python_exe;
  const venv = "c:\\enterprise-master-agent\\.venv\\scripts\\python.exe";
  return fs.existsSync(venv) ? venv : "python";
}

function callHelper(action, payload = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(pythonExe(), [path.join(here, "db_helper.py")], {
      cwd: here,
      env: process.env,
      windowsHide: true,
      stdio: ["pipe", "pipe", "pipe"],
    });

    let stdout = Buffer.alloc(0);
    let stderr = "";
    let settled = false;

    const finishReject = (error) => {
      if (settled) return;
      settled = true;
      try { child.kill(); } catch {}
      reject(error);
    };

    const timer = setTimeout(() => finishReject(new Error("database helper timeout")), helperTimeoutMs);

    child.stdout.on("data", (chunk) => {
      if (settled) return;
      stdout = Buffer.concat([stdout, chunk]);
      if (stdout.length > helperMaxBytes) finishReject(new Error("database result exceeded 2 MiB"));
    });
    child.stderr.on("data", (chunk) => {
      if (stderr.length < 4096) stderr += chunk.toString("utf8");
    });
    child.on("error", (error) => finishReject(error));
    child.on("close", (code) => {
      clearTimeout(timer);
      if (settled) return;
      settled = true;
      const text = stdout.toString("utf8").trim();
      if (code !== 0) return reject(new Error(stderr.trim() || text || `helper exited ${code}`));
      try {
        const parsed = JSON.parse(text || "{}");
        if (!parsed.ok) return reject(new Error(parsed.error || "database helper failed"));
        resolve(parsed);
      } catch (error) {
        reject(new Error(`invalid helper response: ${error.message}`));
      }
    });

    child.stdin.end(JSON.stringify({ action, ...payload }));
  });
}

function result(data) {
  return {
    content: [{ type: "text", text: JSON.stringify(data) }],
    structuredContent: data,
  };
}

function makeServer() {
  const server = new McpServer(
    { name: "negin-varanegar-readonly", version: "0.1.0" },
    {
      instructions:
        "Strict read-only Varanegar SQL MCP. Use schema discovery before business queries. " +
        "Never attempt writes, DDL, EXEC, DBCC, cross-database three-part identifiers, or unbounded extraction.",
    }
  );

  const dbSchema = z.enum(databases);

  server.tool(
    "varanegar_health",
    "Verify strict read-only connectivity and identity for one Varanegar database.",
    { database: dbSchema.optional() },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ database }) => result(await callHelper("health", { database: database || "NeginPakhsh" }))
  );

  server.tool(
    "varanegar_database_list",
    "List the allowlisted Varanegar databases and verify which are accessible using Negin_Report_ReadOnly.",
    {},
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async () => result(await callHelper("databases"))
  );

  server.tool(
    "varanegar_permission_audit",
    "Inspect the connected identity, database roles, and any detected write-capable grants. The tool refuses unsafe identities.",
    { database: dbSchema },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ database }) => result(await callHelper("permissions", { database }))
  );

  server.tool(
    "varanegar_schema_search",
    "Search table, view, procedure, function, schema, and column names without scanning business data.",
    {
      database: dbSchema,
      terms: z.array(z.string().min(1).max(100)).min(1).max(12),
      max_rows: z.number().int().min(1).max(500).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ database, terms, max_rows }) =>
      result(await callHelper("schema_search", {
        database,
        terms,
        max_rows: clamp(max_rows, 1, 500, 200),
      }))
  );

  server.tool(
    "varanegar_catalog",
    "List bounded schema objects from the selected Varanegar database.",
    {
      database: dbSchema,
      schema: z.string().min(1).max(128).optional(),
      object_type: z.enum(["all", "table", "view", "procedure", "function"]).optional(),
      max_rows: z.number().int().min(1).max(1000).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ database, schema, object_type, max_rows }) =>
      result(await callHelper("catalog", {
        database,
        schema,
        object_type: object_type || "all",
        max_rows: clamp(max_rows, 1, 1000, 300),
      }))
  );

  server.tool(
    "varanegar_relationships",
    "Read bounded foreign-key relationships from SQL Server metadata.",
    {
      database: dbSchema,
      schema: z.string().min(1).max(128).optional(),
      max_rows: z.number().int().min(1).max(1000).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ database, schema, max_rows }) =>
      result(await callHelper("relationships", {
        database,
        schema,
        max_rows: clamp(max_rows, 1, 1000, 300),
      }))
  );

  server.tool(
    "varanegar_table_sample",
    "Read a very small sample from one explicitly named table or view after identifier validation.",
    {
      database: dbSchema,
      schema: z.string().min(1).max(128),
      table: z.string().min(1).max(128),
      limit: z.number().int().min(1).max(50).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ database, schema, table, limit }) =>
      result(await callHelper("table_sample", {
        database,
        schema,
        table,
        limit: clamp(limit, 1, 50, 10),
      }))
  );

  server.tool(
    "varanegar_readonly_query",
    "Run one bounded SELECT/CTE in exactly one allowlisted Varanegar database. A second SQL firewall runs in the Python database helper.",
    {
      database: dbSchema,
      sql: z.string().min(1).max(20_000),
      max_rows: z.number().int().min(1).max(1000).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ database, sql, max_rows }) => {
      assertReadOnlySql(sql);
      return result(await callHelper("query", {
        database,
        sql,
        max_rows: clamp(max_rows, 1, 1000, 200),
      }));
    }
  );

  return server;
}

function requiredToken() {
  const token = String(process.env.varanegar_mcp_token || "").trim();
  if (token.length < 32) throw new Error("varanegar_mcp_token must be configured with at least 32 characters");
  return token;
}

async function main() {
  const host = process.env.varanegar_mcp_host || defaultHost;
  const port = clamp(process.env.varanegar_mcp_port, 1, 65535, defaultPort);
  const allowRemote = process.env.varanegar_mcp_allow_remote === "1";
  if (!["127.0.0.1", "localhost", "::1"].includes(host) && !allowRemote) {
    throw new Error("remote bind blocked; set varanegar_mcp_allow_remote=1 only after an explicit security review");
  }

  const token = requiredToken();
  const app = express();
  app.disable("x-powered-by");
  app.use(express.json({ limit: "1mb" }));

  function requireBearer(req, res, next) {
    const auth = req.headers.authorization || "";
    if (auth !== `Bearer ${token}`) {
      res.set("WWW-Authenticate", 'Bearer realm="negin-varanegar-readonly-mcp"');
      return res.status(401).json({ error: "unauthorized" });
    }
    next();
  }

  app.get("/health", (_req, res) => {
    res.json({
      ok: true,
      service: "negin-varanegar-readonly-mcp",
      mode: "strict-readonly",
      host,
      port,
      databases,
      sql_env_configured: Boolean(
        process.env.negin_sql_server &&
        process.env.negin_sql_username &&
        process.env.negin_sql_password
      ),
    });
  });

  const transports = new Map();
  const sessionServers = new Map();

  function requestSessionId(req) {
    const raw = req.headers["mcp-session-id"];
    return typeof raw === "string" ? raw : "";
  }

  app.post("/mcp", requireBearer, async (req, res) => {
    const sid = requestSessionId(req);
    let transport;
    try {
      if (sid && transports.has(sid)) {
        transport = transports.get(sid);
      } else if (!sid && req.body?.method === "initialize") {
        const server = makeServer();
        transport = new StreamableHTTPServerTransport({
          sessionIdGenerator: () => randomUUID(),
          onsessioninitialized: (newSid) => {
            transports.set(newSid, transport);
            sessionServers.set(newSid, server);
          },
        });
        transport.onclose = () => {
          const currentSid = transport.sessionId;
          if (currentSid) {
            transports.delete(currentSid);
            const srv = sessionServers.get(currentSid);
            sessionServers.delete(currentSid);
            try {
              const p = srv?.close?.();
              if (p?.catch) p.catch(() => {});
            } catch {}
          }
        };
        await server.connect(transport);
      } else {
        return res.status(400).json({
          jsonrpc: "2.0",
          error: { code: -32000, message: "Bad Request: No valid session ID provided" },
          id: null,
        });
      }
      await transport.handleRequest(req, res, req.body);
    } catch (error) {
      console.error("varanegar mcp POST failed:", error?.message || error);
      if (!res.headersSent) {
        res.status(500).json({
          jsonrpc: "2.0",
          error: { code: -32603, message: "Internal MCP transport error" },
          id: null,
        });
      }
    }
  });

  app.get("/mcp", requireBearer, async (req, res) => {
    const sid = requestSessionId(req);
    if (!sid || !transports.has(sid)) return res.status(400).send("Invalid or missing session ID");
    try {
      await transports.get(sid).handleRequest(req, res);
    } catch {
      if (!res.headersSent) res.status(500).send("SSE stream error");
    }
  });

  app.delete("/mcp", requireBearer, async (req, res) => {
    const sid = requestSessionId(req);
    if (!sid || !transports.has(sid)) return res.status(400).send("Invalid or missing session ID");
    try {
      await transports.get(sid).handleRequest(req, res);
    } catch {
      if (!res.headersSent) res.status(500).send("Session termination error");
    }
  });

  app.head("/mcp", requireBearer, (_req, res) => res.status(200).end());

  app.listen(port, host, () => {
    console.log(`negin varanegar readonly mcp listening on http://${host}:${port}/mcp`);
  });
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(error?.message || error);
    process.exit(1);
  });
}
