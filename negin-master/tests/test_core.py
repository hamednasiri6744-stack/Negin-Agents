from enterprise_master_agent.core import (
    PolicyEngine,
    SemanticDictionary,
    TruthGate,
    QueryPlanner,
    sales_target_kpi,
)

def test_policy_blocks_destructive_sql():
    p = PolicyEngine.__new__(PolicyEngine)
    assert p.sql("select top 10 * from dbo.t").allowed
    assert not p.sql("delete from dbo.t").allowed
    assert not p.sql("select * into x from dbo.t").allowed

def test_semantic_resolution(tmp_path):
    path = tmp_path / "s.yaml"
    path.write_text(
        "version: 1\nterms:\n  - canonical: net_sales_today\n"
        "    domain: sales\n    persian_name: فروش خالص امروز\n"
        "    synonyms: [فروش امروز]\n",
        encoding="utf-8",
    )
    s = SemanticDictionary(str(path))
    r = s.resolve("فروش امروز چقدر است")
    assert r["resolved"]
    assert r["canonical"] == "net_sales_today"

def test_high_risk_requires_crosscheck():
    r = TruthGate().verify(value=10, high_risk=True)
    assert not r["passed"]
    assert r["checks"]["crosscheck"] is False

def test_query_planner_prefers_cache():
    r = QueryPlanner().choose({"semantic_cache": True, "clickhouse": True})
    assert r["route"] == "semantic_cache"

def test_sales_target():
    r = sales_target_kpi(1000, 800, 2)
    assert r["achievement_pct"] == 80.0
    assert r["remaining"] == 200
    assert r["required_daily_run_rate"] == 100
