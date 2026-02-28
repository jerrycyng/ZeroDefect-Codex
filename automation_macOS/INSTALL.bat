@echo off
REM Installation wrapper for Codex Plan Loop
REM This allows users to double-click this file or run it without worrying about ExecutionPolicy.

SET "SCRIPT_DIR=%~dp0"
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%INSTALL.ps1"

if %ERRORLEVEL% equ 0 (
    echo.
    echo ------------------------------------------------------------
    echo Setup complete! 
    echo Please RESTART your terminal/IDE to use the 'plan-loop' command.
    echo ------------------------------------------------------------
    pause
) else (
    echo.
    echo ------------------------------------------------------------
    echo Installation failed. 
    echo ------------------------------------------------------------
    pause
)
