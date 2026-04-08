from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EricaMode(str, Enum):
    writer = "WriterMode"
    operator = "OperatorMode"
    quiet = "QuietMode"


class PlanStep(BaseModel):
    skill_id: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class Plan(BaseModel):
    id: str
    steps: list[PlanStep]
    rationale: str = ""


class IntentRequest(BaseModel):
    text: str
    session_id: str | None = None


class IntentResponse(BaseModel):
    intent: str
    confidence: float = 0.0
    mode: EricaMode | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class PlanRequest(BaseModel):
    text: str
    session_id: str | None = None
    context: str | None = Field(
        default=None,
        description="Optional hint (e.g. active window title, foreground app).",
    )
    use_llm: bool = Field(
        default=True,
        description="When True, try LLM planner if ERICA_LLM_API_KEY is set, then rule-based fallback.",
    )
    include_request_context: bool = Field(
        default=True,
        description="Merge persona + memory context block into the LLM prompt.",
    )


class PlanResponse(BaseModel):
    plan: Plan | None
    message: str = ""


class ExecuteRequest(BaseModel):
    plan: Plan | None = None
    text: str | None = None
    session_id: str | None = None


class ExecuteResponse(BaseModel):
    ok: bool
    results: list[dict[str, Any]] = Field(default_factory=list)
    message: str = ""


class StreamChunk(BaseModel):
    text: str = ""
    done: bool = False


class MemorySearchRequest(BaseModel):
    query: str
    wing: str | None = None
    room: str | None = None


class MemorySearchResponse(BaseModel):
    results: list[str] = Field(default_factory=list)


class MemoryFactRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    subject: str
    predicate: str
    obj: str = Field(alias="object")
    valid_from: str | None = None


class MemoryWakeUpResponse(BaseModel):
    wake_up: str = ""
