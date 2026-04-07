from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import yaml

from erica_agent.config import settings
from erica_agent.models import EricaMode

_SKILLS_SUGGEST_CONFIRM = frozenset({"network.wifi_toggle", "system.launch"})


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

    def response_verbosity(self) -> str:
        """minimal | normal — QuietMode prefers short summaries."""
        with self._lock:
            return "minimal" if self._mode == EricaMode.quiet else "normal"

    def should_confirm_destructive(self, skill_id: str) -> bool:
        """OperatorMode: flag high-impact skills per persona constraints."""
        with self._lock:
            if self._mode != EricaMode.operator:
                return False
        return skill_id in _SKILLS_SUGGEST_CONFIRM

    def shape_plan_message(self, text: str) -> str:
        if self.response_verbosity() != "minimal":
            return text
        if len(text) <= 280:
            return text
        return text[: 277] + "..."

    def format_execute_summary(self, ok: bool, results: list[dict[str, Any]] | None) -> str:
        """Persona-aware one-line or short summary for ExecuteResponse.message."""
        results = results or []
        if self.response_verbosity() == "minimal":
            return "Done." if ok else "Failed."
        lines: list[str] = []
        confirmed = []
        for r in results:
            sk = r.get("skill", "")
            if r.get("ok"):
                lines.append(f"- {sk}: ok")
            else:
                lines.append(f"- {sk}: {r.get('error', 'error')}")
            if sk and self.should_confirm_destructive(sk):
                confirmed.append(sk)
        head = "All steps completed." if ok else "Some steps failed."
        body = "\n".join(lines) if lines else "(no steps)"
        if confirmed:
            head += f" Note: confirm destructive-style actions when unsure: {', '.join(confirmed)}."
        return f"{head}\n{body}"


persona_state = PersonaState()
