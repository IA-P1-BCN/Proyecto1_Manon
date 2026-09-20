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
