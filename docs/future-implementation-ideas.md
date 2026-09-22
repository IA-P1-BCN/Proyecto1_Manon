# Future implementation ideas

Ideas that came up during design discussions but were deliberately postponed or dropped for the current phase. Kept here so they aren't lost, without committing them to the codebase before they're actually needed.

## Real-time fare ticker via background thread (Fase 1 — dropped)

**Context:** while deciding how `Carrera` should accrue fare over time, we considered a background thread that updates `importe` every N milliseconds, so a live-updating counter could be displayed even between state changes (e.g. for a future GUI).

**Why not now:** Fase 1 has no requirement to show a live counter on screen — the CLI only needs a correct `importe` at the moment it's queried (on `cambiar_estado()` or `finalizar()`). A background thread adds real complexity (thread safety around shared state, clean start/stop) for no current benefit.

**What we did instead:** timestamp-delta accrual, computed on demand — `Carrera` stores the timestamp it entered its current `estado`, and each `cambiar_estado()`/`finalizar()` call computes `elapsed * rate` and adds it to `importe`.

**When to reconsider:** if a future phase (e.g. Fase 3's touch GUI, per `docs/project-brief.md`) needs the displayed amount to update continuously on its own, without the user triggering a state change or finalization first.

### Reconsidered and re-dropped — flowchart session

Raised again while drawing `docs/flujo-fase1.md`, from the client-facing angle rather than the domain-model one: the briefing asks for the meter to show *"lo que le cuesta al pasajero en tiempo real"*, and the ideal is an amount permanently on screen refreshing every 1–2 s.

Re-dropped for Fase 1. The reasoning is sharper than the first pass, and worth recording because it is **not** what it looks like at first glance:

- **Rendering is not the obstacle.** Printing with `\r` instead of `\n` rewrites a terminal line in place. That part is trivial.
- **The obstacle is that `input()` blocks.** The main thread sits frozen inside it, so nothing can tick — hence the background thread, exactly as in the original entry.
- **The thread and the typist then fight over the same line.** The ticker rewrites the line every second while the driver is half-way through typing `movimiento`, scrambling their input.
- **Which cascades into the input model.** The standard fix is to abandon typed words for non-blocking single keypresses (`p`/`m`/`f`), which is stdlib but platform-specific — `msvcrt` on Windows, `termios` on macOS/Linux — and would overturn the typed-word decision in `docs/decisions-fase1-scaffold.md` as collateral.

That is a substantial amount of display-layer and platform machinery for a phase whose requisitos only ask for a correct total on `finalizar`.

**What we did instead:** the importe is echoed after every command, plus a dedicated read-only `importe` command for the driver who changes state zero times during a long traffic jam. The driver can always see the number on demand; it just doesn't animate.

**Still cheap to add later.** The timestamp-delta model supports a live display unchanged — "what is the importe right now?" is already a cheap read-only computation (`importe_actual()`). A future ticker only has to call it on a timer; no domain change required. Fase 3's GUI is the natural home, since a GUI has an event loop and separate widgets, so neither the blocking-input nor the shared-line problem exists there at all.

## Round half cents up when charging (Fase 2 — noticed, not changed)

**Context:** while building the US-05 history, a test for a ride of exactly 0,625 € showed that `formato_euros` charges **0,62 €**. Python's `format` rounds an exact binary half to the even digit ("banker's rounding"); customers and cash registers usually expect half-up (0,63 €). It only bites on exact half cents, which at 0,02 / 0,05 €/s means a duration that lands exactly on one, so it's rare in practice.

**Why not now:** it's Fase 1 behaviour, and the MVP is currently being validated by the client exactly as it is. The history stores the amount formatted the same way, so the till always matches the tickets either way.

**If it changes:** round with `decimal.Decimal(...).quantize(Decimal("0.01"), ROUND_HALF_UP)` in **one** place, used by both `formato_euros` and `Historial.registrar`, so the ticket and the till can never disagree. Decide it with the client, since it changes what passengers pay.

## Freeze the amount while FINALIZAR is being confirmed (Fase 3 — requested, not built yet)

**Context:** in the Fase 3 GUI, FINALIZAR opens a confirmation panel (`docs/diseno-interfaz-fase3.md`, *Confirmación al finalizar*), and as first designed the meter keeps running until the driver answers. The user pointed out, on 2026-09-22, that this is unfair to the passenger: the seconds spent answering the question are charged.

**Requested behaviour:**

- On pressing FINALIZAR, the displayed amount **freezes** at that instant.
- **SÍ, FINALIZAR:** the ride is closed and charged the amount **frozen at the first press**, not the amount at the moment of the answer.
- **NO, SEGUIR:** the ride resumes **as if it had never paused**. The time spent on the question is charged at the current state's rate, since the taxi was still occupied. The display jumps to the up-to-date amount.

**What it touches:**

- **Domain, not only the GUI.** Today `Carrera.finalizar()` / `Taximetro.finalizar_carrera()` close the ride at "now" (the injected `reloj`). They would need to close it at a given instant, e.g. `finalizar(en=instante)`, with that instant captured by the GUI when FINALIZAR is pressed. `hora_fin` must match (the `calendario` stamp taken at the same press), so the history row and the ticket agree. Closing at an instant earlier than "now" must still be guarded (not before the last state change).
- **NO needs no domain change.** Accrual is timestamp-based, so resuming without a pause is the existing behaviour. Only the display is frozen during the question.
- **Fase 2's Ctrl+C confirmation** has the same unfairness in the CLI (the meter keeps running while the question is on screen, as `decisions-fase2.md` states). Decide whether to align it, so both interfaces charge the same way.
- **Tests:** a ride confirmed N seconds after pressing FINALIZAR is charged the amount at the press; a cancelled one is charged continuously.

**When:** when the GUI's ride screen is implemented (US-09), or earlier if the client asks for it.
