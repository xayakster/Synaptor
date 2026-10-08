param (
    [string]$TargetPath = ".",
    [switch]$CheckOnly,
    [switch]$Force
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pyScript = Join-Path $scriptDir "bootstrap-agent-environment.py"

$argsList = @($TargetPath)
if ($CheckOnly) { $argsList += "--check-only" }
if ($Force) { $argsList += "--force" }

python $pyScript @argsList
exit $LASTEXITCODE
