<#
.SYNOPSIS
  Sets the Windows user shell registry value to the Erica shell executable.

.DESCRIPTION
  **HIGH RISK.** Replacing explorer.exe can prevent the desktop from loading if Erica fails.
  Always test in a VM or secondary Windows account first. Export a registry backup before use.

  Default shell key (per-user):
    HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon
    Value: Shell

.PARAMETER ShellPath
  Full path to Erica.Shell.exe (built from /shell).

.PARAMETER BackupPath
  Optional path to export the Winlogon key before modification (.reg file).
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [Parameter(Mandatory = $true)]
  [string] $ShellPath,

  [string] $BackupPath = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $ShellPath)) {
  Write-Error "Shell executable not found: $ShellPath"
}

$key = "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon"
if (-not (Test-Path $key)) {
  New-Item -Path $key -Force | Out-Null
}

if ($BackupPath) {
  reg export "HKCU\Software\Microsoft\Windows NT\CurrentVersion\Winlogon" $BackupPath /y | Out-Null
  Write-Host "Backed up Winlogon key to $BackupPath"
}

$current = (Get-ItemProperty -Path $key -Name Shell -ErrorAction SilentlyContinue).Shell
Write-Host "Current Shell value: $current"

if ($PSCmdlet.ShouldProcess($key, "Set Shell to $ShellPath")) {
  Set-ItemProperty -Path $key -Name Shell -Value $ShellPath
  Write-Host "Shell set to: $ShellPath"
  Write-Warning "Sign out or reboot for changes to take effect. Keep Task Manager (Ctrl+Shift+Esc) available to run explorer.exe if needed."
}
