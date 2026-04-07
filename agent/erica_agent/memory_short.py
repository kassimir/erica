from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any

from erica_agent.models import EricaMode


class ShortTermMemory:
    def __init__(self, max_commands: int = 50) -> None:
        self._lock = threading.Lock()
        self._commands: deque[dict[str, Any]] = deque(maxlen=max_commands)
        self._tasks: list[dict[str, Any]] = []
        self._open_apps: list[str] = []
        self._last_mode: EricaMode | None = None

    def add_command(self, text: str, meta: dict[str, Any] | None = None) -> None:
        with self._lock:
            self._commands.append(
                {
                    "text": text,
                    "ts": time.time(),
                    "meta": meta or {},
                }
            )

    def set_active_tasks(self, tasks: list[dict[str, Any]]) -> None:
        with self._lock:
            self._tasks = list(tasks)

    def set_open_apps(self, apps: list[str]) -> None:
        with self._lock:
            self._open_apps = list(apps)

    def set_last_mode(self, mode: EricaMode) -> None:
        with self._lock:
            self._last_mode = mode

    def summary(self) -> str:
        with self._lock:
            recent = list(self._commands)[-10:]
            lines = ["Recent commands:"]
            for c in recent:
                lines.append(f"- {c.get('text', '')}")
            lines.append("Active tasks:")
            for t in self._tasks:
                lines.append(f"- {t}")
            lines.append("Open applications (hint):")
            for a in self._open_apps[:20]:
                lines.append(f"- {a}")
            if self._last_mode:
                lines.append(f"Last mode hint: {self._last_mode.value}")
            return "\n".join(lines)


short_term = ShortTermMemory()
