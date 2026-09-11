new-item -itemtype file -force "c:\enterprise-master-agent\state\maintenance.lock" | out-null
write-host "maintenance mode enabled"
