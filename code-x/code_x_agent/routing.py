from __future__ import annotations
from typing import Any

CODE_X_AGENT="@Code-X"
NEGIN_AGENT="@Negin Agent v4"

CODE_TERMS=("code","coding","implement","refactor","debug","bug","test","repo","repository","git","github","pull request","frontend","backend","fullstack","react","typescript","python","rust","software architecture","mcp server","کد","کدنویسی","برنامه نویسی","پیاده سازی","ریفکتور","دیباگ","باگ","تست","فرانت","بک اند","فول استک","معماری نرم افزار")
NEGIN_TERMS=("negin pakhsh","نگین پخش","production sql","sql","database","varanegar","n8n","workflow","rpa","windows","server","tailscale","network","system","business rule","semantic","kpi","sales","warehouse","treasury","accounting","approval","knowledge","دیتابیس","ورانگر","پروداکشن","فروش","خزانه","حسابداری","انبار","ورکفلو","اتوماسیون","سیستم","ویندوز","سرور","شبکه","قوانین کسب و کار","مجوز","تایید")
CODE_BOUNDS=("repository inspection and source reasoning","implementation/refactoring inside approved roots","tests/build/debug/code review/git/PR","software architecture and MCP implementation")
NEGIN_BOUNDS=("enterprise semantics and business rules","production SQL/data governance","RPA/n8n/workstation/server/network operations","owner approvals, knowledge/observability, independent verification")

def complementarity()->dict[str,Any]:
    return {"ok":True,"contract_version":"1.1.0","semantic_authority":{"name":"NEGIN_PAKHSH_SEMANTIC_CORE","owner":NEGIN_AGENT,"rule":"Semantic Core defines business meaning, formula and scope; live read-only data supplies current values.","conflict_policy":"Report conflicts explicitly; never silently overwrite canonical semantics."},"agents":{"code_x":{"name":CODE_X_AGENT,"role":"software_engineering_specialist","owns":list(CODE_BOUNDS)},"negin":{"name":NEGIN_AGENT,"role":"enterprise_orchestrator_and_safety_boundary","owns":list(NEGIN_BOUNDS)}},"collaboration_policy":{"code_only":"Code-X leads.","enterprise_only":"Negin leads; Code-X hands off.","mixed":"Negin decomposes/approves -> Code-X implements bounded repo work -> Negin independently verifies."},"code_x_forbidden_direct_domains":["production_sql","rpa","n8n_mutation","remote_server_mutation","enterprise_approval"]}

def _hits(text:str,terms:tuple[str,...])->list[str]:
    t=text.casefold()
    return [x for x in terms if x.casefold() in t]

def route_task(task:str)->dict[str,Any]:
    text=str(task or "").strip()
    if not text:
        return {"ok":False,"error":"task is required"}
    ch,nh=_hits(text,CODE_TERMS),_hits(text,NEGIN_TERMS)
    cs=min(100,20+14*len(ch)); ns=min(100,20+14*len(nh))
    if ch and nh:
        mode,primary,secondary,handoff,reason="collaborative",NEGIN_AGENT,CODE_X_AGENT,True,"Mixed software-engineering and enterprise/operational task."
    elif nh:
        mode,primary,secondary,handoff,reason="negin_primary",NEGIN_AGENT,CODE_X_AGENT,True,"Task is primarily inside Negin-owned boundaries."
    elif ch:
        mode,primary,secondary,handoff,reason="code_x_primary",CODE_X_AGENT,NEGIN_AGENT,False,"Task is primarily repository/software engineering."
    else:
        mode,primary,secondary,handoff,reason="collaborative",NEGIN_AGENT,CODE_X_AGENT,True,"No decisive signal; default to Negin orchestration with Code-X available."
        cs,ns=40,50
    return {"ok":True,"task":text,"mode":mode,"primary_agent":primary,"secondary_agent":secondary,"scores":{"code_x":cs,"negin":ns},"signals":{"code_x":ch,"negin":nh},"reason":reason,"handoff_required":handoff,"boundaries":{"code_x":list(CODE_BOUNDS),"negin":list(NEGIN_BOUNDS)}}

def handoff_to_negin(task:str,reason:str="",requested_capability:str="")->dict[str,Any]:
    routed=route_task(task)
    if not routed.get("ok"):
        return routed
    return {"ok":True,"handoff_required":True,"source_agent":CODE_X_AGENT,"target_agent":NEGIN_AGENT,"task":task,"reason":reason.strip() or routed["reason"],"requested_capability":requested_capability.strip() or "enterprise_orchestration","routing":routed,"continuation_contract":["Negin owns enterprise context, approvals and production safety. For Negin Pakhsh/Varanegar business semantics, resolve against active NEGIN_PAKHSH_SEMANTIC_CORE before implementation and never infer business rules from repository/schema/general knowledge.","If repository changes are required, delegate a bounded implementation subtask back to Code-X.","Negin independently verifies final postconditions before COMPLETE."],"network_call_performed":False}
