from fastapi import HTTPException
from enterprise_master_agent.n8n_workflows import N8nWorkflowManageReq, _validate_workflow
import asyncio

def safe_workflow():
    return {
        "name": "Negin n8n CRUD Test",
        "nodes": [{
            "parameters": {},
            "id": "1",
            "name": "Manual Trigger",
            "type": "n8n-nodes-base.manualTrigger",
            "typeVersion": 1,
            "position": [0, 0],
        }],
        "connections": {},
        "settings": {},
    }

def test_validate_safe_workflow():
    r = _validate_workflow(safe_workflow())
    assert r["valid"] is True
    assert r["node_count"] == 1

def test_validate_blocks_risky_node_without_gate():
    wf = safe_workflow()
    wf["nodes"][0]["type"] = "n8n-nodes-base.executeCommand"
    r = _validate_workflow(wf)
    assert r["valid"] is False
    assert r["risky_nodes"]

def test_validate_route_does_not_require_api_key():
    from enterprise_master_agent.n8n_workflows import n8n_workflow_manage
    req = N8nWorkflowManageReq(action="validate", workflow=safe_workflow())
    r = asyncio.run(n8n_workflow_manage(req))
    assert r["valid"] is True
    assert r["target"] == "localhost-n8n"

def test_delete_requires_explicit_confirmation(monkeypatch):
    import enterprise_master_agent.n8n_workflows as n8n
    async def fake_api(*args, **kwargs):
        raise AssertionError("api should not be called before confirmation")
    monkeypatch.setattr(n8n, "_api_request", fake_api)
    req = N8nWorkflowManageReq(action="delete", workflow_id="abc")
    try:
        asyncio.run(n8n.n8n_workflow_manage(req))
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 409
