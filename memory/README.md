# memory

Runtime memory for Erica is implemented in the **agent** package:

- **Short-term:** [`erica_agent/memory_short.py`](../agent/erica_agent/memory_short.py) — recent commands, tasks, app hints.
- **Long-term:** [`erica_agent/memory_long.py`](../agent/erica_agent/memory_long.py) — SQLite file under `../data/memory.sqlite3` with `metadata` and `embeddings` tables.

Context injection for each HTTP request is built in [`erica_agent/context.py`](../agent/erica_agent/context.py).

This folder is reserved for additional assets or documentation if you split memory into a standalone package later.
