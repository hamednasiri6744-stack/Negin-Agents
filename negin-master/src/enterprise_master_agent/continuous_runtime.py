
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .sql_intelligence import conn as sql_conn, row as sql_row

router = APIRouter()
ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "state" / "continuous"
ARTIFACTS = STATE / "artifacts"
DB = STATE / "jobs.sqlite3"
STATE.mkdir(parents=True, exist_ok=True)
ARTIFACTS.mkdir(parents=True, exist_ok=True)

_ALLOWED_KINDS = {"self_test", "sql_ecosystem_discovery"}
_TERMINAL = {"succeeded", "failed", "cancelled"}
_thread: threading.Thread | None = None
_stop = threading.Event()
_lock = threading.Lock()
_init_lock = threading.Lock()
_initialized = False

def _now() -> float:
    return time.time()

def _iso(ts: float | None = None) -> str:
    return datetime.fromtimestamp(ts or _now(), timezone.utc).isoformat()

def _db() -> sqlite3.Connection:
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("pragma journal_mode=wal")
    c.execute("pragma busy_timeout=5000")
    return c

def _init() -> None:
    global _initialized
    with _init_lock:
        if _initialized:
            return
        with _db() as c:
            c.executescript("""
            create table if not exists jobs(
              id text primary key, kind text not null, payload text not null, status text not null,
              control text not null default 'normal', checkpoint text not null default '{}',
              result text, error text, attempts integer not null default 0,
              max_attempts integer not null default 0, retry_base_seconds integer not null default 5,
              repeat_seconds integer not null default 0, next_run real not null,
              created_at real not null, updated_at real not null, started_at real, finished_at real
            );
            create index if not exists ix_jobs_due on jobs(status,next_run);
            create table if not exists events(
              id integer primary key autoincrement, job_id text, ts real not null,
              level text not null, event text not null, data text not null default '{}'
            );
            """)
            c.execute(
                "update jobs set status='retry_wait', control='normal', next_run=?, "
                "error=coalesce(error,'') || ? where status='running'",
                (_now(), "\nrecovered_after_runtime_restart"),
            )
        _initialized = True

def _event(job_id: str | None, level: str, event: str, data: dict[str, Any] | None = None) -> None:
    with _db() as c:
        c.execute(
            "insert into events(job_id,ts,level,event,data) values(?,?,?,?,?)",
            (job_id, _now(), level, event, json.dumps(data or {}, ensure_ascii=False, default=str)),
        )

def _job_dict(r: sqlite3.Row) -> dict[str, Any]:
    d = dict(r)
    for k in ("payload", "checkpoint", "result"):
        if d.get(k):
            try:
                d[k] = json.loads(d[k])
            except Exception:
                pass
    for k in ("created_at", "updated_at", "started_at", "finished_at", "next_run"):
        if d.get(k):
            d[k + "_iso"] = _iso(float(d[k]))
    return d

def _get(job_id: str) -> dict[str, Any]:
    with _db() as c:
        r = c.execute("select * from jobs where id=?", (job_id,)).fetchone()
    if not r:
        raise KeyError(job_id)
    return _job_dict(r)

def _control(job_id: str) -> str:
    with _db() as c:
        r = c.execute("select control from jobs where id=?", (job_id,)).fetchone()
    return str(r["control"]) if r else "cancel"

class PauseJob(Exception):
    pass

class CancelJob(Exception):
    pass

def _checkpoint(job_id: str, step: str, progress: float, data: dict[str, Any] | None = None) -> None:
    ctl = _control(job_id)
    if ctl == "cancel":
        raise CancelJob()
    if ctl == "pause":
        raise PauseJob()
    cp = {"step": step, "progress": round(max(0.0, min(1.0, progress)), 4), "data": data or {}, "ts": _iso()}
    with _db() as c:
        c.execute(
            "update jobs set checkpoint=?,updated_at=? where id=?",
            (json.dumps(cp, ensure_ascii=False, default=str), _now(), job_id),
        )
    _event(job_id, "info", "checkpoint", cp)

def _artifact(job_id: str, name: str, value: Any) -> str:
    folder = ARTIFACTS / job_id
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / name
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, p)
    return str(p)

def _self_test(job_id: str, payload: dict[str, Any], attempt: int) -> dict[str, Any]:
    steps = max(2, min(int(payload.get("steps", 4)), 20))
    fail_until = max(0, min(int(payload.get("fail_until_attempt", 0)), 10))
    for i in range(steps):
        _checkpoint(job_id, f"self_test_{i+1}", (i + 1) / steps, {"attempt": attempt})
        time.sleep(0.15)
    if attempt <= fail_until:
        raise RuntimeError(f"intentional_retry_test_attempt_{attempt}")
    return {"ok": True, "attempt": attempt, "steps": steps}

def _sql_ecosystem_discovery(job_id: str, payload: dict[str, Any], attempt: int) -> dict[str, Any]:
    allowed = ["NeginPakhsh", "Cloud", "grs"]
    requested = payload.get("databases") or allowed
    databases = [x for x in requested if x in allowed]
    if not databases:
        raise ValueError("no allowed database selected")
    c, identity = sql_conn()
    summary: dict[str, Any] = {"identity": identity, "databases": {}, "attempt": attempt}
    try:
        phases = len(databases) * 3 + 1
        done = 0
        for dbn in databases:
            prefix = f"[{dbn}]"
            counts = sql_row(
                c,
                f"select "
                f"(select count(*) from {prefix}.sys.tables) table_count,"
                f"(select count(*) from {prefix}.sys.views) view_count,"
                f"(select count(*) from {prefix}.sys.procedures) procedure_count,"
                f"(select count(*) from {prefix}.sys.objects where type in ('FN','IF','TF')) function_count",
                n=2,
            )[0]
            done += 1
            _checkpoint(job_id, f"{dbn}:counts", done / phases, counts)
            schemas = sql_row(
                c,
                f"select s.name schema_name,count(*) object_count "
                f"from {prefix}.sys.objects o join {prefix}.sys.schemas s on s.schema_id=o.schema_id "
                f"where o.is_ms_shipped=0 group by s.name order by count(*) desc",
                n=500,
            )
            done += 1
            _checkpoint(job_id, f"{dbn}:schemas", done / phases, {"schemas": len(schemas)})
            tables = sql_row(
                c,
                f"select s.name schema_name,t.name table_name,"
                f"coalesce(sum(case when p.index_id in(0,1) then p.rows else 0 end),0) estimated_rows "
                f"from {prefix}.sys.tables t join {prefix}.sys.schemas s on s.schema_id=t.schema_id "
                f"left join {prefix}.sys.partitions p on p.object_id=t.object_id "
                f"group by s.name,t.name order by estimated_rows desc",
                n=10000,
            )
            done += 1
            _checkpoint(job_id, f"{dbn}:tables", done / phases, {"tables": len(tables)})
            db_summary = {"counts": counts, "schemas": schemas, "tables": tables}
            path = _artifact(job_id, f"{dbn}-inventory.json", db_summary)
            summary["databases"][dbn] = {"counts": counts, "artifact": path}
        surface = sql_row(
            c,
            "select top (2000) s.name schema_name,o.name object_name,o.type_desc "
            "from sys.objects o join sys.schemas s on s.schema_id=o.schema_id "
            "where o.is_ms_shipped=0 and "
            "(s.name in ('NGT','FRU','GRS','GRS_') or "
            "o.name like '%api%' or o.name like '%webservice%' or "
            "o.name like '%replicat%' or o.name like '%synchroniz%' or o.name like '%endpoint%') "
            "order by s.name,o.type_desc,o.name",
            n=2000,
        )
        done += 1
        _checkpoint(job_id, "integration_surface", done / phases, {"objects": len(surface)})
        summary["integration_surface_artifact"] = _artifact(job_id, "integration-surface.json", surface)
        summary["completed_at"] = _iso()
        return summary
    finally:
        c.close()

def _run_handler(job_id: str, kind: str, payload: dict[str, Any], attempt: int) -> dict[str, Any]:
    if kind == "self_test":
        return _self_test(job_id, payload, attempt)
    if kind == "sql_ecosystem_discovery":
        return _sql_ecosystem_discovery(job_id, payload, attempt)
    raise ValueError("unsupported job kind")

def _claim() -> sqlite3.Row | None:
    now = _now()
    with _db() as c:
        c.execute("begin immediate")
        r = c.execute(
            "select * from jobs where status in ('queued','retry_wait') and control='normal' "
            "and next_run<=? order by created_at limit 1",
            (now,),
        ).fetchone()
        if not r:
            c.commit()
            return None
        c.execute(
            "update jobs set status='running',attempts=attempts+1,started_at=coalesce(started_at,?),"
            "updated_at=? where id=?",
            (now, now, r["id"]),
        )
        c.commit()
    with _db() as c:
        return c.execute("select * from jobs where id=?", (r["id"],)).fetchone()

def _finish_success(job: sqlite3.Row, result: dict[str, Any]) -> None:
    now=_now()
    repeat=int(job["repeat_seconds"] or 0)
    cycle=repeat>0 and _control(job["id"])=="normal"
    payload=json.dumps(result,ensure_ascii=False,default=str)
    with _db() as c:
        if cycle:
            c.execute("update jobs set status='queued',result=?,error=null,next_run=?,updated_at=?,finished_at=? where id=?",(payload,now+repeat,now,now,job["id"]))
        else:
            c.execute("update jobs set status='succeeded',result=?,error=null,updated_at=?,finished_at=? where id=?",(payload,now,now,job["id"]))
    _event(job["id"],"info","cycle_succeeded" if cycle else "succeeded",{"next_run_seconds":repeat} if cycle else {})

def _finish_error(job: sqlite3.Row, exc: Exception) -> None:
    now = _now()
    attempts = int(job["attempts"])
    max_attempts = int(job["max_attempts"])
    exhausted = max_attempts > 0 and attempts >= max_attempts
    err = f"{type(exc).__name__}: {exc}"
    if exhausted:
        with _db() as c:
            c.execute(
                "update jobs set status='failed',error=?,updated_at=?,finished_at=? where id=?",
                (err, now, now, job["id"]),
            )
        _event(job["id"], "error", "failed", {"error": err, "attempts": attempts})
        return
    base = max(1, int(job["retry_base_seconds"]))
    delay = min(300, base * (2 ** min(max(0, attempts - 1), 6)))
    with _db() as c:
        c.execute(
            "update jobs set status='retry_wait',error=?,next_run=?,updated_at=? where id=?",
            (err, now + delay, now, job["id"]),
        )
    _event(job["id"], "warning", "retry_scheduled", {"error": err, "delay_seconds": delay, "attempt": attempts})

def _worker() -> None:
    _event(None, "info", "worker_started", {"pid": os.getpid()})
    while not _stop.is_set():
        try:
            job = _claim()
            if not job:
                _stop.wait(1.0)
                continue
            job_id = str(job["id"])
            payload = json.loads(job["payload"])
            _event(job_id, "info", "started", {"attempt": int(job["attempts"]), "kind": job["kind"]})
            try:
                result = _run_handler(job_id, str(job["kind"]), payload, int(job["attempts"]))
                _finish_success(job, result)
            except PauseJob:
                with _db() as c:
                    c.execute("update jobs set status='paused',updated_at=? where id=?", (_now(), job_id))
                _event(job_id, "info", "paused")
            except CancelJob:
                with _db() as c:
                    c.execute("update jobs set status='cancelled',updated_at=?,finished_at=? where id=?", (_now(), _now(), job_id))
                _event(job_id, "info", "cancelled")
            except Exception as exc:
                _finish_error(job, exc)
        except Exception as exc:
            _event(None, "error", "worker_loop_error", {"error": f"{type(exc).__name__}: {exc}"})
            _stop.wait(2.0)

def start() -> None:
    global _thread
    _init()
    with _lock:
        if _thread and _thread.is_alive():
            return
        _stop.clear()
        _thread = threading.Thread(target=_worker, name="negin-continuous-worker", daemon=True)
        _thread.start()

class SubmitReq(BaseModel):
    kind: str = Field(min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)
    max_attempts: int = Field(default=0, ge=0, le=1000000)
    retry_base_seconds: int = Field(default=5, ge=1, le=300)
    repeat_seconds: int = Field(default=0, ge=0, le=31536000)

class ControlReq(BaseModel):
    action: str = Field(pattern=r"^(pause|resume|cancel)$")

@router.get("/runtime/continuous/health")
def continuous_health():
    start()
    with _db() as c:
        counts = {r["status"]: r["n"] for r in c.execute("select status,count(*) n from jobs group by status")}
    return {
        "ok": bool(_thread and _thread.is_alive()),
        "worker_alive": bool(_thread and _thread.is_alive()),
        "pid": os.getpid(),
        "durable_store": str(DB),
        "queue_counts": counts,
        "allowed_kinds": sorted(_ALLOWED_KINDS),
        "retry_until_success_supported": True,
        "checkpoint_resume_supported": True,
        "crash_recovery_supported": True,
        "recurring_jobs_supported": True,
        "arbitrary_shell_jobs": False,
        "production_write_jobs": False,
    }

@router.post("/runtime/continuous/jobs")
def submit(req: SubmitReq):
    start()
    if req.kind not in _ALLOWED_KINDS:
        raise HTTPException(status_code=400, detail="unsupported safe job kind")
    job_id = str(uuid.uuid4())
    now = _now()
    with _db() as c:
        c.execute(
            "insert into jobs(id,kind,payload,status,control,checkpoint,attempts,max_attempts,retry_base_seconds,"
            "repeat_seconds,next_run,created_at,updated_at) values(?,?,?,'queued','normal','{}',0,?,?,?,?,?,?)",
            (job_id, req.kind, json.dumps(req.payload, ensure_ascii=False, default=str),
             req.max_attempts, req.retry_base_seconds, req.repeat_seconds, now, now, now),
        )
    _event(job_id, "info", "submitted", {"kind": req.kind})
    return {"ok": True, "job": _get(job_id)}

@router.get("/runtime/continuous/jobs")
def jobs(limit: int = 50):
    start()
    limit = max(1, min(limit, 200))
    with _db() as c:
        rows = c.execute("select * from jobs order by created_at desc limit ?", (limit,)).fetchall()
    return {"jobs": [_job_dict(r) for r in rows]}

@router.get("/runtime/continuous/jobs/{job_id}")
def job(job_id: str):
    start()
    try:
        data = _get(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="job not found")
    with _db() as c:
        ev = c.execute(
            "select ts,level,event,data from events where job_id=? order by id desc limit 50",
            (job_id,),
        ).fetchall()
    data["events"] = [
        {"ts": r["ts"], "ts_iso": _iso(r["ts"]), "level": r["level"], "event": r["event"], "data": json.loads(r["data"])}
        for r in ev
    ]
    return {"job": data}

@router.post("/runtime/continuous/jobs/{job_id}/control")
def control(job_id: str, req: ControlReq):
    start()
    try:
        current = _get(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="job not found")
    if current["status"] in _TERMINAL and req.action != "resume":
        return {"ok": True, "job": current}
    now = _now()
    with _db() as c:
        if req.action == "pause":
            if current["status"] == "running":
                c.execute("update jobs set control='pause',updated_at=? where id=?", (now, job_id))
            else:
                c.execute("update jobs set control='pause',status='paused',updated_at=? where id=?", (now, job_id))
        elif req.action == "cancel":
            if current["status"] == "running":
                c.execute("update jobs set control='cancel',updated_at=? where id=?", (now, job_id))
            else:
                c.execute("update jobs set control='cancel',status='cancelled',updated_at=?,finished_at=? where id=?", (now, now, job_id))
        else:
            c.execute(
                "update jobs set control='normal',status='queued',next_run=?,updated_at=?,finished_at=null where id=?",
                (now, now, job_id),
            )
    _event(job_id, "info", f"control_{req.action}")
    return {"ok": True, "job": _get(job_id)}

start()
