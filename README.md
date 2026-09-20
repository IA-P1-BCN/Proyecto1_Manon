# 🚕 Taxímetro TTX-247

Taxímetro software para **TaxiTech Solutions**, en sustitución de los equipos físicos Hale T200 sin soporte desde 2023. Prototipo en Python con programación orientada a objetos.

**Estado:** Fase 1 (MVP en CLI) en desarrollo. Contexto completo del encargo en [`docs/project-brief.md`](docs/project-brief.md); tareas en [`Backlog.md`](Backlog.md) y en el [tablero del proyecto](https://github.com/orgs/IA-P1-BCN/projects/2).

## Tarifas vigentes

| Estado del taxi | Tarifa |
|---|---:|
| Parado o velocidad < 20 km/h | `0,02 €/segundo` |
| En movimiento | `0,05 €/segundo` |

El importe se acumula de forma continua según el tiempo transcurrido en cada estado.

## Requisitos

Python 3.10 o superior (desarrollado con 3.14, integración continua en 3.13). Solo librería estándar: el taxímetro no tiene dependencias de ejecución.

## Instalación

```bash
git clone https://github.com/IA-P1-BCN/Proyecto1_Manon.git
cd Proyecto1_Manon
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt   # solo para ejecutar los tests
```

## Uso

```bash
python -m taximetro.taximetro_app
```

La aplicación muestra al arrancar las instrucciones y las tarifas: no hace falta consultar esta página para usarla. Los comandos disponibles dependen de si hay una carrera en curso:

| Situación | Comandos |
|---|---|
| Sin carrera | `iniciar` · `ayuda` · `salir` |
| Carrera activa | `parado` · `movimiento` · `importe` · `finalizar` · `ayuda` |

El flujo completo, con todas sus ramas, está en [`docs/flujo-fase1.md`](docs/flujo-fase1.md).

## Tests

```bash
pytest                              # tests + cobertura (falla por debajo del 90 %)
pytest --cov-report=term-missing    # detalle de líneas sin cubrir
```

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/project-brief.md`](docs/project-brief.md) | Encargo del cliente, historias de usuario y fases |
| [`docs/flujo-fase1.md`](docs/flujo-fase1.md) | Diagrama y comportamiento del CLI de Fase 1 |
| [`docs/decisions-fase1-scaffold.md`](docs/decisions-fase1-scaffold.md) | Decisiones de diseño del código |
| [`docs/decisions-proceso.md`](docs/decisions-proceso.md) | Decisiones de proceso: idioma, ramas, CI, cobertura, tablero |
| [`docs/demo-fase1.md`](docs/demo-fase1.md) | Guion de la demo de Fase 1 |
| [`docs/future-implementation-ideas.md`](docs/future-implementation-ideas.md) | Ideas aplazadas y por qué |

---

*Este README se ampliará al cerrar la Fase 1 (T0.4).*
