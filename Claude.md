# CLAUDE.md

Context and instructions for Claude Code working in this repository. Read at the start of every session. Keep this file short and factual — full client context lives in `docs/project-brief.md`; only pull new facts in here if they change how you should work day to day.

## Project

`TTX-247` — a software taxímetro (taxi meter) for TaxiTech Solutions, replacing failing physical hardware. Python, OOP. Full client brief, all 9 user stories, and phase requirements: see **`docs/project-brief.md`** (the client's own wording, unedited — don't rewrite or summarise it in place). Read it before starting any new phase or story.

## Current phase

**Fase 3 — Arquitectura y Experiencia de Usuario** (US-09 GUI, US-08 password, structural refactor), on the `fase-3` integration branch (taken from `fase-2`, which still awaits merging). The **design stage is closed** (2026-09-23): every decision is in `docs/decisions-fase3.md`, the visual spec in `docs/diseno-interfaz-fase3.md`. Work order: the refactor first (T9.10 → T9.12, `ServicioTaximetro`), then US-08, then the rest of US-09. Fase 4 work (API, DB) stays out of scope.

## Fare logic (do not guess — these are the real numbers)

| State | Rate |
|---|---:|
| Parado / < 20 km/h | €0.02 per **second** |
| En movimiento | €0.05 per **second** |

Fare accrues continuously based on elapsed time in each state — not per km, not per fixed step. Final total shown in euros, 2 decimals, Spanish format: `12,34 €` (comma, space before the symbol), produced only by `utils.formato_euros()`.

## Design decisions

Before changing behaviour, check whether it was already decided:

- **`docs/decisions-fase1-scaffold.md`** — structural decisions (what lives where, and why).
- **`docs/flujo-fase1.md`** — authority on CLI behaviour: the command loop, menus per mode, error messages, Ctrl+C / EOF.
- **`docs/flujo-fase2.md`** — what Fase 2 changes in the CLI: role menu, Admin fare change and history, Ctrl+C confirmation mid-ride (supersedes Fase 1's Ctrl+C rule).
- **`docs/decisions-fase2.md`** — Fase 2 decisions: roles, fare config, history, logs, the `fase-2` branch.
- **`docs/decisions-fase3.md`** — Fase 3 decisions: the `fase-3` branch, UI technology, real-time counter, password, refactor. Includes the work order and the Fase 4 replacement points.
- **`docs/diseno-interfaz-fase3.md`** — authority on the GUI: device, touch rules, colours per state, every screen and its texts.
- **`docs/flujo-fase3.md`** — how the GUI screens connect, and how each Fase 2 CLI rule maps onto them.
- **`docs/decisions-proceso.md`** — how the project is run: language, git workflow, CI, coverage gate, board.
- **`docs/future-implementation-ideas.md`** — ideas deliberately postponed; check before "improving" something that was dropped on purpose.
- **`docs/demo-fase1.md`** — the script for the client demo; keep it true to the real CLI output.

## Structure (Fase 1 + Fase 2, Fase 3 so far)

```
taximetro/
    __init__.py
    auth.py             # Auth: scrypt check against config/credenciales.json (Fase 3, US-08)
    carrera.py          # Carrera: id, hora_inicio, hora_fin, estado, distancia, importe
    tarifa.py           # Tarifa: rate lookup + accrual calculation; validates its rates
    config_tarifas.py   # ConfigTarifas: load/save config/tarifas.json (Fase 2, US-07)
    historial.py        # Historial: append-only CSV of finished rides (Fase 2, US-05)
    logs.py             # configurar_logs(): rotating logs/taximetro.log, called only from __main__ (US-06)
    taximetro.py        # Taximetro: owns the Tarifa and the active Carrera
    servicio_taximetro.py  # ServicioTaximetro: the façade the interfaces use (Fase 3, T9.10)
    __main__.py         # python -m taximetro → the GUI
    gui/                # tkinter GUI (Fase 3, US-09): app.py (App: window + screen switching),
                        # pantalla.py (Pantalla base: timers cancelled on leave), estilo.py (theme:
                        # sizes, colours, px fonts ≥ 24), tecla.py (Tecla: touch key ≥ 88 px),
                        # visor.py (Visor: 7-segment amount, digits from formato_euros),
                        # taximetro.py (PantallaTaximetro: the meter, LIBRE/OCUPADO, 200 ms refresh),
                        # confirmacion.py (Confirmacion: full-screen YES/NO panel),
                        # inicio.py, contrasena.py, administrador.py, tarifas.py, historico.py (screens 1, 2, 6-8),
                        # franja.py (top strip), iconos.py (icons drawn on a Canvas)
                        # one module per screen
    taximetro_app.py    # TaximetroApp: CLI loop, prints usage on startup, no docs required to use it
    utils.py            # formato_euros()
tests/
    conftest.py         # shared fixtures: fake reloj / calendario
    test_estructura.py  # design contract: the agreed public API still exists
    test_auth.py
    test_carrera.py
    test_tarifa.py
    test_config_tarifas.py
    test_historial.py
    test_logs.py
    test_taximetro.py
    test_servicio_taximetro.py
    test_taximetro_app.py
    test_utils.py
    gui/                # GUI tests: one Tk per session, a fresh hidden Toplevel per test, no mainloop();
                        # test_cabe.py checks nothing is cut off or out of place on any screen
config/
    tarifas.example.json  # committed; the live tarifas.json is git-ignored
    credenciales.json   # committed: salt + scrypt hash of the Admin password, never the password
docs/                   # see "Design decisions" above
.github/workflows/
    tests.yml           # pytest + coverage on push and PR
Backlog.md
Claude.md
README.md
```

One test file per module (GUI ones under `tests/gui/`). Fase 4 adds `api/` and a DB layer — don't create these ahead of their phase.

## Object responsibilities

- `Carrera` — one ride. Accrues its own importe via timestamp deltas; raises `CarreraFinalizadaError` on any change after `finalizar()`. Reads on a closed ride return the frozen total, they never raise and never accrue.
- `Tarifa` — state → rate lookup and `calcular_importe(estado, segundos)`. Owned by `Taximetro`, injected into each `Carrera`, so Fase 2's `ConfigTarifas` only touches `Taximetro`.
- `Taximetro` — owns the active `Carrera`, the `Tarifa` and the injected clocks. Raises `CarreraActivaError` on a double `iniciar_carrera()`.
- `TaximetroApp` — CLI only. Knows which mode it is in and produces the driver-facing messages itself; no fare logic. Talks only to `ServicioTaximetro` (since T9.11).
- `ServicioTaximetro` (Fase 3) — the only object the CLI and the GUI talk to. Wraps `Taximetro` and `Auth`, returns data (snapshots, numbers), never a live `Carrera`; Fase 4 swaps it for an HTTP client with the same methods.

**Two clocks, injected, never called globally:** `reloj: Callable[[], float] = time.monotonic` measures elapsed time for fare accrual (a wall clock can jump backwards and undercharge); `calendario: Callable[[], datetime] = datetime.now` stamps `hora_inicio` / `hora_fin`. `TaximetroApp` takes `entrada=input` and `salida=print` for the same reason — tests script commands in and read printed lines out.

## Commands

- Tests: `pytest` (coverage and the 90% gate are in `pyproject.toml`'s `addopts`, so a bare `pytest` enforces them)
- Coverage detail: `pytest --cov-report=term-missing`
- Run the GUI: `python -m taximetro`
- Run the CLI: `python -m taximetro.taximetro_app`

Run `pytest` after every change. Don't call a task done with failing tests.

## Conventions

- PEP 8, type hints on public methods, short docstrings on every class/public method.
- One class per file, snake_case filename matching the class.
- Domain vocabulary in Spanish for consistency with the user stories (`Carrera`, `iniciar_carrera`, `cambiar_estado`, `finalizar`); generic utility code can be English (`formato_euros`).
- **Language:** anything the client or an evaluator reads is Spanish — `README.md`, `docs/project-brief.md`, `docs/flujo-fase1.md`, `docs/demo-fase1.md`, docstrings, CLI output, commit subjects. Internal working notes (`docs/decisions-*.md`, `docs/future-implementation-ideas.md`) may stay in English.
- Keep the interface layers thin — they parse input and call `ServicioTaximetro`; no fare logic there. The CLI and everything under `taximetro/gui/` may import only `servicio_taximetro`, `logs` and `utils` from the package; `test_estructura.py` fails otherwise (T9.12).
- Fase 1 requires no external libraries beyond the standard library (`time`, `datetime`) unless a specific later-phase story calls for one (justify any new dependency in the PR description, per the client's technical constraints).
- Commits: [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/) format, referencing the story/task id, e.g. `feat(carrera): implement cambiar_estado (US-02)`.

## Git workflow

- Branch per user story off `dev`: `feature/US-01-iniciar-carrera`. Docs-only work: `docs/<tema>`.
- PR into `dev`, CI green before merge. `dev` → `main` once per phase, so `main` always holds a demoable release.
- Never commit straight to `main`.
- **During Fase 2:** story branches come off `fase-2` and PR into `fase-2`. Fixes to the Fase 1 MVP still go to `dev` and are then merged into `fase-2`. `fase-2` → `dev` only after Fase 1 reaches `main`.

## Working style

- One user story (or one task from `Backlog.md`) at a time, in priority order within the current phase.
- Write or update tests alongside any new logic, not after.
- I'm a junior developer using this project to learn agentic workflows — **explain your plan before making changes**, and briefly say why when you make a non-obvious decision (e.g. why a method lives on `Carrera` vs `Tarifa`). Don't just silently execute.
- When a requirement is ambiguous, state the assumption you're making rather than picking silently, and prefer the simplest implementation that satisfies the acceptance criteria in `docs/project-brief.md` / `Backlog.md`.

## Project management

Task board: GitHub Projects, `Status` = one column per phase (User Stories · Fase 1 → Fase 4), as the client requires. Day-to-day progress is tracked by the `Progreso` field (To Do / En curso / En review / Done) and by closing issues as PRs merge — not by moving cards between phases. Each phase's deliverables: repo state, a live demo, and the updated board link — keep issues current as work progresses, don't just code silently against the backlog.
The existing GitHub project is `IAS_P1_Taximetro_Manon` (org `IA-P1-BCN`, project #2: https://github.com/orgs/IA-P1-BCN/projects/2), tracking issues in `IA-P1-BCN/Proyecto1_Manon`. Every task in `Backlog.md` carries its issue number — keep those links accurate.
