<#
.SYNOPSIS
  Initializes a git repository in the Erica project root (parent of /scripts).
#>
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Error "git is not installed or not on PATH. Install Git for Windows, then re-run."
}
if (Test-Path (Join-Path $root ".git")) {
  Write-Host "Git repository already exists at $root"
  exit 0
}
git init
Write-Host "Initialized empty Git repository in $root"
