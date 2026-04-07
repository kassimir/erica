from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any, Callable

import yaml
from pydantic import BaseModel, Field, field_validator

from erica_agent.config import settings

log = logging.getLogger(__name__)


class ParameterSpec(BaseModel):
    name: str
    type: str = "string"
    required: bool = False
    description: str = ""


class SkillManifest(BaseModel):
    name: str
    description: str = ""
    entrypoint: str
    parameters: list[ParameterSpec] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)

    @field_validator("entrypoint")
    @classmethod
    def entrypoint_ok(cls, v: str) -> str:
        if ":" not in v:
            raise ValueError("entrypoint must be 'module:function'")
        return v


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, SkillManifest] = {}
        self._handlers: dict[str, Callable[..., Any]] = {}

    def load_directory(self, base: Path | None = None) -> int:
        root = base or settings.skills_path
        if not root.is_dir():
            log.warning("Skills path missing: %s", root)
            return 0
        manifest_root = root / "manifests" if (root / "manifests").is_dir() else root
        loaded = 0
        for path in sorted(manifest_root.rglob("*.yaml")):
            if "schema" in path.parts:
                continue
            try:
                raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                m = SkillManifest.model_validate(raw)
                self._skills[m.name] = m
                mod_name, fn_name = m.entrypoint.split(":", 1)
                mod = importlib.import_module(mod_name)
                fn = getattr(mod, fn_name)
                self._handlers[m.name] = fn
                loaded += 1
            except Exception as e:
                log.error("Skip invalid skill manifest %s: %s", path, e)
        return loaded

    def get(self, name: str) -> SkillManifest | None:
        return self._skills.get(name)

    def call(self, name: str, args: dict[str, Any], permissions_ok: set[str]) -> Any:
        m = self._skills.get(name)
        if not m:
            raise KeyError(f"Unknown skill: {name}")
        missing = set(m.permissions) - permissions_ok
        if missing:
            raise PermissionError(f"Missing permissions for {name}: {missing}")
        fn = self._handlers.get(name)
        if not fn:
            raise RuntimeError(f"No handler for {name}")
        return fn(**args)


registry = SkillRegistry()
