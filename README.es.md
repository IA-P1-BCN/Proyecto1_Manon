[🇬🇧 English](README.md) · 🇪🇸 **Español**

# 🚕 Taxímetro TTX-247

<p align="center">
  <img src="docs/img/taxi-8bit.gif" alt="Un taxi amarillo de 8 bits circulando por una ciudad" width="480" />
</p>

## 📑 Contenido

- [¿Qué es?](#que-es)
- [¿Qué puedo hacer con él?](#que-puedo-hacer-con-el)
- [Estado](#estado)
- [¿Cómo puedo probarlo?](#como-puedo-probarlo)
- [Cómo está construido](#como-esta-construido)
  - [Tecnologías](#tecnologias)
  - [Arquitectura](#arquitectura)
  - [Decisiones de diseño](#decisiones-de-diseno)
- [Cómo trabajo](#como-trabajo)
- [Documentación](#documentacion)
- [Autor](#autor)
- [Licencia](#licencia)

<a id="que-es"></a>
## ❓ ¿Qué es?

Un taxímetro software. El cliente ficticio, **TaxiTech Solutions**, tiene taxis con taxímetros físicos Hale T200 que llevan sin soporte desde 2023 y no dejan de fallar. Este proyecto los sustituye por un programa que cobra la carrera por el **tiempo** que el taxi pasa en cada estado, no por distancia:

| Estado del taxi | Tarifa |
|---|---:|
| Parado o velocidad < 20 km/h | `0,02 €/segundo` |
| En movimiento | `0,05 €/segundo` |

Es un proyecto de curso, construido por fases con una demo al final de cada una. Está pensado para **leerse, no para cobrar carreras de verdad**.

<a id="que-puedo-hacer-con-el"></a>
## ✨ ¿Qué puedo hacer con él?

![La interfaz gráfica del taxímetro durante una carrera](docs/img/gui-ride.png)

*La interfaz gráfica en plena carrera: carrera nº 1, taxi ocupado y en movimiento, con el importe subiendo a 0,05 €/s.*

- **Cobrar una carrera como conductor:** iniciarla, alternar entre parado y en movimiento, ver cómo crece el importe en tiempo real y finalizarla para obtener el total.
- **No perder una carrera por descuido:** finalizar (o cerrar la ventana) pide confirmación, y el importe se congela en el momento de pulsar.
- **Gestionarlo como administrador** (con contraseña): cambiar las tarifas y ver las carreras de hoy con el total de caja.
- **Usarlo de dos formas:** una **interfaz gráfica** táctil o un **CLI**, las dos sobre la misma lógica.
- **Dejar constancia:** cada carrera terminada se guarda en un histórico CSV, y todo lo que ocurre se escribe en un fichero de logs con rotación.

<a id="estado"></a>
## 📊 Estado

| | |
|---|---|
| **Compilación** | ![CI](https://img.shields.io/github/actions/workflow/status/IA-P1-BCN/Proyecto1_Manon/tests.yml?branch=dev&label=CI&logo=githubactions&logoColor=white) ![Último commit](https://img.shields.io/github/last-commit/IA-P1-BCN/Proyecto1_Manon/dev?label=%C3%BAltimo%20commit) |
| **Calidad** | ![Cobertura](https://img.shields.io/badge/cobertura-99.7%25-brightgreen) ![Tests](https://img.shields.io/badge/tests-635%20pasan-brightgreen) ![Umbral de cobertura](https://img.shields.io/badge/umbral%20de%20cobertura-%E2%89%A5%2090%25-blue) |
| **Paquetes** | ![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white) ![pytest](https://img.shields.io/badge/pytest-9.1.1-0A9EDC?logo=pytest&logoColor=white) ![pytest-cov](https://img.shields.io/badge/pytest--cov-7.1.0-0A9EDC?logo=pytest&logoColor=white) ![Dependencias de ejecución](https://img.shields.io/badge/dependencias%20de%20ejecuci%C3%B3n-ninguna-brightgreen) |
| **Progreso** | ![Fase](https://img.shields.io/badge/fase-3%20de%204-orange) ![Issues cerradas](https://img.shields.io/github/issues-closed/IA-P1-BCN/Proyecto1_Manon?label=issues%20cerradas) ![PRs cerradas](https://img.shields.io/github/issues-pr-closed/IA-P1-BCN/Proyecto1_Manon?label=PRs%20cerradas) |
| **Licencia** | ![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-green) |

*La cobertura y el número de tests son una foto del 25/09/2026 (`pytest`); el CI, el último commit, las issues y las PRs se actualizan solos. La ejecución falla por debajo del 90 % de cobertura.*

| Fase | Contenido | Estado |
|---|---|---|
| 1 | MVP en línea de comandos: iniciar, parar/arrancar y finalizar carrera, con el importe (US-01 a US-04) | ✅ Congelada en la rama `fase-1` para la demo |
| 2 | Tarifas configurables, histórico de carreras y logs (US-05 a US-07) | ✅ |
| 3 | Contraseña de Administrador, interfaz gráfica táctil y refactorización (US-08, US-09) | ✅ |
| 4 | Base de datos, API REST y despliegue con un comando | ⏳ Sin empezar |

Las fases 1 a 3 están en la rama `dev`. El encargo original del cliente está en [`docs/project-brief.md`](docs/project-brief.md); las tareas, en [`Backlog.md`](Backlog.md) y en el [tablero del proyecto](https://github.com/orgs/IA-P1-BCN/projects/2).

<a id="como-puedo-probarlo"></a>
## ▶️ ¿Cómo puedo probarlo?

Requisitos: Python 3.10 o superior. La aplicación usa solo la librería estándar; la interfaz gráfica usa `tkinter`, que ya viene con Python en Windows y macOS (en Linux: `sudo apt install python3-tk`).

```bash
git clone https://github.com/IA-P1-BCN/Proyecto1_Manon.git
cd Proyecto1_Manon
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt    # solo hace falta para los tests

python -m taximetro                    # interfaz gráfica
python -m taximetro.taximetro_app      # CLI
pytest                                 # los tests
```

Se ejecuta desde la raíz del repositorio, porque las tarifas, el histórico y los logs se guardan en `config/`, `data/` y `logs/`. Para entrar como Administrador, la contraseña de la demo es **`taxi`**.

Para una visita guiada con lo que hay que pulsar y lo que debería verse, están los guiones de demo: [fase 1](docs/demo-fase1.md), [fase 2](docs/demo-fase2.md) y [fase 3](docs/demo-fase3.md). Los tests de la interfaz gráfica abren ventanas de verdad (en el CI las pone `xvfb-run`) y comprueban que ninguna pantalla corta un texto ni se sale de su sitio.

<a id="como-esta-construido"></a>
## 🏗️ Cómo está construido

<a id="tecnologias"></a>
### Tecnologías

<p>
  <img src="https://skillicons.dev/icons?i=python,git,github,githubactions" alt="Python, Git, GitHub, GitHub Actions" />
  <br />
  <img src="https://img.shields.io/badge/tkinter-GUI-3776AB?logo=python&logoColor=white" alt="tkinter" />
  <img src="https://img.shields.io/badge/pytest-tests-0A9EDC?logo=pytest&logoColor=white" alt="pytest" />
</p>

- **Python**, orientado a objetos, solo con la librería estándar en ejecución (`hashlib.scrypt` para la contraseña, `csv` para el histórico, `logging` para los logs).
- **tkinter** para la interfaz gráfica táctil.
- **pytest** y **pytest-cov** para más de 600 tests con un 99 % de cobertura.
- **Git y GitHub**, con **GitHub Actions** ejecutando los tests en cada push y pull request (con `xvfb` para dar pantalla a los tests de la interfaz).

<a id="arquitectura"></a>
### Arquitectura

```
Proyecto1_Manon/
├── taximetro/                    # la aplicación
│   ├── carrera.py                # una carrera, su estado y su importe
│   ├── tarifa.py                 # € por segundo según el estado, validadas
│   ├── taximetro.py              # carrera activa, tarifa y relojes inyectados
│   ├── config_tarifas.py         # tarifas en config/tarifas.json
│   ├── historial.py              # carreras terminadas en data/historial.csv
│   ├── auth.py                   # contraseña comprobada contra un hash scrypt
│   ├── logs.py                   # logs/taximetro.log con rotación
│   ├── servicio_taximetro.py     # lo único que usan las dos interfaces
│   ├── taximetro_app.py          # interfaz CLI
│   ├── utils.py                  # formato de euros
│   ├── __main__.py               # python -m taximetro → la interfaz gráfica
│   └── gui/                      # interfaz gráfica (tkinter), una pantalla por módulo
├── tests/                        # un fichero por módulo (tests/gui/ para la interfaz)
├── config/                       # formato del fichero de tarifas, sal y hash de la contraseña
├── docs/                         # briefing, flujos, diseño, decisiones, guiones de demo
├── .github/workflows/tests.yml   # CI: pytest + cobertura
├── Backlog.md                    # tareas, enlazadas a las issues de GitHub
├── pyproject.toml                # configuración de pytest y cobertura
└── requirements-dev.txt          # dependencias de los tests
```

<a id="decisiones-de-diseno"></a>
### Decisiones de diseño

- **Una lógica, dos interfaces.** El CLI y la GUI hablan solo con `ServicioTaximetro`, que devuelve datos y nunca objetos vivos del dominio. Un test falla si una interfaz importa algo más. En la Fase 4 ese servicio se podrá sustituir por un cliente de la API sin tocar las pantallas.
- **Dos relojes inyectados.** Uno monótono para calcular el importe (un reloj de pared puede saltar hacia atrás y cobrar de menos) y otro de calendario para las horas de inicio y fin. Por eso los tests son rápidos y deterministas.
- **La contraseña no se guarda.** `config/credenciales.json` solo contiene una sal y el hash `scrypt`, por lo que puede estar en el repositorio.
- **El importe se congela al pulsar Finalizar.** Se cobra lo que marcaba en ese instante, no lo que se tarda en confirmar.
- **Una clase por fichero**, vocabulario del dominio en español y formato de importes en un único sitio (`utils.formato_euros`).

<a id="como-trabajo"></a>
## 🛠️ Cómo trabajo

- **Una rama por historia de usuario** desde `dev`, con PR y CI en verde antes de fusionar; `main` solo recibe una versión demostrable por fase. Cada fase queda congelada en su rama (`fase-1`, `fase-2`, `fase-3`) como punto de referencia de su demo.
- **Commits convencionales** que citan la historia o tarea (`feat(carrera): ... (US-02)`).
- **Tests a la vez que el código**, con puerta de cobertura del 90 % en el CI.
- **Las decisiones se escriben** antes de cambiar el comportamiento, con su porqué y lo que se descartó, y las ideas aplazadas se apuntan en lugar de implementarse.
- **Tablero de GitHub Projects** con una columna por fase, como pedía el cliente, y un campo `Progreso` para el día a día.

<a id="documentacion"></a>
## 📚 Documentación

| Para qué | Dónde |
|---|---|
| El encargo del cliente | [`docs/project-brief.md`](docs/project-brief.md) |
| Cómo se comporta cada interfaz | [`docs/flujo-fase1.md`](docs/flujo-fase1.md), [`flujo-fase2.md`](docs/flujo-fase2.md), [`flujo-fase3.md`](docs/flujo-fase3.md) y el diseño de pantallas [`diseno-interfaz-fase3.md`](docs/diseno-interfaz-fase3.md) |
| Por qué se hizo así | [`decisions-fase1-scaffold.md`](docs/decisions-fase1-scaffold.md), [`decisions-fase2.md`](docs/decisions-fase2.md), [`decisions-fase3.md`](docs/decisions-fase3.md) |
| Cómo se organiza el proyecto | [`docs/decisions-proceso.md`](docs/decisions-proceso.md) |
| Qué se dejó para más adelante | [`docs/future-implementation-ideas.md`](docs/future-implementation-ideas.md) |

<a id="autor"></a>
## 👤 Autor

**[Manon](https://github.com/ManonChab)**: diseño, código, tests y documentación.

<a id="licencia"></a>
## 📄 Licencia

Publicado bajo la [licencia MIT](LICENSE): se puede usar, copiar, modificar y compartir, siempre que se mantenga el aviso de copyright.
