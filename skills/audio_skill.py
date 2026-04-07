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


def set_volume(percent: int) -> dict:
    data = _cli_json("audio_volume", {"percent": max(0, min(100, int(percent)))})
    if data:
        return data
    return {"ok": False, "message": "Set ERICA_WINDOWS_CLI to Erica.Windows.Cli for volume control"}


def switch_audio_device(device_name: str) -> dict:
    data = _cli_json("audio_device", {"name": device_name})
    if data:
        return data
    return {"ok": False, "message": "Requires Erica.Windows.Cli audio_device"}
