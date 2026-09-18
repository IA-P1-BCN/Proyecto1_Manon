# CLAUDE.md

Context and instructions for Claude Code working in this repository. Read at the start of every session. Keep this file short and factual — full client context lives in `docs/project-brief.md`; only pull new facts in here if they change how you should work day to day.

## Project

`TTX-247` — a software taxímetro (taxi meter) for TaxiTech Solutions, replacing failing physical hardware. Python, OOP. Full client brief, all 9 user stories, and phase requirements: see **`docs/project-brief.md`**. Read it before starting any new phase or story.

## Current phase

**Fase 1 — MVP** (US-01 to US-04, all Must-have). Build the CLI ride loop: start → toggle parado/en movimiento → finish with total → start another ride, same process. Don't start Fase 2+ work (logging, persistence, config file, auth, GUI, API, DB) unless explicitly asked — the client validates each phase before the next is greenlit.

## Fare logic (do not guess — these are the real numbers)

| State | Rate |
|---|---:|
| Parado / < 20 km/h | €0.02 per **second** |
| En movimiento | €0.05 per **second** |

Fare accrues continuously based on elapsed time in each state — not per km, not per fixed step. Final total shown in euros, 2 decimals.

## Structure (Fase 1)

```
taximetro/
    __init__.py
    carrera.py         # Carrera: id, hora_inicio, estado, importe
    tarifa.py           # Tarifa: rate lookup + accrual calculation
    taximetro_app.py    # TaximetroApp: CLI loop, prints usage on startup, no docs required to use it
tests/
    test_carrera.py
    test_tarifa.py
docs/
    project-brief.md
BACKLOG.md
CLAUDE.md
README.md
```

Later phases add `historial.py`, `config_tarifas.py`, `auth.py`, a GUI module, then `api/` and a DB layer — don't create these ahead of their phase.

## Commands

- Tests: `pytest`
- Tests with coverage: `pytest --cov=taximetro`
- Run: `python -m taximetro.taximetro_app`

Run `pytest` after every change. Don't call a task done with failing tests.

## Conventions

- PEP 8, type hints on public methods, short docstrings on every class/public method.
- One class per file, snake_case filename matching the class.
- Domain vocabulary in Spanish for consistency with the user stories (`Carrera`, `iniciar_carrera`, `cambiar_estado`, `finalizar`); generic utility code can be English.
- Keep the CLI layer thin — it parses input and calls methods on `TaximetroApp`/`Carrera`; no fare logic there.
- Fase 1 requires no external libraries beyond the standard library (`time`) unless a specific later-phase story calls for one (justify any new dependency in the PR description, per the client's technical constraints).
- Commits: [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/) format, referencing the story/task id, e.g. `feat(carrera): implement cambiar_estado (US-02)`.

## Working style

- One user story (or one task from `BACKLOG.md`) at a time, in priority order within the current phase.
- Write or update tests alongside any new logic, not after.
- I'm a junior developer using this project to learn agentic workflows — **explain your plan before making changes**, and briefly say why when you make a non-obvious decision (e.g. why a method lives on `Carrera` vs `Tarifa`). Don't just silently execute.
- When a requirement is ambiguous, state the assumption you're making rather than picking silently, and prefer the simplest implementation that satisfies the acceptance criteria in `docs/project-brief.md` / `BACKLOG.md`.

## Project management

Task board: GitHub Projects, one column per phase (Fase 1 → Fase 2 → Fase 3 → Fase 4). Each phase's deliverables: repo state, a live demo, and the updated board link — keep issues current as work progresses, don't just code silently against the backlog.