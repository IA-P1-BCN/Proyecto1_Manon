# 🚕 Taxímetro TTX-247

Taxímetro software para **TaxiTech Solutions**, en sustitución de los equipos físicos Hale T200 sin soporte desde 2023. Prototipo en Python con programación orientada a objetos.

**Estado:** Fase 1 (MVP en CLI) completa — US-01 a US-04 — y en validación por el cliente. Fase 2 (tarifas configurables, histórico y logs: US-05 a US-07) completa en la rama `fase-2`. Fase 3 (interfaz gráfica táctil, contraseña de Administrador y refactorización: US-08, US-09) completa en la rama `fase-3`, a falta de la prueba en pantalla táctil. Cada fase espera la validación de la anterior. Contexto completo del encargo en [`docs/project-brief.md`](docs/project-brief.md); tareas en [`Backlog.md`](Backlog.md) y en el [tablero del proyecto](https://github.com/orgs/IA-P1-BCN/projects/2).

## Tarifas vigentes

| Estado del taxi | Tarifa |
|---|---:|
| Parado o velocidad < 20 km/h | `0,02 €/segundo` |
| En movimiento | `0,05 €/segundo` |

El importe se acumula de forma continua según el tiempo transcurrido en cada estado. No se cobra por distancia.

Estas son las tarifas por defecto. Desde la Fase 2 se pueden cambiar desde el perfil Administrador o editando `config/tarifas.json` (ver [Tarifas configurables](#tarifas-configurables)).

## Requisitos

Python 3.10 o superior (desarrollado con 3.14, integración continua en 3.13). Solo librería estándar: el taxímetro no tiene dependencias de ejecución.

La interfaz gráfica usa `tkinter`, que viene con Python en Windows y macOS. En Linux puede hacer falta instalarlo aparte (`sudo apt install python3-tk`).

## Instalación

```bash
git clone https://github.com/IA-P1-BCN/Proyecto1_Manon.git
cd Proyecto1_Manon
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt   # solo para ejecutar los tests
```

## Uso

Hay dos formas de usar el taxímetro, sobre la misma lógica: la **interfaz gráfica** (la principal desde la Fase 3) y el **CLI**. Las dos se lanzan desde la raíz del repositorio, porque las tarifas, el histórico y los logs se guardan en `config/`, `data/` y `logs/` a partir de ahí.

### Interfaz gráfica (Fase 3)

```bash
python -m taximetro
```

Una ventana del tamaño de una tablet de 10" en horizontal (1280 × 800), pensada para el dedo: teclas grandes, el estado del taxi a la vista y el importe refrescándose solo.

- **Inicio.** Se elige **CONDUCTOR** (el taxímetro) o **ADMINISTRADOR** (tarifas e histórico; pide contraseña).
- **Taxímetro.** En **LIBRE**, una tecla: INICIAR CARRERA. En **OCUPADO**, el importe en dígitos de 7 segmentos, el estado en color y con su nombre (*EN MOVIMIENTO* en verde, *PARADO* en ámbar), y las teclas PARAR/ARRANCAR y FINALIZAR. A la derecha, el número de carrera, el tiempo y la hora de inicio.
- **FINALIZAR pregunta antes de cerrar**, y **el importe se congela al pulsar**: si se confirma, se cobra lo que marcaba en ese momento, no lo que se tarda en contestar. Si no, la carrera sigue. El total se queda en el visor (**TOTAL A COBRAR**) hasta la siguiente carrera.
- **Cerrar la ventana (✕) con una carrera en curso** hace la misma pregunta. Un segundo ✕ cuenta como *no*, para que un doble clic nervioso nunca termine una carrera.
- **Administrador.** Tras la contraseña: *Cambiar tarifas* (los campos vienen con las vigentes; mismos mensajes que el CLI) y *Ver histórico* (las carreras de hoy y el total de caja).

El detalle de cada pantalla está en [`docs/diseno-interfaz-fase3.md`](docs/diseno-interfaz-fase3.md), y cómo se enlazan, en [`docs/flujo-fase3.md`](docs/flujo-fase3.md).

### CLI

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
El perfil Administrador pide contraseña.
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
| | 2 | Administrador | Pide la contraseña y entra en la gestión: tarifas e histórico |
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

**Interrupciones.** `Ctrl+C` con una carrera abierta pregunta antes de salir, y el importe se **congela** en ese momento:

```
Vas a salir del programa con la carrera nº 1 en curso.
Importe a cobrar: 0,50 €
  1) Sí, finalizar la carrera y salir
  2) No, seguir con la carrera
```

*Sí* cobra el importe del momento del `Ctrl+C`, no lo que se tarda en contestar (Fase 3). *No* vuelve a la carrera como si nada, y ese tiempo sí se cobra, porque el taxi seguía ocupado. *Sí* la finaliza, la guarda en el histórico, muestra el total y cierra el programa. Un segundo `Ctrl+C` cuenta como *No*. Cerrar la entrada (`Ctrl+D`) durante una carrera la finaliza y muestra el total antes de salir, de modo que el importe nunca se pierde sin verse. Fuera de una carrera, `Ctrl+C` y `Ctrl+D` cierran el programa.

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

## Contraseña del Administrador

Desde la Fase 3 (US-08), elegir **Administrador** pide una contraseña. El perfil Conductor no la pide. La misma contraseña sirve en las dos interfaces:

- **Interfaz gráfica:** una pantalla con un campo que muestra `•` en lugar de lo tecleado, la tecla ENTRAR (o Intro) y *Cancelar* en el lateral.
- **CLI:** la pregunta `Contraseña (Intro vacío para volver):`, sin que se vea lo tecleado. Intro sin escribir nada, o `Ctrl+C`, vuelve al menú de inicio.

En las dos, una contraseña incorrecta avisa con «Contraseña incorrecta. Inténtalo de nuevo.» y deja volver a probar, y cada vez que se entra en Administrador se pide de nuevo.

**Contraseña de la demo: `taxi`.** Se da por facilitada por el equipo técnico del cliente, que es quien la pone y la cambia; la aplicación no tiene ninguna opción para cambiarla.

La contraseña **no se guarda en ningún sitio**: `config/credenciales.json` solo contiene una sal aleatoria y el hash `scrypt` de la contraseña, del que no se puede recuperar. Por eso ese fichero sí está en el repositorio. Si falta o está dañado, el Administrador no se abre («No se puede comprobar la contraseña. Avisa al equipo técnico.») y el perfil Conductor sigue funcionando. Los intentos quedan en el log (`acceso_admin_concedido` / `acceso_admin_denegado`), nunca lo que se tecleó.

## Logs de operación

El programa registra su actividad en `logs/taximetro.log`, sin mostrar nada en pantalla: está pensado para el equipo técnico. Una línea por evento, con fecha, nivel y datos en formato `clave=valor`:

```
2026-09-21 18:48:54 INFO taximetro.taximetro_app aplicacion_iniciada parado=0.02 movimiento=0.05
2026-09-21 18:48:54 INFO taximetro.carrera carrera_iniciada carrera=1 estado=en_movimiento tarifa=0.05
2026-09-21 18:49:54 INFO taximetro.carrera carrera_finalizada carrera=1 importe=3.00 duracion_s=60
2026-09-21 18:49:54 INFO taximetro.historial carrera_guardada carrera=1 importe=3.00 ruta=data/historial.csv
2026-09-21 18:50:02 WARNING taximetro.taximetro_app tarifa_rechazada tecleado='abc' motivo=no_numerica
2026-09-21 18:50:10 INFO taximetro.taximetro_app aplicacion_cerrada motivo=salir
```

| Nivel | Cuándo |
|---|---|
| `INFO` | Funcionamiento normal: arranque y cierre (con el motivo), perfil elegido, inicio, cambios de estado y fin de cada carrera, carrera guardada, tarifas cargadas o cambiadas |
| `WARNING` | Algo rechazado o ignorado: fichero de tarifas no válido, tarifa mal tecleada, fila ilegible en el histórico |
| `ERROR` | Un fichero que no se pudo escribir, o un error inesperado (con su traza) |

El fichero rota al llegar a 1 MB y se conservan 5 copias (`taximetro.log.1` … `.5`), así que nunca llena el disco. Si no se puede escribir, el taxímetro funciona igual, sin logs. No se versiona.

## Tests

```bash
pytest                              # tests + cobertura (falla por debajo del 90 %)
pytest --cov-report=term-missing    # detalle de líneas sin cubrir
```

Más de 600 tests, 99 % de cobertura. La lógica de tarifas se comprueba contra los valores del briefing, y los relojes se inyectan, así que la batería no espera tiempo real.

Los tests de la interfaz gráfica abren ventanas de verdad, así que necesitan pantalla. En el CI (Linux, sin pantalla) la pone `xvfb-run`. Además de comprobar el comportamiento, verifican que en ninguna pantalla se corte un texto ni se salga nada de su sitio, con la fuente del sistema y con la más ancha disponible.

## Estructura

```
taximetro/
    __main__.py              # python -m taximetro: arranca la interfaz gráfica
    carrera.py               # Carrera: una carrera, su estado y su importe
    tarifa.py                # Tarifa: € por segundo según el estado, validadas
    config_tarifas.py        # ConfigTarifas: lee y guarda config/tarifas.json
    historial.py             # Historial: carreras terminadas en data/historial.csv
    logs.py                  # configurar_logs(): logs/taximetro.log con rotación
    auth.py                  # Auth: comprueba la contraseña contra su hash scrypt
    taximetro.py             # Taximetro: carrera activa, tarifa y numeración
    servicio_taximetro.py    # ServicioTaximetro: lo único que usan las dos interfaces
    taximetro_app.py         # TaximetroApp: el CLI
    gui/                     # la interfaz gráfica (tkinter): una pantalla por módulo
    utils.py                 # formato_euros()
config/
    tarifas.example.json     # formato del fichero de tarifas
    credenciales.json        # sal y hash de la contraseña (nunca la contraseña)
tests/                       # un fichero por módulo; tests/gui/ para la interfaz gráfica
docs/                        # briefing, flujos, diseño, decisiones, demos
```

**Arquitectura (Fase 3).** Las dos interfaces hablan solo con `ServicioTaximetro`, que devuelve datos y nunca objetos vivos del dominio. Un test comprueba que ninguna interfaz importe nada más del dominio. En la Fase 4 ese servicio podrá sustituirse por un cliente de la API con los mismos métodos, sin tocar las pantallas.

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/project-brief.md`](docs/project-brief.md) | Encargo del cliente, historias de usuario y fases |
| [`docs/flujo-fase1.md`](docs/flujo-fase1.md) | Diagrama y comportamiento del CLI de Fase 1 |
| [`docs/flujo-fase2.md`](docs/flujo-fase2.md) | Perfiles, tarifas, histórico y `Ctrl+C` en la Fase 2 |
| [`docs/decisions-fase2.md`](docs/decisions-fase2.md) | Decisiones de la Fase 2 |
| [`docs/decisions-fase1-scaffold.md`](docs/decisions-fase1-scaffold.md) | Decisiones de diseño del código |
| [`docs/decisions-proceso.md`](docs/decisions-proceso.md) | Decisiones de proceso: idioma, ramas, CI, cobertura, tablero |
| [`docs/flujo-fase3.md`](docs/flujo-fase3.md) | Pantallas de la interfaz gráfica y cómo se enlazan |
| [`docs/diseno-interfaz-fase3.md`](docs/diseno-interfaz-fase3.md) | Diseño de cada pantalla: medidas, colores y textos |
| [`docs/decisions-fase3.md`](docs/decisions-fase3.md) | Decisiones de la Fase 3 |
| [`docs/demo-fase1.md`](docs/demo-fase1.md) | Guion de la demo de Fase 1 |
| [`docs/demo-fase3.md`](docs/demo-fase3.md) | Guion de la demo de Fase 3 |
| [`docs/future-implementation-ideas.md`](docs/future-implementation-ideas.md) | Ideas aplazadas y por qué |

## Siguientes fases

| Fase | Contenido |
|---|---|
| 🟡 Fase 2 | Histórico de carreras, logs de operación y tarifas configurables (US-05 a US-07) — hecha, en `fase-2` |
| 🟠 Fase 3 | Contraseña e interfaz gráfica táctil (US-08, US-09) — hecha, en `fase-3` |
| 🔴 Fase 4 | Base de datos, API REST y despliegue con un comando |
