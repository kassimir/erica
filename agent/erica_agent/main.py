from __future__ import annotations

import json
import logging
import sys
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from erica_agent.context import build_request_context
from erica_agent.erica_memory import get_erica_memory, init_erica_memory
from erica_agent.memory import short_term
from erica_agent.memory_backend import get_memory_backend
from erica_agent.models import (
    EricaMode,
    ExecuteRequest,
    ExecuteResponse,
    IntentRequest,
    IntentResponse,
    MemoryFactRequest,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryWakeUpResponse,
    Plan,
    PlanRequest,
    PlanResponse,
)
from erica_agent.palace_config import looks_like_preference_statement
from erica_agent.persona import persona_state
from erica_agent.llm_planner import plan_with_llm
from erica_agent.planner import intent_from_text, plan_from_text
from erica_agent.registry import registry
from erica_agent.workflows import engine as workflow_engine

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _permissions_for_mode(mode: EricaMode) -> set[str]:
    base = {"persona", "memory.read", "memory.write"}
    if mode == EricaMode.quiet:
        return base | {"process.launch"}
    if mode == EricaMode.writer:
        return base | {
            "process.launch",
            "window.manage",
            "audio.volume",
            "audio.device",
        }
    return base | {
        "process.launch",
        "window.manage",
        "audio.volume",
        "audio.device",
        "network.wifi",
    }


def _execute_plan(plan, session_id: str | None) -> ExecuteResponse:
    if not plan or not plan.steps:
        return ExecuteResponse(
            ok=True,
            results=[],
            message=persona_state.format_execute_summary(True, []),
        )
    results: list[dict] = []
    mode = persona_state.mode
    perms = _permissions_for_mode(mode)
    for step in plan.steps:
        log.info("Execute step skill_id=%s args=%s", step.skill_id, step.arguments)
        try:
            out = registry.call(step.skill_id, step.arguments, perms)
            log.info("Execute step ok skill_id=%s result_type=%s", step.skill_id, type(out).__name__)
            results.append({"skill": step.skill_id, "ok": True, "result": out})
            short_term.add_command(f"exec:{step.skill_id}", {"args": step.arguments})
        except Exception as e:
            log.exception("Skill failed")
            results.append({"skill": step.skill_id, "ok": False, "error": str(e)})
    ok = all(r.get("ok") for r in results)
    return ExecuteResponse(
        ok=ok,
        results=results,
        message=persona_state.format_execute_summary(ok, results),
    )


def _persist_execute_memory(body: ExecuteRequest, res: ExecuteResponse) -> None:
    """MemPalace interaction drawer + diary + SQLite cache (utterance path already wrote via backend)."""
    try:
        backend = get_memory_backend()
        parts: list[str] = []
        if body.text:
            parts.append(f"User: {body.text}")
        parts.append(f"ok={res.ok} {res.message}")
        if res.results:
            parts.append(f"results={json.dumps(res.results, default=str)[:4000]}")
        backend.diary("\n".join(parts), wing=persona_state.mode.value)
        skill_id = None
        if res.results:
            for r in reversed(res.results):
                if r.get("skill"):
                    skill_id = str(r["skill"])
                    break
        elif body.plan and body.plan.steps:
            skill_id = body.plan.steps[-1].skill_id
        status = "ok" if res.ok else "error"
        get_erica_memory().save_interaction(
            body.text,
            res.message,
            skill_id,
            status,
            res.results,
        )
    except Exception:
        log.exception("Persist execute memory failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    persona_state.load()
    n = registry.load_directory()
    log.info("Loaded %d skills", n)
    wf = workflow_engine.load_directory()
    log.info("Loaded %d workflows", wf)
    mem = init_erica_memory()
    app.state.memory = mem

    def _on_wf(wid: str, payload: dict):
        p = workflow_engine.to_plan(wid)
        if p:
            _execute_plan(p, None)

    workflow_engine.on_trigger(_on_wf)
    asyncio.create_task(workflow_engine.run_app_trigger_loop())
    yield
    sched = getattr(workflow_engine, "_scheduler", None)
    if sched:
        sched.shutdown(wait=False)


app = FastAPI(title="Erica Agent", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def inject_context(request: Request, call_next):
    request.state.context_text = build_request_context(None)
    return await call_next(request)


@app.post("/intent", response_model=IntentResponse)
async def post_intent(body: IntentRequest, request: Request):
    short_term.add_command(body.text)
    if looks_like_preference_statement(body.text):
        try:
            get_erica_memory().store_preference_fact(body.text)
        except Exception:
            log.exception("Preference capture failed")
    info = intent_from_text(body.text)
    mode_switch = plan_from_text(body.text)
    mode: EricaMode | None = None
    if mode_switch:
        for s in mode_switch.steps:
            if s.skill_id == "persona.set_mode" and "mode" in s.arguments:
                try:
                    mode = EricaMode(s.arguments["mode"])
                except ValueError:
                    mode = None
    wf_id = workflow_engine.match_command(body.text)
    if wf_id:
        info["workflow"] = wf_id
    ctx = build_request_context(body.text)
    return IntentResponse(
        intent=info.get("intent", "unknown"),
        confidence=0.7 if mode_switch or wf_id else 0.2,
        mode=mode,
        raw={**info, "context_preview": ctx[:800]},
    )


def _plan_extra_context(body: PlanRequest) -> str | None:
    parts: list[str] = []
    if body.context:
        parts.append(body.context.strip())
    if body.include_request_context:
        ctx = build_request_context(body.text)
        if ctx:
            parts.append(ctx[:4000])
    return "\n\n".join(parts) if parts else None


@app.post("/plan", response_model=PlanResponse)
async def post_plan(body: PlanRequest):
    short_term.add_command(body.text)
    ctx = build_request_context(body.text)
    p: Plan | None = None
    if body.use_llm:
        extra = _plan_extra_context(body)
        p = await plan_with_llm(body.text, registry, extra_context=extra)
    if p is None or not p.steps:
        p = plan_from_text(body.text)
    if not p:
        wf_id = workflow_engine.match_command(body.text)
        if wf_id:
            p = workflow_engine.to_plan(wf_id)
    if not p:
        return PlanResponse(
            plan=None,
            message=persona_state.shape_plan_message(f"No rule or LLM plan matched. Context:\n{ctx[:2000]}"),
        )
    return PlanResponse(plan=p, message=persona_state.shape_plan_message("ok"))


@app.get("/tools")
async def get_tools():
    """Registered skills in LLM-friendly form (for debugging and external planners)."""
    return {"tools": registry.get_tool_definitions()}


@app.get("/memory/wake-up", response_model=MemoryWakeUpResponse)
async def get_memory_wake_up():
    return MemoryWakeUpResponse(wake_up=get_erica_memory().wake_up_context())


@app.post("/memory/search", response_model=MemorySearchResponse)
async def post_memory_search(body: MemorySearchRequest):
    return MemorySearchResponse(results=get_erica_memory().recall(body.query, wing=body.wing, room=body.room))


@app.post("/memory/fact")
async def post_memory_fact(body: MemoryFactRequest):
    return get_erica_memory().add_fact(body.subject, body.predicate, body.obj, valid_from=body.valid_from)


@app.post("/execute", response_model=ExecuteResponse)
async def post_execute(body: ExecuteRequest):
    if body.text:
        try:
            get_memory_backend().write(
                body.text,
                metadata={"kind": "utterance"},
                tags=["utterance"],
                source="session",
                label="utterance",
            )
        except Exception:
            log.exception("Long-term write skipped")

    if body.plan:
        res = _execute_plan(body.plan, body.session_id)
        _persist_execute_memory(body, res)
        return res
    if body.text:
        p = plan_from_text(body.text)
        if not p:
            return ExecuteResponse(ok=False, message="Could not plan from text.")
        res = _execute_plan(p, body.session_id)
        _persist_execute_memory(body, res)
        return res
    return ExecuteResponse(ok=False, message="No plan or text provided.")


@app.post("/execute/stream")
async def post_execute_stream(body: ExecuteRequest):
    """Streams newline-delimited JSON chunks for the Quake console."""

    async def gen():
        if body.text:
            try:
                get_memory_backend().write(
                    body.text,
                    metadata={"kind": "utterance"},
                    tags=["utterance"],
                    source="session",
                    label="utterance",
                )
            except Exception:
                log.exception("Long-term write skipped")
        if body.plan:
            res = _execute_plan(body.plan, body.session_id)
        elif body.text:
            p = plan_from_text(body.text)
            if not p:
                yield json.dumps({"text": "Could not plan.", "done": True}) + "\n"
                return
            res = _execute_plan(p, body.session_id)
        else:
            yield json.dumps({"text": "No input.", "done": True}) + "\n"
            return
        _persist_execute_memory(body, res)
        yield json.dumps({"text": json.dumps(res.model_dump(), indent=2), "done": False}) + "\n"
        yield json.dumps({"text": "", "done": True}) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


@app.get("/health")
async def health():
    return {"ok": True, "mode": persona_state.mode.value}


@app.post("/voice/stt")
async def voice_stt(request: Request):
    """Optional STT hook: POST raw audio bytes; returns JSON { text }."""
    body = await request.body()
    from erica_agent.voice import stt

    text = stt.transcribe(body)
    return {"text": text}


@app.post("/voice/tts")
async def voice_tts(payload: dict):
    """Optional TTS hook: JSON { text }; speaks via configured provider (stub)."""
    from erica_agent.voice import tts

    t = str(payload.get("text", ""))
    tts.speak(t)
    return {"ok": True}
