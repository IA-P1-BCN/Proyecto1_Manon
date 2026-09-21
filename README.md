# 🚕 Taxímetro TTX-247

Taxímetro software para **TaxiTech Solutions**, en sustitución de los equipos físicos Hale T200 sin soporte desde 2023. Prototipo en Python con programación orientada a objetos.

**Estado:** Fase 1 (MVP en CLI) completa — US-01 a US-04. Contexto completo del encargo en [`docs/project-brief.md`](docs/project-brief.md); tareas en [`Backlog.md`](Backlog.md) y en el [tablero del proyecto](https://github.com/orgs/IA-P1-BCN/projects/2).

## Tarifas vigentes

| Estado del taxi | Tarifa |
|---|---:|
| Parado o velocidad < 20 km/h | `0,02 €/segundo` |
| En movimiento | `0,05 €/segundo` |

El importe se acumula de forma continua según el tiempo transcurrido en cada estado. No se cobra por distancia.

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

La aplicación muestra al arrancar las instrucciones y las tarifas: no hace falta consultar esta página para usarla.

No se escriben comandos: cada opción lleva un número y el conductor teclea el número.

```
======================================================
  TAXÍMETRO TTX-247 · TaxiTech Solutions
======================================================
Tarifas vigentes:
  Parado o < 20 km/h ... 0,02 €/s
  En movimiento ........ 0,05 €/s

Escribe el número de la opción que quieras y pulsa Intro.
El menú ofrece Arrancar o Parar según cómo esté el taxi.

Opciones:
  Iniciar carrera    empieza una carrera nueva y cobra desde ese segundo
  Arrancar           el taxi se pone en movimiento
  Parar              el taxi se detiene
  Ver importe        muestra el importe acumulado
  Finalizar carrera  cierra la carrera y muestra el total
  Ayuda              vuelve a mostrar estas instrucciones
  Salir              cierra el programa

======================================================

Sin carrera
  1) Iniciar carrera
  2) Ayuda
  3) Salir
> 1
Carrera nº 1 iniciada · EN MOVIMIENTO · 0,05 €/s

Carrera nº 1 en curso (EN MOVIMIENTO)
  1) Parar
  2) Ver importe
  3) Finalizar carrera
  4) Ayuda
> 1
PARADO · 1,50 € acumulado

Carrera nº 1 en curso (PARADO)
  1) Arrancar
  2) Ver importe
  3) Finalizar carrera
  4) Ayuda
> 2
Carrera nº 1 · PARADO · 1,90 € acumulado

Carrera nº 1 en curso (PARADO)
  1) Arrancar
  2) Ver importe
  3) Finalizar carrera
  4) Ayuda
> 3
TOTAL A COBRAR: 2,25 €

Sin carrera
  1) Iniciar carrera
  2) Ayuda
  3) Salir
```

Las opciones disponibles dependen de si hay una carrera en curso; en cada momento solo se ofrecen las válidas, y **los números son propios de cada menú** (el `1` inicia una carrera si no hay ninguna, y cambia el estado del vehículo si la hay):

| Situación | Nº | Opción | Qué hace |
|---|---:|---|---|
| Sin carrera | 1 | Iniciar carrera | Empieza una carrera nueva y cobra desde ese segundo |
| | 2 | Ayuda | Reimprime las instrucciones |
| | 3 | Salir | Cierra el programa |
| Carrera activa | 1 | Parar / Arrancar | Alterna el estado del vehículo; el menú ofrece siempre el contrario del actual |
| | 2 | Ver importe | Muestra el importe acumulado sin alterarlo |
| | 3 | Finalizar carrera | Cierra la carrera y muestra el total a cobrar |
| | 4 | Ayuda | Reimprime las instrucciones |

La carrera nace **en movimiento**, porque se inicia cuando el taxi arranca con el pasajero dentro: cobra a 0,05 €/s desde el primer segundo. Si el taxi arranca detenido, el conductor pulsa `Parar`.

Cualquier otra cosa que se teclee —un número que no esté en el menú, una letra o una línea vacía— responde `Opción no válida. Elige un número del menú.` y deja la carrera intacta.

**Interrupciones.** `Ctrl+C` con una carrera abierta no cierra el programa: avisa de que hay que finalizar primero, para que una carrera solo termine de forma deliberada. Cerrar la entrada (`Ctrl+D`) durante una carrera la finaliza y muestra el total antes de salir, de modo que el importe nunca se pierde sin verse.

El flujo completo, con todas sus ramas, está en [`docs/flujo-fase1.md`](docs/flujo-fase1.md).

## Tests

```bash
pytest                              # tests + cobertura (falla por debajo del 90 %)
pytest --cov-report=term-missing    # detalle de líneas sin cubrir
```

109 tests, 98 % de cobertura. La lógica de tarifas se comprueba contra los valores del briefing, y los relojes se inyectan, así que la batería corre en décimas de segundo sin esperar tiempo real.

## Estructura

```
taximetro/
    carrera.py          # Carrera: una carrera, su estado y su importe
    tarifa.py           # Tarifa: € por segundo según el estado
    taximetro.py        # Taximetro: carrera activa, tarifa y numeración
    taximetro_app.py    # TaximetroApp: bucle CLI
    utils.py            # formato_euros()
tests/                  # un fichero por módulo + conftest con relojes falsos
docs/                   # briefing, flujo, decisiones, demo
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

## Siguientes fases

| Fase | Contenido |
|---|---|
| 🟡 Fase 2 | Histórico de carreras, logs de operación y tarifas configurables (US-05 a US-07) |
| 🟠 Fase 3 | Contraseña e interfaz gráfica táctil (US-08, US-09) |
| 🔴 Fase 4 | Base de datos, API REST y despliegue con un comando |
