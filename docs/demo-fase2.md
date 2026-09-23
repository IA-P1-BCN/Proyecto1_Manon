# Guion de la demo — Fase 2

Secuencia exacta para la demo en directo de la Fase 2 ante TaxiTech Solutions: **histórico (US-05), logs (US-06) y tarifas configurables (US-07)**, más la separación Conductor / Administrador. Cada paso indica qué se teclea, qué debe aparecer y qué requisito demuestra.

> **Estado:** contrastado con la salida real del CLI al terminar la US-06. Los textos entre bloques de código son los que imprime la aplicación; si alguno cambia, hay que corregirlo aquí también. Las horas y los importes exactos dependen de los segundos que se dejen pasar.

## Antes de empezar

- [ ] **Rama correcta.** Hasta que el cliente apruebe la Fase 1, la Fase 2 vive en `fase-2`: `git checkout fase-2 && git pull`. Después de la aprobación, se demuestra desde `main`.
- [ ] **Estado limpio**, para que la carrera sea la nº 1, las tarifas las de por defecto y el log esté vacío. Los tres ficheros no se versionan y el programa los recrea:
  ```powershell
  Remove-Item -Recurse -Force data, logs, config\tarifas.json -ErrorAction SilentlyContinue
  ```
  (en bash: `rm -rf data logs config/tarifas.json`)
- [ ] Entorno activado y `pytest` en verde delante del cliente.
- [ ] Terminal a pantalla completa y fuente grande. **Un segundo terminal** en la misma carpeta para enseñar los ficheros (pasos 7 y 8).
- [ ] El [tablero](https://github.com/orgs/IA-P1-BCN/projects/2) abierto en otra pestaña, con la columna **Fase 2**.

## Duración

Unos 6 minutos, a velocidad y con tarifas reales.

## Guion

### 1. Arranque: se elige perfil

```bash
python -m taximetro.taximetro_app
```

El banner explica las opciones **de cada perfil**, y debajo aparece el menú de inicio:

```
Menú de inicio
  1) Conductor
  2) Administrador
  3) Salir
```

> **Qué decir:** "Desde esta fase hay dos perfiles. El conductor ve exactamente el taxímetro que validaron en la Fase 1. Todo lo nuevo de gestión está separado en *Administrador*, para que el conductor no lo tenga delante mientras trabaja."

### 2. Una carrera, como en la Fase 1

```
1        ← Conductor
1        ← Iniciar carrera
```

→ `Carrera nº 1 iniciada · EN MOVIMIENTO · 0,05 €/s`

Esperar ~20 segundos y teclear `3` (Finalizar carrera):

→ `TOTAL A COBRAR: 1,00 €` (aprox.)

> **Qué decir:** "Nada cambia para el conductor. Pero esta carrera ya no se pierde al cerrarla: se acaba de guardar en el histórico."

Teclear `3` (**Volver**) para regresar al menú de inicio.

> **Qué decir:** "Fíjense en que *Volver* solo aparece sin carrera en curso. Con un pasajero dentro no se puede salir al Administrador, así que **las tarifas nunca pueden cambiar a mitad de una carrera**: al pasajero se le cobra la tarifa que se le anunció al subir."

### 3. Histórico del día — US-05

```
2        ← Administrador
2        ← Ver histórico
```

```
Histórico de hoy · 22/09/2026
    Nº  Inicio    Fin          Importe
     1  09:23:02  09:23:22      1,00 €
  1 carrera · Total del día: 1,00 €
```

> **Qué decir:** "Esto es para cuadrar caja: cada carrera terminada, con su hora y el importe **exacto que se cobró**, el mismo del ticket. El total del día es la suma de los tickets, céntimo a céntimo."

**Demuestra:** *"El sistema guarda cada carrera finalizada"* y *"existe un comando que muestra el listado del día y el total acumulado"*.

### 4. Cambiar las tarifas — US-07

Primero, un error a propósito:

```
1        ← Cambiar tarifas
0,06     ← parado
0,05     ← en movimiento
```

→ `La tarifa parado no puede ser mayor que la de en movimiento. No se ha guardado nada.`

> **Qué decir:** "El sistema protege de los despistes: parado nunca puede costar más que en marcha, ninguna tarifa puede pasar de un euro por segundo, y si algo no cuadra no se guarda nada."

Ahora bien:

```
1        ← Cambiar tarifas
0,03
0,06
```

→ `Tarifas guardadas: parado 0,03 €/s · en movimiento 0,06 €/s. Se aplican desde la próxima carrera.`

Teclear `3` (Volver).

### 5. La tarifa nueva se aplica a la siguiente carrera

```
1        ← Conductor
1        ← Iniciar carrera
```

→ `Carrera nº 2 iniciada · EN MOVIMIENTO · 0,06 €/s`

> **Qué decir:** "Tarifa nueva, sin tocar código y sin reinstalar nada."

**Demuestra:** *"Las tarifas deben poder modificarse sin necesidad de tocar el código ni redeployar."*

### 6. Ctrl+C durante una carrera

Con la carrera nº 2 en curso, pulsar **Ctrl+C**:

```
Vas a salir del programa con la carrera nº 2 en curso.
  1) Sí, finalizar la carrera y salir
  2) No, seguir con la carrera
```

Teclear `2`: se vuelve a la carrera **como si nada**. Teclear `2` (Ver importe) para enseñar que el importe siguió subiendo mientras se preguntaba.

> **Qué decir:** "Si el conductor pulsa Ctrl+C sin querer, no pierde la carrera: el programa pregunta, y el taxímetro sigue contando mientras tanto."

Pulsar **Ctrl+C** otra vez y teclear `1`:

→ `TOTAL A COBRAR: X,XX €` y el programa se cierra.

> **Qué decir:** "Y si de verdad quiere salir, primero se cobra y se guarda la carrera. Un importe nunca se pierde sin haberse visto."

### 7. Los datos sobreviven al cierre

En el segundo terminal, el fichero de tarifas que acaba de escribir el Administrador:

```bash
cat config/tarifas.json
```

```json
{
  "parado": 0.03,
  "en_movimiento": 0.06
}
```

> **Qué decir:** "Es un fichero de texto normal. Un técnico también puede cambiar las tarifas aquí, con el programa cerrado, que es lo que pedía la US-07."

Volver a arrancar en el primer terminal:

```bash
python -m taximetro.taximetro_app
```

El banner ya muestra `0,03 €/s` y `0,06 €/s`. Teclear `2` (Administrador) y `2` (Ver histórico): aparecen **las dos carreras**, también la que se cerró con Ctrl+C.

> **Qué decir:** "El histórico está disponible en la siguiente sesión sin intervención manual. Y la numeración continúa: la próxima carrera será la nº 3, nunca se repite un número en el mismo día."

**Demuestra:** *"El historial de carreras debe escribirse en disco de forma incremental y estar disponible en la siguiente sesión sin intervención manual."*

Teclear `3` (Volver) y `3` (Salir).

### 8. Logs de operación — US-06

En el segundo terminal:

```bash
cat logs/taximetro.log
```

Una línea por evento, con fecha, nivel y datos (extracto; también aparecen, por ejemplo, el perfil elegido y los cambios de estado):

```
... INFO taximetro.taximetro_app aplicacion_iniciada parado=0.02 movimiento=0.05
... INFO taximetro.carrera carrera_iniciada carrera=1 estado=en_movimiento tarifa=0.05
... INFO taximetro.carrera carrera_finalizada carrera=1 importe=1.00 duracion_s=20
... INFO taximetro.historial carrera_guardada carrera=1 importe=1.00 ruta=data\historial.csv
... WARNING taximetro.taximetro_app tarifa_rechazada parado=0.06 movimiento=0.05 motivo='La tarifa parado no puede ser mayor que la de en movimiento.'
... INFO taximetro.taximetro tarifa_cambiada parado_antes=0.02 movimiento_antes=0.05 parado=0.03 movimiento=0.06
... INFO taximetro.taximetro_app salida_confirmada carrera=2
... INFO taximetro.taximetro_app aplicacion_cerrada motivo=ctrl_c_con_carrera
```

> **Qué decir:** "Todo lo que ha pasado en la demo está aquí: arranque, carreras, cambios de estado, el cambio de tarifas, incluso el error que cometimos a propósito, que aparece como WARNING. Si algo falla en producción, el técnico sabe qué pasó y cuándo. El fichero rota a 1 MB y guarda cinco copias, así que nunca llena el disco del taxi."

**Demuestra:** *"El sistema debe registrar todos los eventos relevantes —arranque, cambios de estado, cierre de carrera, errores— en un log estructurado."*

### 9. Robustez del fichero de tarifas (si hay tiempo o preguntan)

En el segundo terminal, estropear el fichero a propósito, por ejemplo invirtiendo las tarifas:

```powershell
Set-Content config\tarifas.json '{"parado": 0.06, "en_movimiento": 0.05}'
```

Arrancar: el programa **no falla** y usa las tarifas por defecto (`0,02` / `0,05`). En el log:

```
... WARNING taximetro.config_tarifas tarifas_invalidas ruta=config\tarifas.json error=TarifaInvalidaError detalle='La tarifa parado no puede ser mayor que la de en movimiento.'
```

> **Qué decir:** "Si el técnico se equivoca al editar el fichero, el taxímetro sigue funcionando con las tarifas seguras, deja el fichero como estaba para que se pueda corregir y explica el motivo en el log."

**Demuestra:** *"Si el fichero es inválido o falta, se usan valores por defecto sin que el programa falle."*

## Cierre

Mostrar el tablero: columna **Fase 2** completa, US-05, US-06 y US-07 cerradas.

**Decirlo claramente:** en esta fase **el perfil Administrador no tiene contraseña**, así que cualquiera que tenga el terminal podría cambiar las tarifas. La contraseña es la US-08, en la Fase 3. La separación de perfiles ya deja preparado el sitio donde irá.

## Preguntas para el cliente

Dos cosas que decide el cliente y no el equipo. Anotar la respuesta:

1. **Redondeo del medio céntimo.** Si una carrera sale a exactamente 0,625 €, hoy se cobra **0,62 €**: Python redondea el medio céntimo exacto al par. ¿Prefieren redondear siempre hacia arriba (0,63 €)? Es un cambio de una línea, pero cambia lo que paga el pasajero. Detalle en `docs/future-implementation-ideas.md`.
2. **Abrir el histórico en Excel.** `data/historial.csv` usa comas y punto decimal, el formato estándar. Un Excel configurado en español puede necesitar *Datos → Desde texto/CSV* para separar bien las columnas. ¿Les vale así, o prefieren punto y coma y coma decimal?

## Si algo falla

- **La carrera no es la nº 1 o las tarifas no son las de por defecto:** no se limpió el estado antes de empezar (ver *Antes de empezar*). No es un fallo: los datos de una sesión anterior se han conservado, que es justo lo que pide la Fase 2.
- **El importe no es el esperado:** se han contado mal los segundos. Enseñar `pytest` en verde.
- **La aplicación no arranca:** comprobar el entorno virtual y que se ejecuta desde la raíz del repositorio (los ficheros `config/`, `data/` y `logs/` se crean ahí).
- **Traceback en pantalla:** no improvisar un arreglo. Enseñar que el error ha quedado en `logs/taximetro.log` como `error_inesperado`, con su traza (eso también es la US-06), terminar la demo y abrir una issue.
