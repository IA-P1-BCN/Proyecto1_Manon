🇬🇧 **English** · [🇪🇸 Español](README.es.md)

# 🚕 TTX-247 Taxímetro

A software taxi meter for a fictional client, **TaxiTech Solutions**, whose physical Hale T200 units have been unsupported since 2023. A course project in Python, object-oriented, built in phases with a demo at the end of each.

It is meant to be **read, not used to charge real rides**: what matters here is **how it is built** and **how the work is run** (the last two sections before the documentation index).

![The taxímetro GUI during a ride](docs/img/gui-ride.png)

*The GUI mid-ride: ride nº 1, taxi occupied and moving, amount ticking at €0.05/s. The interface text is in Spanish because the client is in Madrid.*

## 📍 Status

| Phase | Content | Status |
|---|---|---|
| 1 | Command-line MVP: start, stop/go and finish a ride, with the amount (US-01 to US-04) | ✅ Frozen in the `fase-1` branch for the demo |
| 2 | Configurable fares, ride history and logs (US-05 to US-07) | ✅ |
| 3 | Admin password, touch GUI and refactoring (US-08, US-09) | ✅ |
| 4 | Database, REST API and one-command deploy | ⏳ Not started |

Phases 1 to 3 are in the `dev` branch. The client's original brief is in [`docs/project-brief.md`](docs/project-brief.md) (Spanish); tasks are in [`Backlog.md`](Backlog.md) and on the [project board](https://github.com/orgs/IA-P1-BCN/projects/2).

## 🧾 What it does

The amount accrues continuously according to the **time** the taxi spends in each state (not by distance):

| Taxi state | Rate |
|---|---:|
| Stopped, or speed < 20 km/h | `€0.02 / second` |
| Moving | `€0.05 / second` |

There are two profiles: **Driver** (charges rides) and **Administrator** (changes fares and views today's history; password protected). It can be used from a touch **GUI** or from a **CLI**, both on top of the same logic.

## ▶️ Try it

Requirements: Python 3.10 or later, standard library only (the GUI uses `tkinter`, which ships with Python on Windows and macOS; on Linux, `sudo apt install python3-tk`).

```bash
git clone https://github.com/IA-P1-BCN/Proyecto1_Manon.git
cd Proyecto1_Manon
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt    # only needed for the tests

python -m taximetro                    # graphical interface
python -m taximetro.taximetro_app      # CLI
```

Run it from the repository root: fares, history and logs are stored in `config/`, `data/` and `logs/` relative to it. To enter as Administrator, the demo password is **`taxi`**.

For a guided tour with what to press and what you should see, there are demo scripts (in Spanish): [phase 1](docs/demo-fase1.md), [phase 2](docs/demo-fase2.md) and [phase 3](docs/demo-fase3.md).

## 🧪 Tests

```bash
pytest
```

600+ tests with 99% coverage; the run fails below 90%. Clocks are injected, so the suite never waits in real time. The GUI tests open real windows (CI provides a display with `xvfb-run`) and check that no screen cuts off a text or pushes anything out of place.

## 🏗️ How it's built

```
taximetro/
    carrera.py, tarifa.py      # domain: one ride and its amount, € per second by state
    taximetro.py               # active ride, fare and clocks
    config_tarifas.py          # fares in config/tarifas.json
    historial.py               # finished rides in data/historial.csv
    auth.py                    # password checked against a scrypt hash
    logs.py                    # logs/taximetro.log with rotation
    servicio_taximetro.py      # the only thing both interfaces use
    taximetro_app.py           # CLI interface
    gui/                       # graphical interface (tkinter), one screen per module
tests/                         # one file per module
docs/                          # brief, flows, design, decisions, demos
```

Decisions worth knowing about:

- **One logic, two interfaces.** The CLI and the GUI talk only to `ServicioTaximetro`, which returns data and never live domain objects. A test fails if an interface imports anything else. In Phase 4 that service can be swapped for an API client without touching the screens.
- **Two injected clocks.** A monotonic one to compute the amount (a wall clock can jump backwards and undercharge) and a calendar one for start and end times. This is what keeps the tests fast and deterministic.
- **The password is never stored.** `config/credenciales.json` holds only a salt and the `scrypt` hash, so it can live in the repository.
- **The amount freezes when you press Finish.** The rider pays what the meter showed at that instant, not what it showed by the time they confirmed.
- **One class per file**, domain vocabulary in Spanish, and money formatting in a single place (`utils.formato_euros`).

## 🛠️ How I work

- **One branch per user story** off `dev`, with a PR and green CI before merging; `main` only receives a demoable version per phase. Each phase is frozen in its own branch (`fase-1`, `fase-2`, `fase-3`) as a reference point for its demo.
- **Conventional Commits** that cite the story or task (`feat(carrera): ... (US-02)`).
- **Tests written alongside the code**, with a 90% coverage gate in CI (GitHub Actions).
- **Decisions are written down** before behaviour changes, with the reasoning and what was rejected; postponed ideas are recorded instead of implemented.
- **GitHub Projects board** with one column per phase, as the client required, and a `Progreso` field for day-to-day tracking.

## 📚 Documentation

Most design documents are in Spanish (they are client-facing); the `decisions-*` notes are in English.

| For | Where |
|---|---|
| The client's brief | [`docs/project-brief.md`](docs/project-brief.md) |
| How each interface behaves | [`docs/flujo-fase1.md`](docs/flujo-fase1.md), [`flujo-fase2.md`](docs/flujo-fase2.md), [`flujo-fase3.md`](docs/flujo-fase3.md) and the screen design [`diseno-interfaz-fase3.md`](docs/diseno-interfaz-fase3.md) |
| Why it was done this way | [`decisions-fase1-scaffold.md`](docs/decisions-fase1-scaffold.md), [`decisions-fase2.md`](docs/decisions-fase2.md), [`decisions-fase3.md`](docs/decisions-fase3.md) |
| How the project is run | [`docs/decisions-proceso.md`](docs/decisions-proceso.md) |
| What was postponed | [`docs/future-implementation-ideas.md`](docs/future-implementation-ideas.md) |
