from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/n8n", tags=["n8n-workflows"])

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_N8N_URL = "http://127.0.0.1:5678"
API_PREFIX = "/api/v1"

RISKY_NODE_TYPES = {
    "n8n-nodes-base.executeCommand",
    "n8n-nodes-base.ssh",
    "n8n-nodes-base.readWriteFile",
    "n8n-nodes-base.code",
    "n8n-nodes-base.function",
    "n8n-nodes-base.functionItem",
}


def _cfg(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value.strip()
    env_path = ROOT / ".env"
    if env_path.exists():
        for raw in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, candidate = line.split("=", 1)
            if key.strip().lower() == name.lower():
                return candidate.strip()
    return default


def _n8n_url() -> str:
    return _cfg("N8N_URL", DEFAULT_N8N_URL).rstrip("/")


def _api_key() -> str:
    key = _cfg("N8N_API_KEY")
    if not key:
        raise HTTPException(
            status_code=503,
            detail="N8N_API_KEY is not configured. Create one in n8n Settings > n8n API and store it in the local .env file.",
        )
    return key


def _headers() -> dict[str, str]:
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "X-N8N-API-KEY": _api_key(),
    }


def _redacted_error(response: httpx.Response) -> str:
    text = (response.text or "").replace(_api_key(), "[REDACTED]")
    return f"n8n API {response.status_code}: {text[:1000]}"


async def _api_request(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> httpx.Response:
    async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
        response = await client.request(
            method,
            _n8n_url() + API_PREFIX + path,
            headers=_headers(),
            json=json_body,
            params=params,
        )
    if response.status_code >= 400:
        if response.status_code in {401, 403}:
            raise HTTPException(
                status_code=502,
                detail="n8n API authentication/authorization failed; verify the local N8N_API_KEY.",
            )
        raise HTTPException(status_code=502, detail=_redacted_error(response))
    return response


def _workflow_for_write(workflow: dict[str, Any]) -> dict[str, Any]:
    allowed = ("name", "nodes", "connections", "settings", "staticData")
    body = {key: deepcopy(workflow[key]) for key in allowed if key in workflow}
    body.setdefault("settings", {})
    return body


def _validate_workflow(
    workflow: dict[str, Any] | None,
    *,
    allow_risky_nodes: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    risky_nodes: list[dict[str, str]] = []

    if not isinstance(workflow, dict):
        return {
            "ok": False,
            "valid": False,
            "errors": ["workflow must be an object"],
            "risky_nodes": [],
        }

    name = workflow.get("name")
    nodes = workflow.get("nodes")
    connections = workflow.get("connections")

    if not isinstance(name, str) or not name.strip():
        errors.append("workflow.name must be a non-empty string")
    if not isinstance(nodes, list) or not nodes:
        errors.append("workflow.nodes must be a non-empty array")
        nodes = []
    if not isinstance(connections, dict):
        errors.append("workflow.connections must be an object")

    node_names: list[str] = []
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"workflow.nodes[{index}] must be an object")
            continue
        node_name = node.get("name")
        node_type = node.get("type")
        if not isinstance(node_name, str) or not node_name.strip():
            errors.append(f"workflow.nodes[{index}].name must be non-empty")
        else:
            node_names.append(node_name)
        if not isinstance(node_type, str) or not node_type.strip():
            errors.append(f"workflow.nodes[{index}].type must be non-empty")
        elif node_type in RISKY_NODE_TYPES:
            risky_nodes.append({"name": str(node_name or index), "type": node_type})

    if len(node_names) != len(set(node_names)):
        errors.append("workflow node names must be unique")

    if risky_nodes and not allow_risky_nodes:
        errors.append(
            "workflow contains gated local-execution/file/SSH/code nodes; explicit allow_risky_nodes=true is required"
        )

    return {
        "ok": not errors,
        "valid": not errors,
        "errors": errors,
        "risky_nodes": risky_nodes,
        "node_count": len(nodes),
    }


def _sanitize_workflow_read(
    workflow: dict[str, Any],
    *,
    include_credential_refs: bool = False,
) -> dict[str, Any]:
    clean = deepcopy(workflow)

    if not include_credential_refs:
        for node in clean.get("nodes", []) if isinstance(clean.get("nodes"), list) else []:
            if isinstance(node, dict):
                node.pop("credentials", None)

    # Shared/project ownership metadata is not required for workflow management
    # and can contain personal identity information.
    clean.pop("shared", None)

    return clean


def _sanitize_workflow_list(
    payload: dict[str, Any],
    *,
    include_credential_refs: bool = False,
) -> dict[str, Any]:
    clean = deepcopy(payload)
    workflows = clean.get("data")

    if isinstance(workflows, list):
        clean["data"] = [
            _sanitize_workflow_read(
                workflow,
                include_credential_refs=include_credential_refs,
            )
            if isinstance(workflow, dict)
            else workflow
            for workflow in workflows
        ]

    return clean


Action = Literal[
    "auth_health",
    "list",
    "get",
    "validate",
    "create",
    "update",
    "activate",
    "deactivate",
    "delete",
    "export",
    "import",
]


class N8nWorkflowManageReq(BaseModel):
    action: Action
    workflow_id: str | None = Field(default=None, min_length=1, max_length=200)
    workflow: dict[str, Any] | None = None
    allow_risky_nodes: bool = False
    confirm_destructive: bool = False
    include_credential_refs: bool = False
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = Field(default=None, max_length=1000)


def _require_id(req: N8nWorkflowManageReq) -> str:
    if not req.workflow_id:
        raise HTTPException(status_code=422, detail="workflow_id is required for this action")
    return req.workflow_id


@router.post("/workflows/manage")
async def n8n_workflow_manage(req: N8nWorkflowManageReq):
    if req.action == "validate":
        workflow = req.workflow
        validation_source = "inline"

        if workflow is None and req.workflow_id:
            response = await _api_request("GET", f"/workflows/{req.workflow_id}")
            fetched = response.json()
            if isinstance(fetched, dict):
                workflow = fetched
                validation_source = "workflow_id"

        validation = _validate_workflow(
            workflow,
            allow_risky_nodes=req.allow_risky_nodes,
        )
        return {
            "action": "validate",
            **validation,
            "validation_source": validation_source,
            "workflow_id": req.workflow_id if validation_source == "workflow_id" else None,
            "target": "localhost-n8n",
        }

    if req.action == "auth_health":
        response = await _api_request("GET", "/workflows", params={"limit": 1})
        return {
            "ok": True,
            "action": "auth_health",
            "authenticated": True,
            "status_code": response.status_code,
            "target": "localhost-n8n",
            "auth_source": "N8N_API_KEY",
        }

    if req.action == "list":
        params: dict[str, Any] = {"limit": req.limit}
        if req.cursor:
            params["cursor"] = req.cursor

        response = await _api_request("GET", "/workflows", params=params)
        data = response.json()

        if isinstance(data, dict):
            data = _sanitize_workflow_list(
                data,
                include_credential_refs=req.include_credential_refs,
            )

        return {
            "ok": True,
            "action": "list",
            "status_code": response.status_code,
            "data": data,
            "credential_refs_included": bool(req.include_credential_refs),
            "target": "localhost-n8n",
        }

    if req.action in {"get", "export"}:
        workflow_id = _require_id(req)
        response = await _api_request("GET", f"/workflows/{workflow_id}")
        data = response.json()

        if isinstance(data, dict):
            data = _sanitize_workflow_read(
                data,
                include_credential_refs=req.include_credential_refs,
            )

        return {
            "ok": True,
            "action": req.action,
            "status_code": response.status_code,
            "data": data,
            "credential_refs_included": bool(req.include_credential_refs),
            "target": "localhost-n8n",
        }

    if req.action in {"create", "import", "update"}:
        validation = _validate_workflow(req.workflow, allow_risky_nodes=req.allow_risky_nodes)
        if not validation["valid"]:
            raise HTTPException(status_code=422, detail=validation)
        body = _workflow_for_write(req.workflow or {})
        if req.action == "update":
            workflow_id = _require_id(req)
            response = await _api_request("PUT", f"/workflows/{workflow_id}", json_body=body)
        else:
            response = await _api_request("POST", "/workflows", json_body=body)
        return {
            "ok": True,
            "action": req.action,
            "status_code": response.status_code,
            "data": response.json(),
            "validation": validation,
            "target": "localhost-n8n",
        }

    if req.action in {"activate", "deactivate"}:
        workflow_id = _require_id(req)
        response = await _api_request("POST", f"/workflows/{workflow_id}/{req.action}")
        return {
            "ok": True,
            "action": req.action,
            "status_code": response.status_code,
            "data": response.json(),
            "target": "localhost-n8n",
        }

    if req.action == "delete":
        workflow_id = _require_id(req)
        if not req.confirm_destructive:
            raise HTTPException(
                status_code=409,
                detail="workflow deletion requires explicit confirm_destructive=true",
            )
        response = await _api_request("DELETE", f"/workflows/{workflow_id}")
        data: Any
        try:
            data = response.json()
        except Exception:
            data = {"deleted": True}
        return {
            "ok": True,
            "action": "delete",
            "status_code": response.status_code,
            "data": data,
            "target": "localhost-n8n",
        }

    raise HTTPException(status_code=400, detail="unsupported n8n workflow action")

