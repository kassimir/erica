from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml
from apscheduler.schedulers.background import BackgroundScheduler

from erica_agent.config import settings
from erica_agent.models import Plan, PlanStep
log = logging.getLogger(__name__)


@dataclass
class WorkflowDef:
    id: str
    name: str
    steps: list[dict[str, Any]]
    triggers: dict[str, Any] = field(default_factory=dict)
    required_skills: list[str] = field(default_factory=list)


class WorkflowEngine:
    def __init__(self) -> None:
        self._workflows: dict[str, WorkflowDef] = {}
        self._scheduler = BackgroundScheduler()
        self._scheduler.start()
        self._listeners: list[Callable[[str, dict[str, Any]], None]] = []

    def load_directory(self, base: Path | None = None) -> int:
        root = (base or settings.config_path) / "workflows"
        if not root.is_dir():
            root.mkdir(parents=True, exist_ok=True)
            return 0
        n = 0
        for path in sorted(root.glob("*.yaml")):
            try:
                raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                wid = raw.get("id") or path.stem
                wf = WorkflowDef(
                    id=wid,
                    name=raw.get("name", wid),
                    steps=list(raw.get("steps", [])),
                    triggers=dict(raw.get("triggers", {})),
                    required_skills=list(raw.get("required_skills", [])),
                )
                self._workflows[wf.id] = wf
                self._register_triggers(wf)
                n += 1
            except Exception as e:
                log.error("Failed workflow %s: %s", path, e)
        return n

    def _register_triggers(self, wf: WorkflowDef) -> None:
        tr = wf.triggers or {}
        if "interval_seconds" in tr:
            sec = int(tr["interval_seconds"])
            self._scheduler.add_job(
                lambda w=wf.id: self._emit(w, {"trigger": "time"}),
                "interval",
                seconds=sec,
                id=f"wf-time-{wf.id}",
                replace_existing=True,
            )
        if "cron" in tr and isinstance(tr["cron"], dict):
            self._scheduler.add_job(
                lambda w=wf.id: self._emit(w, {"trigger": "time"}),
                "cron",
                **tr["cron"],
                id=f"wf-cron-{wf.id}",
                replace_existing=True,
            )

    def _emit(self, workflow_id: str, payload: dict[str, Any]) -> None:
        for fn in self._listeners:
            try:
                fn(workflow_id, payload)
            except Exception as e:
                log.exception("Workflow listener error: %s", e)

    def on_trigger(self, fn: Callable[[str, dict[str, Any]], None]) -> None:
        self._listeners.append(fn)

    def match_command(self, text: str) -> str | None:
        t = text.strip().lower()
        for wf in self._workflows.values():
            cmd = (wf.triggers or {}).get("command")
            if cmd and t == str(cmd).strip().lower():
                return wf.id
        return None

    def to_plan(self, workflow_id: str) -> Plan | None:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return None
        steps: list[PlanStep] = []
        for s in wf.steps:
            steps.append(
                PlanStep(
                    skill_id=s["skill"],
                    arguments=dict(s.get("arguments", {})),
                )
            )
        return Plan(id=str(uuid.uuid4()), steps=steps, rationale=f"Workflow {wf.name}")


engine = WorkflowEngine()


def check_foreground_app_trigger(foreground: str) -> str | None:
    for wf in engine._workflows.values():
        app = (wf.triggers or {}).get("app")
        if app and foreground.lower().find(str(app).lower()) >= 0:
            return wf.id
    return None
