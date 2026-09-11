from __future__ import annotations
import os,re,json,time,threading
from pathlib import Path
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
router=APIRouter()
root=Path(__file__).resolve().parents[2]
_prod_sql_permit = root / "state" / "sql-production-permit.json"
_prod_sql_audit = root / "logs" / "sql-production-access.jsonl"
_prod_sql_lock = threading.Lock()

def _consume_prod_sql_permit():
    with _prod_sql_lock:
        if not _prod_sql_permit.exists():
            raise PermissionError("production SQL blocked: explicit owner approval required")
        try:
            permit=json.loads(_prod_sql_permit.read_text(encoding="utf-8"))
        except Exception:
            raise PermissionError("production SQL blocked: invalid approval permit")
        now=time.time()
        expires=float(permit.get("expires_at",0) or 0)
        remaining=int(permit.get("remaining_connections",0) or 0)
        if expires <= now or remaining <= 0:
            try: _prod_sql_permit.unlink(missing_ok=True)
            except Exception: pass
            raise PermissionError("production SQL blocked: explicit owner approval required")
        permit["remaining_connections"]=remaining-1
        permit["last_used_at"]=now
        if permit["remaining_connections"] <= 0:
            try: _prod_sql_permit.unlink(missing_ok=True)
            except Exception: pass
        else:
            tmp=_prod_sql_permit.with_suffix(".tmp")
            tmp.write_text(json.dumps(permit,ensure_ascii=False),encoding="utf-8")
            os.replace(tmp,_prod_sql_permit)
        try:
            _prod_sql_audit.parent.mkdir(parents=True,exist_ok=True)
            with _prod_sql_audit.open("a",encoding="utf-8") as f:
                f.write(json.dumps({"ts":now,"event":"permit_consumed","case_id":permit.get("case_id"),"reason":permit.get("reason"),"remaining_connections":max(0,remaining-1)},ensure_ascii=False)+"\n")
        except Exception:
            pass
        return permit
def cfg(k,d=""):
    v=os.getenv(k)
    if v:return v
    p=root/".env"
    if p.exists():
        for x in p.read_text(encoding="utf-8-sig").splitlines():
            if "=" in x and not x.lstrip().startswith("#"):
                a,b=x.split("=",1)
                if a.strip().lower()==k.lower(): return b.strip()
    return d
def cs():
    x=cfg("negin_sql_connection_string") or os.getenv("NEGIN_SQL_MCP_CONNECTION_STRING","").strip()
    if x:
        if "driver=" not in x.lower(): x="DRIVER={ODBC Driver 18 for SQL Server};"+x
        x=re.sub(r"(?i)user\s+id\s*=","UID=",x)
        x=re.sub(r"(?i)password\s*=","PWD=",x)
        x=re.sub(r"(?i)encrypt\s*=\s*false","Encrypt=no",x)
        x=re.sub(r"(?i)encrypt\s*=\s*true","Encrypt=yes",x)
        x=re.sub(r"(?i)trustservercertificate\s*=\s*false","TrustServerCertificate=no",x)
        x=re.sub(r"(?i)trustservercertificate\s*=\s*true","TrustServerCertificate=yes",x)
        return x
    vals={k:cfg(k) for k in ("negin_sql_server","negin_sql_username","negin_sql_password")}
    if not all(vals.values()): raise RuntimeError("readonly sql credentials are not configured")
    drv=cfg("negin_sql_driver","ODBC Driver 18 for SQL Server")
    db=cfg("negin_sql_database","NeginPakhsh")
    return f"DRIVER={{{drv}}};SERVER={vals['negin_sql_server']};DATABASE={db};UID={vals['negin_sql_username']};PWD={vals['negin_sql_password']};Encrypt=yes;TrustServerCertificate=yes;Application Name=NeginAgents-ReadOnly;"
def conn():
    _consume_prod_sql_permit()
    import pyodbc
    c=pyodbc.connect(cs(),timeout=5,autocommit=True)
    q="""select db_name() db,original_login() login,is_srvrolemember('sysadmin') sa,is_member('db_owner') dbo,is_member('db_datawriter') dw,has_perms_by_name(db_name(),'database','insert') ins,has_perms_by_name(db_name(),'database','update') upd,has_perms_by_name(db_name(),'database','delete') delp,has_perms_by_name(db_name(),'database','alter') alt"""
    r=row(c,q)[0]
    if str(r["db"]).lower()!=cfg("negin_sql_database","NeginPakhsh").lower() or any(int(r[k] or 0) for k in ("sa","dbo","dw","ins","upd","delp","alt")):
        c.close(); raise PermissionError("SQL identity is not accepted as strict read-only")
    return c,r
def guard(q):
    s=" "+re.sub(r"\s+"," ",q.strip().lower())+" "
    if not (s.lstrip().startswith("select ") or s.lstrip().startswith("with ")): raise PermissionError("SELECT/CTE only")
    for x in (";","--","/*","*/"," insert "," update "," delete "," merge "," drop "," alter "," create "," truncate "," exec "," execute "," dbcc "," into "," use "):
        if x in s: raise PermissionError("forbidden sql token")
def row(c,q,p=(),n=20000):
    guard(q);c.timeout=8;u=c.cursor();u.execute(q,p);cols=[x[0] for x in u.description];out=[]
    for r in u.fetchmany(n):
        d={}
        for i,k in enumerate(cols):
            v=r[i]
            if hasattr(v,"isoformat"):
                try:v=v.isoformat()
                except:pass
            if v is not None and not isinstance(v,(str,int,float,bool)):v=str(v)
            d[k]=v
        out.append(d)
    return out
class Req(BaseModel):
    action:str
    schema:str|None=None
    table:str|None=None
    sample_rows:int=Field(500,ge=1,le=1000)

@router.get("/sql/readonly/policy")
def production_sql_policy():
    return {"ok":True,"production_sql_default":"blocked","explicit_owner_approval_required":True,"permit_file":str(_prod_sql_permit),"production_server_execution":False}

@router.get("/sql/readonly/health")
def health():
    try:
        c,i=conn()
        try:p=row(c,"select 1 ok",n=1)
        finally:c.close()
        return {"ok":True,"agent_enforced_readonly":True,"database_level_writer":False,"identity":i,"probe":p}
    except PermissionError as e: raise HTTPException(403,str(e))
    except Exception as e: raise HTTPException(503,str(e))
class QueryReq(BaseModel):
    sql:str=Field(min_length=1,max_length=20000)
    max_rows:int=Field(1000,ge=1,le=5000)

@router.post("/sql/readonly/query")
def readonly_query(x:QueryReq):
    try:
        c,i=conn()
        try:
            r=row(c,x.sql,n=x.max_rows)
        finally:
            c.close()
        return {"ok":True,"agent_enforced_readonly":True,"bounded_result_rows":True,"identity":i,"row_count":len(r),"rows":r}
    except PermissionError as e:
        raise HTTPException(403,str(e))
    except Exception as e:
        raise HTTPException(503,str(e))


class VaranegarSchemaSearchReq(BaseModel):
    terms:list[str]=Field(min_length=1,max_length=12)
    max_rows:int=Field(500,ge=1,le=2000)

class VaranegarPricingReq(BaseModel):
    goods_code:str=Field(min_length=1,max_length=100)
    limit:int=Field(30,ge=1,le=200)

@router.post("/varanegar/schema/search")
def varanegar_schema_search(x:VaranegarSchemaSearchReq):
    try:
        terms=[str(t).strip().lower() for t in x.terms if str(t).strip()]
        if not terms: raise ValueError("at least one non-empty term required")
        c,i=conn()
        try:
            clauses=[]
            params=[]
            for term in terms:
                clauses.extend(["lower(s.name) like ?","lower(t.name) like ?","lower(c.name) like ?"])
                pat=f"%{term}%"
                params.extend([pat,pat,pat])
            q="select top ("+str(x.max_rows)+") s.name schema_name,t.name table_name,c.column_id,c.name column_name,ty.name data_type,c.max_length,c.is_nullable from sys.tables t join sys.schemas s on s.schema_id=t.schema_id join sys.columns c on c.object_id=t.object_id join sys.types ty on ty.user_type_id=c.user_type_id where "+" or ".join(clauses)+" order by s.name,t.name,c.column_id"
            r=row(c,q,tuple(params),n=x.max_rows)
        finally:
            c.close()
        return {"ok":True,"strict_readonly":True,"terms":terms,"row_count":len(r),"rows":r,"identity":i}
    except (PermissionError,ValueError) as e: raise HTTPException(403,str(e))
    except Exception as e: raise HTTPException(503,str(e))

@router.post("/varanegar/item/latest-pricing")
def varanegar_item_latest_pricing(x:VaranegarPricingReq):
    try:
        c,i=conn()
        try:
            q="""with g as (
select ID,GoodsCode,GoodsName,PGoodsCode,Barcode,ModifiedDate
from GNR.tblGoods
where GoodsCode=?
)
select top (""" + str(x.limit) + """)
x.SourceTable,x.PriceKind,x.RecordId,x.GoodsRef,x.Price,x.UserPrice,x.SupplierPrice,x.ManufacturerPrice,
x.StartDate,x.EndDate,x.ModifiedDate,x.CreationDate,x.DCRef,x.CustRef,x.CustCtgrRef,x.StatusInfo,
g.GoodsCode,g.GoodsName,g.PGoodsCode,g.Barcode
from (
select 'SLE.tblPrice' SourceTable,'sale' PriceKind,p.ID RecordId,p.GoodsRef,p.SalePrice Price,p.UserPrice,p.SupplierPrice,p.ManufacturerPrice,p.StartDate,p.EndDate,p.ModifiedDate,p.CreationDate,p.DCRef,p.CustRef,p.CustCtgrRef,cast(null as varchar(100)) StatusInfo
from SLE.tblPrice p join g on g.ID=p.GoodsRef
union all
select 'SLE.tblCPrice','customer_sale',p.ID,p.GoodsRef,p.SalePrice,p.UserPrice,cast(null as money),p.ManufacturerPrice,p.StartDate,p.EndDate,p.ModifiedDate,p.CreationDate,p.DCRef,p.CustRef,p.CustCtgrRef,concat('wizard=',coalesce(convert(varchar(20),p.CPriceWizardRef),''),',status=',coalesce(convert(varchar(10),p.CPriceWizardStatus),''))
from SLE.tblCPrice p join g on g.ID=p.GoodsRef
union all
select 'SLE.tblBuyPrice','buy',p.ID,p.GoodsRef,p.Price,cast(null as money),cast(null as money),cast(null as money),p.StartDate,p.EndDate,cast(null as datetime),cast(null as datetime),cast(null as int),cast(null as int),cast(null as int),concat('active=',coalesce(convert(varchar(10),p.IsActive),''))
from SLE.tblBuyPrice p join g on g.ID=p.GoodsRef
union all
select 'ICA.TblICABuyPrice','ica_buy',p.ID,p.GoodsRef,p.UnitPrice,cast(null as money),cast(null as money),cast(null as money),p.StartDate,p.EndDate,cast(null as datetime),cast(null as datetime),p.DCRef,cast(null as int),cast(null as int),concat('notactive=',coalesce(convert(varchar(10),p.ISNotActive),''),',tolled=',coalesce(convert(varchar(50),p.TolledUnitPrice),''))
from ICA.TblICABuyPrice p join g on g.ID=p.GoodsRef
union all
select 'SLE.tblCPriceWizardItem','wizard_item',p.ID,p.GoodsRef,p.SalePrice,cast(null as money),cast(null as money),cast(null as money),p.StartDate,p.EndDate,cast(null as datetime),cast(null as datetime),p.DCRef,p.CustRef,p.CustCtgrRef,concat('wizard=',convert(varchar(20),p.CPriceWizardRef),',base=',coalesce(convert(varchar(50),p.BasePrice),''))
from SLE.tblCPriceWizardItem p join g on g.ID=p.GoodsRef
) x cross join g
order by coalesce(x.CreationDate,x.ModifiedDate,try_convert(datetime,x.StartDate,111)) desc,x.RecordId desc"""
            r=row(c,q,(x.goods_code,),n=x.limit)
            master=row(c,"select top (1) ID GoodsRef,GoodsCode,GoodsName,PGoodsCode,Barcode,MainCode,FormalCode,GTIN,IRC,Tax,MoadianTaxPercent,ModifiedDate,ShowInSale,ShowInBuy from GNR.tblGoods where GoodsCode=?",(x.goods_code,),n=1)
        finally:
            c.close()
        return {"ok":True,"strict_readonly":True,"goods_code":x.goods_code,"found":bool(master),"master":master[0] if master else None,"row_count":len(r),"pricing":r,"identity":i}
    except PermissionError as e: raise HTTPException(403,str(e))
    except Exception as e: raise HTTPException(503,str(e))

@router.post("/sql/readonly/deep-intelligence")
def deep(x:Req):
    try:
        c,i=conn()
        try:
            if x.action=="catalog":
                tq="select s.name schema_name,t.name table_name,t.object_id,coalesce(sum(case when p.index_id in(0,1) then p.rows else 0 end),0) estimated_rows from sys.tables t join sys.schemas s on s.schema_id=t.schema_id left join sys.partitions p on p.object_id=t.object_id"
                cq="select s.name schema_name,o.name object_name,o.type_desc,c.column_id,c.name column_name,ty.name data_type,c.max_length,c.is_nullable,c.is_identity,c.is_computed from sys.objects o join sys.schemas s on s.schema_id=o.schema_id join sys.columns c on c.object_id=o.object_id join sys.types ty on ty.user_type_id=c.user_type_id where o.type in('U','V')"
                if x.schema:
                    tq += " where s.name=?"
                    cq += " and s.name=?"
                    tp=(x.schema,); cp=(x.schema,)
                else:
                    tp=(); cp=()
                tq += " group by s.name,t.name,t.object_id order by s.name,t.name"
                cq += " order by s.name,o.name,c.column_id"
                r={"tables":row(c,tq,tp,n=10000),"columns":row(c,cq,cp,n=50000),"schema_filter":x.schema}
            elif x.action=="relationships":
                r={"foreign_keys":row(c,"select fk.name fk_name,sp.name parent_schema,tp.name parent_table,cp.name parent_column,sr.name ref_schema,tr.name ref_table,cr.name ref_column from sys.foreign_keys fk join sys.foreign_key_columns f on f.constraint_object_id=fk.object_id join sys.tables tp on tp.object_id=f.parent_object_id join sys.schemas sp on sp.schema_id=tp.schema_id join sys.columns cp on cp.object_id=f.parent_object_id and cp.column_id=f.parent_column_id join sys.tables tr on tr.object_id=f.referenced_object_id join sys.schemas sr on sr.schema_id=tr.schema_id join sys.columns cr on cr.object_id=f.referenced_object_id and cr.column_id=f.referenced_column_id order by sp.name,tp.name,fk.name")}
            elif x.action=="dependencies":
                r={"dependencies":row(c,"select schema_name(o.schema_id) referencing_schema,o.name referencing_object,o.type_desc,d.referenced_schema_name,d.referenced_entity_name,d.referenced_minor_id from sys.sql_expression_dependencies d join sys.objects o on o.object_id=d.referencing_id where o.is_ms_shipped=0 order by schema_name(o.schema_id),o.name")}
            elif x.action=="definitions":
                r={"definitions":row(c,"select s.name schema_name,o.name object_name,o.type_desc,object_definition(o.object_id) definition from sys.objects o join sys.schemas s on s.schema_id=o.schema_id where o.is_ms_shipped=0 and o.type in('V','P','FN','IF','TF') order by s.name,o.name")}
            elif x.action=="permissions":
                r={
                    "database_effective":row(c,"select permission_name,subentity_name from fn_my_permissions(null,'database') order by permission_name",n=5000),
                    "server_effective":row(c,"select permission_name,subentity_name from fn_my_permissions(null,'server') order by permission_name",n=5000),
                    "roles":row(c,"select r.name role_name from sys.database_role_members drm join sys.database_principals r on r.principal_id=drm.role_principal_id join sys.database_principals m on m.principal_id=drm.member_principal_id where m.name=user_name() order by r.name",n=1000),
                    "explicit_permissions":row(c,"select p.state_desc,p.permission_name,p.class_desc,object_schema_name(p.major_id) schema_name,object_name(p.major_id) object_name from sys.database_permissions p where p.grantee_principal_id in (user_id(),database_principal_id('public')) order by p.class_desc,p.permission_name",n=20000)
                }
            elif x.action=="table_profile":
                if not x.schema or not x.table: raise ValueError("schema and table required")
                if not re.fullmatch(r"[\w\u0600-\u06ff]+",x.schema) or not re.fullmatch(r"[\w\u0600-\u06ff]+",x.table): raise ValueError("invalid identifier")
                q=f"select top ({x.sample_rows}) * from [{x.schema}].[{x.table}]"
                r={"sample":row(c,q,n=x.sample_rows),"bounded":True,"full_scan":False}
            else: raise ValueError("action must be catalog, relationships, dependencies, definitions, or table_profile")
        finally:c.close()
        return {"ok":True,"strict_readonly":True,"production_full_scan":False,"identity":i,"action":x.action,"result":r}
    except (PermissionError,ValueError) as e: raise HTTPException(403,str(e))
    except Exception as e: raise HTTPException(503,str(e))

