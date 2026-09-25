[🇬🇧 English](README.md) · 🇪🇸 **Español**

# 🚕 Taxímetro TTX-247

Taxímetro software para un cliente ficticio, **TaxiTech Solutions**, cuyos equipos físicos (Hale T200) llevan sin soporte desde 2023. Proyecto de curso en Python con programación orientada a objetos, construido por fases, cada una con su demo.

Está pensado para leerse, no para cobrar carreras de verdad: lo que interesa aquí es **cómo está construido** y **cómo se ha trabajado** (las dos últimas secciones antes del índice de documentación).

![La interfaz gráfica del taxímetro durante una carrera](docs/img/gui-ride.png)

*La interfaz gráfica en plena carrera: carrera nº 1, taxi ocupado y en movimiento, con el importe subiendo a 0,05 €/s.*

## 📍 Estado

| Fase | Contenido | Estado |
|---|---|---|
| 1 | MVP en línea de comandos: iniciar, parar/arrancar y finalizar carrera, con el importe (US-01 a US-04) | ✅ Congelada en la rama `fase-1` para la demo |
| 2 | Tarifas configurables, histórico de carreras y logs (US-05 a US-07) | ✅ |
| 3 | Contraseña de Administrador, interfaz gráfica táctil y refactorización (US-08, US-09) | ✅ |
| 4 | Base de datos, API REST y despliegue con un comando | ⏳ Sin empezar |

Las fases 1 a 3 están en la rama `dev`. El encargo original del cliente está en [`docs/project-brief.md`](docs/project-brief.md); las tareas, en [`Backlog.md`](Backlog.md) y en el [tablero del proyecto](https://github.com/orgs/IA-P1-BCN/projects/2).

## 🧾 Qué hace

El importe se acumula de forma continua según el **tiempo** que el taxi pasa en cada estado (no por distancia):

| Estado del taxi | Tarifa |
|---|---:|
| Parado o velocidad < 20 km/h | `0,02 €/segundo` |
| En movimiento | `0,05 €/segundo` |

Hay dos perfiles: **Conductor** (cobra carreras) y **Administrador** (cambia tarifas y consulta el histórico del día; pide contraseña). Se puede usar desde una **interfaz gráfica** táctil o desde un **CLI**, las dos sobre la misma lógica.

## ▶️ Probarlo

Requisitos: Python 3.10 o superior, solo librería estándar (la interfaz gráfica usa `tkinter`, que ya viene con Python en Windows y macOS; en Linux, `sudo apt install python3-tk`).

```bash
git clone https://github.com/IA-P1-BCN/Proyecto1_Manon.git
cd Proyecto1_Manon
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt    # solo hace falta para los tests

python -m taximetro                    # interfaz gráfica
python -m taximetro.taximetro_app      # CLI
```

Se ejecuta desde la raíz del repositorio, porque las tarifas, el histórico y los logs se guardan en `config/`, `data/` y `logs/`. Para entrar como Administrador, la contraseña de la demo es **`taxi`**.

Para una visita guiada con lo que hay que pulsar y lo que debería verse, están los guiones de demo: [fase 1](docs/demo-fase1.md), [fase 2](docs/demo-fase2.md) y [fase 3](docs/demo-fase3.md).

## 🧪 Tests

```bash
pytest
```

Más de 600 tests con un 99 % de cobertura; por debajo del 90 % la ejecución falla. Los relojes se inyectan, así que la batería no espera tiempo real. Los tests de la interfaz gráfica abren ventanas de verdad (en el CI las pone `xvfb-run`) y comprueban que ninguna pantalla corta un texto ni se sale de su sitio.

## 🏗️ Cómo está hecho

```
taximetro/
    carrera.py, tarifa.py      # dominio: una carrera y su importe, € por segundo según estado
    taximetro.py               # carrera activa, tarifa y relojes
    config_tarifas.py          # tarifas en config/tarifas.json
    historial.py               # carreras terminadas en data/historial.csv
    auth.py                    # contraseña comprobada contra un hash scrypt
    logs.py                    # logs/taximetro.log con rotación
    servicio_taximetro.py      # lo único que usan las dos interfaces
    taximetro_app.py           # interfaz CLI
    gui/                       # interfaz gráfica (tkinter), una pantalla por módulo
tests/                         # un fichero por módulo
docs/                          # briefing, flujos, diseño, decisiones, demos
```

Decisiones que conviene conocer:

- **Una lógica, dos interfaces.** El CLI y la GUI hablan solo con `ServicioTaximetro`, que devuelve datos y nunca objetos vivos del dominio. Un test falla si una interfaz importa algo más. En la Fase 4 ese servicio se podrá sustituir por un cliente de la API sin tocar las pantallas.
- **Dos relojes inyectados.** Uno monótono para calcular el importe (un reloj de pared puede saltar hacia atrás y cobrar de menos) y otro de calendario para las horas de inicio y fin. Por eso los tests son rápidos y deterministas.
- **La contraseña no se guarda.** `config/credenciales.json` solo contiene una sal y el hash `scrypt`, por lo que puede estar en el repositorio.
- **El importe se congela al pulsar Finalizar.** Se cobra lo que marcaba en ese instante, no lo que se tarda en confirmar.
- **Una clase por fichero**, vocabulario del dominio en español y formato de importes en un único sitio (`utils.formato_euros`).

## 🛠️ Cómo trabajo

- **Una rama por historia de usuario** desde `dev`, con PR y CI en verde antes de fusionar; `main` solo recibe una versión demostrable por fase. Cada fase queda congelada en su rama (`fase-1`, `fase-2`, `fase-3`) como punto de referencia de su demo.
- **Commits convencionales** que citan la historia o tarea (`feat(carrera): ... (US-02)`).
- **Tests a la vez que el código**, con puerta de cobertura del 90 % en el CI (GitHub Actions).
- **Las decisiones se escriben** antes de cambiar el comportamiento, con su porqué y lo que se descartó, y las ideas aplazadas se apuntan en lugar de implementarse.
- **Tablero de GitHub Projects** con una columna por fase, como pedía el cliente, y un campo `Progreso` para el día a día.

## 📚 Documentación

| Para qué | Dónde |
|---|---|
| El encargo del cliente | [`docs/project-brief.md`](docs/project-brief.md) |
| Cómo se comporta cada interfaz | [`docs/flujo-fase1.md`](docs/flujo-fase1.md), [`flujo-fase2.md`](docs/flujo-fase2.md), [`flujo-fase3.md`](docs/flujo-fase3.md) y el diseño de pantallas [`diseno-interfaz-fase3.md`](docs/diseno-interfaz-fase3.md) |
| Por qué se hizo así | [`decisions-fase1-scaffold.md`](docs/decisions-fase1-scaffold.md), [`decisions-fase2.md`](docs/decisions-fase2.md), [`decisions-fase3.md`](docs/decisions-fase3.md) |
| Cómo se organiza el proyecto | [`docs/decisions-proceso.md`](docs/decisions-proceso.md) |
| Qué se dejó para más adelante | [`docs/future-implementation-ideas.md`](docs/future-implementation-ideas.md) |
