"""Quick smoke test for the FastAPI agent (run from the agent/ directory)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from erica_agent.main import app


def main() -> None:
    client = TestClient(app)
    h = client.get("/health")
    assert h.status_code == 200, h.text
    assert h.json().get("ok") is True
    p = client.post("/plan", json={"text": "test"})
    assert p.status_code == 200, p.text
    print("smoke_agent: ok")


if __name__ == "__main__":
    main()
