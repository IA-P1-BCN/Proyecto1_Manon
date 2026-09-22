# Fase 3 decisions

Decisions for **Fase 3 — Arquitectura y Experiencia de Usuario** (US-09 graphical interface, US-08 password, structural refactor), started on 2026-09-22 while Fase 2 was still on its integration branch. Same format as the other decision docs: what was decided, why, and what it costs.

Companion docs: `docs/project-brief.md` (client requirements, Fase 3 section), `docs/diseno-interfaz-fase3.md` (the visual spec: screens, sizes, colours, texts), `docs/flujo-fase3.md` (how the screens connect), `docs/decisions-fase2.md` (roles, fares, history, logs — the behaviour the GUI must keep).

**How this doc is filled:** decisions are taken in a grilling session, one question at a time, and recorded here as they are answered. Visual choices are tried on an HTML mockup first and only written into `diseno-interfaz-fase3.md` once agreed. A section marked **Pendiente** has not been decided yet; the questions under it are the agenda.

## Decided at kickoff (2026-09-22)

### Git: a `fase-3` integration branch off `fase-2`

**Decision:** a long-lived `fase-3` branch taken from `fase-2`. Story branches come off `fase-3` and PR back into it; docs work goes on `docs/<tema>` off `fase-3`. `fase-3` → `fase-2` (or `dev`, whichever is then current) only once Fase 2 has been merged.

**Why:** the GUI needs everything Fase 2 built (role menu, configurable fares, history, logs), and Fase 2 is not in `dev` yet. Same reasoning as the `fase-2` branch: whatever is being validated stays free of unapproved code.

**Consequence:** `.github/workflows/tests.yml` must also trigger on `fase-3`, otherwise story PRs into it get no CI. Fixes landing on `fase-2` (e.g. from the Fase 2 demo) are merged into `fase-3`.

### Scope of the design docs: every screen, including the login

**Decision:** `diseno-interfaz-fase3.md` designs every screen the user sees, including the password screen from US-08. How the password is hashed and stored is decided here, not in the design doc.

**Why:** the login screen is part of the interface. Designing it apart from the other screens would risk a screen that doesn't match the rest.

### Process: grilling session + HTML mockup

**Decision:** decisions are taken one question at a time. The visual design is reviewed on a clickable, tablet-sized HTML mockup; the agreed version is written into the repo as wireframes.

**Why:** "are these buttons big enough?" is judged on a real page, not in ASCII. The repo doc remains the reference the code is checked against, as `flujo-fase1.md` was for the CLI.

## Target device: a laptop, laid out as a landscape tablet

**Decision:** the GUI runs on a laptop for development and for the demo, in a viewport the size of a **landscape 10" tablet**. Layout, button sizes and font sizes follow tablet touch rules, not desktop mouse rules.

**Why:** no real tablet is needed to develop or demo, but the design stays honest to the brief ("funcional en una tablet montada en el vehículo"). Designing for touch on a laptop costs nothing; retrofitting touch onto a mouse-sized UI would.

**Consequence:** the exact reference resolution and the minimum touch target are set in `diseno-interfaz-fase3.md`.

## UI technology: `tkinter` (T9.1)

**Decision:** the driver's interface is built with `tkinter`, Python's standard GUI library. No new dependency.

**Why:** the brief fixes Python as the development language and lists `tkinter` in its resources. It plugs straight into the existing domain with no HTTP layer, and keeps pytest as the only toolchain.

**Alternative considered: React + CSS Modules** (the user's own front-end stack). A browser can't call Python, so React would have meant a Python HTTP API in Fase 3, i.e. pulling part of Fase 4 forward, plus Node/Vite/Vitest in the repo and a JavaScript front end to justify against the "Python" constraint. Its real argument was Fase 4's web panel.

**Fase 4 outlook:** tkinter stays as the **in-car driver app** ("instalar la aplicación en los vehículos"). Fase 4's web panel is a *separate* front end for the fleet manager ("consultar el historial sin instalar nada"), and React remains an option there. For the driver app to survive Fase 4, the tkinter screens must talk to the domain through **one intermediate object**; in Fase 4 that object is swapped for an HTTP client with the same methods, and the screens don't change (see *Structural refactor*).

**Costs:**
- No CSS: the look is set with widget options and `ttk.Style`, kept in one module so it reads like a theme.
- Taps act as clicks, with no gestures. Buttons don't need them.
- GUI tests need a display. CI runs on headless Linux, so the workflow needs a virtual display (`xvfb`).
- Fase 4's "deploy with one command" fits the server side; the in-car app is installed separately. Explain this at the Fase 4 demo.
- HTML mockups must stay within what tkinter can draw: flat colours, rectangular buttons, no shadows or gradients. Rounded corners would need a `Canvas`.

## Real-time counter and "never freezes"

**Decision (mechanism):** the amount is refreshed by a `tkinter` timer (`widget.after(ms, callback)`) on the main thread. It reads `Carrera.importe_actual()` and formats it with `formato_euros()`. No background thread.

**Why:** tkinter runs one event loop on one thread, as JavaScript does in a browser. A timer callback that only reads a timestamp delta returns in microseconds, so the screen never freezes. This is the path `future-implementation-ideas.md` anticipated; there's no domain change. Only the main thread may touch widgets, which is one more reason to avoid threads.

**Rule for every callback:** return quickly. The only I/O is a CSV line or a small JSON file (milliseconds). Anything slower would need a thread that hands its result back through `after()`.

Pendiente:
- Refresh interval (e.g. 500 ms, so the displayed cents never lag a whole second).

## Operation logs (US-06) carry over to the GUI

The Fase 2 requirement still holds: *"registrar en todo momento qué está ocurriendo: arranque, cambios de estado del vehículo, cierre de carrera y cualquier error […] accesible para el equipo técnico sin necesidad de intervenir en el proceso en ejecución"*. Fase 2 met it with `logs/taximetro.log` (see `decisions-fase2.md`, *US-06*). The file can be read (`tail`, `grep`, a text editor) while the app runs, and the GUI doesn't change that.

**What carries over for free:** every domain event is logged by the module that knows it (`Carrera`: ride started / state changed / finished; `Taximetro`, `ConfigTarifas`, `Historial`: fares, files). The GUI calls the same methods, so these lines appear unchanged.

**What the GUI must do itself** (today done by `TaximetroApp`, which the GUI doesn't use):

- **Call `configurar_logs()` at its entry point**, and only there, as the CLI's `__main__` does.
- **Use a fixed logger name** under `taximetro` (e.g. `getLogger("taximetro.gui")`), not `__name__`. This is the Fase 2 gotcha: under `python -m`, `__name__` is `__main__`, outside the `taximetro` tree, so its lines would miss the file.
- **Log what only the interface knows:** startup, exit reason (Salir, window closed), role chosen, the FINALIZAR confirmation answer, fares rejected, history viewed. Reuse the CLI's event names (`perfil_elegido`, `salida_solicitada`, `aplicacion_cerrada`…) so a technician's `grep` works for both interfaces.
- **New in Fase 3, US-08:** log `acceso_admin_concedido` / `acceso_admin_denegado` (WARNING). **Never log the typed password**, not even when it's wrong: a wrong password is often a typo of the right one.
- **Catch errors raised inside tkinter callbacks.** Pitfall: tkinter doesn't let an exception from a button's callback escape `mainloop()`. It prints the traceback to the console (`Tk.report_callback_exception`) and carries on, so the CLI's `error_inesperado` handler around the loop would never see it. The GUI must override `report_callback_exception` to log it as `error_inesperado` with its traceback, then show the driver a short message. Otherwise "cualquier error" is silently missing from the log.
- **Tests** read the events through the existing `eventos` fixture (`caplog`), as in Fase 2.

**Not added:** a log viewer in the Admin menu. It was offered in Fase 2 and declined, because the log's reader is the technician, who opens the file. Reconsider only if the client asks.

## GUI and CLI coexist

**Decision (2026-09-22):** the GUI becomes the main interface, and the CLI stays as a second entry point (`python -m taximetro.taximetro_app`).

**Why:** two interfaces running on the same domain without duplicating it is the strongest proof of the refactor and of US-09's criterion ("se apoya en la lógica de backend ya existente sin duplicarla"). It also keeps the Fase 1 and Fase 2 demos runnable. Replacing the CLI would have meant less code to maintain, but that proof would be lost.

**Consequences:**
- **The CLI's Admin must ask for the password too.** Otherwise the CLI would be a way around US-08: anyone could change the fares from a terminal. Both interfaces use the same password check, which lives outside either interface.
- The CLI and its tests are kept up to date. Anything the two interfaces do the same way (e.g. the password check, possibly the future FINALIZAR freeze) belongs below them, not copied into each.
- Fase 2's Ctrl+C rule stays the CLI's. The GUI's equivalent is decided in `flujo-fase3.md`.

## US-08: the password protects *Administrador* only

**Decision (2026-09-22):** choosing *Administrador* on the start screen asks for the password. *Conductor* opens the meter directly, with no password.

**Why:** the tampering risk the client worries about is someone changing the fares, which is an Admin action. A password on the driver's side would slow down every shift start and protect nothing the driver can change. This is what the Fase 2 role split was built for: the check goes in front of an existing branch. Alternatives considered: a driver PIN plus an admin password (closer to the backlog's "iniciar el turno" example, but a second secret and a keypad to design), and one password for the whole app (the driver would then know the password that unlocks the fares).

**Consequence:** the backlog's example ("p.ej. iniciar el turno") is not followed literally; the acceptance criterion ("antes de permitir operaciones sensibles") is. State this at the Fase 3 demo.

## Password entry: typed on the keyboard

**Decision (2026-09-22):** a masked text field (`show="•"` on a tkinter `Entry`) typed on the physical keyboard, with an ENTRAR key (Enter also works) and Cancelar.

**Why:** simplest to build, and it allows a real password rather than a short PIN. Development and demo run on a laptop (see *Target device*).

**Known limit:** tkinter does not reliably bring up a tablet's on-screen keyboard. On a touch-only tablet an on-screen keypad would have to be added. Considered and not taken for now: a numeric PIN with an on-screen keypad (works everywhere, weaker secret), and both at once (more to build and test).

## Pendiente — US-08: how the password works

- Hashing: stdlib `hashlib.pbkdf2_hmac` / `hashlib.scrypt` with a salt, or `bcrypt` (a new dependency)?
- Where the hash lives (a file under `config/`?), how the first password is set, how it is changed or reset.
- Failed attempts: limit, delay, log event?

## Pendiente — Structural refactor

- Which boundaries change so that the CLI and the GUI both sit on the same domain without duplicating it (US-09's acceptance criterion)? E.g. a layer between `Taximetro` and the interfaces holding what `TaximetroApp` does today beyond parsing input.
- Constraint already set by the tkinter decision: the screens talk to a single intermediate object, so Fase 4 can replace it with an HTTP client exposing the same methods.
- What must stay replaceable for Fase 4 (history → database, logic → API).

## Pendiente — Tracking and order

- Order of US-08 / US-09 / refactor, and whether the refactor gets its own epic.
- New Fase 3 tasks in `Backlog.md` and on the board.
