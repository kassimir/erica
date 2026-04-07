from __future__ import annotations

import re
import uuid
from typing import Any

from erica_agent.models import Plan, PlanStep


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def plan_from_text(text: str) -> Plan | None:
    """Rule-based planner: maps phrases to skill invocations."""
    t = _norm(text)

    if "writer mode" in t or t.endswith("writer mode"):
        return Plan(
            id=str(uuid.uuid4()),
            steps=[PlanStep(skill_id="persona.set_mode", arguments={"mode": "WriterMode"})],
            rationale="User requested writer mode.",
        )
    if "operator mode" in t or t.endswith("operator mode"):
        return Plan(
            id=str(uuid.uuid4()),
            steps=[PlanStep(skill_id="persona.set_mode", arguments={"mode": "OperatorMode"})],
            rationale="User requested operator mode.",
        )
    if "go quiet" in t or "quiet mode" in t:
        return Plan(
            id=str(uuid.uuid4()),
            steps=[PlanStep(skill_id="persona.set_mode", arguments={"mode": "QuietMode"})],
            rationale="User requested quiet mode.",
        )

    if t.startswith("launch ") or " open " in f" {t} ":
        # e.g. "launch notepad"
        m = re.search(r"(?:launch|open)\s+(.+)$", t)
        target = (m.group(1).strip() if m else "").strip(" '\"")
        if target:
            return Plan(
                id=str(uuid.uuid4()),
                steps=[PlanStep(skill_id="system.launch", arguments={"target": target})],
                rationale="Launch/open application.",
            )

    if "minimize" in t and "window" in t:
        return Plan(
            id=str(uuid.uuid4()),
            steps=[PlanStep(skill_id="window.minimize_foreground", arguments={})],
            rationale="Minimize foreground window.",
        )

    if "wifi" in t and ("off" in t or "disable" in t):
        return Plan(
            id=str(uuid.uuid4()),
            steps=[PlanStep(skill_id="network.wifi_toggle", arguments={"enable": False})],
            rationale="Toggle Wi-Fi off.",
        )
    if "wifi" in t and ("on" in t or "enable" in t):
        return Plan(
            id=str(uuid.uuid4()),
            steps=[PlanStep(skill_id="network.wifi_toggle", arguments={"enable": True})],
            rationale="Toggle Wi-Fi on.",
        )

    return None


def intent_from_text(text: str) -> dict[str, Any]:
    """Lightweight intent labeling for /intent."""
    t = _norm(text)
    intent = "unknown"
    if any(x in t for x in ("writer mode", "operator mode", "quiet mode", "go quiet")):
        intent = "mode_switch"
    elif "launch" in t or "open " in t:
        intent = "launch_app"
    elif "wifi" in t:
        intent = "network"
    elif "volume" in t:
        intent = "audio"
    return {"intent": intent, "normalized": t}
