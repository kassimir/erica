# skills

- **`manifests/`** — one YAML manifest per skill (name, description, entrypoint, parameters, permissions, examples).
- **`schema/`** — JSON Schema for manifests (`skill_manifest.schema.json`).
- **Python modules** — implementations imported via `entrypoint` (e.g. `skills.persona_skill:set_mode`).

The agent loads manifests at startup from this directory (see `ERICA_SKILLS_PATH`).
