# Fase 3 decisions

Decisions for **Fase 3 — Arquitectura y Experiencia de Usuario** (US-09 graphical interface, US-08 password, structural refactor), started on 2026-09-22 while Fase 2 was still on its integration branch. Same format as the other decision docs: what was decided, why, and what it costs.

Companion docs: `docs/project-brief.md` (client requirements, Fase 3 section), `docs/diseno-interfaz-fase3.md` (the visual spec: screens, sizes, colours, texts), `docs/flujo-fase3.md` (how the screens connect), `docs/decisions-fase2.md` (roles, fares, history, logs — the behaviour the GUI must keep).

**How this doc is filled:** decisions are taken in a grilling session, one question at a time, and recorded here as they are answered. Visual choices are tried on an HTML mockup first and only written into `diseno-interfaz-fase3.md` once agreed. A section marked **Pendiente** has not been decided yet; the questions under it are the agenda. All of them were closed on 2026-09-23.

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

**Decision (mechanism):** the amount is refreshed by a `tkinter` timer (`widget.after(ms, callback)`) on the main thread. It reads the snapshot from `ServicioTaximetro.estado_actual()` (which in turn uses `Carrera.importe_actual()`; see *Structural refactor*) and formats the amount with `formato_euros()`. No background thread.

**Why:** tkinter runs one event loop on one thread, as JavaScript does in a browser. A timer callback that only reads a timestamp delta returns in microseconds, so the screen never freezes. This is the path `future-implementation-ideas.md` anticipated; there's no domain change. Only the main thread may touch widgets, which is one more reason to avoid threads.

**Rule for every callback:** return quickly. The only I/O is a CSV line or a small JSON file (milliseconds). Anything slower would need a thread that hands its result back through `after()`.

**Decision (interval, 2026-09-23):** the timer fires every **200 ms**. At the highest rate (0,05 €/s) one cent takes 200 ms, so the display never skips a visible cent and the counter looks continuous. Locally each call costs microseconds. *Assumption:* after any key press (PARAR/ARRANCAR, FINALIZAR…) the screen repaints at once, without waiting for the next tick.

**Fase 4 note:** once the service is an HTTP client, this means 5 requests per second per taxi. Revisit then, e.g. poll less often, or have the snapshot carry the current rate and its timestamp so the screen can extrapolate between polls. That would move a sliver of fare arithmetic into the interface, which is why it isn't done now. Considered: 500 ms (jumps 2–3 cents at a time while moving) and 1 s (classic-meter feel, but up to a second's lag after PARAR/ARRANCAR).

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

## US-08: password hashed with `hashlib.scrypt` (T8.2)

**Decision (2026-09-23):** the Admin password is hashed with `hashlib.scrypt` (standard library), with a random 16-byte salt from `secrets.token_bytes`. Checking a typed password recomputes the hash with the stored salt and parameters and compares with `hmac.compare_digest`. The scrypt parameters (`n`, `r`, `p`) are stored next to the hash, so they can be raised later without invalidating the existing password.

**Why:** no new dependency. scrypt is deliberately memory-hungry, so a stolen hash is expensive to brute-force even on GPUs. One check takes roughly 50–100 ms, which is imperceptible after pressing ENTRAR and costly to an attacker. `compare_digest` takes the same time whether the first byte or the last one differs, so the comparison leaks nothing through timing.

**Alternatives considered:** `hashlib.pbkdf2_hmac` (also stdlib and better known, but not memory-hard, so weaker against GPUs); `bcrypt` (the industry default, but a new dependency to justify, with nothing to add over scrypt for one local password).

## US-08: the hash lives in `config/credenciales.json`

**Decision (2026-09-23):** a file of its own, `config/credenciales.json`, **committed to the repo** (unlike `config/tarifas.json`; see the next section for why). It holds the algorithm name, the scrypt parameters, the salt and the hash (both hex), e.g. `{"algoritmo": "scrypt", "n": 16384, "r": 8, "p": 1, "sal": "…", "hash": "…"}`. Only `Auth` reads and writes it.

**Why:** one file per responsibility, as with fares and history. `ConfigTarifas` rewrites `tarifas.json` whole on every GUARDAR, and a technician edits it by hand, so a hash stored there could be dropped or broken by either. Keeping it apart also means `ConfigTarifas` never has to preserve a field it doesn't own.

**Alternatives considered:** a field inside `tarifas.json` (see above); an environment variable (no file, but the password could never be changed from the app, and setting one on Windows is awkward for the demo).

## US-08: the password is supplied by the technical team (simulated)

**Decision (2026-09-23):** the Admin password is **`taxi`**. The project treats it as supplied, set and changed by the client's technical team. The app has no code to create, change or reset it. Its hash (never the word itself) ships in the committed `config/credenciales.json`, generated once when `Auth` is built.

**Why:** this is a school project and no technical team exists. Setting and rotating passwords would add a setup command or a screen to a *Could* story without touching an acceptance criterion. The Fase 3 requirement ("almacenada de forma segura", "ningún valor sensible en texto plano") is about how the password is **stored**, and scrypt covers that in full.

**Consequences:**
- `config/credenciales.json` is committed rather than git-ignored, since nothing would create it otherwise. It contains only a salt and a hash, so committing it doesn't expose the password.
- `taxi` appears only where a human needs it to run the demo (README, demo script), presented as "provided by the technical team". It never appears in code, tests or config. Tests use their own password and a `tmp_path` credentials file.
- **Missing or unreadable file** (assumption): Admin access is denied with a message, the event is logged as ERROR, and Conductor keeps working. Access is never granted by default.
- A real mechanism for setting and changing the password is recorded in `future-implementation-ideas.md`.

## US-08: `Auth` as built (T8.1, T8.2)

**Settled while building it (2026-09-23):**

- **"Can't check" is not "wrong".** The password screen has two different messages («Contraseña incorrecta…» and «No se puede comprobar la contraseña. Avisa al equipo técnico.»), so a `bool` isn't enough. `Auth.comprobar(contrasena) -> bool` answers right/wrong and **raises `CredencialesError`** when the file is missing or broken. That includes a malformed JSON, broken hex, an unknown algorithm, and scrypt parameters it rejects or that exceed a 64 MB memory cap. It logs `credenciales_ilegibles` (ERROR) with the path and error type, never the password. In T8.3 the service turns this into `AlmacenamientoError`, the contract exception it already has for unreadable files. Access is denied either way.
- **The file is re-read on every check**, so a change by the technical team applies without a restart. One scrypt check costs ~50 ms.
- **`Auth.generar_credenciales(contrasena)`** builds the file's content. No screen uses it: it produced the committed file once, and tests use it to build their own files with a cheap `n` (the cost is stored in the file, so that's the same code path).
- **The committed file is tested without its password:** a test checks that it can be read, rejects an arbitrary password and uses the real cost (`n=2**14, r=8, p=1`).

## US-08: `comprobar_contrasena` in the service (T8.3)

**As built (2026-09-23):** `ServicioTaximetro(taximetro, auth=None)`, and `por_defecto()` passes the real `Auth()`. `comprobar_contrasena(texto)` has three outcomes:

| Case | Returns / raises | Log |
|---|---|---|
| Right password | `True` | `acceso_admin_concedido` (INFO) |
| Wrong password | `False` | `acceso_admin_denegado motivo=contrasena_incorrecta` (WARNING) |
| Credentials file missing or broken | `AlmacenamientoError` (cause: `CredencialesError`) | `acceso_admin_denegado motivo=credenciales_ilegibles` (WARNING), plus `Auth`'s `credenciales_ilegibles` (ERROR) with the detail |

The typed text is never logged. The events are logged in the service, so the CLI and the GUI can't name them differently.

**Without `auth`, access is always denied** (`AlmacenamientoError`); `config/credenciales.json` is not read by default. This mirrors `Taximetro`, which without `config` never touches the disk, and it means no test depends on the real credentials file. Fail closed: the Admin menu never opens because something wasn't configured.

## US-08: the CLI asks too (T8.5)

**Decided (2026-09-23):** the CLI's rules follow the password screen, adapted to a terminal. See `flujo-fase3.md`, *Contraseña en el CLI*. Wrong: retry. Empty line or Ctrl+C: back to the start menu. Unreadable credentials: warn and go back, no retry.

**Hidden typing, and the Windows pitfall.** The password is read through an injected `entrada_oculta` (tests script it like `entrada`). Its default, `leer_contrasena`, uses `getpass` when stdin is a terminal and plain `input` when input is redirected. With redirected input nobody is typing, so there's nothing to hide. The fallback is also *needed*: on Windows `getpass` reads straight from the console keyboard and ignores redirected stdin, so a scripted run (like `test_logs.py`'s real `python -m` subprocess) hung until its timeout. On Linux, `getpass` already falls back to stdin with a warning, so the helper makes both platforms behave the same.

**Tests:** CLI tests use an `AuthFalso` (a duck-typed `comprobar` accepting a test password) instead of `Auth`: no files, no scrypt, and `Auth` already has its own tests. Every `TaximetroApp` in the tests passes an `entrada_oculta`, so none can reach the real `getpass` and wait on the keyboard.

## US-08: failed attempts are logged, not limited

**Decision (2026-09-23):** a wrong password shows «Contraseña incorrecta. Inténtalo de nuevo.» and logs `acceso_admin_denegado` (WARNING, without the typed text). There's no attempt counter, lockout or delay, in either the GUI or the CLI.

**Why:** the only way to guess is by hand, on the touch screen or at the CLI prompt, at human speed. An attack on the stolen file is already slowed by scrypt. A run of failures shows up in the log with a `grep`, which is where the technical team looks. `Auth` stays stateless: no counter, no clock, no extra message.

**Alternatives considered:** a 30 s in-memory lockout after 3 failures (needs state and an injected clock in `Auth`, plus a new message and tests); a fixed 1–2 s delay per failure (must use `after()`, not `sleep()`, or the screen freezes, and it adds little against a human).

## Structural refactor: a `ServicioTaximetro` façade between the interfaces and the domain

**Starting point (`fase-2`):** `Taximetro` already offers `iniciar_carrera`, `finalizar_carrera`, `cambiar_tarifa` and `resumen_del_dia`. But the CLI also holds **live `Carrera` objects** (it calls `carrera.cambiar_estado()` and reads `carrera.estado` and `importe_actual()`), and it builds `Tarifa(...)` itself and catches `TarifaInvalidaError`. An HTTP client can't hand back a live object, so this shape can't be swapped in Fase 4.

**Decision (2026-09-23):** a new class, `ServicioTaximetro` (`taximetro/servicio_taximetro.py`), is the **only** object the GUI and the CLI talk to. It wraps `Taximetro` and `Auth` and exposes intent-level methods: `iniciar_carrera`, `cambiar_estado`, `finalizar_carrera`, `estado_actual`, `tarifas`, `cambiar_tarifas(parado, en_movimiento)`, `resumen_del_dia`, `comprobar_contrasena`. It returns **data only**: an immutable snapshot of the ride, plain numbers and `ResumenDia`, never a `Carrera` or `Tarifa`. The interfaces import this module and nothing else from the domain (apart from `formato_euros`).

**Why:** it meets the brief's "cada componente […] poder modificarse o sustituirse sin afectar al resto" and US-09's "sin duplicarla" at the one boundary where they matter. In Fase 4 an HTTP client with the same methods and the same return types replaces it, and neither interface changes. Returning data instead of live objects is what makes that swap possible. `Taximetro` stays a pure domain object (state and rules); access control stays out of it.

**Alternatives considered:** growing `Taximetro` into the façade (one class fewer, but it would mix domain and access, and Fase 4 would have to imitate a stateful domain class); a new façade that still returns `Carrera` objects (fewer CLI changes, but it breaks the Fase 4 swap, the reason the façade exists).

## Refactor: the password gates the screen, not the service

**Decision (2026-09-23):** `ServicioTaximetro.comprobar_contrasena(texto) -> bool` delegates to `Auth` and logs `acceso_admin_concedido` / `acceso_admin_denegado`. On `True`, the interface shows the Admin menu. `cambiar_tarifas` and `resumen_del_dia` don't check anything themselves.

**Why:** simplest. It meets US-08's criterion ("solicita contraseña antes de permitir operaciones sensibles"), and in Fase 3 the interfaces are the only callers of the service. Logging inside the service means the GUI and the CLI can't disagree about the event names.

**Known limit, Fase 4:** once the service's methods are HTTP endpoints, anyone can call `cambiar_tarifas` directly, so the API needs its own authentication (e.g. a token issued on login). Decide it then. Considered and not taken now: an admin session in the service (`entrar_admin` / `salir_admin`, with `AccesoDenegadoError` otherwise), which adds session state and a close on every Volver; and passing the password on every call, which would keep it in memory for the whole Admin menu.

## Refactor: errors cross the boundary as the contract's own exceptions

**Decision (2026-09-23):** `servicio_taximetro.py` publishes the exceptions its methods can raise (e.g. `TarifaInvalidaError`, `CarreraActivaError`, `SinCarreraError`, and one error for a failed save to disk), and the interfaces import them from there, never from the domain modules. They are part of the contract, like the methods and return types. Each interface still writes its own driver-facing messages.

**Why:** it's what the CLI already does, so the refactor changes where the exceptions are imported from, not how errors are handled. In Fase 4 the HTTP client maps error responses back onto the same exceptions, and the interfaces don't notice. Wording stays in the interfaces, as `CLAUDE.md` requires.

**Alternatives considered:** result objects (`Resultado(ok, datos, error)`, fits HTTP well but is unidiomatic Python and rewrites all the CLI's error handling); the service returning final Spanish messages (no duplication, but it moves wording out of the interface layer).

## Refactor: closing a ride never fails because of the disk (T9.10)

**Decision (2026-09-23):** `finalizar_carrera()` returns `CarreraCerrada(carrera: InstantaneaCarrera, guardada: bool)` and does **not** raise when the history can't be written. `guardada=False` tells the interface to add its warning under the total. It still raises `SinCarreraError` when there is no ride. This is the one exception to the rule above. Every other failed read or write (`cambiar_tarifas`, `resumen_del_dia`) raises `AlmacenamientoError`, which wraps the original `OSError` in `__cause__`.

**Why:** closing and charging always succeed. By the time the save is attempted the ride is already closed and its total frozen (`decisions-fase2.md`). If this failure were an exception carrying the total inside it, an interface that forgot the `except` would never show the passenger the amount. As a return value it can't be skipped. Same behaviour as the Fase 2 CLI, which shows the total and then the warning.

**Also settled while building it:** the snapshot is `InstantaneaCarrera(id, estado, importe)` (nothing else is on screen). The rates come back as `TarifasVigentes(parado, en_movimiento)`, not as a `Tarifa`. `cambiar_estado(estado)` takes the target state, so each interface maps its single PARAR/ARRANCAR key to the opposite state. The service adds no log lines of its own for rides and fares, because the domain already logs each event where it happens. The one exception is US-08 access (see *`comprobar_contrasena` in the service* below).

**Wiring in one place (T9.11):** `ServicioTaximetro.por_defecto()` builds the real program: `Taximetro` with `config/tarifas.json` and `data/historial.csv`. Both entry points (the CLI's `__main__` and, later, `python -m taximetro`) call it, so neither interface imports `Taximetro`, `ConfigTarifas` or `Historial`, and they can't wire the domain differently. `TaximetroApp` now requires a `servicio`; there is no hidden in-memory default any more.

**Pitfall found while moving the CLI (T9.11):** the menu is drawn from a snapshot taken *before* waiting for input. Anything that shows the amount must ask again (`estado_actual()`), or the driver sees the amount from before they typed. A regression test covers *Ver importe*. The GUI has the same trap, because a snapshot never updates itself.

**Enforced by a test (T9.12):** `test_estructura.py` parses (with `ast`) every import in `taximetro_app.py` and in everything under `taximetro/gui/`, including screens that don't exist yet. From the `taximetro` package they may import only `servicio_taximetro`, `logs` and `utils`, plus their own package (the GUI screens among themselves). `ast` rather than a regex, so comments and strings are ignored, and imports inside functions, under `TYPE_CHECKING` or written as relative (`from ..carrera`) are still caught. The checker has its own tests with each way of sneaking a domain import in, so a broken checker can't pass silently.

## Refactor: Fase 4 replacement points are already in place

**Decision (2026-09-23):** no extra code for Fase 4. The replacement points are written down:

| Replaced in Fase 4 | By | Seam that already exists |
|---|---|---|
| `Historial` (CSV) | a database-backed class | injected into `Taximetro`'s constructor |
| `ConfigTarifas` (JSON) | a database-backed class | injected into `Taximetro`'s constructor |
| `ServicioTaximetro` (in-process) | an HTTP client with the same methods | the only object the interfaces use (see above) |

A replacement only has to offer the same methods with the same return types (duck typing). `test_estructura.py` already pins those names.

**Why:** YAGNI. The seams exist because of Fase 2's dependency injection. Formal `typing.Protocol` classes would be code nobody uses until Fase 4, and Fase 4 can add them when a second implementation actually exists.

## Module layout and entry points

**Decision (2026-09-23):**

```
taximetro/
    __main__.py              # python -m taximetro → the GUI (main interface)
    auth.py                  # Auth: scrypt hash check against config/credenciales.json
    servicio_taximetro.py    # ServicioTaximetro + its snapshot dataclass and contract exceptions
    taximetro_app.py         # CLI, unchanged location: python -m taximetro.taximetro_app
    gui/
        __init__.py
        app.py               # window, screen switching, report_callback_exception, configurar_logs()
        estilo.py            # the ttk.Style theme (colours, fonts, sizes from diseno-interfaz-fase3.md)
        inicio.py  contrasena.py  taximetro.py  administrador.py  tarifas.py  historico.py
config/
    credenciales.json        # committed: salt + hash of the Admin password
```

**Why:** one screen per file follows "una clase por fichero" and the phase's own "responsabilidades claramente delimitadas". `python -m taximetro` is the shortest command, so it goes to the main interface. The CLI stays where it is, which keeps the Fase 1/2 demo commands, the README and the test imports valid.

**Assumptions:** the snapshot dataclass and the contract exceptions live in `servicio_taximetro.py`, next to the class whose contract they are (as `ResumenDia` lives in `historial.py`). GUI tests mirror the package (`tests/gui/test_<pantalla>.py`), one test file per module as before.

**Alternatives considered:** one `interfaz_grafica.py` module (600–800 lines, against both conventions); moving the CLI to `taximetro/cli/` too (more symmetrical, but it changes the CLI's command and breaks the Fase 1/2 demo scripts).

## Order of work: refactor → US-08 → US-09

**Decision (2026-09-23):**

1. **Refactor.** Build `ServicioTaximetro` and move the CLI onto it **without changing its behaviour**. The existing CLI tests staying green prove the refactor broke nothing.
2. **US-08.** `Auth`, `comprobar_contrasena` on the service, and the password in front of the CLI's Admin. It's small, and it can be tested from the CLI before any GUI exists.
3. **US-09.** The GUI, built straight on the final contract, so nothing is rewired later.

**Why:** each step sits on a finished, tested base. Starting with US-08 would have meant wiring the CLI's password into `TaximetroApp` and then rewiring it into the service. Starting with the GUI would have left the password screen unconnected until the end.

## GUI skeleton (T9.3, T9.14)

**As built (2026-09-23):**

- **`App`** (`gui/app.py`) owns the `Tk` window (1280×800 minimum, title, background) and shows one `Pantalla` at a time. `mostrar(Tipo, **datos)` destroys the current screen and builds the next, and screens ask each other for navigation through it. The ✕ calls `al_cerrar_ventana()`, which just closes for now; T9.8 adds the "carrera en curso" confirmation there.
- **`Pantalla`** (`gui/pantalla.py`) is the base of every screen. It gives access to `app` and `servicio`, and `programar(ms, fn)` wraps `after()` so that **pending timers are cancelled when the screen is destroyed**. Otherwise the 200 ms refresh (T9.13) would keep calling widgets that no longer exist, raising `TclError` inside a callback, which tkinter swallows (see *Operation logs*).
- **`python -m taximetro`** (`taximetro/__main__.py`) calls `configurar_logs()` first, then `App(ServicioTaximetro.por_defecto()).ejecutar()`. It uses the same wiring as the CLI.
- **`inicio.py` is a placeholder** (title + Salir) so the window opens on something. T9.7 replaces it with the approved screen.
- **Tests** (`tests/gui/`, a package so names don't clash with `tests/`) use a hidden `Tk()` window injected into `App`. They never enter `mainloop()`: they call methods and process events with `update()`. Without a display the GUI tests are **skipped locally but fail in CI** (`CI` is set there), so a missing display can't silently hide them. CI installs `xvfb` and runs `xvfb-run -a pytest`.

## GUI theme and the touch key (T9.5)

**As built (2026-09-23):**

- **`gui/estilo.py` is the theme.** Every measure, colour and font comes from the approved mockup and lives there, so no screen carries loose values. Font sizes are in **pixels** (a negative size in tkinter), so they match the mockup's px on any screen. **`fuente(px)` raises below 24 px**, which enforces the minimum text rule in code rather than by review. Each vehicle state is defined as colour + text together (`ESTADOS`), so the state is never shown by colour alone.
- **`gui/tecla.py` → `Tecla`**, the touch key used by every screen. A `tk.Button` measures its height in text lines and takes one font, while the design needs a fixed pixel height and a smaller subtitle («FINALIZAR» / «Termina y muestra el total»). `Tecla` is a `Frame` of fixed height (**it raises below 88 px**) with title and optional subtitle, in four variants (green, red, grey, sidebar). It acts **on release over the key**, like a real button, so a finger that slides off cancels. `configurar()` switches PARAR ↔ ARRANCAR without rebuilding the key.
- **Assumption:** a pressed key turns slightly lighter (`aclarar`, 18 % towards white). The mockup has no pressed colour, and touch needs visible feedback.
- A screenshot of a sample window built from the theme was checked against the mockup (visor, lamps, state colours, keys, sidebar).

## Tracking: the refactor lives inside US-09

**Decision (2026-09-23):** no separate epic. The refactor is tasks **T9.10–T9.12** of US-09 ([#100](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/100)–[#102](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/102)), whose acceptance criterion ("se apoya en la lógica de backend ya existente sin duplicarla") is what it delivers. Also added: T9.13, the meter screen with its 200 ms refresh ([#103](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/103)), which had no task, and T9.14, `xvfb` in CI ([#104](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/104)). T8.2, T8.3 and T9.3 (#45, #46, #50) were reworded to match today's decisions. The work order above still applies: T9.10–T9.12 first, even though they're numbered inside US-09.

**Consequence:** at the demo, point to T9.10–T9.12 when the brief's "refactorización estructural" comes up, since the board has no column or epic named after it.
