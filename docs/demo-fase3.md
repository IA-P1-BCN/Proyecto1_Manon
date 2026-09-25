# Guion de la demo — Fase 3

Secuencia para la demo en directo de la Fase 3 ante TaxiTech Solutions: **la interfaz gráfica táctil (US-09), la contraseña de Administrador (US-08) y la refactorización estructural**. Cada paso indica qué se pulsa, qué debe aparecer y qué requisito demuestra.

> **Estado:** escrito a partir del código. Los textos entre comillas y en bloques de código son los de la aplicación, pero el guion **aún no se ha contrastado en pantalla**. Se contrasta al hacer la prueba manual (T9.4): cualquier diferencia se corrige aquí. Los importes y las horas dependen de los segundos que se dejen pasar.

## Antes de empezar

- [ ] **Rama correcta.** La Fase 3 vive en `fase-3` hasta que el cliente apruebe las anteriores: `git checkout fase-3 && git pull`. Tienen que estar fusionados los logs de la interfaz (PR #118).
- [ ] **Estado limpio**, para que la carrera sea la nº 1, las tarifas las de por defecto y el log esté vacío. Los tres se recrean solos. **No borrar `config/credenciales.json`**: es la contraseña, y sin él el Administrador no se abre.
  ```powershell
  Remove-Item -Recurse -Force data, logs, config\tarifas.json -ErrorAction SilentlyContinue
  ```
  (en bash: `rm -rf data logs config/tarifas.json`)
- [ ] Entorno activado y `pytest` en verde delante del cliente.
- [ ] **Un terminal aparte** en la misma carpeta, para enseñar el log y el fichero de la contraseña (pasos 6 y 10) y el CLI (paso 11).
- [ ] El [tablero](https://github.com/orgs/IA-P1-BCN/projects/2) abierto en otra pestaña, con la columna **Fase 3**.
- [ ] Contraseña de la demo a mano: **`taxi`**.

## Duración

Unos 8 minutos, a velocidad y con tarifas reales.

## Guion

### 1. Arranque: la interfaz gráfica — US-09

```bash
python -m taximetro
```

Se abre una ventana de 1280 × 800, el tamaño de una tablet de 10" en horizontal. Arriba, una franja negra con **TTX-247** en rojo y «Tarifas vigentes: parado 0,02 €/s · en movimiento 0,05 €/s». Debajo, dos tejas grandes: **CONDUCTOR** («Abrir el taxímetro»), en verde y ocupando dos tercios, y **ADMINISTRADOR** («Tarifas e histórico / con contraseña»), en gris y con candado. Abajo a la derecha, *Salir*.

> **Qué decir:** "El conductor ya no teclea números: toca botones grandes, pensados para un dedo en una tablet montada en el salpicadero, a un brazo de distancia. La acción de todos los días, abrir el taxímetro, es la más grande."

**Demuestra:** *"Existe una UI gráfica (no solo CLI) con botones grandes."*

### 2. El taxímetro: LIBRE → OCUPADO — US-01, US-09

Pulsar **CONDUCTOR**. La pantalla es un taxímetro clásico: lámpara **LIBRE** encendida en verde, visor a `0,00 €` con el rótulo *IMPORTE* y una sola tecla, **INICIAR CARRERA** («Empieza en movimiento · 0,05 €/s»).

Pulsar **INICIAR CARRERA**:
- se enciende **OCUPADO** en rojo;
- a la izquierda del visor, **EN MOVIMIENTO** y «0,05 €/s» en verde;
- el importe **empieza a subir solo** en dígitos de 7 segmentos;
- a la derecha, *Carrera Nº 1*, el tiempo corriendo y la hora de inicio;
- abajo, dos teclas: **PARAR** y **FINALIZAR**.

> **Qué decir:** "El importe se actualiza cinco veces por segundo, sin que el conductor haga nada: a 5 céntimos por segundo, nunca se salta un céntimo. Y la pantalla nunca se bloquea: puede pulsar cualquier tecla en cualquier momento."

**Demuestra:** *"El importe debe actualizarse en tiempo real"* y *"la interfaz no debe bloquearse durante el uso"*.

### 3. Parar y arrancar — US-02

Esperar ~10 segundos y pulsar **PARAR**: el estado pasa a **PARADO** en ámbar, «0,02 €/s», y la tecla ahora dice **ARRANCAR**. El importe sigue subiendo, más despacio.

Pulsar **ARRANCAR**: vuelve a verde.

> **Qué decir:** "El estado se ve de un vistazo por el color, verde en marcha y ámbar parado, pero nunca solo por el color: siempre va escrito al lado. Y la tecla ofrece siempre lo contrario de lo que está pasando, igual que el menú del CLI."

**Demuestra:** *"El estado del taxi debe ser visible de un vistazo."*

### 4. Finalizar con confirmación y el importe congelado — US-03

Pulsar **FINALIZAR**. Aparece un panel encima:

```
¿Finalizar la carrera nº 1?
Importe a cobrar: 1,34 €
   [ SÍ, FINALIZAR ]   [ NO, SEGUIR ]
```

Dejar pasar ~10 segundos **sin contestar** y señalar que «Importe a cobrar» no se mueve. Pulsar **NO, SEGUIR**: la carrera sigue y el visor salta al importe actual.

> **Qué decir:** "Con el coche en marcha, un toque sin querer cerraría una carrera que ya no se puede reabrir, así que FINALIZAR pregunta. Y mientras pregunta, **el importe se congela**: el pasajero no paga los segundos que el conductor tarda en contestar. Si dice que no, la carrera sigue como si nada. Ese tiempo sí se cobra, porque el taxi seguía ocupado."

Pulsar otra vez **FINALIZAR** y luego **SÍ, FINALIZAR**:
- el visor se queda en el total, con el rótulo **TOTAL A COBRAR**;
- aparecen *CARRERA FINALIZADA* y «Cobrar al pasajero»;
- la lámpara vuelve a **LIBRE**.

> **Qué decir:** "El total se queda en pantalla hasta la siguiente carrera, para que el pasajero lo lea y pague. **SÍ** está a la izquierda y **NO** a la derecha, justo donde estaba FINALIZAR: si el conductor toca dos veces sin querer, el segundo toque cae en *no*."

**Demuestra:** *"Al finalizar se muestra el total en euros."*

### 5. Ayuda

Pulsar **Ayuda** (abajo a la derecha): un panel con qué hace cada tecla y las tarifas vigentes. **Cerrar**.

> **Qué decir:** "Las acciones secundarias, como Ayuda, Volver o Salir, están siempre en el mismo sitio, en la columna de la derecha, y más pequeñas, pero nunca por debajo del tamaño cómodo para un dedo."

### 6. Contraseña de Administrador — US-08

Pulsar **Volver** (solo aparece sin carrera en curso) y después **ADMINISTRADOR**.

1. Pulsar **ENTRAR** sin escribir nada: «Escribe la contraseña.», en rojo.
2. Escribir `Taxi` y pulsar Intro: «Contraseña incorrecta. Inténtalo de nuevo.», y el campo se vacía.
3. Escribir `taxi` y pulsar **ENTRAR**: se abre el menú de Administrador.

En el terminal aparte, enseñar el fichero de la contraseña:

```bash
cat config/credenciales.json
```

Aparecen `algoritmo`, `n`, `r`, `p`, `sal` y `hash`: la palabra `taxi` no está en ningún sitio.

> **Qué decir:** "Solo el Administrador tiene contraseña, porque lo que hay que proteger de manipulaciones son las tarifas. Al conductor no se le hace teclear nada al empezar el turno. La contraseña no se guarda en ningún sitio: solo una sal aleatoria y un hash *scrypt*, del que no se puede recuperar. La entrega y la cambia el equipo técnico, no la aplicación."

**Demuestra:** *"El acceso debe estar protegido por contraseña"* y *"ningún valor sensible puede guardarse en texto plano"*.

### 7. Cambiar las tarifas — US-07 en la interfaz gráfica

Pulsar **CAMBIAR TARIFAS**. Los campos vienen **rellenos con las tarifas vigentes**, `0,02` en ámbar y `0,05` en verde.

1. Cambiar *Parado* a `0,06` y pulsar **GUARDAR**: «La tarifa parado no puede ser mayor que la de en movimiento. No se ha guardado nada.», con los **dos campos** en rojo.
2. Poner *Parado* en `0,03` y *En movimiento* en `0,06`, y pulsar **GUARDAR**: en verde, «Tarifas guardadas: parado 0,03 €/s · en movimiento 0,06 €/s. Se aplican desde la próxima carrera.».

> **Qué decir:** "Los mensajes son los mismos que en el CLI, palabra por palabra, porque las reglas de qué es una tarifa válida viven en un solo sitio y las dos interfaces las comparten. El campo que falla se marca en rojo."

### 8. Histórico del día — US-05

Pulsar **Volver** y después **VER HISTÓRICO**: «Histórico de hoy · dd/mm/aaaa», una fila con la carrera nº 1 (inicio, fin, importe) y, abajo, «1 carrera · Total del día» con el total en rojo LED. Con más de 6 carreras se pasa de página con **▲ ▼**.

> **Qué decir:** "Filas grandes y flechas en lugar de una barra de desplazamiento, que es demasiado fina para un dedo."

Volver al Inicio: la franja ya muestra las **tarifas nuevas**.

### 9. Cerrar la ventana con una carrera en curso

**CONDUCTOR** → **INICIAR CARRERA** (ahora cobra a 0,06 €/s). Esperar unos segundos y **cerrar la ventana con la ✕**:

```
Vas a salir del programa con la carrera nº 2 en curso.
Importe a cobrar: 0,36 €
   [ SÍ, FINALIZAR / Y SALIR ]   [ NO, SEGUIR ]
```

Pulsar la **✕ otra vez**: el panel se cierra y la carrera sigue.

> **Qué decir:** "Un doble clic nervioso en la ✕ nunca termina una carrera: el segundo cuenta como *no*."

Pulsar la ✕ una tercera vez y ahora **SÍ, FINALIZAR Y SALIR**. El programa **no se cierra de golpe**: el visor queda en **TOTAL A COBRAR** con una sola tecla, **CERRAR** («Sale del programa»). Pulsar **CERRAR**.

> **Qué decir:** "Si la ventana se cerrara en el acto, el pasajero no vería lo que tiene que pagar."

### 10. Los logs — US-06 en la interfaz gráfica

En el terminal aparte:

```bash
grep -E "taximetro.gui|acceso_admin|cierre_" logs/taximetro.log
```

Se ven, por orden:
- el arranque y el cierre (`aplicacion_cerrada motivo=ventana_con_carrera`);
- `perfil_elegido`;
- `cierre_solicitado` y `cierre_cancelado` (el NO del paso 4);
- `acceso_admin_denegado motivo=contrasena_incorrecta` y `acceso_admin_concedido`;
- `tarifa_rechazada`;
- `salida_solicitada` / `salida_cancelada` / `salida_confirmada`.

> **Qué decir:** "Todo queda registrado para el equipo técnico, con los mismos nombres de evento en las dos interfaces. Fíjense en que el intento fallido de contraseña está, pero **lo que se tecleó no**: un error de contraseña suele ser una errata de la buena. Y si algún día fallara algo dentro de la interfaz, quedaría aquí con todo el detalle, mientras el conductor ve un aviso corto y puede seguir trabajando."

**Demuestra:** *"Registrar en todo momento qué está ocurriendo… y cualquier error."*

### 11. Una sola lógica para dos interfaces — refactorización

En el terminal aparte, arrancar el CLI de la Fase 2:

```bash
python -m taximetro.taximetro_app
```

- El banner ya enseña las **tarifas cambiadas desde la ventana** (0,03 y 0,06).
- **Administrador** pide **la misma contraseña**: `Taxi` se rechaza y `taxi` entra.
- **Ver histórico** lista las **dos carreras hechas en la interfaz gráfica**.

> **Qué decir:** "Las dos interfaces son dos formas de usar el mismo taxímetro. Ninguna tiene lógica propia de tarifas ni de carreras: las dos hablan con un único servicio, y un test comprueba en cada cambio que ninguna se lo salte. Por eso los mensajes, la contraseña, el histórico y la forma de cobrar son idénticos. En la Fase 4 ese servicio podrá sustituirse por la API sin tocar las pantallas."

**Demuestra:** *"La UI se apoya en la lógica de backend ya existente sin duplicarla"* y *"cada componente debe tener una responsabilidad clara y poder modificarse o sustituirse sin afectar al resto del sistema"*.

### 12. Tests y tablero

```bash
pytest
```

Más de 600 tests en verde y 99 % de cobertura, incluidos los de la interfaz gráfica. Abrir el tablero en la columna **Fase 3**.

> **Qué decir:** "Los tests de la interfaz abren ventanas de verdad, y además comprueban que en ninguna pantalla se corte un texto, con la fuente de Windows y con la de Linux, que es más ancha."

## Si algo sale mal

- **El Administrador dice «No se puede comprobar la contraseña. Avisa al equipo técnico.»**: falta `config/credenciales.json` (¿se borró con `config`?). Recuperarlo con `git checkout config/credenciales.json`.
- **La carrera no es la nº 1**: quedaba un `data/historial.csv` de antes; la numeración continúa a propósito. Explicarlo o volver a limpiar.

## Lo que queda por decir

- **Pantalla táctil real (T9.4).** La interfaz está diseñada con reglas táctiles (zonas de 88 px, texto de 24 px como mínimo) y se ha probado en un portátil al tamaño de una tablet. **Falta probarla en una tablet de verdad.**
- **Teclado en pantalla.** Para la contraseña y las tarifas se usa el teclado físico. En una tablet sin teclado haría falta un teclado en pantalla, que tkinter no abre solo (`docs/decisions-fase3.md`, *Password entry*).
- **Fase 4.** La interfaz gráfica sigue siendo la aplicación de a bordo. El panel web para el responsable de flota será otra interfaz sobre la API.
