param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
$root = split-path -parent $myinvocation.mycommand.path
python (join-path $root 'code-x.py') @Args
exit $lastexitcode
