from __future__ import annotations

import hmac
import json
import time

import httpx
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from .sql_intelligence import cfg, cs, row

router = APIRouter()
root = Path(__file__).resolve().parents[2]
_policy_path = root / "state" / "data-api-policy.json"
_audit_path = root / "logs" / "data-api-access.jsonl"


class SalesSummaryReq(BaseModel):
    period: Literal["latest_day", "mtd"] = "mtd"


def _require_gateway_key(x_negin_key: str | None) -> None:
    expected = cfg("negin_gateway_api_key", "")
    if not expected:
        raise HTTPException(status_code=503, detail="data API authentication is not configured")
    if not hmac.compare_digest(x_negin_key or "", expected):
        raise HTTPException(status_code=401, detail="unauthorized")


def _load_policy() -> dict:
    if not _policy_path.exists():
        raise HTTPException(status_code=403, detail="data API policy is not approved")
    try:
        p = json.loads(_policy_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="data API policy is invalid") from exc
    if not p.get("enabled"):
        raise HTTPException(status_code=403, detail="data API policy is disabled")
    return p


def _require_policy(operation: str, period: str) -> dict:
    p = _load_policy()
    allowed = (p.get("operations") or {}).get(operation) or []
    if period not in allowed:
        raise HTTPException(status_code=403, detail="operation is not approved by data API policy")
    return p


def _service_conn():
    import pyodbc
    c = pyodbc.connect(cs(), timeout=5, autocommit=True)
    ident_q = ("select db_name() db,original_login() login,"
               "is_srvrolemember('sysadmin') sa,is_member('db_owner') dbo,"
               "is_member('db_datawriter') dw,"
               "has_perms_by_name(db_name(),'database','insert') ins,"
               "has_perms_by_name(db_name(),'database','update') upd,"
               "has_perms_by_name(db_name(),'database','delete') delp,"
               "has_perms_by_name(db_name(),'database','alter') alt")
    ident = row(c, ident_q, n=1)[0]
    expected_db = cfg("negin_sql_database", "NeginPakhsh")
    if str(ident["db"]).lower() != expected_db.lower() or any(
        int(ident[k] or 0) for k in ("sa", "dbo", "dw", "ins", "upd", "delp", "alt")
    ):
        c.close()
        raise PermissionError("SQL identity is not accepted as strict read-only")
    return c, ident


def _sales_summary_sql(period: str) -> tuple[str, tuple]:
    q = (
        "with d as (select max(SaleDate) SaleDate from SLE.tblSaleHdr where isnull(CancelFlag,0)=0), "
        "b as (select case when ?='mtd' then left(SaleDate,7)+'/01' else SaleDate end FromDate, SaleDate ToDate from d) "
        "select b.FromDate from_date,b.ToDate to_date,"
        "(select count_big(*) from SLE.tblSaleHdr s where s.SaleDate between b.FromDate and b.ToDate and isnull(s.CancelFlag,0)=0) sale_count,"
        "(select coalesce(sum(cast(s.TotalAmount as decimal(38,2))),0) from SLE.tblSaleHdr s where s.SaleDate between b.FromDate and b.ToDate and isnull(s.CancelFlag,0)=0) gross_sales,"
        "(select count_big(*) from SLE.tblRetSaleHdr r where r.RetSaleDate between b.FromDate and b.ToDate and isnull(r.CancelFlag,0)=0) return_count,"
        "(select coalesce(sum(cast(r.TotalAmount as decimal(38,2))),0) from SLE.tblRetSaleHdr r where r.RetSaleDate between b.FromDate and b.ToDate and isnull(r.CancelFlag,0)=0) returns,"
        "(select coalesce(sum(cast(s.TotalAmount as decimal(38,2))),0) from SLE.tblSaleHdr s where s.SaleDate between b.FromDate and b.ToDate and isnull(s.CancelFlag,0)=0)"
        " - "
        "(select coalesce(sum(cast(r.TotalAmount as decimal(38,2))),0) from SLE.tblRetSaleHdr r where r.RetSaleDate between b.FromDate and b.ToDate and isnull(r.CancelFlag,0)=0) net_sales "
        "from b"
    )
    return q, (period,)


def _audit(**event) -> None:
    try:
        _audit_path.parent.mkdir(parents=True, exist_ok=True)
        event["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with _audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
    except Exception:
        pass


@router.post("/data/sales/summary")
def sales_summary(req: SalesSummaryReq, x_negin_key: str | None = Header(default=None, alias="x-negin-key")):
    started = time.perf_counter()
    _require_gateway_key(x_negin_key)
    policy = _require_policy("sales_summary", req.period)
    try:
        c, ident = _service_conn()
        try:
            q, params = _sales_summary_sql(req.period)
            rows = row(c, q, params, n=1)
        finally:
            c.close()
        if not rows:
            raise RuntimeError("sales summary returned no rows")
        r = rows[0]
        result = {
            "ok": True,
            "o`eration": "sales_summary",
            "period": req.period,
            "from_date": r["from_date"],
            "to_date": r["to_date"],
            "sale_count": int(r["sale_count"] or 0),
            "gross_sales": float(r["gross_sales"] or 0),
            "return_count": int(r["return_count"] or 0),
            "returns": float(r["returns"] or 0),
            "net_sales": float(r["net_sales"] or 0),
            "source": "NeginAgents.DataAPI",
            "database": ident["db"],
            "db_login": ident["login"],
            "readonly_verified": True,
            "policy_id": policy.get("policy_id"),
        }
        _audit(operation="sales_summary", period=req.period, ok=True, database=ident["db"],
               db_login=ident["login"], duration_ms=round((time.perf_counter() - started) * 1000, 2))
        return result
    except PermissionError as exc:
        _audit(operation="sales_summary", period=req.period, ok=False, error="readonly_identity_rejected")
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        _audit(operation="sales_summary", period=req.period, ok=False, error=type(exc).__name__)
        raise HTTPException(status_code=503, detail="sales data source unavailable") from exc

class AnalyticsSalesSummaryReq(BaseModel):
    period: Literal["latest_day", "mtd"] = "mtd"


def _clickhouse_sales_summary(period: str) -> dict:
    import subprocess
    if period == "latest_day":
        where = "sale_date=(select max(sale_date) from negin_analytics.sales_daily final)"
    else:
        where = "sale_date between concat(substring((select max(sale_date) from negin_analytics.sales_daily final),1,7),'/01') and (select max(sale_date) from negin_analytics.sales_daily final)"
    q = (
        "select min(sale_date) from_date,max(sale_date) to_date,"
        "sum(sale_count) sale_count,toFloat64(sum(gross_sales)) gross_sales,"
        "sum(return_count) return_count,toFloat64(sum(returns)) returns,"
        "toFloat64(sum(net_sales)) net_sales,max(synced_at) last_synced_at "
        "from negin_analytics.sales_daily final where " + where + " format JSONEachRow"
    )
    try:
        with httpx.Client(timeout=15, trust_env=False) as client:
            r = client.post("http://127.0.0.1:8123/", content=q.encode("utf-8"))
            r.raise_for_status()
            text = r.text
    except httpx.HTTPError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        raise RuntimeError((detail or "ClickHouse HTTP query failed")[:1000]) from exc
    lines=[x for x in text.splitlines() if x.strip()]
    if not lines:
        raise RuntimeError("ClickHouse sales summary returned no rows")
    return json.loads(lines[-1])


@router.post("/data/analytics/sales-summary")
def analytics_sales_summary(req: AnalyticsSalesSummaryReq, x_negin_key: str | None = Header(default=None, alias="x-negin-key")):
    started=time.perf_counter()
    _require_gateway_key(x_negin_key)
    try:
        r=_clickhouse_sales_summary(req.period)
        result={
            "ok":True,
            "operation":"analytics_sales_summary",
            "period":req.period,
            "from_date":r.get("from_date"),
            "to_date":r.get("to_date"),
            "sale_count":int(r.get("sale_count") or 0),
            "gross_sales":float(r.get("gross_sales") or 0),
            "return_count":int(r.get("return_count") or 0),
            "returns":float(r.get("returns") or 0),
            "net_sales":float(r.get("net_sales") or 0),
            "last_synced_at":r.get("last_synced_at"),
            "source":"ClickHouse",
            "target":"negin_analytics.sales_daily",
            "production_sql_accessed":False,
        }
        _audit(operation="analytics_sales_summary",period=req.period,ok=True,source="ClickHouse",
               duration_ms=round((time.perf_counter()-started)*1000,2))
        return result
    except Exception as exc:
        _audit(operation="analytics_sales_summary",period=req.period,ok=False,error=type(exc).__name__)
        raise HTTPException(status_code=503, detail="analytics sales source unavailable") from exc
