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
