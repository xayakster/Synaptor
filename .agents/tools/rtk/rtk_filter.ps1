param (
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CommandArgs
)

if (-not $CommandArgs) {
    Write-Host "Usage: rtk_filter.ps1 <command> [args...]"
    exit 1
}

$scriptPath = Join-Path $PSScriptRoot "rtk_filter.py"
python $scriptPath @CommandArgs
exit $LASTEXITCODE
