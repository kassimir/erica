"""LLM-backed planning: natural language to validated Plan (skill steps)."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import httpx

from erica_agent.config import settings
from erica_agent.models import Plan, PlanStep
from erica_agent.registry import SkillRegistry

log = logging.getLogger(__name__)

_PLANNER_SYSTEM = """You are EriCA's planner. You output ONLY valid JSON (no markdown).

Schema:
{
  "steps": [
    {
      "skill_id": "<exact id from the allowed list>",
      "arguments": { "<parameter names>": <values> }
    }
  ],
  "rationale": "<one sentence>"
}

Rules:
- Use only skill_id values from the allowed list exactly as given.
- Provide every required parameter for each skill; use empty object {} if a skill has no parameters.
- Order steps logically (e.g. set mode before launching apps if needed).
- If the user request cannot be satisfied with the listed skills, return {"steps": [], "rationale": "..."} explaining why.
"""


async def plan_with_llm(
    user_input: str,
    registry: SkillRegistry,
    extra_context: str | None = None,
) -> Plan | None:
    """Call OpenAI-compatible Chat Completions to build a Plan, or None if LLM disabled/unavailable."""
    if not settings.llm_api_key:
        log.debug("LLM planning skipped: ERICA_LLM_API_KEY not set")
        return None

    tools = registry.get_tool_definitions()
    if not tools:
        log.warning("LLM planning: no skills loaded")
        return None

    allowed_ids = "\n".join(f"- {t['skill_id']}" for t in tools)
    tools_json = json.dumps(tools, indent=2)
    user_block = f"User request:\n{user_input.strip()}\n"
    if extra_context:
        user_block += f"\nAdditional context:\n{extra_context.strip()}\n"

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": _PLANNER_SYSTEM
            + f"\n\nAllowed skill_id values (exact strings):\n{allowed_ids}\n\n"
            + "Skill details (parameters and permissions):\n"
            + tools_json,
        },
        {"role": "user", "content": user_block},
    ]

    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
    payload: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            res.raise_for_status()
            data = res.json()
    except Exception as e:
        log.warning("LLM planning request failed: %s", e)
        return None

    try:
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        log.warning("LLM planning bad response: %s", e)
        return None

    steps_raw = parsed.get("steps")
    if not isinstance(steps_raw, list):
        log.warning("LLM planning: missing steps array")
        return None

    rationale = str(parsed.get("rationale", "")).strip()
    valid_ids = registry.skill_ids()
    steps: list[PlanStep] = []
    for i, raw in enumerate(steps_raw):
        if not isinstance(raw, dict):
            continue
        sid = raw.get("skill_id") or raw.get("tool")
        if not isinstance(sid, str) or sid not in valid_ids:
            log.warning("LLM planning: drop unknown skill_id at step %s: %s", i, sid)
            continue
        args = raw.get("arguments") or raw.get("args") or {}
        if not isinstance(args, dict):
            args = {}
        steps.append(PlanStep(skill_id=sid, arguments=args))

    if not steps:
        if rationale:
            log.info("LLM planner empty steps: %s", rationale[:200])
        return None

    return Plan(
        id=str(uuid.uuid4()),
        steps=steps,
        rationale=rationale or "LLM plan",
    )
