const a = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const host = require("../server/reconnect-host.js");

const dir = fs.mkdtempSync(path.join(os.tmpdir(), "uxx-reload-"));
const entry = path.join(dir, "index.js");

function writeVersion(version, broken=false) {
  if (broken) {
    fs.writeFileSync(entry, "module.exports = { broken: ;", "utf8");
    return;
  }
  fs.writeFileSync(entry, `
module.exports = {
  status(){ return { ok:true, version:${JSON.stringify(version)}, tool_count:1 }; },
  toolSchemas(){ return [{ name:"ux_status" }]; },
  mcpHandle(message){ return { jsonrpc:"2.0", id:message.id, result:{ serverInfo:{ name:"ux-x", version:${JSON.stringify(version)} } } }; }
};
`, "utf8");
}

writeVersion("test-1");
const r = host.createReloader(entry);
let x = r.load(true);
a.strictEqual(x.status.version, "test-1");

writeVersion("test-2-longer");
x = r.load(false);
a.strictEqual(x.status.version, "test-2-longer");
a.strictEqual(x.changed, true);

writeVersion("broken", true);
x = r.load(false);
a.strictEqual(x.status.version, "test-2-longer");
a(x.lastError);

const plugin = JSON.parse(fs.readFileSync(path.join(__dirname, "..", ".codex-plugin", "plugin.json"), "utf8"));
a.strictEqual(plugin.mcp.command, "node");
a(plugin.mcp.args.includes("server/reconnect-host.js"));

console.log("ux-x reconnect host tests passed");
