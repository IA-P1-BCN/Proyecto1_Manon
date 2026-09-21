# Fase 2 decisions

Decisions for **Fase 2 — Observabilidad y Persistencia** (US-05, US-06, US-07), taken in a grilling session on 2026-09-21, started while the Fase 1 MVP was waiting for client approval. Same format as the other decision docs: what was decided, why, and what it costs.

Companion docs: `docs/project-brief.md` (client requirements, Fase 2 section), `docs/decisions-proceso.md` (git, CI, board), `docs/decisions-fase1-scaffold.md` (code structure), `docs/flujo-fase1.md` (Fase 1 CLI behaviour, which Fase 2 extends).

## Starting point

The user asked for three things up front:

1. A branch dedicated to Fase 2, so work can start while the MVP is being validated.
2. A **Driver / Admin split at the very start** of the flow: the user chooses a role first, and the Fase 2 features (ride history, fare change) are reachable only from Admin. This is the seed of a "super-user" access.
3. Tests left for the end of the phase.

Point 3 was reversed during the session (see *Tests*). The rest shaped every decision below.

## Tests stay alongside the code

**Decision:** tests are written with each story, as in Fase 1. The 90% coverage gate in `pyproject.toml` stays as it is.

**Why:** leaving tests to the end collides with two things already in place: CI fails any PR under 90% coverage, and `CLAUDE.md` asks for tests alongside new logic. Untested Fase 2 code would turn every PR red, or force the gate down and leave the integration branch under-tested for weeks. Options considered: a red integration branch until the end, a temporarily lowered gate, and testing last within each story. The user chose to keep the Fase 1 practice.

## Git: a `fase-2` integration branch

**Decision:** a long-lived `fase-2` branch off `dev`. Each story gets its own branch off `fase-2` (`feature/US-07-tarifas-configurables`, …) and a PR back into `fase-2`, with CI green. Docs work: `docs/<tema>` off `fase-2`. Fixes the client asks for on the MVP go to `dev` as usual and are then merged into `fase-2`. `fase-2` → `dev` only after Fase 1 has been approved and merged `dev` → `main`.

**Why:** `dev` holds Fase 1 exactly as it is being validated. If the client asks for MVP changes, they must ship without unapproved Fase 2 code attached. Story branches off `dev` couldn't guarantee that. A single branch with no per-story PRs would lose the review trail against the backlog that Fase 1 had.

**Consequence:** `.github/workflows/tests.yml` also triggers on `fase-2` (push and pull request), otherwise story PRs into it would get no CI. This amends *Git workflow* in `decisions-proceso.md` for the duration of Fase 2.

## Roles: Driver / Admin chosen at startup

**Decision:** the program opens on a role menu: `Conductor · Administrador · Salir`. *Conductor* is the Fase 1 ride loop, unchanged except that `Salir` becomes `Volver` (back to the role menu). *Administrador* holds the Fase 2 features: change the fares (US-07) and see today's history (US-05), plus `Volver`.

**Why:** the user wants "super-user" access prepared now, so the password in Fase 3 (US-08) only has to be put in front of an existing branch rather than retrofitted into a flat menu. Keeping administration out of the driver's menu also keeps the driver's screen as short as it was in Fase 1.

### Switching roles

**Decision:** `Volver` returns to the role menu. The driver's `Volver` exists only in the *Sin carrera* menu. With a ride open, the only way out is to finish it, exactly like `Salir` in Fase 1.

**Why:** it makes "a fare change never lands mid-ride" true by construction: while a ride is running you cannot reach Admin, so the passenger is always charged the fare announced when the ride started. The alternatives were a role fixed until the program exits (clumsy for the demo) and switching at any time (needs a rule for what a running ride pays after a fare change).

### Quitting

**Decision:** `Salir` appears only in the role menu. Driver and Admin menus offer `Volver` instead.

**Why:** one exit point and shorter menus. Quitting from the driver's screen costs one extra keypress (`Volver`, then `Salir`).

### Ctrl+C and EOF (assumption, not asked)

Extended from `flujo-fase1.md` rather than re-decided. Outside an active ride (role menu, Admin menu, driver *Sin carrera*), Ctrl+C and EOF exit cleanly. During a ride, behaviour is unchanged: Ctrl+C is ignored with a message, and EOF finishes the ride, shows the total and exits. A finished ride is written to the history whichever way it ends. Ctrl+C in the middle of typing a new fare cancels the edit and nothing is saved.

### No protection on Admin in Fase 2

**Decision:** anyone can choose *Administrador* in Fase 2. The password is US-08, in Fase 3.

**Why:** US-08 is a *Could* planned for Fase 3, and pulling it forward goes beyond the Fase 2 scope the client greenlights. The role split already provides the place where the check will go.

**Consequence:** in Fase 2 a passenger could change the fares. Say so explicitly at the Fase 2 demo, so the client doesn't read the Admin menu as a security feature.

## US-07: fares from a config file, editable from Admin

**Decision:** fares live in `config/tarifas.json` and are read at startup. Admin → *Cambiar tarifas* asks for both €/s values, validates them, applies them to the `Taximetro` and writes the file. The file can also still be edited by hand, which is the client's literal wording ("un técnico cambia las tarifas en un fichero de configuración").

**Why:** the user described fare change as an Admin feature, and the client's story is about a file. Editing through the menu and saving to that file satisfies both. It also avoids asking a technician to hand-edit JSON during the demo.

**Consequence:** as planned in Fase 1 (`tarifa.py` comment), the change stays in `Taximetro`, which builds the `Tarifa` and injects it into each `Carrera`. A new fare applies from the next ride, and the role-switching rule means no ride can be open during the change anyway.

### Validation

**Decision:** a fare set is valid when both values are > 0, at most 1 €/s (typo guard), and *parado* ≤ *en movimiento*. Input accepts `0,03` and `0.03`. Invalid Admin input shows a message and saves nothing. A missing or invalid file at startup falls back to the defaults (0,02 / 0,05 €/s) and logs a WARNING, without failing, as US-07's acceptance criteria require.

**Why:** the brief says the meter runs "más despacio" when stopped, so an inverted pair is certainly a mistake. The upper bound catches the classic slip of typing euros per minute into a per-second field. A confirmation step (old → new, "¿Confirmar?") was offered and not taken.

## US-05: ride history

**Decision:** every finished ride is appended as one row to a CSV file (stdlib `csv`) and kept indefinitely. Admin → *Ver histórico* lists **today's** rides, selected by the date of `hora_fin`, with hora inicio / fin and importe, plus the day's total.

**Why:** appending one row per ride is truly incremental: a crash can't corrupt earlier rides, and the fleet manager can open the file in a spreadsheet to reconcile the till ("cuadrar caja"). Keeping all rows costs nothing and gives Fase 4 (migration to a relational DB) real data to migrate. Picking an arbitrary date and one file per day were considered. Today-only matches the story ("del día") with the least input handling.

## US-06: operation logs

**Decision:** `logging` runs in both roles, silently, to a rotating file (`RotatingFileHandler`): startup, role chosen, ride started / state changed / finished, fare changed, invalid config, errors. It isn't shown in any menu.

**Why:** the story's user is the technician, who reads a file, not the driver or the fleet manager. An Admin log viewer was offered and not taken.

## Runtime files and git

**Decision:** commit `config/tarifas.example.json` with the default fares. The app creates `config/tarifas.json` from the defaults if it's missing. `.gitignore` the live `config/tarifas.json`, the history CSV (under `data/`) and `logs/`.

**Why:** a demo run, or a test run that forgets a temp dir, must never leave the repo dirty. The example file documents the schema for the technician.

## Tracking and order

**Decision:** no new epic. The role menu is folded into the first Admin story, **US-07**, as extra tasks. Order: **US-07 → US-05 → US-06**.

**Why:** US-07 is the smallest domain change (only `Taximetro` touches `Tarifa`, as prepared in Fase 1) and brings the role menu with the Admin mode it needs. US-05 then adds the second Admin option. US-06 comes last and instruments everything that exists by then in one pass. A separate "EPIC R" for roles was offered and declined, since the split is only there to serve these two stories.
