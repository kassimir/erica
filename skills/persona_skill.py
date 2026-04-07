from __future__ import annotations

from erica_agent.memory import short_term
from erica_agent.models import EricaMode
from erica_agent.persona import persona_state


def set_mode(mode: str) -> dict:
    em = EricaMode(mode)
    persona_state.set_mode(em)
    short_term.set_last_mode(em)
    return {"ok": True, "mode": em.value}
