from __future__ import annotations

import datetime as dt
import decimal
import json
import os
import re
import sys
from typing import Any

ALLOWED_DATABASES = ("NeginPakhsh", "Cloud", "grs")
EXPECTED_LOGIN = "Negin_Report_ReadOnly"
MAX_ROWS = 1000
IDENTIFIER_RE = re.compile(r"^[\w\u0600-\u06ff]+$", re.UNICODE)

BLOCKED_WORDS = (
    "insert", "update", "delete", "merge", "drop", "alter", "create", "truncate",
    "exec", "execute", "dbcc", "into", "use", "grant", "revoke", "deny",
    "backup", "restore", "reconfigure", "shutdown", "kill", "waitfor", "bulk",
    "openrowset", "openquery", "opendatasource",
)


def fail(message: str, code: int = 2) -> None:
    sys.stdout.write(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
    raise SystemExit(code)


def env(name: str, default: str = "") -> str:
    return str(os.environ.get(name, default)).strip()


def validate_database(database: str) -> str:
    for item in ALLOWED_DATABASES:
        if item.lower() == str(database or "").lower():
            return item
    raise PermissionError("database is not allowlisted")


def guard_sql(sql: str) -> None:
    raw = str(sql or "")
    if not (1 <= len(raw) <= 20000):
        raise PermissionError("sql length must be 1..20000")
    start = raw.lstrip().lower()
    if not re.match(r"^(select|with)\b", start):
        raise PermissionError("SELECT/CTE only")
    for token in (";", "--", "/*", "*/"):
        if token in raw:
            raise PermissionError(f"forbidden sql token: {token}")
    for word in BLOCKED_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", raw, re.IGNORECASE):
            raise PermissionError(f"forbidden sql token: {word}")
    if re.search(r"\bnext\s+value\s+for\b", raw, re.IGNORECASE):
        raise PermissionError("sequences are not allowed")
    if re.search(r"\bxp_[a-z0-9_]*\b|\bsp_oa[a-z0-9_]*\b", raw, re.IGNORECASE):
        raise PermissionError("extended procedures are not allowed")
    three_part = re.compile(
        r"(?:\[[^\]]+\]|[a-z_][\w$]*)\s*\.\s*"
        r"(?:\[[^\]]+\]|[a-z_][\w$]*)\s*\.\s*"
        r"(?:\[[^\]]+\]|[a-z_][\w$]*)",
        re.IGNORECASE,
    )
    if three_part.search(raw):
        raise PermissionError("cross-database three-part identifiers are not allowed")


def connection_string(database: str) -> str:
    server = env("negin_sql_server")
    username = env("negin_sql_username")
    password = env("negin_sql_password")
    driver = env("negin_sql_driver", "ODBC Driver 18 for SQL Server")
    if not server or not username or not password:
        raise RuntimeError("readonly sql credentials are not configured")
    if username.casefold() != EXPECTED_LOGIN.casefold():
        raise PermissionError("only Negin_Report_ReadOnly is accepted")
    database = validate_database(database)
    return (
        f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};"
        f"UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;"
        f"Application Name=Negin-Varanegar-Readonly-MCP;"
    )


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        data = bytes(value)
        return {"type": "bytes", "hex": data[:256].hex(), "truncated": len(data) > 256}
    return str(value)


def rows(cursor, limit: int) -> list[dict[str, Any]]:
    limit = max(1, min(MAX_ROWS, int(limit)))
    names = [col[0] for col in (cursor.description or [])]
    out: list[dict[str, Any]] = []
    for record in cursor.fetchmany(limit):
        out.append({names[i]: json_safe(record[i]) for i in range(len(names))})
    return out


def permission_snapshot(cursor) -> dict[str, Any]:
    cursor.execute(
        """
        select
          db_name() as database_name,
          original_login() as original_login,
          user_name() as database_user,
          is_srvrolemember('sysadmin') as is_sysadmin,
          is_member('db_owner') as is_db_owner,
          is_member('db_datawriter') as is_db_datawriter,
          has_perms_by_name(db_name(),'database','insert') as db_insert,
          has_perms_by_name(db_name(),'database','update') as db_update,
          has_perms_by_name(db_name(),'database','delete') as db_delete,
          has_perms_by_name(db_name(),'database','alter') as db_alter,
          has_perms_by_name(db_name(),'database','control') as db_control
        """
    )
    identity = rows(cursor, 1)[0]

    cursor.execute(
        """
        select r.name as role_name
        from sys.database_role_members drm
        join sys.database_principals r on r.principal_id=drm.role_principal_id
        join sys.database_principals m on m.principal_id=drm.member_principal_id
        where m.name=user_name()
        order by r.name
        """
    )
    roles = rows(cursor, 100)

    cursor.execute(
        """
        with principals as (
          select user_id() as principal_id
          union all select database_principal_id('public')
          union all
          select drm.role_principal_id
          from sys.database_role_members drm
          where drm.member_principal_id=user_id()
        )
        select
          p.state_desc,
          p.permission_name,
          p.class_desc,
          object_schema_name(p.major_id) as schema_name,
          object_name(p.major_id) as object_name
        from sys.database_permissions p
        where p.grantee_principal_id in (select principal_id from principals)
          and p.state in ('G','W')
          and p.permission_name in
            ('INSERT','UPDATE','DELETE','ALTER','CONTROL','TAKE OWNERSHIP')
        order by p.class_desc,p.permission_name
        """
    )
    write_grants = rows(cursor, 500)

    unsafe_flags = (
        identity["is_sysadmin"], identity["is_db_owner"], identity["is_db_datawriter"],
        identity["db_insert"], identity["db_update"], identity["db_delete"],
        identity["db_alter"], identity["db_control"],
    )
    if any(int(x or 0) for x in unsafe_flags) or write_grants:
        raise PermissionError("SQL identity is not accepted as strict read-only in this database")
    if str(identity["original_login"]).casefold() != EXPECTED_LOGIN.casefold():
        raise PermissionError("unexpected SQL login identity")

    return {
        "identity": identity,
        "roles": roles,
        "write_grants_detected": write_grants,
        "strict_readonly_verified": True,
    }


def connect(database: str):
    import pyodbc

    database = validate_database(database)
    conn = pyodbc.connect(connection_string(database), timeout=5, autocommit=True)
    cursor = conn.cursor()
    try:
        cursor.timeout = 15
    except Exception:
        pass
    cursor.execute("set lock_timeout 3000")
    permission_snapshot(cursor)
    return conn, cursor


def action_health(database: str) -> dict[str, Any]:
    database = validate_database(database)
    conn, cursor = connect(database)
    try:
        snapshot = permission_snapshot(cursor)
        cursor.execute("select 1 as ok")
        probe = rows(cursor, 1)
        return {"ok": True, "database": database, "probe": probe, **snapshot}
    finally:
        conn.close()


def action_databases() -> dict[str, Any]:
    result = []
    for database in ALLOWED_DATABASES:
        try:
            info = action_health(database)
            result.append({
                "database": database,
                "accessible": True,
                "strict_readonly_verified": info["strict_readonly_verified"],
                "identity": info["identity"],
            })
        except Exception as exc:
            result.append({"database": database, "accessible": False, "error": str(exc)})
    return {"ok": True, "databases": result}


def action_permissions(database: str) -> dict[str, Any]:
    database = validate_database(database)
    conn, cursor = connect(database)
    try:
        return {"ok": True, "database": database, **permission_snapshot(cursor)}
    finally:
        conn.close()


def action_schema_search(database: str, terms: list[str], max_rows: int) -> dict[str, Any]:
    database = validate_database(database)
    clean_terms = [str(t).strip()[:100] for t in terms if str(t).strip()][:12]
    if not clean_terms:
        raise ValueError("at least one search term is required")
    limit = max(1, min(500, int(max_rows)))
    conn, cursor = connect(database)
    try:
        clauses = []
        params: list[str] = []
        for term in clean_terms:
            like = f"%{term}%"
            clauses.append("(s.name like ? or o.name like ? or c.name like ?)")
            params.extend([like, like, like])
        sql = f"""
        select top ({limit})
          s.name as schema_name,
          o.name as object_name,
          o.type_desc as object_type,
          c.name as column_name,
          ty.name as data_type,
          c.max_length,
          c.is_nullable
        from sys.objects o
        join sys.schemas s on s.schema_id=o.schema_id
        left join sys.columns c on c.object_id=o.object_id
        left join sys.types ty on ty.user_type_id=c.user_type_id
        where o.is_ms_shipped=0
          and ({" or ".join(clauses)})
        order by s.name,o.name,c.column_id
        """
        cursor.execute(sql, params)
        data = rows(cursor, limit)
        return {"ok": True, "database": database, "terms": clean_terms, "row_count": len(data), "rows": data}
    finally:
        conn.close()


def action_catalog(database: str, schema: str | None, object_type: str, max_rows: int) -> dict[str, Any]:
    database = validate_database(database)
    limit = max(1, min(1000, int(max_rows)))
    type_map = {
        "table": ("U",),
        "view": ("V",),
        "procedure": ("P", "PC"),
        "function": ("FN", "IF", "TF", "FS", "FT"),
        "all": ("U", "V", "P", "PC", "FN", "IF", "TF", "FS", "FT"),
    }
    if object_type not in type_map:
        raise ValueError("invalid object_type")
    if schema and not IDENTIFIER_RE.fullmatch(schema):
        raise ValueError("invalid schema identifier")
    types = type_map[object_type]
    marks = ",".join("?" for _ in types)
    params: list[Any] = list(types)
    schema_filter = ""
    if schema:
        schema_filter = " and s.name=?"
        params.append(schema)
    conn, cursor = connect(database)
    try:
        cursor.execute(
            f"""
            select top ({limit})
              s.name as schema_name,
              o.name as object_name,
              o.type_desc as object_type,
              o.create_date,
              o.modify_date
            from sys.objects o
            join sys.schemas s on s.schema_id=o.schema_id
            where o.is_ms_shipped=0
              and o.type in ({marks})
              {schema_filter}
            order by s.name,o.type_desc,o.name
            """,
            params,
        )
        data = rows(cursor, limit)
        return {"ok": True, "database": database, "row_count": len(data), "rows": data}
    finally:
        conn.close()


def action_relationships(database: str, schema: str | None, max_rows: int) -> dict[str, Any]:
    database = validate_database(database)
    limit = max(1, min(1000, int(max_rows)))
    if schema and not IDENTIFIER_RE.fullmatch(schema):
        raise ValueError("invalid schema identifier")
    conn, cursor = connect(database)
    try:
        sql = f"""
        select top ({limit})
          fk.name as foreign_key,
          ps.name as parent_schema,
          pt.name as parent_table,
          pc.name as parent_column,
          rs.name as referenced_schema,
          rt.name as referenced_table,
          rc.name as referenced_column
        from sys.foreign_keys fk
        join sys.foreign_key_columns fkc on fkc.constraint_object_id=fk.object_id
        join sys.tables pt on pt.object_id=fkc.parent_object_id
        join sys.schemas ps on ps.schema_id=pt.schema_id
        join sys.columns pc on pc.object_id=pt.object_id and pc.column_id=fkc.parent_column_id
        join sys.tables rt on rt.object_id=fkc.referenced_object_id
        join sys.schemas rs on rs.schema_id=rt.schema_id
        join sys.columns rc on rc.object_id=rt.object_id and rc.column_id=fkc.referenced_column_id
        where (? is null or ps.name=? or rs.name=?)
        order by ps.name,pt.name,fk.name,fkc.constraint_column_id
        """
        cursor.execute(sql, schema, schema, schema)
        data = rows(cursor, limit)
        return {"ok": True, "database": database, "row_count": len(data), "rows": data}
    finally:
        conn.close()


def action_table_sample(database: str, schema: str, table: str, limit: int) -> dict[str, Any]:
    database = validate_database(database)
    limit = max(1, min(50, int(limit)))
    if not IDENTIFIER_RE.fullmatch(schema) or not IDENTIFIER_RE.fullmatch(table):
        raise ValueError("invalid table identifier")
    conn, cursor = connect(database)
    try:
        cursor.execute(
            """
            select top (1) o.type_desc
            from sys.objects o
            join sys.schemas s on s.schema_id=o.schema_id
            where s.name=? and o.name=? and o.type in ('U','V')
            """,
            schema,
            table,
        )
        found = rows(cursor, 1)
        if not found:
            raise ValueError("table or view not found")
        cursor.execute(f"select top ({limit}) * from [{schema}].[{table}]")
        data = rows(cursor, limit)
        return {
            "ok": True,
            "database": database,
            "schema": schema,
            "table": table,
            "bounded": True,
            "row_count": len(data),
            "rows": data,
        }
    finally:
        conn.close()


def action_query(database: str, sql: str, max_rows: int) -> dict[str, Any]:
    database = validate_database(database)
    guard_sql(sql)
    limit = max(1, min(MAX_ROWS, int(max_rows)))
    conn, cursor = connect(database)
    try:
        cursor.execute(sql)
        data = rows(cursor, limit)
        return {
            "ok": True,
            "database": database,
            "agent_enforced_readonly": True,
            "bounded_result_rows": True,
            "row_count": len(data),
            "max_rows": limit,
            "rows": data,
        }
    finally:
        conn.close()


def main() -> None:
    try:
        request = json.loads(sys.stdin.read() or "{}")
        action = str(request.get("action") or "")
        if action == "health":
            response = action_health(request.get("database") or "NeginPakhsh")
        elif action == "databases":
            response = action_databases()
        elif action == "permissions":
            response = action_permissions(request.get("database"))
        elif action == "schema_search":
            response = action_schema_search(
                request.get("database"), request.get("terms") or [], request.get("max_rows") or 200
            )
        elif action == "catalog":
            response = action_catalog(
                request.get("database"), request.get("schema"), request.get("object_type") or "all",
                request.get("max_rows") or 300,
            )
        elif action == "relationships":
            response = action_relationships(
                request.get("database"), request.get("schema"), request.get("max_rows") or 300
            )
        elif action == "table_sample":
            response = action_table_sample(
                request.get("database"), request.get("schema"), request.get("table"), request.get("limit") or 10
            )
        elif action == "query":
            response = action_query(
                request.get("database"), request.get("sql") or "", request.get("max_rows") or 200
            )
        else:
            raise ValueError("unknown action")
        sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")))
    except Exception as exc:
        fail(str(exc))


if __name__ == "__main__":
    main()
