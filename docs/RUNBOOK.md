# Erica runbook

## Prerequisites

- Python 3.11+ (agent)
- Windows 10+ with .NET 8 SDK (shell + `Erica.Windows.Cli`)
- Optional: `ERICA_WINDOWS_CLI` pointing at `Erica.Windows.Cli.exe` (build output under `windows/Erica.Windows.Cli/bin/...`)

## Agent (FastAPI)

```powershell
cd agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pip install -e ".[voice]"
python -m uvicorn erica_agent.main:app --host 127.0.0.1 --port 8742
```

Smoke (from `agent/`):

```powershell
python scripts\smoke_agent.py
```

Manual checks:

- `GET http://127.0.0.1:8742/health` → `{"ok":true,...}`
- `POST http://127.0.0.1:8742/plan` with JSON `{"text":"start writing session"}` returns a plan when workflows are loaded

## Shell (WinUI)

Open `Erica.sln`, build configuration **Release** | **x64**, run the shell project. Ensure the agent URL matches `AgentClient` (default `http://127.0.0.1:8742`).

## Windows CLI bridge

Build the solution so `Erica.Windows.Cli` exists, then:

```powershell
$env:ERICA_WINDOWS_CLI = "C:\path\to\Erica.Windows.Cli.exe"
```

Retry skills that call `audio_volume`, `wifi`, `window_*`, `foreground_title`, etc.

## Optional dependencies

- `pip install -e ".[windows]"` — `pycaw`/`comtypes` for volume without CLI
- `pip install -e ".[voice]"` — SpeechRecognition for `/voice/stt` (WAV upload)

## Build C# projects (verification)

From the `erica/` directory (same folder as `Erica.sln`), with **.NET 8 SDK** installed and on `PATH`:

```powershell
dotnet build .\Erica.sln -c Release -p:Platform=x64
```

This builds **Erica.Shell**, **Erica.Windows**, and **Erica.Windows.Cli**. Fix any compile errors before shipping.

## Manual end-to-end checklist

1. Start the agent on `127.0.0.1:8742` (see above). Confirm `GET /health`.
2. Set `ERICA_WINDOWS_CLI` to your built `Erica.Windows.Cli.exe` path (Release output under `windows\Erica.Windows.Cli\bin\x64\Release\net8.0-windows10.0.19041.0\` or similar).
3. Run **Erica.Shell**. Status bar should show **Agent: online** and the active persona **Mode** from `/health`.
4. **Command palette** (`Ctrl+Space`): submit text; expect a JSON response from `/execute` echoed in the Quake output area.
5. **Quake console** (`Ctrl+``): submit text; expect streaming NDJSON chunks from `/execute/stream`.
6. Optional: invoke a skill that uses the CLI (e.g. workflow “start writing session” or a plan that hits `audio.volume`) and confirm structured JSON in skill results.

## Shell architecture note

**Global hotkeys** are registered in [`MainWindow`](../shell/MainWindow.xaml.cs) after the window exists (`GlobalHotkeyService` + HWND). [`ShellAppHost`](../shell/ShellAppHost.cs) loads `appsettings.json`, `ERICA_AGENT_URL`, and `--agent-url`, and constructs `AgentClient` / routers; it does not register hotkeys itself.
