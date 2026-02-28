param(
    [Parameter(Mandatory = $true)]
    [string]$PlanPath,

    [ValidateSet("auto", "hybrid", "manual")]
    [string]$Mode = "hybrid",

    [int]$MaxRounds = 999,

    [string]$Model = "gpt-5.3-codex",

    [switch]$NoCap,

    [switch]$Resume
)

$ErrorActionPreference = "Stop"

$toolRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$scriptPath = Join-Path $toolRoot "scripts\plan_loop.py"

if (-not (Test-Path $scriptPath)) {
    Write-Error "Python orchestrator not found: $scriptPath"
    exit 1
}

if ([System.IO.Path]::IsPathRooted($PlanPath)) {
    $resolvedPlanPath = $PlanPath
} else {
    $resolvedPlanPath = Join-Path $PWD $PlanPath
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $pythonCmd) {
    Write-Error "Python runtime not found. Install Python or ensure it is on PATH."
    exit 1
}

$argsList = @(
    $scriptPath
    "--plan"
    $resolvedPlanPath
    "--mode"
    $Mode
    "--max-rounds"
    "$MaxRounds"
)

if ("" -ne $Model) {
    $argsList += "--model"
    $argsList += $Model
}

if ($NoCap) {
    $argsList += "--no-cap"
}
if ($Resume) {
    $argsList += "--resume"
}

Write-Host "[runner] starting plan loop..."
Write-Host "[runner] toolRoot=$toolRoot"
Write-Host "[runner] planPath=$resolvedPlanPath"
Write-Host "[runner] mode=$Mode, maxRounds=$MaxRounds, model=$Model, noCap=$($NoCap.IsPresent), resume=$($Resume.IsPresent)"

& $pythonCmd.Source @argsList
$exitCode = $LASTEXITCODE
Write-Host "[runner] plan loop exited with code $exitCode"
exit $exitCode
