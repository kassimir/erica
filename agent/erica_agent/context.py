from __future__ import annotations

import json

from erica_agent.memory import short_term
from erica_agent.memory_backend import get_memory_backend
from erica_agent.persona import persona_state


def _format_lt_row(r: dict) -> str:
    payload = r.get("payload")
    if isinstance(payload, dict):
        text = payload.get("text")
        if text is not None:
            body = str(text)
        else:
            body = json.dumps(payload, ensure_ascii=False)[:500]
    else:
        body = str(payload)
    sc = r.get("score")
    suffix = f" score={sc:.3f}" if isinstance(sc, (int, float)) else ""
    label = r.get("label", "")
    return f"- ({label}){suffix} {body}"


def build_request_context(query_text: str | None = None) -> str:
    """Build context: MemPalace identity + persona + short-term + long-term (search or cache)."""
    backend = get_memory_backend()
    ident = backend.identity_core().strip()
    id_block = f"Identity core (MemPalace L0):\n{ident}\n\n" if ident else ""

    if query_text and query_text.strip():
        lt_rows = backend.search(query_text.strip(), limit=5)
    else:
        lt_rows = backend.search("", limit=5)

    st = short_term.summary()
    lt_lines = ["Long-term snippets:"]
    for r in lt_rows:
        lt_lines.append(_format_lt_row(r))
    persona = persona_state.context_block()
    return "\n".join([id_block, persona, st, "\n".join(lt_lines)])
