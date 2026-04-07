from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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
