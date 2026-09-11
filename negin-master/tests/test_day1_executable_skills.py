from enterprise_master_agent.day1_skills import PerformanceReq, ApiScanReq, system_performance_triage, mcp_transport_diagnostics, api_intelligence

def test_performance_triage_readonly():
    r=system_performance_triage(PerformanceReq(sample_seconds=0.4,top_n=5))
    assert r['ok'] is True
    assert r['mutations_performed'] is False
    assert r['scope']=='local_workstation_only'

def test_mcp_transport_readonly():
    r=mcp_transport_diagnostics()
    assert r['ok'] is True
    assert r['mutations_performed'] is False

def test_api_intelligence_no_production_sql():
    r=api_intelligence(ApiScanReq(max_files=60,max_results=20))
    assert r['ok'] is True
    assert r['production_sql_used'] is False
    assert r['secrets_redacted'] is True
