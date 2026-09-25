# Fase 1 scaffold — design decisions

Record of the design questions resolved before writing the Fase 1 (US-01–US-04) scaffold, and the reasoning behind each answer. Kept for future reference — if a later phase needs to revisit one of these, the "why" is here instead of only in git history.

> **Update — flowchart design session.** Drawing the CLI flow in `docs/flujo-fase1.md` reopened three of the decisions below. Superseded entries are marked and keep their original reasoning, so the reversal is readable rather than silently overwritten. Affected: **CLI input style**, **Error handling for invalid operations**, **Fare accrual model** (amended, not reversed). `docs/flujo-fase1.md` is now the authority on CLI behaviour; this file remains the authority on structure.

> **Update — pre-implementation grilling session.** A second design interview, held before writing any Fase 1 logic, reopened four decisions below and added five new ones. Superseded entries keep their original reasoning so the reversal stays readable. Affected: **Fare accrual model**, **Time source for testability**, **Euro-formatting location**, **Tarifa's public interface**. New: *Carrera's attribute set*, *Reads on a finalised carrera*, *CLI input/output injection*, *EOF handling*, *Test file layout*. Repo- and process-level decisions from the same session (language, branching, CI, coverage, board) live in `docs/decisions-proceso.md`.

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

**Amended again (grilling session).** The deltas are now measured with `time.monotonic()`, not `time.time()`. A wall clock is subject to NTP corrections and manual changes: if it steps backwards mid-tramo, `ahora - marca` goes negative and the tramo *subtracts* from the fare. Nothing in the code would raise, and the passenger would simply be undercharged. `time.monotonic()` is guaranteed never to go backwards, which is exactly the guarantee an accrual model needs. See "Time source for testability" below for the second clock this forced.

## Estado representation

**Decision:** `Estado` is a Python `Enum` (`PARADO`, `EN_MOVIMIENTO`), defined in `carrera.py`.

**Why:** type-safe against typos in state strings, and reads clearly at call sites (`Estado.PARADO` vs. `"parado"`).

## Carrera.id generation

**Decision:** incrementing class-level counter starting at 1.

**Why:** human-readable, deterministic, easy to assert in tests. No persistence across process restarts is needed yet in Fase 1.

**Superseded (US-01 implementation).** The counter moved to `Taximetro`, which passes `id` to each `Carrera` it creates. `Carrera` holds no counter at all.

**Why the reversal:** the original entry was written before `Taximetro` existed as the factory. A class-level counter is global mutable state, and it fails on exactly the ground the entry claimed as its advantage — being *easy to assert in tests*:

- It never resets between tests, so `assert carrera.id == 1` passes or fails depending on which tests ran before it. The usual patch is an autouse fixture reaching into `Carrera._siguiente_id`, i.e. tests manipulating private class state to stay isolated.
- Two `Taximetro` instances would share one sequence, so the second taxi's first ride of the day would be "Carrera nº 2".

With the counter in `Taximetro` both problems disappear without a fixture, and "Carrera nº 1" means the first ride of *this* taxi's shift — which is what it means to the driver reading it. Covered by `test_cada_taximetro_numera_sus_propias_carreras`.

## Error handling for invalid operations

**Decision:** invalid operations raise custom domain exceptions — `CarreraActivaError` (double `iniciar_carrera`), `CarreraFinalizadaError` (changes after `finalizar()`). `TaximetroApp`'s CLI layer catches them and prints a message to the driver.

**Why:** keeps domain classes (`Carrera`, `Taximetro`) pure and easy to unit test (`pytest.raises(...)`), consistent with the "CLI layer stays thin" convention in `CLAUDE.md`.

**Superseded in part (flowchart session).** The exceptions stay exactly as described — they remain the domain's own guarantees and are still unit-tested with `pytest.raises(...)`. What changed is that the CLI no longer *relies* on catching them for its error messages.

Because the loop is now mode-aware (see "Context-sensitive menus" in `docs/flujo-fase1.md`), `TaximetroApp` already knows whether a carrera is active before dispatching, so it produces the driver-facing message itself:

- Ride command typed while idle → `'No hay ninguna carrera activa.'`
- `iniciar` typed during a ride → `'Ya hay una carrera activa.'`
- Anything unrecognised → `'Comando no reconocido.'`

In normal CLI use the domain exceptions should therefore **never surface** — the menu prevents reaching them. They are now a safety net for direct API use (and for Fase 4's REST layer, which will have no menu to lean on), not the CLI's primary error path. A `try/except` around dispatch is still worth keeping as defence in depth, but it is no longer what makes the messages correct.

**Superseded again (numbered-menu session).** The three messages above collapsed into one. With a numbered menu, a valid option for the *other* mode cannot be typed at all — there is no key that finalises a non-existent ride, and none that opens a second ride while one is open — so the only remaining error is input that isn't a number in the menu on screen: `'Opción no válida. Elige un número del menú.'` The conclusion about the domain exceptions is unchanged and, if anything, stronger: they are now unreachable from the CLI by construction.

## Rounding / precision

**Decision:** `importe` stays full-precision internally (a `float`); rounding to 2 decimals happens only at display/formatting time, in `utils.formato_euros()`.

**Why:** avoids compounding rounding error across many state changes over the course of a ride.

## Time source for testability

**Decision:** `Carrera.__init__` accepts an injectable clock, `reloj: Callable[[], float] = time.time`, defaulting to real time in production.

**Why:** tests can pass a fake, deterministic, fast-incrementing clock instead of sleeping for real seconds or monkeypatching the global `time` module.

**Superseded (grilling session): one clock became two.** `time.monotonic()` is the right tool for measuring elapsed time (above) but it returns an arbitrary float with no calendar meaning — you cannot derive `hora_inicio` from it. `Carrera` therefore takes two injectables, each correct for its own job:

```python
def __init__(
    self,
    tarifa: Tarifa,
    reloj: Callable[[], float] = time.monotonic,          # accrual only
    calendario: Callable[[], datetime] = datetime.now,    # hora_inicio / hora_fin
) -> None: ...
```

`reloj` is never used for display; `calendario` is never used for arithmetic. Both are injected by `Taximetro`, so a test can drive a whole fake-timed ride from the top without touching `Carrera` directly. Shared fakes live in `tests/conftest.py`.

Bonus for Fase 2: `hora_inicio` is already a `datetime`, so `Historial` can write a real date without converting an epoch float.

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

**Superseded again (numbered-menu session).** Typed words are gone; the driver types the option's number. Authoritative version, per `docs/flujo-fase1.md`:

| Mode | Options offered |
|---|---|
| Sin carrera (idle) | `1) Iniciar carrera` · `2) Ayuda` · `3) Salir` |
| Carrera activa | `1) Parar` *or* `1) Arrancar` · `2) Ver importe` · `3) Finalizar carrera` · `4) Ayuda` |

Two further changes:

- **Numbers are per-menu, not global.** The `1` starts a ride when idle and toggles the vehicle's state during one. Fixed global numbers would leave gaps (`2 · 3 · 5 · 6`) that force reading instead of counting. Only one menu is ever on screen.
- **`parado` and `movimiento` merged into one toggle.** The menu offers whichever is the opposite of the current state, so it never presents a key that does nothing. The label is derived from `carrera.estado`; the action is `cambiar_estado()` to the opposite state. `cambiar_estado()`'s silent no-op on a repeated state survives as a domain guarantee (still unit-tested) but is now unreachable from the CLI.

The live-ticker rejection above still holds for the same reason: the driver still types into a blocking `input()`, so a background redraw would still corrupt half-typed input.

**Consequence — Ctrl+C:** removing `salir` from the active menu made Ctrl+C the only remaining mid-ride exit, which would have lost the fare and printed a traceback mid-demo. It is therefore caught: during a ride it prints `'Para salir, finaliza la carrera.'` and redraws the menu; while idle it exits cleanly. A ride can only ever end deliberately.

## Euro-formatting location

**Decision:** a standalone function `formato_euros()` in a new `taximetro/utils.py`.

**Why:** matches BACKLOG's T3.2 wording ("formateo de importe en euros (helper/util)") literally. Also flagged as a deviation from `CLAUDE.md`'s listed Fase 1 file tree, alongside `taximetro.py`.

**Amended (grilling session): the output format was contradictory.** The scaffold docstring said `'12.34€'`; every message in `docs/flujo-fase1.md` said `X,XX €`. Resolved in favour of the Spanish convention — the client is in Madrid and the driver reads prices with a comma:

```python
def formato_euros(importe: float) -> str:
    """Formatea un importe: 12.3456 -> '12,35 €'."""
    return f"{importe:.2f} €".replace(".", ",")
```

Deliberately **not** the `locale` module: `locale.setlocale(..., 'es_ES.UTF-8')` raises if that locale isn't installed, so the output would differ between a Windows dev box, an Ubuntu CI runner and the demo laptop — a formatting helper should not be able to fail.

Rounding direction is left as Python's default (`format` rounds the underlying binary float, half-to-even). With per-second accrual producing arbitrary floats, an exact half-cent is effectively unreachable, so a rounding policy would be a rule with no cases.

**Corrected during US-03.** The example in this entry originally read `12.3456 -> '12,34 €'`, which is simply wrong arithmetic: `f"{12.3456:.2f}"` is `12.35`, because formatting *rounds*, it does not truncate. Fixed here and in the `formato_euros` docstring, and pinned by `test_redondea_la_precision_sobrante`. Worth noting because the mistake was copied from the docstring into this document, so neither copy was an independent check on the other.

## Repeated cambiar_estado() to the same estado

**Decision:** silent no-op — nothing changes, fare keeps accruing under the current rate, no exception raised.

**Why:** forgiving of a driver accidentally pressing the same command twice; there's no invalid state being requested, just a redundant one.

## Initial estado on iniciar_carrera()

**Decision:** a new `Carrera` starts in `Estado.PARADO`.

**Why:** a taxi ride typically begins with the vehicle stationary (picking up the passenger) before pulling away.

**Superseded (numbered-menu session).** A new `Carrera` now starts in `Estado.EN_MOVIMIENTO`, billing at 0,05 €/s from the first second. The client's reading: the ride is started when the taxi pulls away with the passenger already aboard, not while waiting for them — so starting `PARADO` billed the low rate over the first seconds of real travel. A taxi that does start stationary is one keypress away (`Parar`). Knock-on: the first segment of every ride is the expensive one, and the accrual tests in `test_carrera.py` were recalculated on 0,05 €/s.

## Tarifa's public interface

**Decision:** a single `Tarifa.calcular_importe(estado: Estado, segundos: float) -> float`, dispatching internally on `estado` (e.g. a rate-per-estado lookup), instead of separate `calcular_parado()`/`calcular_movimiento()` methods.

**Why:** keeps the state-to-rate dispatch logic in one place (`Tarifa`) rather than duplicating an if/else in `Carrera`'s accrual code every time it needs to pick which `Tarifa` method to call.

**Extended (grilling session): who owns the instance.** The scaffold never said where the `Tarifa` comes from, though `Carrera` is what needs it. Decision: **`Taximetro` builds one `Tarifa` and injects it into every `Carrera` it creates.**

```python
class Taximetro:
    def __init__(self, tarifa: Tarifa | None = None) -> None:
        self._tarifa = tarifa or Tarifa()

    def iniciar_carrera(self) -> Carrera:
        return Carrera(tarifa=self._tarifa, reloj=self._reloj, calendario=self._calendario)
```

**Why:** it puts the seam where Fase 2 needs it. US-07 loads tarifas from a config file; with this shape only `Taximetro` changes (`Tarifa(ConfigTarifas.cargar())`) and `Carrera` is untouched. If `Carrera` built its own `Tarifa`, the config would have to reach it through a module-level singleton or a new parameter threaded through anyway. It also lets a test inject a `Tarifa` with round numbers, so assertions don't carry 0.02/0.05 arithmetic.

---

## Decisions added in the pre-implementation grilling session

The four entries above were amendments. These five are new.

### Carrera's attribute set

**Decision:** `id`, `hora_inicio`, `hora_fin` (`None` until finalised), `estado`, `distancia` (`0.0`), `importe`.

**Why `hora_fin`:** T3.1 asks `finalizar()` to record an end time, and `hora_fin is not None` doubles as the "this ride is closed" flag — no separate `finalizada: bool` that could contradict it.

**Why `distancia` stays at 0.0:** the brief prices purely on time, so nothing in Fase 1 reads it, and `Claude.md`'s structure line omits it. Kept anyway because `Backlog.md`'s suggested design for US-01 lists it, and a later phase adding GPS or odometer input would want it. It is a deliberate placeholder, **not** a half-finished per-km feature and not dead code left by accident — recorded here so a reviewer doesn't have to guess which.

### Reads on a finalised carrera

**Decision:** on a closed `Carrera`, `importe_actual()` returns the stored `importe` unchanged — no tramo accrual. `cambiar_estado()` and a second `finalizar()` both raise `CarreraFinalizadaError`.

**Why:** `docs/flujo-fase1.md` specified that writes raise, but said nothing about reads. Left unspecified, the natural implementation (`importe + tramo en curso`) keeps accruing against a timestamp that stopped being meaningful at `finalizar()` — so the "final" total of a closed ride would keep growing for as long as the process stayed open. Freezing reads makes `finalizar()`'s return value permanently reproducible, which is what `Historial` will store in Fase 2.

The CLI never reaches this path (a closed ride returns the loop to the idle menu), so this is a domain-level guarantee, in the same category as the exceptions.

### CLI input/output injection

**Decision:** `TaximetroApp.__init__(self, taximetro=None, entrada=input, salida=print)`. `ejecutar()` calls `self._entrada(...)` and `self._salida(...)`, never the builtins directly.

**Why:** TD.9 requires testing the menus, the two error messages and the Ctrl+C branch, and a loop that calls `input()`/`print()` directly offers no seam. With the injection a test is three lines and asserts on a list of strings, with no `monkeypatch` of builtins and no stdout parsing:

```python
salidas: list[str] = []
app = TaximetroApp(entrada=iter(["iniciar", "movimiento", "finalizar", "salir"]).__next__,
                   salida=salidas.append)
app.ejecutar()
assert "TOTAL A COBRAR" in salidas[-1]
```

Same reasoning as the injected clocks, applied to the I/O boundary instead of the time boundary.

### EOF handling

**Decision:** `EOFError` is caught. While idle it exits cleanly, like `salir`. Mid-ride it finalises the carrera, prints the total, and then exits.

**Why:** the flowchart handled Ctrl+C but never EOF, and `input()` raises `EOFError` on Ctrl+D, on piped stdin running out, and on an injected `entrada` iterator reaching the end of its script — so unhandled it means a traceback at the end of every CLI test and during any piped demo.

Mid-ride it deliberately does **not** copy the Ctrl+C behaviour of printing "finaliza la carrera" and looping: EOF is not retryable, so re-reading would spin forever. Finalising first keeps the promise that a fare is never silently lost, while still terminating. Recorded in the diagram in `docs/flujo-fase1.md`.

### Test file layout

**Decision:** one test file per module — `test_carrera.py`, `test_tarifa.py`, `test_taximetro.py`, `test_taximetro_app.py`, `test_utils.py` — plus `tests/conftest.py` for the shared fake-clock fixtures.

**Why:** consistent with the one-class-per-file convention already in `Claude.md`, and a failing file name points straight at the module that broke. Traceability to the backlog is carried by test names and docstrings (`US-02`, `TD.5`) rather than by file names, so a module's behaviour stays in one place instead of being scattered across story-named files.
