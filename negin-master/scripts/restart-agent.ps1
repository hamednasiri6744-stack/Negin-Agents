$erroractionpreference = "stop"

$root = split-path -parent $psscriptroot
set-location $root
$runtime = "$root\state\runtime.json"

function get-listener-pid {
    param([int]$port)
    try {
        $c = get-nettcpconnection -localport $port -state listen -erroraction stop | select-object -first 1
        if ($c) { return [int]$c.owningprocess }
    } catch {}
    return $null
}

function stop-verified {
    param([int]$id, [string]$kind)
    if (-not $id) { return }
    try {
        $w = get-ciminstance win32_process -filter "processid=$id" -erroraction stop
        if (-not $w) { return }
        $name = [string]$w.name
        $cmd = [string]$w.commandline
        $ok = $false
        if ($kind -eq "core") {
            $ok = ($name -ieq "python.exe" -and $cmd -like "*enterprise_master_agent.main*")
        } elseif ($kind -eq "bridge") {
            $ok = ($name -ieq "node.exe" -and (($cmd -like "*enterprise-master-agent*bridge*server.mjs*") -or ($cmd -like "*src\server.mjs*")))
        }
        if ($ok) {
            stop-process -id $id -force -erroraction silentlycontinue
        }
    } catch {}
}

$r = $null
if (test-path $runtime) {
    try { $r = get-content $runtime -raw | convertfrom-json } catch {}
}

$coreids = new-object system.collections.generic.list[int]
$bridgeids = new-object system.collections.generic.list[int]

$corelistener = get-listener-pid 8765
$bridgelistener = get-listener-pid 8766
if ($corelistener) { $coreids.add($corelistener) }
if ($bridgelistener) { $bridgeids.add($bridgelistener) }

if ($r) {
    foreach ($v in @($r.core_listener_pid,$r.core_pid,$r.core_launcher_pid)) {
        if ($v) { $coreids.add([int]$v) }
    }
    foreach ($v in @($r.bridge_listener_pid,$r.bridge_pid)) {
        if ($v) { $bridgeids.add([int]$v) }
    }
}

foreach ($id in ($bridgeids | select-object -unique)) { stop-verified $id "bridge" }
foreach ($id in ($coreids | select-object -unique)) { stop-verified $id "core" }

for ($i=0; $i -lt 30; $i++) {
    if (-not (get-listener-pid 8765) -and -not (get-listener-pid 8766)) { break }
    start-sleep -milliseconds 250
}

if (get-listener-pid 8765) { throw "core_port_8765_not_released" }
if (get-listener-pid 8766) { throw "bridge_port_8766_not_released" }

$python = "$root\.venv\scripts\python.exe"
$core = start-process -filepath $python -argumentlist "-m","enterprise_master_agent.main" -workingdirectory $root -passthru

$coreok = $false
$coreactual = $null
for ($i=0; $i -lt 40; $i++) {
    start-sleep -milliseconds 500
    try {
        $h = invoke-restmethod "http://127.0.0.1:8765/health" -timeoutsec 2
        if ($h.ok) {
            $coreok = $true
            $coreactual = get-listener-pid 8765
            break
        }
    } catch {}
}
if (-not $coreok) {
    stop-verified $core.id "core"
    throw "core_health_failed"
}

$node = (get-command node).source
$bridge = start-process -filepath $node -argumentlist "$root\bridge\src\server.mjs" -workingdirectory "$root\bridge" -passthru

$bridgeok = $false
$bridgeactual = $null
for ($i=0; $i -lt 30; $i++) {
    start-sleep -milliseconds 500
    try {
        $h = invoke-restmethod "http://127.0.0.1:8766/health" -timeoutsec 2
        if ($h.ok) {
            $bridgeok = $true
            $bridgeactual = get-listener-pid 8766
            break
        }
    } catch {}
}
if (-not $bridgeok) {
    stop-verified $bridge.id "bridge"
    throw "bridge_health_failed"
}

[ordered]@{
    core_pid = $coreactual
    core_listener_pid = $coreactual
    core_launcher_pid = $core.id
    bridge_pid = $bridgeactual
    bridge_listener_pid = $bridgeactual
    started = (get-date).tostring("o")
    health = @{
        core = $coreok
        bridge = $bridgeok
    }
} | convertto-json -depth 5 | set-content $runtime -encoding utf8

[ordered]@{
    ok = $true
    core_listener_pid = $coreactual
    core_launcher_pid = $core.id
    bridge_listener_pid = $bridgeactual
} | convertto-json -compress

