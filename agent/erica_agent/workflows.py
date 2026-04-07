from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml
from apscheduler.schedulers.background import BackgroundScheduler

from erica_agent.config import settings
from erica_agent.models import Plan, PlanStep
from erica_agent.registry import registry

log = logging.getLogger(__name__)


def get_foreground_title_via_cli() -> str | None:
    """Return foreground window title via Erica.Windows.Cli, or None if unavailable."""
    cli = settings.windows_cli
    if not cli:
        return None
    try:
        r = subprocess.run(
            [cli, "foreground_title"],
            input="{}",
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode != 0:
            return None
        data = json.loads(r.stdout)
        t = (data.get("title") or "").strip()
        return t or None
    except Exception:
        log.debug("foreground_title CLI failed", exc_info=True)
        return None


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
        self._app_trigger_cooldown: dict[str, float] = {}

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
                missing = [s for s in wf.required_skills if registry.get(s) is None]
                if missing:
                    log.error(
                        "Skip workflow %s: required_skills not in registry: %s",
                        wid,
                        missing,
                    )
                    continue
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

    async def run_app_trigger_loop(self, interval_seconds: float = 15.0, cooldown_seconds: float = 90.0) -> None:
        """Poll foreground window title; match workflows with triggers.app substring."""
        while True:
            await asyncio.sleep(interval_seconds)
            title = get_foreground_title_via_cli()
            if not title:
                continue
            wf_id = check_foreground_app_trigger(title)
            if not wf_id:
                continue
            now = time.time()
            last = self._app_trigger_cooldown.get(wf_id, 0.0)
            if now - last < cooldown_seconds:
                continue
            self._app_trigger_cooldown[wf_id] = now
            self._emit(wf_id, {"trigger": "app"})

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
