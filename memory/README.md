# memory

Runtime memory for Erica is implemented in the **agent** package:

- **Short-term + long-term:** [`erica_agent/memory.py`](../agent/erica_agent/memory.py) — `ShortTermMemory` and `LongTermMemory`; SQLite under `../data/memory.sqlite3` with `metadata` and `embeddings` tables.

Context injection for each HTTP request is built in [`erica_agent/context.py`](../agent/erica_agent/context.py).

This folder is reserved for additional assets or documentation if you split memory into a standalone package later.
