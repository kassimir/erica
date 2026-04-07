# Erica

AI-mediated Windows shell: WinUI 3 **shell**, Python **FastAPI agent**, optional **C# Win32** bridge, **YAML skills**, **memory**, **persona**, and **workflows**.

## Layout

| Path | Role |
|------|------|
| [`ERICA_ARCHITECTURE.md`](ERICA_ARCHITECTURE.md) | Developer architecture spec |
| [`agent/`](agent/) | FastAPI service (`uvicorn erica_agent.main:app`) |
| [`shell/`](shell/) | WinUI 3 desktop shell |
| [`windows/`](windows/) | C# P/Invoke + CLI |
| [`skills/`](skills/) | Skill manifests + Python implementations |
| [`config/`](config/) | `persona.yaml`, `workflows/*.yaml` |
| [`memory/`](memory/) | Notes; SQLite lives in `data/` |
| [`scripts/`](scripts/) | Registry helpers, deployment notes |
| [`Erica.sln`](Erica.sln) | Visual Studio solution (shell + windows) |

## Quick start

See **[`docs/RUNBOOK.md`](docs/RUNBOOK.md)** for smoke tests, `ERICA_WINDOWS_CLI`, and optional extras.

1. **Agent:** `cd agent` → create venv → `pip install -e .` → `py -3 -m uvicorn erica_agent.main:app --host 127.0.0.1 --port 8742`
2. **Shell:** open `Erica.sln`, build **Erica.Shell**, run the executable.
3. **Git:** run [`scripts/Initialize-GitRepo.ps1`](scripts/Initialize-GitRepo.ps1) or `git init` in this folder.

## Safety

Replacing Explorer as the shell is **high risk**. Read [`scripts/README.md`](scripts/README.md) before changing registry values.
