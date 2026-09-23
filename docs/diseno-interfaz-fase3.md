# Diseño de la interfaz — Fase 3

Especificación visual de la interfaz gráfica del taxímetro (**US-09**) y de la pantalla de contraseña (**US-08**). Es la referencia con la que se comprueba cada pantalla al programarla, igual que [`flujo-fase1.md`](flujo-fase1.md) lo fue para el CLI.

- Cómo se enlazan las pantallas: [`flujo-fase3.md`](flujo-fase3.md).
- Por qué se decidió cada cosa: [`decisions-fase3.md`](decisions-fase3.md).
- Requisitos del cliente: [`project-brief.md`](project-brief.md), sección *Fase 3*.

**Cómo se rellena:** cada decisión visual se prueba primero en una maqueta HTML con el tamaño de una tablet. Solo cuando se aprueba se copia aquí. Las secciones marcadas **Pendiente** aún no están decididas.

---

## Requisitos que debe cumplir (del briefing)

| Requisito del cliente | Dónde se resuelve en este documento |
|---|---|
| Funcional en una tablet montada en el vehículo | *Dispositivo y orientación* |
| Botones grandes, interacción táctil cómoda | *Reglas de diseño táctil* |
| Estado del taxi visible de un vistazo | *Colores y estados* |
| Importe actualizado en tiempo real | *Pantalla de carrera activa* |
| La interfaz no se bloquea nunca | *Comportamiento* (y `decisions-fase3.md`) |
| Acceso protegido por contraseña | *Pantalla de contraseña* |
| La UI usa la lógica ya existente, sin duplicarla (US-09) | Fuera de este documento: `decisions-fase3.md`, *Structural refactor* |

---

## Dispositivo y orientación

**Decidido:** la interfaz se ejecuta en un portátil (desarrollo y demo), dentro de una ventana con el tamaño de una **tablet de 10" en horizontal**. Todo se diseña con reglas táctiles: se pulsa con el dedo, no se hace clic con el ratón.

**Resolución de referencia: 1280 × 800 px, horizontal.** Es la más habitual en tablets de 10" y cabe en la pantalla de un portátil sin desplazamiento.

Pendiente:
- ¿Debe funcionar también en móvil (la US-09 dice "móvil o tablet")?

## Reglas de diseño táctil

| Elemento | Medida | Por qué |
|---|---|---|
| Zona táctil mínima (cualquier botón) | **88 px** (≈ 15 mm en una tablet de 10") | Tablet fija en el salpicadero, a un brazo de distancia y con el coche en marcha: más margen que los 48 px de un móvil en la mano |
| Botones principales (Iniciar, Parar/Arrancar, Finalizar) | **≥ 120 px de alto**, todo el ancho de su columna | Son los que se pulsan conduciendo |
| Separación entre botones | **≥ 24 px** | Evita pulsar *Finalizar* queriendo pulsar *Parar* |
| Importe | **≈ 96 px** | La información más importante; el pasajero la lee desde el asiento de atrás |
| Texto mínimo | **24 px** | Nada más pequeño en ninguna pantalla, ni siquiera la ayuda |

**Jerarquía durante una carrera:** los botones principales y el importe ocupan casi toda la pantalla. El resto de acciones (ayuda, volver…) son más pequeñas y van a un lado, sin bajar nunca de los 88 px.

**Confirmación al finalizar (decidido 2026-09-22).** FINALIZAR no cierra la carrera al momento: abre un panel encima de la pantalla.

```
┌──────────────────────────────────────────────────────────┐
│  ¿Finalizar la carrera nº 7?                             │
│  El taxímetro sigue contando: 12,34 €                    │
│  ┌──────────────────────────┐ ┌────────────────────────┐ │
│  │      SÍ, FINALIZAR       │ │       NO, SEGUIR       │ │
│  └──────────────────────────┘ └────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

- **Por qué:** un toque accidental con el coche en marcha cerraría la carrera y la escribiría en el histórico, y no se puede reabrir. Cuesta un toque más por carrera. Se descartaron la pulsación larga (menos evidente para un conductor nuevo) y no confirmar.
- **El taxímetro sigue contando** mientras se pregunta, y el panel muestra el importe en vivo. Es la misma regla que la confirmación de Ctrl+C en la Fase 2.
  - **Cambio previsto:** congelar el importe al pulsar FINALIZAR y cobrar ese importe si se confirma; si se cancela, la carrera sigue como si no se hubiera parado. Detalle en `future-implementation-ideas.md`, *Freeze the amount while FINALIZAR is being confirmed*.
- **SÍ va a la izquierda y NO a la derecha**, justo donde estaba FINALIZAR. Así, un doble toque sin querer sobre FINALIZAR cae en *NO, SEGUIR* y no cierra nada.
- Teclas de 220 px de alto.

Pendiente:
- Si alguna otra acción necesita confirmación.

## Inspiración visual: el taxímetro clásico

El cliente sustituye taxímetros físicos **Hale T200** (ver `project-brief.md`). La interfaz toma prestado el lenguaje visual del taxímetro clásico para que el conductor lo reconozca sin aprender nada:

- Importe en **dígitos de 7 segmentos**, luminosos sobre fondo negro.
- **Indicador de tarifa** junto al importe.
- Luz de estado tipo **LIBRE / OCUPADO**.
- **Teclas físicas** grandes y rectangulares bajo la pantalla.

*Supuesto:* no se dispone de fotos del modelo T200 concreto; se usa el aspecto común de los taxímetros clásicos. Se ajustará si aparece una referencia del modelo real.

**Decidido (2026-09-22): dirección "A · Clásico".** Se compararon dos maquetas de la carrera activa: *A · Clásico* (visor LED) y *B · Estado a color* (todo el panel central cambia de color según el estado). Se elige A. B queda en el lienzo de la maqueta solo como registro.

- En tkinter, los dígitos de 7 segmentos se dibujan como polígonos en un `Canvas`, con los segmentos apagados visibles en tono muy oscuro, como en un LED real.
- Fuentes: las del sistema (Segoe UI en Windows, DejaVu Sans en Linux). tkinter no carga fuentes propias con facilidad, así que la maqueta usa las mismas.

## Colores y estados

Usados en la pantalla de carrera activa (aprobada):

| Elemento | Color | Nota |
|---|---|---|
| Fondo de la aplicación / visor | `#1c1c1c` / `#070707` | Oscuro: no deslumbra de noche |
| Dígitos del importe | `#ff2a1a` encendido, `#260806` apagado | Rojo LED clásico |
| Estado *en movimiento* | `#3ddc6e` (verde LED) | Siempre acompañado del texto *EN MOVIMIENTO* |
| Estado *parado* | `#ffb020` (ámbar LED) | Siempre acompañado del texto *PARADO* |
| Lámpara OCUPADO encendida / LIBRE encendida | `#c62828` / `#1e7a3c` | La apagada se ve en tono muy oscuro |
| Tecla FINALIZAR | `#8e1b17` | Rojo: acción que termina la carrera |
| Tecla INICIAR CARRERA | `#1e6b37` | Verde |

Pendiente:
- Modo día / modo noche (se conduce de noche).
- El estado no se comunica solo con el color (texto o icono también).

## Tipografía y formato — Pendiente

- Fuente y tamaños.
- Importe siempre en formato español, generado por `utils.formato_euros()`: `12,34 €`.

---

## Pantallas

Cada pantalla tendrá: su maqueta (wireframe), qué muestra, qué botones tiene y qué hace cada uno, y los mensajes que puede enseñar. La lista sale de los menús del CLI de la Fase 2 (ver `flujo-fase2.md`) y se confirmará en la sesión de diseño.

### 1. Pantalla de inicio (elección de perfil)

Equivale al *menú de inicio* de la Fase 2. Aprobada el 2026-09-22.

```
┌──────────────────────────────────────────────────────────────┬────────────┐
│ ┌──────────────────────────────────────────────────────────┐ │            │
│ │ TTX-247        Tarifas vigentes: parado 0,02 · mov. 0,05 │ │            │
│ └──────────────────────────────────────────────────────────┘ │            │
│ ┌──────────────────────────────────────┐ ┌─────────────────┐ │            │
│ │               (taxi)                 │ │    (candado)    │ │            │
│ │             CONDUCTOR                │ │  ADMINISTRADOR  │ │            │
│ │         Abrir el taxímetro           │ │ Tarifas e hist. │ │ ┌────────┐ │
│ │                                      │ │ con contraseña  │ │ │ Salir  │ │
│ └──────────────────────────────────────┘ └─────────────────┘ │ └────────┘ │
└──────────────────────────────────────────────────────────────┴────────────┘
```

- **CONDUCTOR**: teja verde, dos tercios del ancho (es la acción diaria). Abre el taxímetro en estado LIBRE.
- **ADMINISTRADOR**: teja gris, un tercio, con candado. Lleva a la pantalla de contraseña.
- Franja superior en estilo visor, con las tarifas vigentes (como el banner del CLI).
- **Salir** abajo en el lateral: las acciones secundarias siempre en el mismo sitio.

### 2. Pantalla de contraseña (US-08)

Aprobada el 2026-09-22. Solo protege al Administrador (ver `decisions-fase3.md`).

- Título *Administrador* con candado; campo **Contraseña** enmascarado (96 px de alto, texto 40 px), escrito con el teclado.
- Tecla **ENTRAR** (160 px de alto, verde); Enter también entra.
- **Cancelar** abajo en el lateral: vuelve a Inicio.
- Mensajes bajo el campo, en rojo y con el borde del campo en rojo:
  - vacío → «Escribe la contraseña.»
  - incorrecta → «Contraseña incorrecta. Inténtalo de nuevo.» (el campo se vacía). No hay límite de intentos.
  - falta `config/credenciales.json` o no se puede leer → «No se puede comprobar la contraseña. Avisa al equipo técnico.» No se entra nunca por defecto.
- Correcta → menú de Administrador.

### 3. Conductor — sin carrera (y total a cobrar)

**Decidido (2026-09-22):** *sin carrera* y *total a cobrar* son **la misma pantalla que la carrera activa**, en estado LIBRE. El conductor solo tiene una pantalla, el taxímetro, que pasa de OCUPADO a LIBRE y vuelta, como un taxímetro real. La pantalla 5 queda absorbida aquí.

Al confirmar *SÍ, FINALIZAR*:
- El visor muestra el importe **congelado**, con el rótulo **TOTAL A COBRAR**, *CARRERA FINALIZADA* y la lámpara **LIBRE** encendida.
- Las dos teclas se sustituyen por una sola, **INICIAR CARRERA** (verde, "Empieza en movimiento · 0,05 €/s"). La carrera nace en movimiento, como en la Fase 1.
- En el lateral aparece **Volver** (a la pantalla de inicio), encima de *Ayuda*. Nº de carrera, tiempo e inicio siguen mostrando la carrera terminada.
- El total se queda en el visor hasta la siguiente carrera: el pasajero tiene tiempo de leerlo y pagar.

Primer arranque (todavía no hay carrera en esta sesión): visor a `0,00`, LIBRE encendida, rótulo *IMPORTE*.

**Por qué:** una pantalla separada con una tecla *Cobrado* añadía un toque por carrera sin aportar información nueva.

### 4. Conductor — carrera activa

Equivale a *CARRERA ACTIVA* de la Fase 2. Aprobada el 2026-09-22 (maqueta A, sin el rótulo "ESTADO" ni el subtítulo de la tecla PARAR/ARRANCAR).

```
┌──────────────────────────────────────────────────────────────┬────────────┐
│ ┌──────────────────────────────────────────────────────────┐ │ Carrera    │
│ │ ███ OCUPADO ███                                          │ │ Nº 7       │
│ │ ░░░ LIBRE ░░░          █▀▀█  █▀▀█     █▀▀█  █▀▀█         │ ├────────────┤
│ │                        █  █  █▀▀█  ,  █▀▀█  █  █   €     │ │ Tiempo     │
│ │ EN MOVIMIENTO          █▄▄█  █▄▄█     █▄▄█  █▄▄█         │ │ 00:04:12   │
│ │ 0,05 €/s                                     IMPORTE     │ ├────────────┤
│ └──────────────────────────────────────────────────────────┘ │ Inicio     │
│ ┌───────────────────────────┐ ┌────────────────────────────┐ │ 18:42      │
│ │                           │ │                            │ │            │
│ │          PARAR            │ │         FINALIZAR          │ │            │
│ │                           │ │ Termina y muestra el total │ │ ┌────────┐ │
│ │                           │ │                            │ │ │ Ayuda  │ │
│ └───────────────────────────┘ └────────────────────────────┘ │ └────────┘ │
└──────────────────────────────────────────────────────────────┴────────────┘
          zona principal (≈ 970 px)                           lateral 240 px
```

| Zona | Contenido | Medidas |
|---|---|---|
| Visor (arriba, fondo negro) | Lámparas **OCUPADO** (encendida en rojo) y **LIBRE** (apagada); estado y tarifa vigente en color LED; importe en dígitos de 7 segmentos rojos con `€`; rótulo *IMPORTE* | Visor 420 px de alto; dígitos ≈ 147 px |
| Teclas (abajo) | **PARAR** / **ARRANCAR** (una sola tecla, siempre la acción contraria al estado actual, como en el CLI) y **FINALIZAR** (roja, con subtítulo "Termina y muestra el total") | ≈ 300 px de alto, mitad del ancho cada una, 24 px entre ellas |
| Lateral | Nº de carrera, tiempo transcurrido, hora de inicio; botón **Ayuda** abajo | 240 px de ancho; botón 96 px de alto |

- El importe se refresca solo (ver `decisions-fase3.md`, *Real-time counter*). *Ver importe* del CLI desaparece: el importe está siempre en pantalla.
- *Ayuda* abre un panel encima con lo que hace cada tecla y las tarifas vigentes, y un botón **Cerrar**.
- El importe no cabe en más de 3 cifras enteras (999,99 €). Pendiente: decidir qué se muestra si se supera.

### 5. Total a cobrar — absorbida por la pantalla 3

Ver pantalla 3.

### 6. Administrador — menú

Equivale al menú de Administrador de la Fase 2. Aprobada el 2026-09-22.

- Misma estructura que Inicio. Franja superior en estilo visor: candado + **ADMINISTRADOR** y las tarifas vigentes.
- Dos tejas iguales, en gris:
  - **CAMBIAR TARIFAS**: «Los €/s de cada estado, desde la próxima carrera».
  - **VER HISTÓRICO**: «Carreras terminadas hoy y total de caja».
- **Volver** abajo en el lateral: vuelve a Inicio. Para volver a entrar hay que teclear otra vez la contraseña.

### 7. Administrador — cambiar tarifas

Aprobada el 2026-09-22.

```
┌──────────────────────────────────────────────────────────────┬────────────┐
│ Cambiar tarifas                                              │ Coma o     │
│ Tarifas vigentes: parado 0,02 €/s · en movimiento 0,05 €/s   │ punto:     │
│                                                              │ 0,03 o 0.03│
│ Parado o < 20 km/h       [      0,02 ]  €/s   (ámbar)        │            │
│ En movimiento            [      0,05 ]  €/s   (verde)        │            │
│                                                              │            │
│ (mensaje de error o de confirmación)                         │            │
│ ┌──────────────────────────────────────────────────────────┐ │ ┌────────┐ │
│ │                        GUARDAR                           │ │ │ Volver │ │
│ └──────────────────────────────────────────────────────────┘ │ └────────┘ │
└──────────────────────────────────────────────────────────────┴────────────┘
```

- **Los campos vienen rellenos con las tarifas vigentes**, así que se puede cambiar solo una. Es el único cambio respecto al CLI, donde se teclean las dos.
- Campos de 96 px, texto 44 px, del color del estado que representan (ámbar parado, verde en movimiento), igual que en el taxímetro.
- **GUARDAR** (150 px, verde); Enter también guarda. **Volver** sale sin guardar.
- **Validación y mensajes idénticos al CLI.** Las reglas son de `Tarifa`, no de la interfaz. Se acepta coma o punto decimal. Un error pone en rojo el borde del campo culpable y no guarda nada:
  - ««abc» no es un número. Escribe, por ejemplo, 0,03. No se ha guardado nada.»
  - «Cada tarifa debe ser mayor que 0 y como máximo 1,00 €/s. No se ha guardado nada.»
  - «Cada tarifa admite como máximo 2 decimales. No se ha guardado nada.»
  - «La tarifa parado no puede ser mayor que la de en movimiento. No se ha guardado nada.» (los dos campos en rojo)
  - «No se pudo escribir el fichero de tarifas. No se ha guardado nada.»
- Si se guarda, en verde: «Tarifas guardadas: parado X €/s · en movimiento Y €/s. Se aplican desde la próxima carrera.», y la línea de tarifas vigentes se actualiza.

### 8. Administrador — histórico del día

Aprobada el 2026-09-22.

- Título «Histórico de hoy · dd/mm/aaaa».
- Tabla con las columnas del CLI (Nº, Inicio, Fin, Importe): filas de 64 px, texto 28 px, sombreado alterno.
- Abajo, en un recuadro estilo visor: «N carreras · Total del día» y el total en rojo LED.
- **▲ / ▼** en el lateral para desplazarse cuando no caben todas (unas 7 filas por pantalla). Una barra de desplazamiento es demasiado fina para un dedo.
- **Sin carreras hoy:** tabla vacía con «No hay carreras terminadas hoy.» (el texto del CLI) y total `0,00 €`.
- Si el fichero no se puede leer: «No se pudo leer el histórico.» (el texto del CLI).
- **Volver** abajo en el lateral: vuelve al menú de Administrador.

---

## Mensajes y textos — Pendiente

Tabla de todos los textos que aparecen en pantalla (títulos, botones, errores, confirmaciones), en español. Se reutilizan los del CLI cuando tengan sentido.

## Comportamiento — Pendiente

- Cerrar la ventana con una carrera en curso: decidido, ver `flujo-fase3.md`, *Cerrar la ventana con una carrera en curso*.
- Qué ve el usuario si no se puede guardar el histórico o las tarifas.
