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

## MemPalace (long-term memory)

Erica uses **MemPalace** (`mempalace>=3`) as the primary palace: drawers, agent diary, `MemoryStack` wake-up (L0+L1), and a dedicated knowledge graph DB. SQLite under `data/` remains a read-through cache. Palace layout and skill routing are defined in `erica_agent/palace_config.py`; the facade is `erica_agent/erica_memory.py`.

**One-time palace init** (creates Chroma persist dir):

```powershell
mempalace init $env:USERPROFILE\.mempalace\erica_palace
```

On first agent startup, `EricaMemory.initialize()` seeds `identity.txt` and `wing_config.json` from [`memory/identity.txt`](../memory/identity.txt) and [`memory/wing_config_seed.json`](../memory/wing_config_seed.json) when missing.

| Variable | Default | Description |
|----------|---------|--------------|
| `ERICA_MEMPALACE_PALACE_PATH` | `%USERPROFILE%\.mempalace\erica_palace` | ChromaDB persist path |
| `ERICA_MEMPALACE_IDENTITY_PATH` | `<palace>\identity.txt` | L0 identity file for `MemoryStack` |
| `ERICA_MEMORY_BACKEND` | `local` | `local` = Erica palace + SQLite cache; `http` = SQLite-only placeholder |

**Agent endpoints**

- `GET /memory/wake-up` — JSON `{ "wake_up": "<L0+L1 text>" }` for prompts; the WinUI shell calls this at startup and passes the text as the `context` field on `POST /plan`.
- `POST /memory/search` — `{ "query", "wing"?, "room"? }` → `{ "results": [strings] }`.
- `POST /memory/fact` — `{ "subject", "predicate", "object", "valid_from"? }` → KG triple in `~/.mempalace/erica_knowledge_graph.sqlite3`.

**Inspect the palace** (with MemPalace CLI on PATH):

```powershell
mempalace status --palace $env:USERPROFILE\.mempalace\erica_palace
```

**MCP server for Cursor** — activate the agent venv, then:

```powershell
.\scripts\Start-MemPalaceMCP.ps1
```

Or register: `claude mcp add mempalace -- pwsh -File C:\path\to\erica\scripts\Start-MemPalaceMCP.ps1`

## Optional dependencies

- Core agent already depends on `mempalace`; optional `[mempalace]` extra is redundant but harmless
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
