# Erica Agent

Python FastAPI service for the Erica shell.

## Prerequisites

- Python 3.11+
- Windows (for full skill execution; API still runs elsewhere for tests)

## Setup

```powershell
cd agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## Run

```powershell
uvicorn erica_agent.main:app --host 127.0.0.1 --port 8742 --reload
```

Default base URL: `http://127.0.0.1:8742`

## Modules (`erica_agent/`)

| Module | Role |
|--------|------|
| `main.py` | FastAPI app: `/intent`, `/plan`, `/execute`, `/execute/stream`, `/health`, voice stubs |
| `planner.py` | Rule-based `plan_from_text` / `intent_from_text` |
| `registry.py` | Skill manifests (YAML), validation, `registry.call` |
| `memory.py` | `short_term` + SQLite read-through cache (`long_term`) |
| `memory_backend.py` | `MemoryBackend` protocol; MemPalace local + HTTP stub |
| `mempalace_client.py` | In-process MemPalace (search, drawers, diary, identity file) |
| `persona.py` | Loads `config/persona.yaml`, active mode |
| `workflows.py` | YAML workflows under `config/workflows/` |
| `context.py` | Request context from persona + memory |
| `models.py`, `config.py`, `voice.py` | Shared models, settings, STT/TTS hooks |

When testing with `fastapi.testclient.TestClient`, use `with TestClient(app) as c:` so the ASGI **lifespan** runs (skills and workflows load). A bare `TestClient(app)` without the context manager may skip startup.

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `ERICA_SKILLS_PATH` | `../skills` | Directory of skill manifests |
| `ERICA_CONFIG_PATH` | `../config` | Persona + workflows |
| `ERICA_DATA_PATH` | `../data` | SQLite cache and runtime data |
| `ERICA_WINDOWS_CLI` | _(empty)_ | Optional path to `Erica.Windows.Cli.exe` for Win32 helpers |
| `ERICA_MEMPALACE_PALACE_PATH` | `%USERPROFILE%\.mempalace\palace` | MemPalace Chroma persist directory |
| `ERICA_MEMPALACE_IDENTITY_PATH` | `%USERPROFILE%\.mempalace\identity.txt` | Identity core (L0) for prompts |
| `ERICA_MEMORY_BACKEND` | `local` | `local` or `http` (HTTP not implemented yet) |
