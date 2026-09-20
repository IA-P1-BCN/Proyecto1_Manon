# Guion de la demo — Fase 1

Secuencia exacta para la demo en directo del MVP ante TaxiTech Solutions. Cada paso indica qué se teclea, qué debe aparecer y qué requisito demuestra.

> **Estado:** contrastado con la salida real del CLI tras implementar US-04. Los textos de este guion son los que imprime la aplicación; si alguno cambia, hay que corregirlo aquí también.

## Antes de empezar

- [ ] `git checkout main && git pull` — se demuestra lo que está en `main`, no el portátil de nadie.
- [ ] Entorno activado y `pytest` en verde delante del cliente (30 segundos, y respalda el resto de la demo).
- [ ] Terminal a pantalla completa, fuente grande, ventana limpia.
- [ ] Reloj a la vista: los importes dependen de los segundos que se dejen pasar.
- [ ] Tener a mano el [tablero](https://github.com/orgs/IA-P1-BCN/projects/2) en otra pestaña (entregable #3).

## Duración

Unos 4 minutos. Los tramos son de ~20 segundos: suficiente para que los números se muevan de forma visible sin silencios incómodos. Se ejecuta a velocidad real, con las tarifas reales — no hay modo acelerado, y eso es deliberado (ver `docs/decisions-proceso.md`).

## Guion

### 1. Arranque — US-01

```bash
python -m taximetro.taximetro_app
```

Aparece el banner con qué es, cómo se usa y las tarifas vigentes, y debajo el menú sin carrera: `iniciar · ayuda · salir`.

> **Qué decir:** "El conductor no necesita manual: todo lo que puede hacer está en pantalla. Y solo ve los comandos que son válidos en este momento."

**Demuestra:** *"Al arrancar, el sistema explica al conductor cómo usarlo sin documentación externa."*

### 2. Iniciar la carrera — US-01

```
iniciar
```

→ `Carrera nº 1 iniciada · PARADO · 0,02 €/s`

> **Qué decir:** "Empieza a cobrar desde este segundo. Arranca en PARADO porque el taxi está recogiendo al pasajero."

**Demuestra:** cobro inmediato desde el arranque, con un solo comando.

### 3. Consultar el importe en el atasco — US-02 / briefing

Esperar ~20 segundos y teclear:

```
importe
```

→ `Carrera nº 1 · PARADO · 0,40 € acumulado`

Volver a teclear `importe` unos segundos después para que se vea subir.

> **Qué decir:** "Esto es el 'en tiempo real' que pedían: el conductor parado en un semáforo puede consultar el importe cuando quiera, y el contador no se ha detenido."

**Demuestra:** acumulación continua según el tiempo, sin cambiar de estado.

### 4. Arrancar el taxi — US-02

```
movimiento
```

→ `EN MOVIMIENTO · 0,4X € acumulado`

Esperar ~20 segundos y:

```
importe
```

→ el importe ha subido ~1,00 € (0,05 €/s), dos veces y media más rápido que antes.

> **Qué decir:** "Misma carrera, tarifa distinta. El tramo parado se cerró al precio de parado y el nuevo corre a 0,05 por segundo."

**Demuestra:** *"El conductor puede indicar en cada momento si el vehículo está parado o en movimiento"* y la tarifa por tramos.

### 5. Semáforo: volver a parar — US-02

```
parado
```

Esperar unos segundos, y volver a `movimiento`. Con `importe` se ve que el total sigue creciendo, más despacio o más deprisa según el estado.

**Demuestra:** los cambios de estado no interrumpen el cálculo acumulado.

### 6. Llegada al destino — US-03

```
finalizar
```

→ `TOTAL A COBRAR: X,XX €`

Vuelve el menú sin carrera.

> **Qué decir:** "Importe en euros con dos decimales, listo para cobrar. La carrera queda cerrada: ya no admite cambios de estado."

**Demuestra:** *"Al cerrar la carrera, se muestra el importe total a cobrar."*

### 7. Siguiente servicio — US-04

```
iniciar
```

→ `Carrera nº 2 iniciada · PARADO · 0,02 €/s`

> **Qué decir:** "Sin cerrar el programa ni reiniciar nada. El siguiente pasajero ya está subiendo."

**Demuestra:** *"Se pueden encadenar carreras de forma inmediata, sin interrupciones."*

### 8. Robustez (si hay tiempo o preguntan)

Con la carrera nº 2 aún activa:

| Se teclea | Responde |
|---|---|
| `iniciar` | `Ya hay una carrera activa.` |
| `finalizr` (mal escrito) | `Comando no reconocido.` |
| `Ctrl+C` | `Para salir, finaliza la carrera.` — la carrera **no** se pierde |
| `ayuda` | reimprime el banner completo |

Después `finalizar` y `salir` para cerrar limpiamente.

> **Qué decir:** "Un error de tecleo y un estado imposible dan mensajes distintos, porque se arreglan de forma distinta. Y una carrera solo termina cuando el conductor lo decide: ni un Ctrl+C accidental le hace perder el importe."

**Demuestra:** las decisiones de EPIC D — menús contextuales, errores diferenciados y gestión de Ctrl+C.

## Cierre

Mostrar el tablero con la columna **Fase 1** completa y las historias US-01 a US-04 cerradas, y mencionar qué entra en la Fase 2 (histórico, logs, tarifas configurables) para que el cliente valide el paso.

## Si algo falla

- **El importe no es el esperado:** se han contado mal los segundos, no es un fallo de cálculo. Enseñar `pytest` en verde y la cobertura.
- **La aplicación no arranca:** comprobar que el entorno virtual está activado y que se ejecuta desde la raíz del repositorio.
- **Traceback en pantalla:** no improvisar un arreglo delante del cliente. Anotarlo, terminar la demo con el resto del guion y abrir una issue.
