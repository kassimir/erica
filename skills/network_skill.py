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
    if data and data.get("ok"):
        return {**data, "enable": enable}

    arg = "enable" if enable else "disable"
    try:
        r = subprocess.run(
            ["netsh", "interface", "set", "interface", "Wi-Fi", f"admin={arg}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        ok = r.returncode == 0
        err = (r.stderr or "").strip()
        out = (r.stdout or "").strip()
        return {
            "ok": ok,
            "enable": enable,
            "method": "netsh_interface",
            "exitCode": r.returncode,
            "stderr": err[:800],
            "stdout": out[:800],
        }
    except Exception as e:
        return {"ok": False, "enable": enable, "error": str(e), "method": "netsh_interface"}
