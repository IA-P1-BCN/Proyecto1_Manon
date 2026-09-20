# Process & repo decisions

Decisions about how the project is *run* rather than how the taxímetro *works*: documentation layout, language, git workflow, CI, quality gates and the task board. Taken in the pre-implementation grilling session, before Fase 1 logic was written.

Companion docs: `docs/decisions-fase1-scaffold.md` (code structure), `docs/flujo-fase1.md` (CLI behaviour), `docs/project-brief.md` (client requirements).

## One copy of the client brief

**Decision:** `docs/project-brief.md` is the client's brief **verbatim**. The condensed rewrite that previously lived there was deleted, and the untouched original (`Context.md`) moved into its place with `git mv`, so the file keeps its history.

**Why:** there were two copies of the requirements — a full one at the repo root and a summarised one in `docs/` — and `Claude.md` pointed only at the summary. Acceptance criteria are what the project is graded against; a summary of them can only lose detail, and two copies drift silently as soon as one is edited. Nothing in the condensed version was absent from the original.

**Consequence:** don't "tidy" `docs/project-brief.md`. If something about it needs explaining, explain it here or in `Claude.md`.

## Language policy

**Decision:** Spanish for anything the client or an evaluator reads — `README.md`, `docs/project-brief.md`, `docs/flujo-fase1.md`, `docs/demo-fase1.md`, all docstrings, all CLI output, commit subjects. English is allowed in internal working notes: `docs/decisions-*.md` and `docs/future-implementation-ideas.md`.

**Why:** the deliverables (repo, live demo, board) go to a Madrid client, and the user stories are written in Spanish. The split keeps the client-facing surface consistent without forcing a translation pass over design notes that only the team reads. Code identifiers keep the rule already in `Claude.md`: Spanish domain vocabulary (`Carrera`, `iniciar_carrera`), English for generic helpers (`formato_euros`).

## Git workflow

**Decision:** one branch per user story off `dev` (`feature/US-01-iniciar-carrera`), docs-only work on `docs/<tema>`, PR into `dev` with CI green before merge. `dev` → `main` once per phase. Never commit to `main` directly.

**Why:** a PR per story gives a reviewable trail against the backlog without the churn of ~20 PRs (one per task) for a single phase. Merging to `main` only at phase boundaries means `main` always holds the last state demoed to the client, which is what the phase deliverable asks for.

**Gotcha — `Closes #NN` does not fire on merges into `dev`.** GitHub only auto-closes linked issues when a PR merges into the repository'''s *default* branch, which here is `main`. Since every story PR targets `dev`, the keywords are inert: issues have to be closed by hand after the merge, ideally with a comment naming the PR and the merge commit. Keep writing the `Closes #NN` lines anyway — they create the visible link between issue and PR, and they will close correctly on the `dev` → `main` merge at the end of the phase.

## Continuous integration

**Decision:** `.github/workflows/tests.yml` runs `pytest` on every push and PR to `main`/`dev`.

**Why:** `Claude.md` requires tests to pass before a task is considered done; until now that was enforced only by remembering. CI makes it a visible check on the PR, and it is concrete evidence of engineering practice for the evaluation.

**Python version:** the workflow pins a single version rather than a matrix. The local `.venv` is 3.14, the workflow runs 3.13 — the project uses nothing version-specific, and running CI on a slightly older interpreter than the dev machine catches accidental use of very new syntax. The minimum supported version is stated in the README.

## Coverage gate

**Decision:** `--cov=taximetro --cov-fail-under=90` lives in `pyproject.toml`'s `addopts`, so a bare `pytest` enforces it locally and in CI alike.

**Why:** `pytest-cov` was already installed but no target was defined, which makes coverage a number nobody acts on. Fase 2's requirements explicitly demand the fare logic be covered by automated tests, and 90% is reachable in Fase 1 precisely because the design is injectable end to end (clocks, `Tarifa`, CLI I/O). Putting it in `addopts` rather than only in CI means the gate fails on the developer's machine first.

**When to revisit:** if the first real measurement comes out far above 90%, raise it; the number is a floor, not a target to aim at with tests written only to move it.

## Task board

**Decision:** the board's `Status` field stays as one column per phase (`User Stories · Fase 1 … Fase 4`), exactly as the client's constraints require. Day-to-day progress is tracked by a separate `Progreso` single-select field (`To Do · En curso · En review · Done`) and by closing issues as PRs merge. A second, filtered view is used for daily work; the per-phase board view is what gets shown at the demo.

**Why:** the client asked for "una columna por fase", which spends the only column axis GitHub Projects offers. Without a second field, twenty Fase 1 cards sit in one column with no visible todo/doing/done during the demo. Milestones were considered for the phases instead (freeing `Status` for a workflow) but that stops the board literally showing a column per phase.

**Consequence:** `Backlog.md` previously documented a five-column flow (`Backlog → To Do → In Progress → In Review → Done`) that never existed on the board. Corrected to describe what is actually there.

## README

**Decision:** a minimal README now (instalación, uso, tests), expanded into the full version at the end of Fase 1.

**Why:** T0.4 has been open since the start and the repo is deliverable #1, but a README written before the CLI exists would document commands that don't work yet. Minimal now keeps it honest; the expansion happens when there is something real to describe.

## Demo preparation

**Decision:** a written demo script, `docs/demo-fase1.md` — the exact commands to type, the output each should produce and the requirement it proves — run live at real speed. No accelerated-clock flag in production code.

**Why:** the live demo is a deliverable for every phase, and with €/second rates an unrehearsed ride is minutes of dead air. A `--demo` flag with a 10× clock was considered and rejected: it is production code that exists only for the demo, and it shows the client amounts that aren't real. Waiting ~20 seconds per tramo is enough to show the numbers moving, and the injected clocks already make the *tests* fast, which is where speed actually matters.
