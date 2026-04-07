<#
.SYNOPSIS
  Restores the default Windows shell to explorer.exe.

.DESCRIPTION
  Sets HKCU Winlogon Shell back to explorer.exe. Use if Erica shell fails to start or for recovery.
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param()

$ErrorActionPreference = "Stop"
$key = "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon"
if (-not (Test-Path $key)) {
  New-Item -Path $key -Force | Out-Null
}

if ($PSCmdlet.ShouldProcess($key, "Set Shell to explorer.exe")) {
  Set-ItemProperty -Path $key -Name Shell -Value "explorer.exe"
  Write-Host "Shell restored to explorer.exe"
}
