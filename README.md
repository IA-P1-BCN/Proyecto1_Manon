# 🚕 Taxímetro TTX-247

Taxímetro software para **TaxiTech Solutions**, en sustitución de los equipos físicos Hale T200 sin soporte desde 2023. Prototipo en Python con programación orientada a objetos.

**Estado:** Fase 1 (MVP en CLI) completa — US-01 a US-04 — y en validación por el cliente. Fase 2 en curso en la rama `fase-2`: tarifas configurables (US-07) e histórico de carreras (US-05) hechos; logs (US-06) pendientes. Contexto completo del encargo en [`docs/project-brief.md`](docs/project-brief.md); tareas en [`Backlog.md`](Backlog.md) y en el [tablero del proyecto](https://github.com/orgs/IA-P1-BCN/projects/2).

## Tarifas vigentes

| Estado del taxi | Tarifa |
|---|---:|
| Parado o velocidad < 20 km/h | `0,02 €/segundo` |
| En movimiento | `0,05 €/segundo` |

El importe se acumula de forma continua según el tiempo transcurrido en cada estado. No se cobra por distancia.

Estas son las tarifas por defecto. Desde la Fase 2 se pueden cambiar desde el perfil Administrador o editando `config/tarifas.json` (ver [Tarifas configurables](#tarifas-configurables)).

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

No se escriben comandos: cada opción lleva un número y se teclea el número. Al arrancar se elige perfil: **Conductor** para cobrar carreras, **Administrador** para gestionar las tarifas y ver el histórico del día.

```
======================================================
  TAXÍMETRO TTX-247 · TaxiTech Solutions
======================================================
Tarifas vigentes:
  Parado o < 20 km/h ... 0,02 €/s
  En movimiento ........ 0,05 €/s

Escribe el número de la opción que quieras y pulsa Intro.
Al empezar, elige tu perfil: Conductor o Administrador.
Salir, en el menú de inicio, cierra el programa.

Conductor:
  Iniciar carrera    empieza una carrera nueva y cobra desde ese segundo
  Arrancar           el taxi se pone en movimiento
  Parar              el taxi se detiene
  Ver importe        muestra el importe acumulado
  Finalizar carrera  cierra la carrera y muestra el total
  Ayuda              vuelve a mostrar estas instrucciones
  Volver             vuelve al menú de inicio (sin carrera en curso)

Administrador:
  Cambiar tarifas    fija los €/s de cada estado, desde la próxima carrera
  Ver histórico      carreras terminadas hoy y total de caja
  Volver             vuelve al menú de inicio

======================================================

Menú de inicio
  1) Conductor
  2) Administrador
  3) Salir
> 1

Sin carrera
  1) Iniciar carrera
  2) Ayuda
  3) Volver
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
  3) Volver
```

En cada momento solo se ofrecen las opciones válidas, y **los números son propios de cada menú** (el `1` elige Conductor en el menú de inicio, inicia una carrera si no hay ninguna, y cambia el estado del vehículo si la hay):

| Situación | Nº | Opción | Qué hace |
|---|---:|---|---|
| Menú de inicio | 1 | Conductor | Entra en el taxímetro |
| | 2 | Administrador | Entra en la gestión: tarifas e histórico |
| | 3 | Salir | Cierra el programa |
| Sin carrera | 1 | Iniciar carrera | Empieza una carrera nueva y cobra desde ese segundo |
| | 2 | Ayuda | Reimprime las instrucciones |
| | 3 | Volver | Vuelve al menú de inicio |
| Carrera activa | 1 | Parar / Arrancar | Alterna el estado del vehículo; el menú ofrece siempre el contrario del actual |
| | 2 | Ver importe | Muestra el importe acumulado sin alterarlo |
| | 3 | Finalizar carrera | Cierra la carrera y muestra el total a cobrar |
| | 4 | Ayuda | Reimprime las instrucciones |
| Administrador | 1 | Cambiar tarifas | Pide las tarifas nuevas y las guarda |
| | 2 | Ver histórico | Carreras terminadas hoy y total de caja |
| | 3 | Volver | Vuelve al menú de inicio |

Con una carrera en curso no hay `Volver`: primero se finaliza. Así las tarifas nunca cambian a mitad de carrera.

La carrera nace **en movimiento**, porque se inicia cuando el taxi arranca con el pasajero dentro: cobra a 0,05 €/s desde el primer segundo. Si el taxi arranca detenido, el conductor pulsa `Parar`.

Cualquier otra cosa que se teclee —un número que no esté en el menú, una letra o una línea vacía— responde `Opción no válida. Elige un número del menú.` y deja la carrera intacta.

**Interrupciones.** `Ctrl+C` con una carrera abierta pregunta antes de salir, mientras el taxímetro sigue contando:

```
Vas a salir del programa con la carrera nº 1 en curso.
  1) Sí, finalizar la carrera y salir
  2) No, seguir con la carrera
```

*No* vuelve a la carrera como si nada. *Sí* la finaliza, la guarda en el histórico, muestra el total y cierra el programa. Un segundo `Ctrl+C` cuenta como *No*. Cerrar la entrada (`Ctrl+D`) durante una carrera la finaliza y muestra el total antes de salir, de modo que el importe nunca se pierde sin verse. Fuera de una carrera, `Ctrl+C` y `Ctrl+D` cierran el programa.

El flujo completo, con todas sus ramas, está en [`docs/flujo-fase1.md`](docs/flujo-fase1.md) (bucle de carreras) y [`docs/flujo-fase2.md`](docs/flujo-fase2.md) (perfiles, tarifas, histórico y `Ctrl+C`).

## Tarifas configurables

Desde el perfil **Administrador → Cambiar tarifas**:

```
Tarifas vigentes: parado 0,02 €/s · en movimiento 0,05 €/s
Nueva tarifa parado (€/s): 0,03
Nueva tarifa en movimiento (€/s): 0,06
Tarifas guardadas: parado 0,03 €/s · en movimiento 0,06 €/s. Se aplican desde la próxima carrera.
```

Cada tarifa debe ser mayor que 0 y como máximo 1,00 €/s, con 2 decimales como mucho, y la de parado no puede superar la de en movimiento. Si no se cumple, no se guarda nada.

Las tarifas viven en `config/tarifas.json` (en €/s), que también se puede editar a mano con el programa cerrado:

```json
{
  "parado": 0.02,
  "en_movimiento": 0.05
}
```

Si el fichero no existe, se crea al arrancar con las tarifas por defecto. Si no es válido, el programa arranca igualmente con las tarifas por defecto y deja el fichero como está para que se pueda corregir. [`config/tarifas.example.json`](config/tarifas.example.json) documenta el formato; el `tarifas.json` real no se versiona.

## Histórico de carreras

Cada carrera terminada se guarda en `data/historial.csv`, termine como termine (menú, `Ctrl+C` → *Sí* o `Ctrl+D`). Desde **Administrador → Ver histórico** se ven las de hoy y el total de caja:

```
Histórico de hoy · 21/09/2026
    Nº  Inicio    Fin          Importe
     1  08:00:00  08:01:00      3,00 €
     2  08:01:00  08:01:20      1,00 €
  2 carreras · Total del día: 4,00 €
```

Se guarda el importe cobrado, el mismo del ticket, así que el total del día cuadra con la caja. La numeración de carreras continúa de una sesión a otra. El fichero solo crece (una fila por carrera, nunca se reescribe), se puede abrir con una hoja de cálculo y no se versiona.

> En la Fase 2 el perfil Administrador **no tiene contraseña**. La protección llega con la US-08 (Fase 3).

## Tests

```bash
pytest                              # tests + cobertura (falla por debajo del 90 %)
pytest --cov-report=term-missing    # detalle de líneas sin cubrir
```

234 tests, 99 % de cobertura. La lógica de tarifas se comprueba contra los valores del briefing, y los relojes se inyectan, así que la batería corre en décimas de segundo sin esperar tiempo real.

## Estructura

```
taximetro/
    carrera.py          # Carrera: una carrera, su estado y su importe
    tarifa.py           # Tarifa: € por segundo según el estado, validadas
    config_tarifas.py   # ConfigTarifas: lee y guarda config/tarifas.json
    historial.py        # Historial: carreras terminadas en data/historial.csv
    taximetro.py        # Taximetro: carrera activa, tarifa y numeración
    taximetro_app.py    # TaximetroApp: menú de inicio y bucles de cada perfil
    utils.py            # formato_euros()
config/
    tarifas.example.json  # formato del fichero de tarifas
tests/                  # un fichero por módulo + conftest con relojes falsos
docs/                   # briefing, flujo, decisiones, demo
```

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/project-brief.md`](docs/project-brief.md) | Encargo del cliente, historias de usuario y fases |
| [`docs/flujo-fase1.md`](docs/flujo-fase1.md) | Diagrama y comportamiento del CLI de Fase 1 |
| [`docs/flujo-fase2.md`](docs/flujo-fase2.md) | Perfiles, tarifas, histórico y `Ctrl+C` en la Fase 2 |
| [`docs/decisions-fase2.md`](docs/decisions-fase2.md) | Decisiones de la Fase 2 |
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
