"""Erica MemPalace layout: wings, rooms, halls, skill routing, L0/L1 seeds."""

from __future__ import annotations

from typing import Any

HALL_FACTS = "hall_facts"
HALL_EVENTS = "hall_events"
HALL_PREFERENCES = "hall_preferences"
HALL_ERRORS = "hall_errors"

ERICA_PALACE: dict[str, Any] = {
    "wings": {
        "wing_user": {
            "type": "person",
            "rooms": ["preferences", "habits", "identity", "corrections", "personal-facts"],
        },
        "wing_tasks": {
            "type": "project",
            "rooms": [
                "notepad",
                "excel",
                "word",
                "browser",
                "file-system",
                "email",
                "system-settings",
                "media",
                "code",
            ],
        },
        "wing_computer": {
            "type": "project",
            "rooms": [
                "installed-apps",
                "file-locations",
                "network",
                "hardware",
                "scheduled-tasks",
            ],
        },
    },
    "halls": [HALL_FACTS, HALL_EVENTS, HALL_PREFERENCES, HALL_ERRORS],
}

_SKILL_TO_ROOM: dict[str, tuple[str, str]] = {
    "persona.set_mode": ("wing_user", "preferences"),
    "system.launch": ("wing_tasks", "file-system"),
    "window.move_resize": ("wing_tasks", "system-settings"),
    "window.minimize_foreground": ("wing_tasks", "system-settings"),
    "audio.volume": ("wing_tasks", "media"),
    "audio.device": ("wing_tasks", "media"),
    "network.wifi_toggle": ("wing_computer", "network"),
}


def infer_room(skill_id: str) -> tuple[str, str]:
    """Return (wing, room) for a skill. Unknown skills default to task execution history."""
    if skill_id in _SKILL_TO_ROOM:
        return _SKILL_TO_ROOM[skill_id]
    prefix = skill_id.split(".", 1)[0] if "." in skill_id else skill_id
    if prefix == "network":
        return ("wing_computer", "network")
    if prefix in ("window", "audio"):
        return ("wing_tasks", "system-settings")
    if prefix == "system":
        return ("wing_tasks", "file-system")
    if prefix == "persona":
        return ("wing_user", "preferences")
    return ("wing_tasks", "hall_events")


ERICA_IDENTITY = """## Erica — L0 Identity

You are Erica, the user's AI-mediated Windows shell. You replace scattered assistants with one
Jarvis-like presence: voice and text, direct control of applications, files, spreadsheets, browser,
and system settings. You remember what happened (MemPalace), prefer action over chatter, and only
stop to confirm when an operation is destructive or irreversible. You are precise, calm, and loyal to
the user's intent. You run locally alongside the user; you do not exfiltrate secrets or credentials.
"""

ERICA_FACTS: list[tuple[str, str, str]] = [
    ("Erica", "runs_on", "Windows"),
    ("Erica", "uses_memory", "MemPalace"),
]

_PREFERENCE_MARKERS = (
    "i prefer",
    "i always",
    "i like",
    "i never",
    "i want you to",
    "always use",
    "never use",
    "prefer ",
)


def looks_like_preference_statement(text: str) -> bool:
    t = text.strip().lower()
    return any(m in t for m in _PREFERENCE_MARKERS)
