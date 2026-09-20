# Fase 1 scaffold — design decisions

Record of the design questions resolved before writing the Fase 1 (US-01–US-04) scaffold, and the reasoning behind each answer. Kept for future reference — if a later phase needs to revisit one of these, the "why" is here instead of only in git history.

> **Update — flowchart design session.** Drawing the CLI flow in `docs/flujo-fase1.md` reopened three of the decisions below. Superseded entries are marked and keep their original reasoning, so the reversal is readable rather than silently overwritten. Affected: **CLI input style**, **Error handling for invalid operations**, **Fare accrual model** (amended, not reversed). `docs/flujo-fase1.md` is now the authority on CLI behaviour; this file remains the authority on structure.

## Step order

**Decision:** scaffold the empty package/test structure first, get it reviewed, then implement US-01 (`Carrera`) as a separate step.

**Why:** keeps the structural decision (what files exist, what depends on what) separable from the logic decisions, so both can be reviewed independently.

## Taximetro vs. folding into TaximetroApp

**Decision:** keep `Taximetro` as its own class in `taximetro/taximetro.py`, orchestrating the active `Carrera`. `TaximetroApp` wraps it for the CLI loop.

**Why:** matches BACKLOG.md's suggested design (`Taximetro.iniciar_carrera()`) more closely than folding everything into the CLI layer.

**Note:** this adds a file not listed in `CLAUDE.md`'s Fase 1 structure (`taximetro/taximetro.py`), same for `taximetro/utils.py` below — flagged here and in the corresponding commit/PR as an intentional deviation.

## Fare accrual model

**Decision:** timestamp-delta accrual computed on demand. `Carrera` stores the timestamp it entered the current `estado`; `cambiar_estado()` and `finalizar()` compute `elapsed * rate` and add it to `importe`, then reset the timestamp. No background thread.

**Why:** Fase 1's CLI has no live-updating display — importe only needs to be correct at the moment it's queried. A polling/ticking thread would add concurrency complexity for no current benefit. See `docs/future-implementation-ideas.md` for the discarded alternative.

**Amended (flowchart session):** still correct, but the model now has a *third* caller. The `importe` command added in `docs/flujo-fase1.md` queries the running total on demand, so `Carrera` also needs a **read-only** accessor — e.g. `importe_actual() -> float` — returning `importe + tramo en curso` **without** accruing into `importe` or resetting the timestamp.

The accrue-and-reset behaviour stays exclusive to `cambiar_estado()` and `finalizar()`. This is the sharpest edge in the whole model: if a read mutates state, every `importe` call silently discards the current tramo and the passenger is under-charged, with no error anywhere. Regression test to write alongside it: *two consecutive `importe_actual()` calls followed by `finalizar()` must produce the same total as `finalizar()` alone.*

The no-thread half of this decision was re-confirmed in the same session — see "No live ticker in Fase 1" in `docs/flujo-fase1.md` for why a continuously refreshing display was rejected again for Fase 1.

## Estado representation

**Decision:** `Estado` is a Python `Enum` (`PARADO`, `EN_MOVIMIENTO`), defined in `carrera.py`.

**Why:** type-safe against typos in state strings, and reads clearly at call sites (`Estado.PARADO` vs. `"parado"`).

## Carrera.id generation

**Decision:** incrementing class-level counter starting at 1.

**Why:** human-readable, deterministic, easy to assert in tests. No persistence across process restarts is needed yet in Fase 1.

## Error handling for invalid operations

**Decision:** invalid operations raise custom domain exceptions — `CarreraActivaError` (double `iniciar_carrera`), `CarreraFinalizadaError` (changes after `finalizar()`). `TaximetroApp`'s CLI layer catches them and prints a message to the driver.

**Why:** keeps domain classes (`Carrera`, `Taximetro`) pure and easy to unit test (`pytest.raises(...)`), consistent with the "CLI layer stays thin" convention in `CLAUDE.md`.

**Superseded in part (flowchart session).** The exceptions stay exactly as described — they remain the domain's own guarantees and are still unit-tested with `pytest.raises(...)`. What changed is that the CLI no longer *relies* on catching them for its error messages.

Because the loop is now mode-aware (see "Context-sensitive menus" in `docs/flujo-fase1.md`), `TaximetroApp` already knows whether a carrera is active before dispatching, so it produces the driver-facing message itself:

- Ride command typed while idle → `'No hay ninguna carrera activa.'`
- `iniciar` typed during a ride → `'Ya hay una carrera activa.'`
- Anything unrecognised → `'Comando no reconocido.'`

In normal CLI use the domain exceptions should therefore **never surface** — the menu prevents reaching them. They are now a safety net for direct API use (and for Fase 4's REST layer, which will have no menu to lean on), not the CLI's primary error path. A `try/except` around dispatch is still worth keeping as defence in depth, but it is no longer what makes the messages correct.

## Rounding / precision

**Decision:** `importe` stays full-precision internally (a `float`); rounding to 2 decimals happens only at display/formatting time, in `utils.formato_euros()`.

**Why:** avoids compounding rounding error across many state changes over the course of a ride.

## Time source for testability

**Decision:** `Carrera.__init__` accepts an injectable clock, `reloj: Callable[[], float] = time.time`, defaulting to real time in production.

**Why:** tests can pass a fake, deterministic, fast-incrementing clock instead of sleeping for real seconds or monkeypatching the global `time` module.

## CLI input style

**Decision:** typed-word commands (`iniciar`, `parado`, `movimiento`, `finalizar`, `salir`), documented in the startup banner.

**Why:** self-documenting per US-01's requirement that the driver needs no external docs, and easy to test by feeding strings to the input loop.

**Superseded (flowchart session).** Typed words survive — that part was re-confirmed, and it is what let the live-ticker idea be rejected (a ticker's redraws corrupt half-typed input, forcing single-keypress, platform-specific reads). The *command set* and its *availability* changed. Authoritative version, per `docs/flujo-fase1.md`:

| Mode | Commands offered |
|---|---|
| Sin carrera (idle) | `iniciar` · `ayuda` · `salir` |
| Carrera activa | `parado` · `movimiento` · `importe` · `finalizar` · `ayuda` |

Three changes from the original entry:

- **`importe` added** — read-only running total, for the driver sitting in traffic who changes state zero times and would otherwise see no number until `finalizar`. Drives the `importe_actual()` requirement under "Fare accrual model" above.
- **`ayuda` added** — reprints the banner, available in both modes, because the banner scrolls off screen after a couple of rides and US-01's "no external docs" requirement shouldn't expire when the terminal scrolls.
- **`salir` removed from the active menu** — it now exists only while idle. To leave mid-ride the driver runs `finalizar` (which prints the total and returns to the idle menu, where `iniciar` and `salir` are both offered). This gives each command one meaning — `finalizar` ends a *ride*, `salir` ends the *program* — and dissolves the "should `salir` auto-finalizar or discard the fare?" question rather than answering it. It also makes US-04 a visible prompt instead of an implicit property of the loop.

**Consequence — Ctrl+C:** removing `salir` from the active menu made Ctrl+C the only remaining mid-ride exit, which would have lost the fare and printed a traceback mid-demo. It is therefore caught: during a ride it prints `'Para salir, finaliza la carrera.'` and redraws the menu; while idle it exits cleanly. A ride can only ever end deliberately.

## Euro-formatting location

**Decision:** a standalone function `formato_euros()` in a new `taximetro/utils.py`.

**Why:** matches BACKLOG's T3.2 wording ("formateo de importe en euros (helper/util)") literally. Also flagged as a deviation from `CLAUDE.md`'s listed Fase 1 file tree, alongside `taximetro.py`.

## Repeated cambiar_estado() to the same estado

**Decision:** silent no-op — nothing changes, fare keeps accruing under the current rate, no exception raised.

**Why:** forgiving of a driver accidentally pressing the same command twice; there's no invalid state being requested, just a redundant one.

## Initial estado on iniciar_carrera()

**Decision:** a new `Carrera` starts in `Estado.PARADO`.

**Why:** a taxi ride typically begins with the vehicle stationary (picking up the passenger) before pulling away.

## Tarifa's public interface

**Decision:** a single `Tarifa.calcular_importe(estado: Estado, segundos: float) -> float`, dispatching internally on `estado` (e.g. a rate-per-estado lookup), instead of separate `calcular_parado()`/`calcular_movimiento()` methods.

**Why:** keeps the state-to-rate dispatch logic in one place (`Tarifa`) rather than duplicating an if/else in `Carrera`'s accrual code every time it needs to pick which `Tarifa` method to call.
