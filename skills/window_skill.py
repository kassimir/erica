from __future__ import annotations

import json
import subprocess
from pathlib import Path

from erica_agent.config import settings


def _cli_json(cmd: str, payload: dict) -> dict:
    exe = settings.windows_cli
    if not exe or not Path(exe).is_file():
        return {}
    try:
        r = subprocess.run(
            [exe, cmd],
            input=json.dumps(payload).encode(),
            capture_output=True,
            timeout=30,
            check=False,
        )
        if r.stdout:
            return json.loads(r.stdout.decode())
    except Exception:
        pass
    return {}


def minimize_foreground() -> dict:
    data = _cli_json("window_minimize", {})
    if data:
        return data
    return {"ok": False, "message": "Set ERICA_WINDOWS_CLI to Erica.Windows.Cli"}


def move_resize(title_substr: str, x: int, y: int, width: int, height: int) -> dict:
    data = _cli_json(
        "window_move",
        {"title": title_substr, "x": x, "y": y, "width": width, "height": height},
    )
    if data:
        return data
    return {"ok": False, "message": "Set ERICA_WINDOWS_CLI to Erica.Windows.Cli"}
