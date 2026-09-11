import os,json,time,hmac,urllib.request,urllib.error
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from collections import defaultdict,deque
from pathlib import Path
import ipaddress

host="0.0.0.0"
port=8770
up="http://127.0.0.1:8765"
key=os.environ.get("negin_gateway_api_key","")
log=Path(r"c:\programdata\neginagent\gateway-audit.jsonl")

get_paths={"/health","/integrations/health","/capabilities"}
post_paths={"/semantic/resolve","/query/plan","/kpi/sales-target","/clickhouse/query","/data/sales/summary","/data/analytics/sales-summary","/etl/sales/sync"}

hits=defaultdict(deque)
allowed_networks=[ipaddress.ip_network('127.0.0.0/8'),ipaddress.ip_network('192.168.80.0/20'),ipaddress.ip_network('172.24.240.0/20')]


def audit(**x):
    try:
        log.parent.mkdir(parents=True,exist_ok=True)
        x["ts"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
        with log.open("a",encoding="utf-8") as f:
            f.write(json.dumps(x,separators=(",",":"))+"\n")
    except Exception:
        pass

def sql_ok(s):
    q=" ".join(str(s).strip().lower().split())
    if not (q.startswith("select ") or q.startswith("with ")):
        return False

    bad=(
        ";","--","/*","*/"," insert "," update "," delete ",
        " drop "," alter "," truncate "," create "," attach ",
        " detach "," rename "," optimize "," system "," kill ",
        " grant "," revoke "," into outfile "," file("
    )

    q=" "+q+" "
    return not any(x in q for x in bad)

class handler(BaseHTTPRequestHandler):
    server_version="negin-gateway/1"

    def log_message(self,*a):
        pass

    def sendj(self,status,obj):
        b=json.dumps(obj,separators=(",",":")).encode()
        self.send_response(status)
        self.send_header("content-type","application/json")
        self.send_header("content-length",str(len(b)))
        self.send_header("cache-control","no-store")
        self.end_headers()
        self.wfile.write(b)

    def pre(self,method):
        ip=self.client_address[0]
        try:
            addr=ipaddress.ip_address(ip)
        except ValueError:
            self.sendj(403,{"error":"forbidden_source"})
            return False
        if not any(addr in n for n in allowed_networks):
            audit(ip=ip,method=method,path=self.path,status=403)
            self.sendj(403,{"error":"forbidden_source"})
            return False
        now=time.time()
        q=hits[ip]

        while q and now-q[0]>60:
            q.popleft()

        if len(q)>=60:
            audit(ip=ip,method=method,path=self.path,status=429)
            self.sendj(429,{"error":"rate_limited"})
            return False

        q.append(now)

        private_data = (self.path.startswith("/data/") or self.path.startswith("/etl/")) and any(addr in n for n in allowed_networks[1:])
        if not private_data:
            supplied=self.headers.get("x-negin-key","")
            if not key or not hmac.compare_digest(supplied,key):
                audit(ip=ip,method=method,path=self.path,status=401)
                self.sendj(401,{"error":"unauthorized"})
                return False

        allowed=(
            method=="GET" and self.path in get_paths
        ) or (
            method=="POST" and self.path in post_paths
        )

        if not allowed:
            audit(ip=ip,method=method,path=self.path,status=404)
            self.sendj(404,{"error":"not_found"})
            return False

        return True

    def proxy(self,method,body=None):
        req=urllib.request.Request(
            up+self.path,
            data=body,
            method=method,
            headers={"content-type":"application/json","x-negin-key":key}
        )

        try:
            with urllib.request.urlopen(req,timeout=20) as r:
                data=r.read()
                status=r.status
                ctype=r.headers.get("content-type","application/json")

        except urllib.error.HTTPError as e:
            data=e.read()
            status=e.code
            ctype=e.headers.get("content-type","application/json")

        except Exception:
            audit(
                ip=self.client_address[0],
                method=method,
                path=self.path,
                status=502
            )
            self.sendj(502,{"error":"upstream_unavailable"})
            return

        audit(
            ip=self.client_address[0],
            method=method,
            path=self.path,
            status=status
        )

        self.send_response(status)
        self.send_header("content-type",ctype)
        self.send_header("content-length",str(len(data)))
        self.send_header("cache-control","no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.pre("GET"):
            self.proxy("GET")

    def do_POST(self):
        if not self.pre("POST"):
            return

        try:
            n=int(self.headers.get("content-length","0"))

            if n<1 or n>65536:
                return self.sendj(413,{"error":"invalid_body_size"})

            body=self.rfile.read(n)
            obj=json.loads(body)

            if self.path=="/clickhouse/query" and not sql_ok(obj.get("sql","")):
                audit(
                    ip=self.client_address[0],
                    method="POST",
                    path=self.path,
                    status=400
                )
                return self.sendj(400,{"error":"read_only_sql_required"})

        except Exception:
            return self.sendj(400,{"error":"invalid_json"})

        self.proxy("POST",body)

if __name__=="__main__":
    if not key:
        raise SystemExit("negin_gateway_api_key is not set")

    ThreadingHTTPServer((host,port),handler).serve_forever()

