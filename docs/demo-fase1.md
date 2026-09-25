# Guion de la demo — Fase 1

Secuencia exacta para la demo en directo del MVP ante TaxiTech Solutions. Cada paso indica qué se teclea, qué debe aparecer y qué requisito demuestra.

> **Estado:** contrastado con la salida real del CLI tras implementar US-04. Los textos de este guion son los que imprime la aplicación; si alguno cambia, hay que corregirlo aquí también.

## Antes de empezar

- [ ] `git checkout fase-1 && git pull` — se demuestra la Fase 1 congelada en su rama, no el portátil de nadie. (`main` recibirá la Fase 1 cuando el cliente la apruebe.)
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

Aparece el banner con qué es, cómo se usa y las tarifas vigentes, y debajo el menú sin carrera, numerado:

```
Sin carrera
  1) Iniciar carrera
  2) Ayuda
  3) Salir
```

> **Qué decir:** "El conductor no necesita manual ni recordar ningún comando: cada opción tiene un número y solo se teclea el número. Y solo ve las opciones que son válidas en este momento."

**Demuestra:** *"Al arrancar, el sistema explica al conductor cómo usarlo sin documentación externa."*

### 2. Iniciar la carrera — US-01

```
1
```

→ `Carrera nº 1 iniciada · EN MOVIMIENTO · 0,05 €/s`

Y el menú cambia solo:

```
Carrera nº 1 en curso (EN MOVIMIENTO)
  1) Parar
  2) Ver importe
  3) Finalizar carrera
  4) Ayuda
```

> **Qué decir:** "Empieza a cobrar desde este segundo. La carrera nace en movimiento porque se inicia cuando el taxi arranca con el pasajero dentro. Y fíjense en el menú: ahora ofrece *Parar*, porque el taxi está circulando."

**Demuestra:** cobro inmediato desde el arranque, con una sola tecla.

### 3. Consultar el importe en marcha — US-02 / briefing

Esperar ~20 segundos y teclear:

```
2
```

→ `Carrera nº 1 · EN MOVIMIENTO · 1,00 € acumulado`

Volver a teclear `2` unos segundos después para que se vea subir.

> **Qué decir:** "Esto es el 'en tiempo real' que pedían: el conductor puede consultar el importe cuando quiera, y consultarlo no altera el contador."

**Demuestra:** acumulación continua según el tiempo, sin cambiar de estado.

### 4. Semáforo: parar el taxi — US-02

```
1
```

→ `PARADO · 1,2X € acumulado`

El menú pasa a ofrecer `1) Arrancar`. Esperar ~20 segundos y teclear `2`:

→ el importe solo ha subido ~0,40 € (0,02 €/s), dos veces y media más despacio que antes.

> **Qué decir:** "Misma carrera, tarifa distinta. El tramo en movimiento se cerró a su precio y la espera corre a 0,02 por segundo. Y la misma tecla, el 1, hace lo contrario según cómo esté el taxi: nunca hay que elegir entre dos estados, solo confirmar el cambio."

**Demuestra:** *"El conductor puede indicar en cada momento si el vehículo está parado o en movimiento"* y la tarifa por tramos.

### 5. Verde: volver a arrancar — US-02

```
1
```

Esperar unos segundos y teclear `2` otra vez: el total sigue creciendo, más deprisa o más despacio según el estado, sin haberse reiniciado en ningún momento.

**Demuestra:** los cambios de estado no interrumpen el cálculo acumulado.

### 6. Llegada al destino — US-03

```
3
```

→ `TOTAL A COBRAR: X,XX €`

Vuelve el menú sin carrera.

> **Qué decir:** "Importe en euros con dos decimales, listo para cobrar. La carrera queda cerrada: ya no admite cambios de estado."

**Demuestra:** *"Al cerrar la carrera, se muestra el importe total a cobrar."*

### 7. Siguiente servicio — US-04

```
1
```

→ `Carrera nº 2 iniciada · EN MOVIMIENTO · 0,05 €/s`

> **Qué decir:** "Sin cerrar el programa ni reiniciar nada. El siguiente pasajero ya está subiendo."

**Demuestra:** *"Se pueden encadenar carreras de forma inmediata, sin interrupciones."*

### 8. Robustez (si hay tiempo o preguntan)

Con la carrera nº 2 aún activa:

| Se teclea | Responde |
|---|---|
| `9` (no está en el menú) | `Opción no válida. Elige un número del menú.` |
| `finalizar` (una palabra) | `Opción no válida. Elige un número del menú.` |
| `Ctrl+C` | `Para salir, finaliza la carrera.` — la carrera **no** se pierde |
| `4` | reimprime el banner completo |

Después `3` (finalizar) y `3` (salir) para cerrar limpiamente.

> **Qué decir:** "No hay forma de teclear algo que rompa la carrera: o es un número del menú, o el taxímetro lo rechaza y sigue exactamente donde estaba. Tampoco hay ninguna tecla que abra una segunda carrera mientras hay una abierta: la opción sencillamente no está. Y una carrera solo termina cuando el conductor lo decide: ni un Ctrl+C accidental le hace perder el importe."

**Demuestra:** las decisiones de EPIC D — menús contextuales y numerados, entrada no válida sin efectos y gestión de Ctrl+C.

## Cierre

Mostrar el tablero con la columna **Fase 1** completa y las historias US-01 a US-04 cerradas, y mencionar qué entra en la Fase 2 (histórico, logs, tarifas configurables) para que el cliente valide el paso.

## Si algo falla

- **El importe no es el esperado:** se han contado mal los segundos, no es un fallo de cálculo. Enseñar `pytest` en verde y la cobertura.
- **La aplicación no arranca:** comprobar que el entorno virtual está activado y que se ejecuta desde la raíz del repositorio.
- **Traceback en pantalla:** no improvisar un arreglo delante del cliente. Anotarlo, terminar la demo con el resto del guion y abrir una issue.
