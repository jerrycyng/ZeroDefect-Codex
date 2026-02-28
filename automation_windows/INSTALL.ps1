param(
    [string]$InstallDir = "$env:USERPROFILE\CodexPlanLoop"
)

$ErrorActionPreference = "Stop"

Write-Host "Installing Codex Plan Loop globally to: $InstallDir"

# 1. Create the installation directory
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
}

# 2. Copy the tool files (excluding git and artifacts)
$sourceDir = $PSScriptRoot
Copy-Item -Path "$sourceDir\*" -Destination $InstallDir -Recurse -Force -Exclude ".git", "plans", "INSTALL.ps1"

# Ensure the plans directory exists but is empty
New-Item -ItemType Directory -Path (Join-Path $InstallDir "plans") -ErrorAction SilentlyContinue | Out-Null

# 3. Create the global wrapper script (plan-loop.bat)
$batPath = Join-Path $InstallDir "plan-loop.bat"
$pythonScript = Join-Path $InstallDir "scripts\plan_loop.py"

$batContent = @"
@echo off
setlocal
set PLAN_PATH=%1
shift
python "$pythonScript" --plan "%PLAN_PATH%" %1 %2 %3 %4 %5 %6 %7 %8 %9
endlocal
"@

Set-Content -Path $batPath -Value $batContent

# 4. Add to User PATH if not already there
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notmatch [regex]::Escape($InstallDir)) {
    Write-Host "Adding $InstallDir to User PATH..."
    $newPath = "$userPath;$InstallDir"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    # Refresh the current session's path so they can use it immediately in this terminal
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "Successfully added to PATH and refreshed current session."
} else {
    Write-Host "Directory is already in your PATH."
}

Write-Host ""
Write-Host "Installation Complete! 🎉"
Write-Host "You can now run 'plan-loop <plan_file.md>' from any folder."
