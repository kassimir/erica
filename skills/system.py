from __future__ import annotations

import json
import os
import shutil
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


def launch(target: str) -> dict:
    data = _cli_json("launch", {"target": target})
    if data and data.get("ok"):
        return {**data, "target": target}
    data_cp = _cli_json("launch", {"target": target, "useCreateProcess": True})
    if data_cp and data_cp.get("ok"):
        return {**data_cp, "target": target}
    if os.name != "nt":
        subprocess.Popen([target])
        return {"ok": True, "method": "direct", "target": target}
    exe = shutil.which(target)
    if exe:
        subprocess.Popen([exe], cwd=str(Path(exe).parent))
        return {"ok": True, "path": exe, "method": "which", "target": target}
    subprocess.Popen(f'start "" {target}', shell=True)
    return {"ok": True, "method": "start", "target": target}
