from __future__ import annotations

import hmac
import json

import httpx
import subprocess
import time
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from .data_api import _service_conn
from .sql_intelligence import cfg, row

router = APIRouter()
root = Path(__file__).resolve().parents[2]
_policy_path = root / "state" / "clickhouse-etl-policy.json"
_audit_path = root / "logs" / "clickhouse-etl.jsonl"


class SalesSyncReq(BaseModel):
    mode: Literal["current_month"] = "current_month"


def _require_gateway_key(x_negin_key: str | None) -> None:
    expected = cfg("negin_gateway_api_key", "")
    if not expected:
        raise HTTPException(status_code=503, detail="ETL authentication is not configured")
    if not hmac.compare_digest(x_negin_key or "", expected):
        raise HTTPException(status_code=401, detail="unauthorized")


def _policy() -> dict:
    if not _policy_path.exists():
        raise HTTPException(status_code=403, detail="ClickHouse ETL policy is not approved")
    try:
        p = json.loads(_policy_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="ClickHouse ETL policy is invalid") from exc
    if not p.get("enabled"):
        raise HTTPException(status_code=403, detail="ClickHouse ETL policy is disabled")
    return p


def _audit(**event) -> None:
    try:
        _audit_path.parent.mkdir(parents=True, exist_ok=True)
        event["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with _audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
    except Exception:
        pass


def _source_daily_rows() -> tuple[list[dict], dict]:
    c, ident = _service_conn()
    try:
        q = """
with d as (
    select max(SaleDate) as ToDate
    from SLE.tblSaleHdr
    where isnull(CancelFlag,0)=0
),
b as (
    select left(ToDate,7) + '/01' as FromDate, ToDate
    from d
),
dates as (
    select s.SaleDate as d
    from SLE.tblSaleHdr s cross join b
    where s.SaleDate between b.FromDate and b.ToDate and isnull(s.CancelFlag,0)=0
    group by s.SaleDate
    union
    select r.RetSaleDate as d
    from SLE.tblRetSaleHdr r cross join b
    where r.RetSaleDate between b.FromDate and b.ToDate and isnull(r.CancelFlag,0)=0
    group by r.RetSaleDate
),
sales as (
    select s.SaleDate as d,
           count_big(*) as sale_count,
           sum(cast(s.TotalAmount as decimal(38,2))) as gross_sales
    from SLE.tblSaleHdr s cross join b
    where s.SaleDate between b.FromDate and b.ToDate and isnull(s.CancelFlag,0)=0
    group by s.SaleDate
),
rets as (
    select r.RetSaleDate as d,
           count_big(*) as return_count,
           sum(cast(r.TotalAmount as decimal(38,2))) as returns
    from SLE.tblRetSaleHdr r cross join b
    where r.RetSaleDate between b.FromDate and b.ToDate and isnull(r.CancelFlag,0)=0
    group by r.RetSaleDate
)
select dates.d as sale_date,
       coalesce(sales.sale_count,0) as sale_count,
       coalesce(sales.gross_sales,0) as gross_sales,
       coalesce(rets.return_count,0) as return_count,
       coalesce(rets.returns,0) as returns,
       coalesce(sales.gross_sales,0)-coalesce(rets.returns,0) as net_sales
from dates
left join sales on sales.d=dates.d
left join rets on rets.d=dates.d
order by dates.d
"""
        rows = row(c, q, n=40)
    finally:
        c.close()
    return rows, ident


def _ch(args: list[str], input_text: str | None = None, timeout: int = 30) -> str:
    query = None
    for i, arg in enumerate(args):
        if arg == "--query" and i + 1 < len(args):
            query = args[i + 1]
            break
    if not query:
        raise ValueError("ClickHouse HTTP transport requires --query")
    try:
        with httpx.Client(timeout=timeout, trust_env=False) as client:
            if input_text is None:
                r = client.post("http://127.0.0.1:8123/", content=query.encode("utf-8"))
            else:
                r = client.post("http://127.0.0.1:8123/", params={"query": query}, content=input_text.encode("utf-8"))
            r.raise_for_status()
            return r.text.strip()
    except httpx.HTTPError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        raise RuntimeError((detail or "ClickHouse HTTP command failed")[:1000]) from exc


def _insert_rows(rows: list[dict], ident: dict) -> int:
    if not rows:
        return 0
    version = int(time.time_ns())
    now_ms = int(time.time() * 1000)
    payload_lines = []
    for r in rows:
        payload_lines.append(json.dumps({
            "sale_date": str(r["sale_date"]),
            "sale_count": int(r["sale_count"] or 0),
            "gross_sales": str(r["gross_sales"] or 0),
            "return_count": int(r["return_count"] or 0),
            "returns": str(r["returns"] or 0),
            "net_sales": str(r["net_sales"] or 0),
            "source_db": str(ident["db"]),
            "source_login": str(ident["login"]),
            "sync_version": version,
            "synced_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_ms / 1000)),
        }, separators=(",", ":")))
    _ch(
        ["--query", "insert into negin_analytics.sales_daily format JSONEachRow"],
        "\n".join(payload_lines) + "\n",
        timeout=30,
    )
    return version


def _source_totals(rows: list[dict]) -> dict:
    return {
        "days": len(rows),
        "sale_count": sum(int(r["sale_count"] or 0) for r in rows),
        "gross_sales": sum(float(r["gross_sales"] or 0) for r in rows),
        "return_count": sum(int(r["return_count"] or 0) for r in rows),
        "returns": sum(float(r["returns"] or 0) for r in rows),
        "net_sales": sum(float(r["net_sales"] or 0) for r in rows),
    }


def _clickhouse_totals(from_date: str, to_date: str) -> dict:
    q = (
        "select count() days, sum(sale_count) sale_count, "
        "toFloat64(sum(gross_sales)) gross_sales, sum(return_count) return_count, "
        "toFloat64(sum(returns)) returns, toFloat64(sum(net_sales)) net_sales "
        "from negin_analytics.sales_daily final "
        f"where sale_date between '{from_date}' and '{to_date}' format JSONEachRow"
    )
    out = _ch(["--query", q], timeout=20)
    return json.loads(out.splitlines()[-1]) if out else {}


@router.post("/etl/sales/sync")
def sales_sync(req: SalesSyncReq, x_negin_key: str | None = Header(default=None, alias="x-negin-key")):
    started = time.perf_counter()
    _require_gateway_key(x_negin_key)
    policy = _policy()
    if req.mode not in (policy.get("modes") or []):
        raise HTTPException(status_code=403, detail="ETL mode is not approved")
    try:
        rows, ident = _source_daily_rows()
        max_days = int(policy.get("max_days_per_sync", 31))
        if len(rows) > max_days:
            raise RuntimeError("source result exceeded ETL day bound")
        if not rows:
            raise RuntimeError("source returned no daily rows")

        source = _source_totals(rows)
        version = _insert_rows(rows, ident)
        from_date = str(rows[0]["sale_date"])
        to_date = str(rows[-1]["sale_date"])
        ch = _clickhouse_totals(from_date, to_date)

        reconciled = (
            int(ch.get("days", -1)) == source["days"]
            and int(ch.get("sale_count", -1)) == source["sale_count"]
            and int(ch.get("return_count", -1)) == source["return_count"]
            and abs(float(ch.get("gross_sales", -1)) - source["gross_sales"]) < 0.01
            and abs(float(ch.get("returns", -1)) - source["returns"]) < 0.01
            and abs(float(ch.get("net_sales", -1)) - source["net_sales"]) < 0.01
        )
        result = {
            "ok": reconciled,
            "mode": req.mode,
            "from_date": from_date,
            "to_date": to_date,
            "rows_written": len(rows),
            "sync_version": version,
            "source": source,
            "clickhouse": ch,
            "reconciled": reconciled,
            "source_db": ident["db"],
            "source_login": ident["login"],
            "readonly_verified": True,
            "target": "negin_analytics.sales_daily",
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        }
        _audit(event="sales_sync", ok=reconciled, mode=req.mode, from_date=from_date, to_date=to_date,
               rows_written=len(rows), source_db=ident["db"], source_login=ident["login"],
               reconciled=reconciled, duration_ms=result["duration_ms"])
        if not reconciled:
            raise HTTPException(status_code=503, detail="ClickHouse reconciliation failed")
        return result
    except HTTPException:
        raise
    except PermissionError as exc:
        _audit(event="sales_sync", ok=False, error="readonly_identity_rejected")
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        _audit(event="sales_sync", ok=False, error=type(exc).__name__)
        raise HTTPException(status_code=503, detail="sales ETL unavailable") from exc
