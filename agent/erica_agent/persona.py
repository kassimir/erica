from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import yaml

from erica_agent.config import settings
from erica_agent.models import EricaMode


class PersonaState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[str, Any] = {}
        self._mode: EricaMode = EricaMode.operator

    def load(self, path: Path | None = None) -> None:
        p = path or (settings.config_path / "persona.yaml")
        if not p.is_file():
            self._data = {
                "name": "Erica",
                "tone": "warm, sharp, noir-adjacent",
                "modes": ["WriterMode", "OperatorMode", "QuietMode"],
            }
            return
        with p.open(encoding="utf-8") as f:
            self._data = yaml.safe_load(f) or {}

    @property
    def mode(self) -> EricaMode:
        with self._lock:
            return self._mode

    def set_mode(self, mode: EricaMode) -> None:
        with self._lock:
            self._mode = mode

    def context_block(self) -> str:
        with self._lock:
            name = self._data.get("name", "Erica")
            tone = self._data.get("tone", "")
            constraints = self._data.get("constraints", [])
            examples = self._data.get("example_responses", [])
            cstr = "\n".join(f"- {c}" for c in constraints) if constraints else ""
            ex = "\n".join(f"- {e}" for e in examples) if examples else ""
            return (
                f"Persona: {name}\n"
                f"Tone: {tone}\n"
                f"Active mode: {self._mode.value}\n"
                f"Constraints:\n{cstr}\n"
                f"Example response style:\n{ex}\n"
            )


persona_state = PersonaState()
