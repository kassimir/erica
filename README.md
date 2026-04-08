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

See **[`docs/RUNBOOK.md`](docs/RUNBOOK.md)** for smoke tests, `ERICA_WINDOWS_CLI`, optional extras, **C# build verification**, and a **manual end-to-end checklist**.

1. **Agent:** `cd agent` → create venv → `pip install -e .` → `py -3 -m uvicorn erica_agent.main:app --host 127.0.0.1 --port 8742`
2. **Shell:** open `Erica.sln`, build **Erica.Shell**, run the executable (or `dotnet build` — see RUNBOOK).
3. **Git:** run [`scripts/Initialize-GitRepo.ps1`](scripts/Initialize-GitRepo.ps1) or `git init` in this folder, then `git add` / commit as usual once the repo exists.

## Extending Erica

**Skills:** Add a YAML manifest under [`skills/manifests/`](skills/manifests/) (see [`skills/schema/skill_manifest.schema.json`](skills/schema/skill_manifest.schema.json)). Point `entrypoint` at a Python function in [`skills/`](skills/) (e.g. `skills.my_module:my_function`). Declare `permissions` that match what [`erica_agent/main.py`](agent/erica_agent/main.py) grants per persona mode. Skills that call Win32 should run [`windows/Erica.Windows.Cli`](windows/Erica.Windows.Cli) via subprocess JSON; set **`ERICA_WINDOWS_CLI`** to that executable’s path (or use optional Python extras from the runbook).

**Workflows:** Add a file under [`config/workflows/`](config/workflows/) with `id`, `name`, `steps` (each step has `skill` and `arguments`), `required_skills` (names must exist in the registry), and optional `triggers` (`command`, `interval_seconds` / `cron`, `app` substring for foreground polling). Restart the agent to load changes.

**Shell note:** Global hotkeys (`RegisterHotKey` / `WM_HOTKEY`) are registered from **`MainWindow`** once the window handle exists. [`ShellAppHost`](shell/ShellAppHost.cs) wires configuration and HTTP clients; it does not create the hotkey service, by design.

## Verification (quick)

- **Python:** from `agent/`, `pip install -e .` and `python scripts\smoke_agent.py` (or `py -3`).
- **Lint:** `pip install ruff` and `ruff check erica_agent` plus `ruff check` on `../skills` from `agent/`.
- **.NET:** with the SDK on `PATH`, `dotnet build Erica.sln -c Release -p:Platform=x64` from this `erica/` folder (see RUNBOOK).

## Safety

Replacing Explorer as the shell is **high risk**. Read [`scripts/README.md`](scripts/README.md) before changing registry values.
