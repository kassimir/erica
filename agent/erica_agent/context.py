from __future__ import annotations

from erica_agent.memory import long_term, short_term
from erica_agent.persona import persona_state


def build_request_context(query_embedding: list[float] | None = None) -> str:
    st = short_term.summary()
    lt_rows = long_term.retrieve_relevant(query_embedding, limit=5)
    lt_lines = ["Long-term snippets:"]
    for r in lt_rows:
        lt_lines.append(f"- ({r.get('label')}) {r.get('payload')}")
    persona = persona_state.context_block()
    return "\n".join([persona, st, "\n".join(lt_lines)])
