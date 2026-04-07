# Scripts

## Safety: replacing the Windows shell

Changing the **Shell** value under `HKCU\Software\Microsoft\Windows NT\CurrentVersion\Winlogon` tells Windows which process starts instead of `explorer.exe` at logon. If that process crashes or never starts, you may get **no taskbar or desktop**.

**Recommended precautions**

- Test in a **virtual machine** or a **secondary Windows account** first.
- Export a **registry backup** before changes (`Set-EricaShell.ps1 -BackupPath`).
- Keep **recovery paths** ready: Task Manager (`Ctrl+Shift+Esc`) → **Run new task** → `explorer.exe`, or run `Restore-ExplorerShell.ps1` from another session.
- Do not deploy this as your only recovery path until you have verified cold-boot behavior.

## Scripts

| Script | Purpose |
|--------|---------|
| `Initialize-GitRepo.ps1` | Runs `git init` in the Erica repo root (requires Git on PATH). |
| `Set-EricaShell.ps1` | Sets `Shell` to your built `Erica.Shell.exe` path. |
| `Restore-ExplorerShell.ps1` | Sets `Shell` back to `explorer.exe`. |
| `Finalize-EricaDeployment.ps1` | Prints smoke-test steps and optional shell registration. |

## Git

If `git` is not available in this environment, run `git init` manually from the `erica` folder after installing [Git for Windows](https://git-scm.com/download/win).
