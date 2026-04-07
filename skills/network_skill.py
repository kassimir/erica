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
            timeout=60,
            check=False,
        )
        if r.stdout:
            return json.loads(r.stdout.decode())
    except Exception:
        pass
    return {}


def wifi_toggle(enable: bool) -> dict:
    data = _cli_json("wifi", {"enable": enable})
    if data:
        return data
    arg = "enable" if enable else "disable"
    try:
        subprocess.run(
            ["netsh", "interface", "set", "interface", "Wi-Fi", "admin=" + arg],
            capture_output=True,
            timeout=30,
            check=False,
        )
        return {"ok": True, "enable": enable, "method": "netsh"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
