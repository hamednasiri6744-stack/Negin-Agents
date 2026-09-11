from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .integrations import router as integrations_router
from .n8n_workflows import router as n8n_workflows_router
from .sql_intelligence import router as sql_intelligence_router
from .data_api import router as data_api_router
from .sales_clickhouse_etl import router as sales_clickhouse_etl_router
from .continuous_runtime import router as continuous_router
from .day1_skills import router as day1_skills_router
from .remote_performance import router as remote_performance_router
from .benchmark_wave1_skills import router as benchmark_wave1_router, ReliabilityMiddleware
from .knowledge import KnowledgeImportError, KnowledgeManager
from .semantic_core import resolve_against_active_core

from .core import (
    PolicyEngine,
    CapabilityRegistry,
    SemanticDictionary,
    TruthGate,
    QueryPlanner,
    GuardedShell,
    sales_target_kpi,
    wol_powershell_script,
)

app = FastAPI(title="Enterprise Master Agent", version="0.1.0")
app.include_router(integrations_router)
app.include_router(n8n_workflows_router)
app.include_router(sql_intelligence_router)
app.include_router(data_api_router)
app.include_router(sales_clickhouse_etl_router)
app.include_router(continuous_router)
app.include_router(day1_skills_router)
app.include_router(remote_performance_router)
app.include_router(benchmark_wave1_router)
app.add_middleware(ReliabilityMiddleware)

policy = PolicyEngine()
registry = CapabilityRegistry()
semantic = SemanticDictionary()
truth = TruthGate()
planner = QueryPlanner()
shell = GuardedShell(policy)
knowledge = KnowledgeManager()

for name, description, perms in [
    ("shell.local", "guarded local shell", ["local.execute"]),
    ("semantic.resolve", "Persian business semantic resolver", ["data.read"]),
    ("truth.verify", "truth and accuracy gate", ["data.read"]),
    ("kpi.sales_target", "sales target KPI calculator", ["data.read"]),
    ("query.plan", "adaptive query planner", ["data.read"]),
    ("wol.script", "Wake-on-LAN script generation only", ["script.generate"]),
    ("n8n.local", "n8n localhost connector contract", ["workflow"]),
    ("n8n.workflow_crud", "authenticated local n8n workflow lifecycle management with validation and safety gates", ["workflow.manage"]),
    ("clickhouse.analytics", "ClickHouse analytical connector", ["data.read"]),
    ("sql.production_readonly", "strict read-only production SQL connector", ["data.read"]),
    ("sql.production_readonly.deep_intelligence", "bounded deep database intelligence over strict readonly SQL", ["data.read"]),
    ("sql.production_readonly.query", "arbitrary bounded SELECT/CTE through Negin_Report_ReadOnly with agent-enforced write blocking", ["data.read"]),
    ("sql.production_readonly.permissions", "effective SQL permission and role introspection", ["data.read"]),
    ("runtime.continuous_execution", "durable safe job queue with checkpoint, retry, recurring execution and crash recovery", ["runtime.schedule"]),
    ("system.performance_triage", "local workstation performance root-cause triage for CPU, RAM, paging, disk, network and runaway processes", ["local.read"]),
    ("remote_server.performance_readonly", "allowlisted Windows server CPU, RAM, paging, disk, network and process telemetry over read-only CIM", ["remote.read"]),
    ("mcp.transport_diagnostics", "MCP bridge, listener and Tailscale transport diagnostics without mutation", ["local.read"]),
    ("api.intelligence", "secret-redacted API, route, auth and MCP surface discovery with Production SQL kept behind approval gate", ["local.read"]),
    ("capability.truth_contract", "evidence-backed capability registry and MCP exposure truth contract", ["local.read"]),
    ("task.universal_verifier", "task-level postcondition verifier requiring explicit evidence before COMPLETE", ["verify"]),
    ("shell.execution_truth", "structured per-step shell execution with command-level verification", ["local.execute"]),
    ("benchmark.regression_harness", "project-venv benchmark-driven regression harness with persisted results", ["local.test"]),
    ("observability.tool_reliability", "structured route latency, error-rate and verification telemetry", ["local.read"]),
    ("rpa.operator", "RPA operator contract; adapters hot-pluggable", ["ui.operate"]),
    ("workers.external", "external agent worker adapter contract", ["delegate"]),
    ("knowledge.import", "verified versioned Markdown knowledge importer", ["knowledge.write"]),
    ("knowledge.search", "search active imported knowledge", ["knowledge.read"]),
    ("knowledge.rollback", "activate a previous imported knowledge version", ["knowledge.write"]),
]:
    registry.register(name, description, permissions=perms)

class ShellReq(BaseModel):
    command: str
    cwd: str | None = None
    timeout: int = Field(default=120, ge=1, le=120)

class TextReq(BaseModel):
    text: str

class VerifyReq(BaseModel):
    value: object | None = None
    schema_ok: bool = True
    business_rule_ok: bool = True
    crosscheck_ok: bool | None = None
    high_risk: bool = False
    source_ts: float | None = None
    max_age_seconds: int | None = None

class TargetReq(BaseModel):
    target: float
    actual: float
    remaining_days: int

class PlanReq(BaseModel):
    availability: dict[str, bool]

class GapReq(BaseModel):
    capability: str
    intent: str

class WolReq(BaseModel):
    mac: str
    broadcast: str
    port: int = 9

class KnowledgeImportReq(BaseModel):
    archive_path: str = Field(min_length=1, max_length=1000)
    expected_sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")


class KnowledgeSearchReq(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=50)


class KnowledgeRollbackReq(BaseModel):
    version_id: str | None = Field(default=None, max_length=300)


@app.get("/health")
async def health():
    return {
        "ok": True,
        "service": "enterprise-master-agent",
        "provider_dependency": False,
        "production_server_execution": False,
    }

@app.get("/capabilities")
async def capabilities():
    return {"capabilities": registry.list()}

@app.post("/semantic/resolve")
async def semantic_resolve(req: TextReq):
    legacy = semantic.resolve(req.text)
    core_result = resolve_against_active_core(req.text, knowledge, legacy)
    if core_result is not None:
        return core_result
    return {**legacy, semantic_authority: legacy_semantic_dictionary, authority_priority: fallback_only}

@app.post("/verify")
async def verify(req: VerifyReq):
    return truth.verify(**req.model_dump())

@app.post("/kpi/sales-target")
async def target(req: TargetReq):
    return sales_target_kpi(**req.model_dump())

@app.post("/query/plan")
async def query_plan(req: PlanReq):
    return planner.choose(req.availability)

@app.post("/capability/require")
async def capability_require(req: GapReq):
    return registry.require(req.capability, req.intent)

@app.post("/shell/run")
async def shell_run(req: ShellReq):
    return await shell.run(req.command, req.cwd, req.timeout)

@app.post("/knowledge/import")
def knowledge_import(req: KnowledgeImportReq):
    try:
        return knowledge.import_archive(
            req.archive_path,
            req.expected_sha256,
        )
    except KnowledgeImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/knowledge/status")
def knowledge_status():
    return knowledge.status()


@app.post("/knowledge/search")
def knowledge_search(req: KnowledgeSearchReq):
    try:
        return knowledge.search(req.query, req.limit)
    except KnowledgeImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/knowledge/rollback")
def knowledge_rollback(req: KnowledgeRollbackReq):
    try:
        return knowledge.rollback(req.version_id)
    except KnowledgeImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/wol/script")
async def wol_script(req: WolReq):
    return {
        "script_only": True,
        "execute_on_server": False,
        "powershell": wol_powershell_script(req.mac, req.broadcast, req.port),
    }







