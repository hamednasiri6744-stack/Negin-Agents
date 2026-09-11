import express from "express";
import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";

const core = process.env.ema_core_url || "http://127.0.0.1:8765";

async function coreJson(path, options = {}) {
  const response = await fetch(`${core}${path}`, {
    ...options,
    headers: { "content-type": "application/json", ...(options.headers || {}) },
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`core ${response.status}: ${text.slice(0, 1000)}`);
  return text ? JSON.parse(text) : {};
}

function result(data) {
  return {
    content: [{ type: "text", text: JSON.stringify(data) }],
    structuredContent: data,
  };
}


// ema-skill-registry-helpers-v1
const skillsRoot =
  process.env.ema_skills_root ||
  "c:\\enterprise-master-agent\\.agents\\skills";

function skillMeta(raw, key) {
  const fm = raw.match(/^---\s*\r?\n([\s\S]*?)\r?\n---/);
  if (!fm) return "";

  const line = fm[1]
    .split(/\r?\n/)
    .find((x) => x.trimStart().toLowerCase().startsWith(`${key.toLowerCase()}:`));

  if (!line) return "";

  let value = line.slice(line.indexOf(":") + 1).trim();

  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    value = value.slice(1, -1);
  }

  return value.replace(/\\"/g, '"');
}

function loadSkills() {
  const result = [];

  if (!fs.existsSync(skillsRoot)) return result;

  function walk(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        walk(full);
        continue;
      }

      if (!entry.isFile() || entry.name.toLowerCase() !== "skill.md") continue;

      const raw = fs.readFileSync(full, "utf8");
      const fallbackName = path.basename(path.dirname(full));

      result.push({
        name: skillMeta(raw, "name") || fallbackName,
        description: skillMeta(raw, "description"),
        category: skillMeta(raw, "category") || "uncategorized",
        relativePath: path.relative(skillsRoot, full),
        content: raw,
      });
    }
  }

  walk(skillsRoot);

  return result.sort((a, b) => a.name.localeCompare(b.name));
}

function tokenizeSkillText(value) {
  return (
    String(value || "")
      .toLowerCase()
      .match(/[\p{L}\p{N}][\p{L}\p{N}_-]{1,}/gu) || []
  );
}

const skillAliases = {
  python: ["\u067e\u0627\u06cc\u062a\u0648\u0646"],
  nodejs: ["\u0646\u0648\u062f","node"],
  typescript: ["\u062a\u0627\u06cc\u067e \u0627\u0633\u06a9\u0631\u06cc\u067e\u062a"],
  react: ["\u0631\u06cc \u0627\u06a9\u062a","\u0641\u0631\u0627\u0646\u062a","frontend"],
  nextjs: ["\u0646\u06a9\u0633\u062a"],
  api: ["api","\u0627\u06cc \u067e\u06cc \u0622\u06cc","\u0628\u06a9 \u0627\u0646\u062f","backend"],
  mcp: ["mcp","\u0627\u0645 \u0633\u06cc \u067e\u06cc"],
  database: ["\u062f\u06cc\u062a\u0627\u0628\u06cc\u0633","\u067e\u0627\u06cc\u06af\u0627\u0647 \u062f\u0627\u062f\u0647","sql"],
  testing: ["\u062a\u0633\u062a","\u0622\u0632\u0645\u0627\u06cc\u0634"],
  debugging: ["\u062f\u06cc\u0628\u0627\u06af","\u0628\u0627\u06af","\u062e\u0637\u0627","\u0627\u0631\u0648\u0631"],
  security: ["\u0627\u0645\u0646\u06cc\u062a"],
  performance: ["\u06a9\u0627\u0631\u0627\u06cc\u06cc","\u0633\u0631\u0639\u062a","\u06a9\u0646\u062f\u06cc","latency"],
  devops: ["\u062f\u0648\u0627\u067e\u0633","\u06a9\u0627\u0646\u062a\u06cc\u0646\u0631","docker","podman"],
  powershell: ["\u067e\u0627\u0648\u0631\u0634\u0644","\u0648\u06cc\u0646\u062f\u0648\u0632"],
  sales: ["\u0641\u0631\u0648\u0634","\u0648\u06cc\u0632\u06cc\u062a","\u0648\u06cc\u0632\u06cc\u062a\u0648\u0631"],
  customer: ["\u0645\u0634\u062a\u0631\u06cc"],
  inventory: ["\u0627\u0646\u0628\u0627\u0631","\u0645\u0648\u062c\u0648\u062f\u06cc"],
  finance: ["\u0645\u0627\u0644\u06cc","\u062d\u0633\u0627\u0628\u062f\u0627\u0631\u06cc"],
  treasury: ["\u062e\u0632\u0627\u0646\u0647","\u0646\u0642\u062f\u06cc\u0646\u06af\u06cc","\u062f\u0631\u06cc\u0627\u0641\u062a","\u067e\u0631\u062f\u0627\u062e\u062a"],
  receivables: ["\u0645\u0637\u0627\u0644\u0628\u0627\u062a","\u0648\u0635\u0648\u0644"],
  payroll: ["\u062d\u0642\u0648\u0642","\u062f\u0633\u062a\u0645\u0632\u062f"],
  hr: ["\u0645\u0646\u0627\u0628\u0639 \u0627\u0646\u0633\u0627\u0646\u06cc","\u067e\u0631\u0633\u0646\u0644"],
  management: ["\u0645\u062f\u06cc\u0631\u06cc\u062a","\u0645\u062f\u06cc\u0631"],
  procurement: ["\u062e\u0631\u06cc\u062f","\u062a\u0627\u0645\u06cc\u0646","\u062a\u0623\u0645\u06cc\u0646"],
  logistics: ["\u0644\u062c\u0633\u062a\u06cc\u06a9","\u062a\u0648\u0632\u06cc\u0639","\u0627\u0631\u0633\u0627\u0644"],
  demand: ["\u062a\u0642\u0627\u0636\u0627","\u067e\u06cc\u0634\u200c\u0628\u06cc\u0646\u06cc"],
  pricing: ["\u0642\u06cc\u0645\u062a","\u062a\u062e\u0641\u06cc\u0641","\u067e\u0631\u0648\u0645\u0648\u0634\u0646"],
  scenario: ["\u0633\u0646\u0627\u0631\u06cc\u0648","what if"],
  root: ["\u0631\u06cc\u0634\u0647","\u0639\u0644\u062a","\u0639\u0644\u062a\u200c\u06cc\u0627\u0628\u06cc"],
  refactoring: ["\u0631\u06cc\u0641\u06a9\u062a\u0648\u0631","\u0628\u0627\u0632\u0622\u0631\u0627\u06cc\u06cc"]
};

function skillAliasText(name) {
  const n = name.toLowerCase();
  const result = [];

  for (const [key, aliases] of Object.entries(skillAliases)) {
    if (n.includes(key)) result.push(...aliases);
  }

  return result.join(" ");
}

function rankSkills(task, limit = 5) {
  const queryTokens = [...new Set(tokenizeSkillText(task))]
    .filter((x) => x.length >= 2);

  return loadSkills()
    .map((skill) => {
      const nameText = skill.name.toLowerCase();
      const descText = skill.description.toLowerCase();
      const aliasText = skillAliasText(skill.name).toLowerCase();
      const contentText = skill.content.toLowerCase();

      let score = 0;

      for (const token of queryTokens) {
        if (nameText.includes(token)) score += 12;
        if (aliasText.includes(token)) score += 10;
        if (descText.includes(token)) score += 5;
        if (contentText.includes(token)) score += 1;
      }

      return {
        name: skill.name,
        description: skill.description,
        category: skill.category,
        score,
      };
    })
    .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name))
    .slice(0, limit);
}

function skillToolResult(value) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(value, null, 2),
      },
    ],
  };
}

function makeServer() {
  const server = new McpServer({ name: "enterprise-master-agent", version: "0.1.0" }, { instructions: "For specialist engineering or enterprise-domain tasks, first call skill_resolve. Then call skill_get for the smallest relevant skill set before execution. Follow the loaded workflow and guardrails. After execution, verify the result. Do not use skill routing for trivial status checks." });

  server.tool(
    "agent_status",
    "Use this when you need to verify that the Enterprise Master Agent is online.",
    {},
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async () => result(await coreJson("/health"))
  );

  server.tool(
    "agent_capabilities",
    "Use this before planning work that may require local, data, RPA, workflow, or delegated capabilities.",
    {},
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async () => result(await coreJson("/capabilities"))
  );

  server.tool(
    "enterprise_semantic_resolve",
    "Use this to map Persian organizational language to canonical business semantics.",
    { text: z.string().min(1) },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ text }) => result(await coreJson("/semantic/resolve", {
      method: "POST",
      body: JSON.stringify({ text }),
    }))
  );

  server.tool(
    "enterprise_query_plan",
    "Use this to select the fastest safe data path; production read-only must remain last resort.",
    { availability: z.record(z.boolean()) },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ availability }) => result(await coreJson("/query/plan", {
      method: "POST",
      body: JSON.stringify({ availability }),
    }))
  );

  server.tool(
    "agent_execute_local_shell",
    "Use this only for guarded execution on the local workstation. Never target the production server.",
    {
      command: z.string().min(1),
      cwd: z.string().optional(),
      timeout: z.number().int().min(1).max(120).optional(),
    },
    { readOnlyHint: false, destructiveHint: true, openWorldHint: false },
    async ({ command, cwd, timeout }) => result(await coreJson("/shell/run", {
      method: "POST",
      body: JSON.stringify({ command, cwd, timeout: timeout || 120 }),
    }))
  );

  server.tool(
    "agent_require_capability",
    "Use this when a required capability is missing. It checkpoints the task and returns the exact capability gap for owner approval.",
    {
      capability: z.string().min(1),
      intent: z.string().min(1),
    },
    { readOnlyHint: false, destructiveHint: false, openWorldHint: false, idempotentHint: true },
    async ({ capability, intent }) => result(await coreJson("/capability/require", {
      method: "POST",
      body: JSON.stringify({ capability, intent }),
    }))
  );


  server.tool(
    "remote_server_performance_readonly",
    "Use this only for owner-approved read-only diagnostics of an allowlisted Windows server. It reads fixed CPU, RAM, paging, disk, network and process telemetry only; no arbitrary command or mutation is available.",
    {
      target: z.string().min(1).max(253).optional(),
      top_n: z.number().int().min(5).max(30).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: true },
    async ({ target, top_n }) => result(await coreJson("/skills/remote-server/performance-readonly", {
      method: "POST",
      body: JSON.stringify({ target: target || "servernew", top_n: top_n || 12 }),
    }))
  );

  server.tool(
    "wol_generate_script",
    "Use this to generate, never execute, a Wake-on-LAN PowerShell script for manual server-side execution by the owner.",
    {
      mac: z.string().min(11),
      broadcast: z.string().min(7),
      port: z.number().int().min(1).max(65535).optional(),
    },
    { readOnlyHint: false, destructiveHint: false, openWorldHint: false, idempotentHint: true },
    async ({ mac, broadcast, port }) => result(await coreJson("/wol/script", {
      method: "POST",
      body: JSON.stringify({ mac, broadcast, port: port || 9 }),
    }))
  );

  // ema-knowledge-tools-v1
  server.tool(
    "knowledge_import",
    "Import one approved local Markdown ZIP as verified, versioned, read-only knowledge. This never installs or overwrites skills.",
    {
      archive_path: z.string().min(1).max(1000),
      expected_sha256: z.string().regex(/^[a-f0-9]{64}$/i),
    },
    {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
    async ({ archive_path, expected_sha256 }) => result(await coreJson("/knowledge/import", {
      method: "POST",
      body: JSON.stringify({ archive_path, expected_sha256 }),
    }))
  );

  server.tool(
    "knowledge_status",
    "Read the active knowledge version and the verified import history.",
    {},
    {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
    async () => result(await coreJson("/knowledge/status"))
  );

  server.tool(
    "knowledge_search",
    "Search the active imported knowledge without activating captured skills.",
    {
      query: z.string().min(1).max(1000),
      limit: z.number().int().min(1).max(50).optional(),
    },
    {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
    async ({ query, limit }) => result(await coreJson("/knowledge/search", {
      method: "POST",
      body: JSON.stringify({ query, limit: limit || 10 }),
    }))
  );

  server.tool(
    "knowledge_rollback",
    "Activate a previously verified knowledge version without deleting content. Use only after explicit owner approval.",
    {
      version_id: z.string().min(1).max(300).optional(),
    },
    {
      readOnlyHint: false,
      destructiveHint: true,
      idempotentHint: true,
      openWorldHint: false,
    },
    async ({ version_id }) => result(await coreJson("/knowledge/rollback", {
      method: "POST",
      body: JSON.stringify({ version_id }),
    }))
  );

  // ema-skill-registry-tools-v1

  server.tool(
    "skill_catalog",
    "List specialist skills installed for Negin Agents. Use this when you need to discover which domain or engineering skills are available before performing specialist work.",
    {
      query: z.string().optional(),
    },
    {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
    async ({ query }) => {
      let skills = loadSkills().map(({ content, ...meta }) => meta);

      if (query) {
        const q = query.toLowerCase();

        skills = skills.filter(
          (x) =>
            x.name.toLowerCase().includes(q) ||
            x.description.toLowerCase().includes(q) ||
            x.category.toLowerCase().includes(q)
        );
      }

      return skillToolResult({
        root: skillsRoot,
        count: skills.length,
        skills,
      });
    }
  );

  server.tool(
    "skill_resolve",
    "Resolve a user task to the most relevant Negin specialist skills. Use this before specialist engineering or enterprise work, then load the selected skill with skill_get.",
    {
      task: z.string().min(2),
      limit: z.number().int().min(1).max(10).optional(),
    },
    {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
    async ({ task, limit }) => {
      const matches = rankSkills(task, limit || 5);

      return skillToolResult({
        task,
        matches,
        instruction:
          "Select the smallest relevant skill set. Load each selected skill with skill_get before executing the specialist task.",
      });
    }
  );

  server.tool(
    "skill_get",
    "Load the full SKILL.md instructions for one exact installed Negin skill. Use after skill_resolve or skill_catalog and follow the returned workflow and guardrails.",
    {
      name: z.string().min(1),
    },
    {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
    async ({ name }) => {
      const skill = loadSkills().find(
        (x) => x.name.toLowerCase() === name.toLowerCase()
      );

      if (!skill) {
        return skillToolResult({
          ok: false,
          error: "skill_not_found",
          requested: name,
          available: loadSkills().map((x) => x.name),
        });
      }

      return skillToolResult({
        ok: true,
        name: skill.name,
        category: skill.category,
        description: skill.description,
        path: skill.relativePath,
        skill: skill.content,
      });
    }
  );

  // ema-integration-tools-v1
  server.tool(
    "integrations_health",
    "Check live local ClickHouse, n8n, and RPA capability health.",
    {},
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async () => result(await coreJson("/integrations/health"))
  );

  server.tool(
    "clickhouse_query",
    "Run a read-only analytical ClickHouse query on the local enterprise analytics plane.",
    { sql: z.string().min(1).max(20000) },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ sql }) => result(await coreJson("/clickhouse/query", {
      method: "POST",
      body: JSON.stringify({ sql }),
    }))
  );

  server.tool(
    "sql_readonly_health",
    "Verify live SQL connectivity for Negin_Report_ReadOnly; the agent independently enforces no-write SQL even if legacy object grants exist.",
    {},
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async () => result(await coreJson("/sql/readonly/health"))
  );

  server.tool(
    "sql_readonly_query",
    "Run arbitrary bounded SELECT/CTE SQL using the Negin_Report_ReadOnly identity. Agent guard blocks writes, DDL, EXEC, comments, multi-statements, USE, INTO and DBCC.",
    {
      sql: z.string().min(1).max(20000),
      max_rows: z.number().int().min(1).max(5000).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ sql, max_rows }) => result(await coreJson("/sql/readonly/query", {
      method: "POST",
      body: JSON.stringify({ sql, max_rows: max_rows || 1000 }),
    }))
  );


  server.tool(
    "sql_deep_intelligence",
    "Bounded deep readonly SQL intelligence for catalog, relationships, dependencies, definitions, permission inventory, or per-table sampling.",
    {
      action: z.enum(["catalog","relationships","dependencies","definitions","permissions","table_profile"]),
      schema: z.string().max(128).optional(),
      table: z.string().max(128).optional(),
      sample_rows: z.number().int().min(1).max(1000).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ action, schema, table, sample_rows }) => result(await coreJson("/sql/readonly/deep-intelligence", {
      method: "POST",
      body: JSON.stringify({ action, schema, table, sample_rows: sample_rows || 500 }),
    }))
  );



  // varanegar-domain-tools-v1
  server.tool(
    "varanegar_item_latest_pricing",
    "Return the latest bounded pricing history for one Varanegar goods code across verified sale, customer-price, buy-price, ICA buy-price and pricing-wizard tables. Strict production read-only approval gate remains mandatory.",
    {
      goods_code: z.string().min(1).max(100),
      limit: z.number().int().min(1).max(200).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ goods_code, limit }) => result(await coreJson("/varanegar/item/latest-pricing", {
      method: "POST",
      body: JSON.stringify({ goods_code, limit: limit || 30 }),
    }))
  );

  server.tool(
    "varanegar_schema_search",
    "Search the live Varanegar/NeginPakhsh SQL catalog by table, schema or column keywords without scanning business data. Use this before building a new domain query.",
    {
      terms: z.array(z.string().min(1).max(100)).min(1).max(12),
      max_rows: z.number().int().min(1).max(2000).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ terms, max_rows }) => result(await coreJson("/varanegar/schema/search", {
      method: "POST",
      body: JSON.stringify({ terms, max_rows: max_rows || 500 }),
    }))
  );

  server.tool(
    "varanegar_domain_discovery",
    "Discover verified Varanegar schema objects for a business domain before querying it. Supported domains: sales, purchase, inventory, warehouse, treasury, banking, discounts, offers, tax, pricing, accounting, customer, supplier, hr.",
    {
      domain: z.enum(["sales","purchase","inventory","warehouse","treasury","banking","discounts","offers","tax","pricing","accounting","customer","supplier","hr"]),
      max_rows: z.number().int().min(1).max(2000).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ domain, max_rows }) => {
      const termsByDomain = {
        sales: ["sale","evc","order","cust"],
        purchase: ["buy","purchase","sup","fact"],
        inventory: ["stock","inventory","goods","onhand"],
        warehouse: ["stock","warehouse","goods","voucher"],
        treasury: ["cash","cheque","payment","treasury"],
        banking: ["bank","reconciliation","statement","payment"],
        discounts: ["discount","cashdiscount","prize","criteria"],
        offers: ["offer","discount","prize","gift"],
        tax: ["moadian","tax","invoice","formal"],
        pricing: ["price","cprice","buyprice","wizard"],
        accounting: ["acc","voucher","ledger","dlcode"],
        customer: ["cust","customer","dealer"],
        supplier: ["sup","supplier","vendor"],
        hr: ["person","employee","payroll","attendance"],
      };
      return result(await coreJson("/varanegar/schema/search", {
        method: "POST",
        body: JSON.stringify({ terms: termsByDomain[domain], max_rows: max_rows || 700 }),
      }));
    }
  );

  server.tool(
    "varanegar_readonly_query",
    "Run a bounded read-only SELECT/CTE against the verified Varanegar NeginPakhsh database after schema discovery. Writes, DDL, EXEC, comments, multi-statements, USE, INTO and DBCC remain blocked.",
    {
      sql: z.string().min(1).max(20000),
      max_rows: z.number().int().min(1).max(5000).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ sql, max_rows }) => result(await coreJson("/sql/readonly/query", {
      method: "POST",
      body: JSON.stringify({ sql, max_rows: max_rows || 1000 }),
    }))
  );


  // ema-day1-executable-skills-v1
  server.tool(
    "system_performance_triage",
    "Diagnose local workstation CPU, RAM, paging, disk, network and runaway-process pressure without making changes.",
    {
      sample_seconds: z.number().min(0.4).max(3).optional(),
      top_n: z.number().int().min(5).max(30).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ sample_seconds, top_n }) => result(await coreJson("/skills/system/performance-triage", {
      method: "POST",
      body: JSON.stringify({ sample_seconds: sample_seconds || 1, top_n: top_n || 12 }),
    }))
  );

  server.tool(
    "mcp_transport_diagnostics",
    "Diagnose Core, MCP Bridge, listener ownership and Tailscale Serve/Funnel transport without mutation.",
    {},
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async () => result(await coreJson("/skills/mcp/transport-diagnostics"))
  );

  server.tool(
    "api_intelligence_scan",
    "Discover local API routes, MCP tools, auth signals and API specs with secret redaction. Production SQL is never used by this skill.",
    {
      max_files: z.number().int().min(50).max(2000).optional(),
      max_results: z.number().int().min(20).max(1000).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ max_files, max_results }) => result(await coreJson("/skills/api/intelligence", {
      method: "POST",
      body: JSON.stringify({ max_files: max_files || 600, max_results: max_results || 300 }),
    }))
  );


  // benchmark-wave1-skills-v1
  server.tool(
    "capability_truth_contract",
    "Audit registered capabilities against executable MCP exposure. Use before claiming a new capability is active.",
    {},
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async () => result(await coreJson("/skills/capability/truth-contract"))
  );

  server.tool(
    "task_universal_verifier",
    "Verify task completion from explicit postconditions and evidence. A task is not complete when required assertions fail or are absent.",
    {
      task_id: z.string().min(1).max(200),
      steps: z.array(z.object({
        name: z.string().min(1).max(200),
        result: z.record(z.any()).optional(),
        assertions: z.array(z.object({
          kind: z.enum(["field_equals","field_true","field_false","field_exists","contains","returncode_zero","status_2xx","nonempty"]),
          field: z.string().max(300).optional(),
          expected: z.any().optional(),
          value: z.any().optional(),
        })).optional(),
      })).min(1).max(100),
      require_all_steps: z.boolean().optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ task_id, steps, require_all_steps }) => result(await coreJson("/skills/task/universal-verifier", {
      method: "POST",
      body: JSON.stringify({ task_id, steps, require_all_steps: require_all_steps ?? true }),
    }))
  );

  server.tool(
    "shell_checked_sequence",
    "Execute local shell work as independently verified steps so one successful final command cannot hide an earlier failed command.",
    {
      steps: z.array(z.object({
        name: z.string().min(1).max(100),
        command: z.string().min(1).max(12000),
        cwd: z.string().max(1000).optional(),
        timeout: z.number().int().min(1).max(120).optional(),
        expect_returncode: z.number().int().optional(),
        stdout_contains: z.string().max(1000).optional(),
      })).min(1).max(30),
      stop_on_error: z.boolean().optional(),
    },
    { readOnlyHint: false, destructiveHint: true, openWorldHint: false },
    async ({ steps, stop_on_error }) => result(await coreJson("/skills/shell/checked-sequence", {
      method: "POST",
      body: JSON.stringify({ steps, stop_on_error: stop_on_error ?? true }),
    }))
  );

  server.tool(
    "benchmark_regression",
    "Run the fixed Negin regression suite inside the project virtual environment and persist evidence.",
    { suite: z.enum(["wave1","core","all_safe"]).optional() },
    { readOnlyHint: false, destructiveHint: false, openWorldHint: false },
    async ({ suite }) => result(await coreJson("/skills/benchmark/regression", {
      method: "POST",
      body: JSON.stringify({ suite: suite || "wave1" }),
    }))
  );

  server.tool(
    "tool_reliability_report",
    "Read structured route reliability telemetry including success rate, verification rate and p50/p95 latency. Request/response bodies and secrets are never stored.",
    {
      window_hours: z.number().int().min(1).max(720).optional(),
      min_samples: z.number().int().min(1).max(1000).optional(),
    },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ window_hours, min_samples }) => result(await coreJson(`/skills/observability/tool-reliability?window_hours=${window_hours || 24}&min_samples=${min_samples || 1}`))
  );

  server.tool(
    "n8n_workflow_manage",
    "Manage local n8n workflow lifecycle through authenticated API with validation and safety gates.",
    {
      action: z.enum(["auth_health","list","get","validate","create","update","activate","deactivate","delete","export","import"]),
      workflow_id: z.string().min(1).max(200).optional(),
      workflow: z.record(z.any()).optional(),
      allow_risky_nodes: z.boolean().optional(),
      confirm_destructive: z.boolean().optional(),
      include_credential_refs: z.boolean().optional(),
      limit: z.number().int().min(1).max(100).optional(),
      cursor: z.string().max(1000).optional(),
    },
    { readOnlyHint: false, destructiveHint: true, openWorldHint: false },
    async ({ action, workflow_id, workflow, allow_risky_nodes, confirm_destructive, include_credential_refs, limit, cursor }) => result(await coreJson("/n8n/workflows/manage", {
      method: "POST",
      body: JSON.stringify({
        action,
        workflow_id,
        workflow,
        allow_risky_nodes: allow_risky_nodes || false,
        confirm_destructive: confirm_destructive || false,
        include_credential_refs: include_credential_refs || false,
        limit: limit || 20,
        cursor,
      }),
    }))
  );

  server.tool(
    "n8n_webhook",
    "Execute a local n8n webhook workflow and recheck n8n after execution.",
    {
      path: z.string().min(1).max(500),
      method: z.enum(["get", "post"]).optional(),
      payload: z.record(z.any()).optional(),
    },
    { readOnlyHint: false, destructiveHint: false, openWorldHint: false },
    async ({ path, method, payload }) => result(await coreJson("/n8n/webhook", {
      method: "POST",
      body: JSON.stringify({ path, method: method || "post", payload: payload || {} }),
    }))
  );

  server.tool(
    "rpa_list_windows",
    "List visible local workstation windows before choosing an RPA target.",
    {},
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async () => result(await coreJson("/rpa/windows"))
  );

  server.tool(
    "rpa_click_control",
    "Click one explicitly named UI control in one explicitly matched local workstation window.",
    {
      window_title_re: z.string().min(1).max(500),
      control_title: z.string().min(1).max(500),
      control_type: z.string().max(100).optional(),
    },
    { readOnlyHint: false, destructiveHint: true, openWorldHint: false },
    async ({ window_title_re, control_title, control_type }) => result(await coreJson("/rpa/click", {
      method: "POST",
      body: JSON.stringify({ window_title_re, control_title, control_type }),
    }))
  );

  server.tool(
    "rpa_type_text",
    "Type explicit text into one explicitly named UI control in one explicitly matched local workstation window.",
    {
      window_title_re: z.string().min(1).max(500),
      control_title: z.string().min(1).max(500),
      text: z.string().max(10000),
      control_type: z.string().max(100).optional(),
    },
    { readOnlyHint: false, destructiveHint: true, openWorldHint: false },
    async ({ window_title_re, control_title, text, control_type }) => result(await coreJson("/rpa/type", {
      method: "POST",
      body: JSON.stringify({ window_title_re, control_title, text, control_type }),
    }))
  );



  // ema-continuous-runtime-v1
  server.tool(
    "continuous_runtime_status",
    "Check durable non-stop execution worker, queue, checkpoint/retry and crash-recovery health.",
    {},
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async () => result(await coreJson("/runtime/continuous/health"))
  );

  server.tool(
    "continuous_submit_job",
    "Submit a whitelisted durable background job. Jobs persist across agent restarts and can retry until success.",
    {
      kind: z.enum(["self_test", "sql_ecosystem_discovery"]),
      payload: z.record(z.any()).optional(),
      max_attempts: z.number().int().min(0).max(1000000).optional(),
      retry_base_seconds: z.number().int().min(1).max(300).optional(),
      repeat_seconds: z.number().int().min(0).max(31536000).optional(),
    },
    { readOnlyHint: false, destructiveHint: false, openWorldHint: false },
    async ({ kind, payload, max_attempts, retry_base_seconds, repeat_seconds }) => result(await coreJson("/runtime/continuous/jobs", {
      method: "POST",
      body: JSON.stringify({
        kind,
        payload: payload || {},
        max_attempts: max_attempts ?? 0,
        retry_base_seconds: retry_base_seconds ?? 5,
        repeat_seconds: repeat_seconds ?? 0,
      }),
    }))
  );

  server.tool(
    "continuous_jobs",
    "List recent durable jobs.",
    { limit: z.number().int().min(1).max(200).optional() },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ limit }) => result(await coreJson(`/runtime/continuous/jobs?limit=${limit || 50}`))
  );

  server.tool(
    "continuous_job_status",
    "Read one durable job including checkpoint and recent events.",
    { job_id: z.string().min(1).max(100) },
    { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    async ({ job_id }) => result(await coreJson(`/runtime/continuous/jobs/${encodeURIComponent(job_id)}`))
  );

  server.tool(
    "continuous_job_control",
    "Pause, resume or cancel a durable job.",
    {
      job_id: z.string().min(1).max(100),
      action: z.enum(["pause", "resume", "cancel"]),
    },
    { readOnlyHint: false, destructiveHint: false, openWorldHint: false },
    async ({ job_id, action }) => result(await coreJson(`/runtime/continuous/jobs/${encodeURIComponent(job_id)}/control`, {
      method: "POST",
      body: JSON.stringify({ action }),
    }))
  );


  return server;
}

const app = express();
app.use(express.json({ limit: "1mb" }));

const endpointToken = process.env.ema_mcp_endpoint_token;
if (!/^[a-f0-9]{64}$/i.test(endpointToken || "")) {
  throw new Error("ema_mcp_endpoint_token missing or invalid");
}
const endpointPath = `/mcp/${endpointToken}`;
// ema-stateless-mcp-transport-v1
// Stateless Streamable HTTP is intentional here:
// tools are independent request/response operations and do not require
// resumable server-side MCP session state.

app.post(endpointPath, async (req, res) => {
  const server = makeServer();
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
  });

  let cleaned = false;
  const cleanup = () => {
    if (cleaned) return;
    cleaned = true;

    try {
      const p = transport.close();
      if (p?.catch) p.catch(() => {});
    } catch {}

    try {
      const p = server.close?.();
      if (p?.catch) p.catch(() => {});
    } catch {}
  };

  res.once("close", cleanup);

  try {
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error("ema mcp request failed:", error);

    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: "2.0",
        error: {
          code: -32603,
          message: "Internal MCP transport error",
        },
        id: null,
      });
    }
  }
});

app.get(endpointPath, (_req, res) => {
  res.status(405).json({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed in stateless MCP mode",
    },
    id: null,
  });
});

app.delete(endpointPath, (_req, res) => {
  res.status(405).json({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed in stateless MCP mode",
    },
    id: null,
  });
});

app.get("/health", (_req, res) => res.json({ ok: true, service: "ema-mcp-bridge" }));

const host = process.env.ema_mcp_host || "127.0.0.1";
const port = Number(process.env.ema_mcp_port || 8766);
app.listen(port, host, () => {
  console.log(`ema mcp bridge listening on http://${host}:${port}/mcp/<secret>`);
});





