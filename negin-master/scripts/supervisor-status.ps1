$path = "c:\enterprise-master-agent\state\supervisor-status.json"
if (-not (test-path $path)) {
    write-host "supervisor status not found"
    exit 1
}
get-content $path -raw | convertfrom-json | convertto-json -depth 10
