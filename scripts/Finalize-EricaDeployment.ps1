<#
.SYNOPSIS
  Deployment checklist helper for Phase 8 — does not replace Explorer by itself.

.DESCRIPTION
  Verifies paths, prints smoke-test steps, and optionally invokes Set-EricaShell.ps1.
  Run elevated only when required by your environment; registry here is per-user (HKCU).
#>
param(
  [string] $ShellExe = "",
  [switch] $SetShell
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Write-Host "Erica root: $root"

if (-not $ShellExe) {
  $ShellExe = Join-Path $root "shell\bin\x64\Release\net8.0-windows10.0.19041.0\win-x64\Erica.Shell.exe"
}

Write-Host "Expected shell path (adjust after build): $ShellExe"
Write-Host @"

Smoke tests:
  1) Start agent:  py -3 -m uvicorn erica_agent.main:app --host 127.0.0.1 --port 8742
  2) Run Erica.Shell.exe — full-screen UI should appear; Ctrl+Space opens palette.
  3) POST http://127.0.0.1:8742/health — expect { ""ok"": true }.

Recovery:
  - Task Manager -> Run -> explorer.exe
  - Or: .\scripts\Restore-ExplorerShell.ps1

"@

if ($SetShell) {
  if (-not (Test-Path -LiteralPath $ShellExe)) {
    Write-Warning "Shell exe not found. Build the solution first."
    exit 1
  }
  & "$PSScriptRoot\Set-EricaShell.ps1" -ShellPath $ShellExe -Confirm
}
