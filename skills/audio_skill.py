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


def _pycaw_set_volume(percent: int) -> dict | None:
    try:
        from ctypes import POINTER, cast

        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    except ImportError:
        return None
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(percent / 100.0, None)
        return {"ok": True, "percent": percent, "method": "pycaw"}
    except Exception as e:
        return {"ok": False, "error": str(e), "method": "pycaw"}


def set_volume(percent: int) -> dict:
    pct = max(0, min(100, int(percent)))
    data = _cli_json("audio_volume", {"percent": pct})
    if data and data.get("ok") is not False:
        return {**data, "percent": pct}
    fallback = _pycaw_set_volume(pct)
    if fallback:
        return fallback
    return {
        "ok": False,
        "percent": pct,
        "message": "Set ERICA_WINDOWS_CLI or install optional deps: pip install erica-agent[windows]",
    }


def switch_audio_device(device_name: str) -> dict:
    data = _cli_json("audio_device", {"name": device_name})
    if data:
        return data
    return {
        "ok": False,
        "message": "Set ERICA_WINDOWS_CLI to Erica.Windows.Cli for device enumeration",
        "device_name": device_name,
    }
