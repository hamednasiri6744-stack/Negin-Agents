from __future__ import annotations

import asyncio
import json
import subprocess
from typing import Any, Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

n8n_url = "http://127.0.0.1:5678"
clickhouse_url = "http://127.0.0.1:8123"


class ClickHouseQueryReq(BaseModel):
    sql: str = Field(min_length=1, max_length=20000)


class N8nWebhookReq(BaseModel):
    path: str = Field(min_length=1, max_length=500)
    method: Literal["get", "post"] = "post"
    payload: dict[str, Any] | None = None


class RpaClickReq(BaseModel):
    window_title_re: str = Field(min_length=1, max_length=500)
    control_title: str = Field(min_length=1, max_length=500)
    control_type: str | None = Field(default=None, max_length=100)


class RpaTypeReq(BaseModel):
    window_title_re: str = Field(min_length=1, max_length=500)
    control_title: str = Field(min_length=1, max_length=500)
    text: str = Field(max_length=10000)
    control_type: str | None = Field(default=None, max_length=100)


def _clickhouse_readonly(sql: str) -> bool:
    q = " ".join(sql.strip().lower().split())
    allowed = ("select ", "with ", "show ", "describe ", "desc ", "explain ")
    return q in {"select 1", "show databases", "show tables"} or q.startswith(allowed)


def _clickhouse_exec_sync(sql: str) -> str:
    if not _clickhouse_readonly(sql):
        raise PermissionError("clickhouse tool is read-only")
    try:
        with httpx.Client(timeout=20, trust_env=False) as client:
            r = client.post(clickhouse_url + "/", content=sql.encode("utf-8"))
            r.raise_for_status()
            return r.text
    except httpx.HTTPError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        raise RuntimeError((detail or "clickhouse http query failed")[:4000]) from exc


async def _clickhouse_exec(sql: str) -> str:
    return await asyncio.to_thread(_clickhouse_exec_sync, sql)


async def _n8n_alive() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3, trust_env=False) as client:
            r = await client.get(n8n_url + "/")
            return r.status_code < 500
    except Exception:
        return False


@router.get("/integrations/health")
async def integrations_health():
    clickhouse = False
    n8n = False
    rpa = False
    errors: dict[str, str] = {}

    try:
        clickhouse = (await _clickhouse_exec("select 1")).strip() == "1"
    except Exception as e:
        errors["clickhouse"] = str(e)

    try:
        n8n = await _n8n_alive()
    except Exception as e:
        errors["n8n"] = str(e)

    try:
        import pywinauto  # noqa: f401
        import pyautogui  # noqa: f401
        rpa = True
    except Exception as e:
        errors["rpa"] = str(e)

    return {
        "ok": clickhouse and n8n and rpa,
        "clickhouse": clickhouse,
        "n8n": n8n,
        "rpa": rpa,
        "errors": errors,
        "clickhouse_transport": "http-local",
    }


@router.post("/clickhouse/query")
async def clickhouse_query(req: ClickHouseQueryReq):
    if not _clickhouse_readonly(req.sql):
        raise HTTPException(
            status_code=403,
            detail="clickhouse tool is read-only; use select/with/show/describe/explain",
        )

    try:
        result = await _clickhouse_exec(req.sql)
        recheck = (await _clickhouse_exec("select 1")).strip() == "1"
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {
        "ok": True,
        "read_only": True,
        "result": result,
        "recheck": recheck,
        "transport": "http-local",
    }


@router.post("/n8n/webhook")
async def n8n_webhook(req: N8nWebhookReq):
    path = "/" + req.path.lstrip("/")
    if not (path.startswith("/webhook/") or path.startswith("/webhook-test/")):
        raise HTTPException(
            status_code=403,
            detail="only local n8n webhook and webhook-test paths are allowed",
        )

    url = n8n_url + path
    async with httpx.AsyncClient(timeout=60, trust_env=False) as client:
        if req.method == "get":
            r = await client.get(url, params=req.payload or {})
        else:
            r = await client.post(url, json=req.payload or {})

    recheck = await _n8n_alive()
    return {
        "ok": r.is_success,
        "status_code": r.status_code,
        "body": r.text[:20000],
        "recheck": recheck,
        "target": "localhost-n8n",
    }


@router.get("/rpa/windows")
def rpa_windows():
    try:
        from pywinauto import Desktop

        titles = []
        for w in Desktop(backend="uia").windows():
            try:
                title = (w.window_text() or "").strip()
                if title and title not in titles:
                    titles.append(title)
            except Exception:
                pass

        return {
            "ok": True,
            "target": "local-workstation",
            "windows": titles[:200],
            "count": len(titles[:200]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rpa/click")
def rpa_click(req: RpaClickReq):
    try:
        from pywinauto import Desktop

        desktop = Desktop(backend="uia")
        win = desktop.window(title_re=req.window_title_re)
        win.wait("exists enabled visible ready", timeout=8)

        kwargs: dict[str, Any] = {"title": req.control_title}
        if req.control_type:
            kwargs["control_type"] = req.control_type

        ctrl = win.child_window(**kwargs).wrapper_object()
        ctrl.click_input()

        return {
            "ok": True,
            "action": "click",
            "target": "local-workstation",
            "window": req.window_title_re,
            "control": req.control_title,
            "recheck": win.exists(timeout=2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rpa/type")
def rpa_type(req: RpaTypeReq):
    try:
        from pywinauto import Desktop

        desktop = Desktop(backend="uia")
        win = desktop.window(title_re=req.window_title_re)
        win.wait("exists enabled visible ready", timeout=8)

        kwargs: dict[str, Any] = {"title": req.control_title}
        if req.control_type:
            kwargs["control_type"] = req.control_type

        ctrl = win.child_window(**kwargs).wrapper_object()
        ctrl.set_focus()
        ctrl.type_keys(req.text, with_spaces=True, pause=0.01)

        return {
            "ok": True,
            "action": "type",
            "target": "local-workstation",
            "window": req.window_title_re,
            "control": req.control_title,
            "characters": len(req.text),
            "recheck": win.exists(timeout=2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

