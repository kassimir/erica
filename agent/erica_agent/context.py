from __future__ import annotations

from erica_agent.embeddings import embed_text
from erica_agent.memory import long_term, short_term
from erica_agent.persona import persona_state


def build_request_context(query_text: str | None = None) -> str:
    """Build context block: persona + short-term + long-term (embedding retrieval when query_text given)."""
    q_emb = embed_text(query_text) if query_text else None
    st = short_term.summary()
    lt_rows = long_term.retrieve_relevant(q_emb, limit=5)
    lt_lines = ["Long-term snippets:"]
    for r in lt_rows:
        sc = r.get("score")
        suffix = f" score={sc:.3f}" if isinstance(sc, (int, float)) else ""
        lt_lines.append(f"- ({r.get('label')}){suffix} {r.get('payload')}")
    persona = persona_state.context_block()
    return "\n".join([persona, st, "\n".join(lt_lines)])
