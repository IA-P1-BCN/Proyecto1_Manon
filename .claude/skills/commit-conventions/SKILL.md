---
name: commit-conventions
description: Use whenever preparing, writing, or running a git commit in this repository (TTX-247 taxímetro) — including `git commit`, amending a message, or drafting one for the user to review. Enforces Conventional Commits format, a scope matching the module touched, and a reference to the relevant BACKLOG.md story/task id (e.g. US-02, T2.3). Trigger this before every commit in this repo, not only when the user explicitly asks about commit style.
---

# Commit conventions (TTX-247)

Source of truth: `CLAUDE.md` "Conventions" and "Working style" sections. This skill exists so the format doesn't have to be re-derived each time.

## Format

```
<type>(<scope>): <description> (<story-id>)
```

- **type** — a [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/) type matching the change: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`, `build`, `style`, `perf`. Don't add `ci`/`revert`/others until a phase actually needs them (Fase 1 has no CI pipeline).
- **scope** — the module or class touched, lowercase, matching the filename without `.py` (e.g. `carrera`, `tarifa`, `taximetro_app`). Use `tests` or `docs` when that's what changed. Omit the scope only for changes that don't belong to one module (e.g. repo-wide scaffolding).
- **description** — English, imperative mood, lowercase, no trailing period, concise (subject line under ~72 chars total). (Domain names inside the description stay in Spanish per CLAUDE.md, e.g. "implement cambiar_estado".)
- **story-id** — the `US-XX` or `TX.X` id from `BACKLOG.md` this commit fulfills. Check `BACKLOG.md` if it's not already obvious from the conversation — don't guess. If a commit genuinely serves no single backlog item (pure tooling/config/docs with no story), omit the `(story-id)` suffix entirely and add a short line in the commit body saying why it isn't story-linked, rather than inventing an id or force-fitting it under an epic.

## Examples

```
feat(carrera): implement cambiar_estado (US-02)
test(tarifa): add tests for parado vs movimiento rates (T2.2)
fix(taximetro_app): prevent double carrera start (US-01)
build: initial project scaffolding (T0.1)
```

## Splitting commits

- Implementation code and its own tests may share one commit (e.g. `carrera.py` + `test_carrera.py` for the same task).
- Two unrelated production modules touched in the same diff still get split into separate commits — one story/task per commit, per CLAUDE.md's working style.

## Attribution trailer

None — the user has opted out of Claude co-authorship on commits (`attribution.commit: ""` in global `settings.json`). Never add a `Co-Authored-By: Claude...` trailer to a commit message in this repo.

## Before committing

1. Confirm which `BACKLOG.md` story/task the change belongs to — ask the user if it's genuinely unclear rather than guessing.
2. Don't bundle unrelated stories or tasks into one commit (see "Splitting commits" above).
3. `pytest` should pass before committing (CLAUDE.md: "Don't call a task done with failing tests").
4. If anything about the message would violate this format — wrong type, a story id that doesn't fit, changes that should be split — **stop and ask the user before running `git commit`**. Don't silently auto-correct and commit, even for small formatting issues; confirm first.
