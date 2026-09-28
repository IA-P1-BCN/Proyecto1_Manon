# Arquitectura del código — TTX-247 Taxímetro

Recorrido completo del paquete `taximetro/`: qué hace cada fichero y cómo
encaja con el resto. Es un documento descriptivo (**qué hay y cómo
funciona**), no de decisiones (**por qué se hizo así** vive en notas
personales, ver `docs/decisions-proceso.md` — ya no en este repositorio).
Referencia rápida para retomar el proyecto o para quien lo lea por primera
vez.

## Vista general

Tres capas, de fuera hacia dentro:

```
CLI (taximetro_app.py)  ──┐
                           ├──►  ServicioTaximetro  ──►  Taximetro  ──►  Carrera
GUI (gui/app.py + pantallas) ┘         │                    │
                                        │                    ├──► Tarifa
                                        ▼                    ├──► ConfigTarifas
                                       Auth                  └──► Historial
```

**Regla de oro del proyecto:** el CLI y la GUI solo importan de
`servicio_taximetro`, `logs` y `utils` — nunca de `carrera`, `tarifa`,
`taximetro`, `config_tarifas`, `historial` ni `auth` directamente.
`tests/test_estructura.py` lo comprueba con un test que falla si una
interfaz rompe esta regla. `ServicioTaximetro` es la única puerta al
dominio, y solo devuelve datos (instantáneas, números), nunca objetos
vivos — así en una futura Fase 4 se podría sustituir por un cliente HTTP
sin tocar ninguna pantalla.

Cada módulo de dominio tiene una responsabilidad y solo una:

| Módulo | Responsabilidad |
|---|---|
| `Carrera` | una carrera: su estado y su importe, con reloj propio |
| `Tarifa` | cuánto cuesta cada segundo según el estado, y su validación |
| `Taximetro` | qué carrera está activa ahora, y el ciclo iniciar → cerrar |
| `ConfigTarifas` | leer/guardar las tarifas en disco |
| `Historial` | leer/guardar las carreras cerradas en disco |
| `Auth` | comprobar la contraseña del Administrador |
| `ServicioTaximetro` | la fachada: traduce intención de la interfaz → llamada al dominio → datos |

---

## `taximetro/` — el dominio y el CLI

### `__init__.py`

Vacío salvo el docstring del paquete. No reexporta nada: cada módulo se
importa por su ruta completa (`from taximetro.carrera import Carrera`).

### `utils.py`

Una sola función, **`formato_euros(importe)`**: `12.3456` → `'12,35 €'`
(coma decimal, espacio antes del símbolo, redondeo a 2 decimales). Es el
**único** sitio donde se redondea para mostrar — internamente el importe se
guarda con toda su precisión, así el redondeo de un tramo no se arrastra al
siguiente. No usa el módulo `locale` de Python a propósito: el formato no
puede depender de qué configuración regional tenga instalada la máquina
(dev, CI o el portátil de la demo).

### `logs.py`

**`configurar_logs(ruta)`** monta un `RotatingFileHandler` (1 MB por
fichero, 5 copias) colgado del logger raíz `"taximetro"`; todos los módulos
cuelgan de él (`logging.getLogger(__name__)`), así que un evento en
`carrera.py` o en `gui/app.py` acaba en el mismo `logs/taximetro.log`. Solo
la envuelve `__main__.py` / el bloque `if __name__ == "__main__"` de
`taximetro_app.py` — nunca el paquete en sí — así que los tests (que
importan el paquete) nunca escriben en disco; leen los eventos con el
`caplog` de pytest. Si el fichero no se puede abrir, cae a un
`NullHandler`: un log roto nunca puede impedir que el taxímetro arranque.

**`campos(**valores)`** da formato `clave=valor clave=valor` a los datos de
cada línea de log (los floats con dos decimales), para poder buscarlos con
`grep` sin parsear frases.

### `carrera.py`

La clase **`Carrera`**: una carrera de taxi, desde que se crea hasta que se
cierra. Guarda `id`, `estado` (`Estado.PARADO` / `Estado.EN_MOVIMIENTO`,
nace siempre en movimiento), `hora_inicio`/`hora_fin`, `distancia` (0.0,
reservado para una fase futura) e `importe`.

**Cómo acumula el importe — el mecanismo central del proyecto:** no hay un
temporizador ni un bucle que sume cada segundo. `Carrera` recuerda el
instante (`self._inicio_tramo`) en que empezó el tramo actual con el reloj
inyectado (`time.monotonic` por defecto). Cada vez que algo pide el importe
o cambia de estado, se resta "ahora" menos `_inicio_tramo`, se multiplica
por la tarifa del estado (`Tarifa.calcular_importe`) y se suma. Esto pasa
en tres sitios:

- **`cambiar_estado(nuevo)`** — cierra el tramo actual (lo suma a
  `self.importe`) y abre uno nuevo en el estado nuevo. Repetir el estado ya
  activo no hace nada.
- **`importe_actual(en=None)`** — de solo lectura: calcula lo que habría
  acumulado *sin mutar nada*, útil para "¿cuánto llevo?" sin cambiar de
  estado. `en` permite preguntar por un instante concreto (una lectura
  anterior del reloj), no solo por "ahora".
- **`finalizar(en=None, hora_fin=None)`** — cierra el último tramo y marca
  `hora_fin`. Con `en`/`hora_fin` explícitos cierra en un instante
  *anterior* a ahora — es lo que usa la "congelación" (ver `taximetro.py`)
  para que el pasajero no pague el tiempo que se tarda en confirmar
  FINALIZAR. `en` nunca puede ser anterior al último cambio de estado
  (`ValueError`): ese tramo ya se cobró a otra tarifa.

Sobre una carrera ya finalizada (`self.finalizada`), tanto `cambiar_estado`
como `finalizar` lanzan `CarreraFinalizadaError`; `importe_actual` en
cambio nunca falla — devuelve el total congelado, porque leer un dato no
debería poder romperse.

**Dos relojes, inyectados, nunca globales:** `reloj: Callable[[], float]`
(por defecto `time.monotonic`) mide tiempo transcurrido para el dinero —
monótono porque un reloj de pared puede saltar hacia atrás (NTP, cambio de
hora) y restaría importe en silencio. `calendario: Callable[[], datetime]`
(por defecto `datetime.now`) solo sella `hora_inicio`/`hora_fin`, datos para
mostrar, no para cobrar. Los tests sustituyen ambos por relojes falsos que
avanzan a mano, así nunca necesitan dormir tiempo real.

### `tarifa.py`

La clase **`Tarifa`**: cuántos €/segundo cobra cada estado. Por defecto,
las tarifas del brief del cliente (0,02 €/s parado, 0,05 €/s en
movimiento). Se valida **al construirse** — no puede existir una `Tarifa`
con valores imposibles — así el fichero editado a mano y el formulario del
Administrador pasan por la misma comprobación (`_validar`): tiene que ser
un número (no un booleano, que en Python es subclase de `int`), estar
entre 0 (exclusivo) y `TARIFA_MAXIMA` (1,00 €/s, un tope de cordura contra
tecleos por minuto en vez de por segundo), tener como mucho 2 decimales, y
la de parado no puede superar a la de en movimiento. `TarifaInvalidaError`
lleva qué campo falló, para que una pantalla pueda marcarlo en rojo sin
repetir las reglas.

**`calcular_importe(estado, segundos)`** es el único cálculo real:
`tarifas[estado] * segundos`. Lo llama `Carrera` cada vez que cierra un
tramo.

### `config_tarifas.py`

La clase **`ConfigTarifas`**: lee y escribe `config/tarifas.json`
(`{"parado": 0.02, "en_movimiento": 0.05}`). Solo sabe de ficheros; las
reglas de qué es una tarifa válida son de `Tarifa`, no de aquí.
**`cargar()` nunca falla**: si el fichero no existe, lo crea con los
valores por defecto; si existe pero está corrupto (JSON roto, campo que
falta, valores inválidos), usa los valores por defecto en memoria **y no
toca el fichero** — sobrescribirlo borraría el error que un técnico tiene
que poder ver y corregir a mano. `guardar()` si acaso levanta `OSError`
(disco lleno, permisos), que sube hasta la interfaz.

### `historial.py`

La clase **`Historial`**: el registro de carreras cerradas, en
`data/historial.csv`. Dos dataclasses inmutables acompañan la clase:
**`RegistroCarrera`** (una fila: carrera, horas, importe, distancia) y
**`ResumenDia`** (las carreras de un día + su `total`, calculado como
`round(sum(...), 2)`).

**`registrar(carrera)`** añade una fila al final del fichero — nunca
reescribe el CSV entero, así un cierre inesperado a mitad de escritura no
puede corromper carreras ya guardadas. Escribe la cabecera solo si el
fichero es nuevo. Guarda el importe ya redondeado a céntimos: lo que de
verdad se cobró al pasajero, así el total del día cuadra exactamente con
la suma de los tickets. **`registros()`** lee todo el CSV; una fila
ilegible (editada a mano, o una escritura cortada) se salta con un aviso
en el log en vez de romper la lectura de las demás. **`resumen_del_dia(fecha)`**
filtra por `hora_fin` (no `hora_inicio`): una carrera que cruza la
medianoche se cuadra el día en que termina. **`ultimo_numero()`** da el
número de la última carrera guardada, para que `Taximetro` siga numerando
sin repetirse tras un reinicio.

### `auth.py`

La clase **`Auth`**: comprueba la contraseña del Administrador contra
`config/credenciales.json`, que solo contiene un algoritmo, una sal y un
hash — nunca la contraseña. **`comprobar(contrasena)`** relee el fichero
en cada llamada (un cambio del equipo técnico vale sin reiniciar el
programa), calcula el hash `scrypt` de lo tecleado con la sal guardada, y
compara con **`hmac.compare_digest`** — no `==` — para que el tiempo de
respuesta no varíe según en qué byte falla la comparación (ataque de
temporización). Cualquier fallo de lectura (fichero ausente, JSON roto,
parámetros que `scrypt` rechaza) se convierte en `CredencialesError`, que
**nunca** significa "contraseña correcta": ante la duda, la puerta queda
cerrada. La contraseña tecleada no se registra en el log jamás, ni cuando
es incorrecta.

`generar_credenciales()` (estático) es lo que produjo el fichero de la
demo; ninguna pantalla la llama — la usan los tests y, en su día, quien
puso la contraseña inicial.

### `taximetro.py`

La clase **`Taximetro`**: el orquestador del ciclo de vida de la carrera
activa. Es el dueño de la `Tarifa` vigente, de los dos relojes, y de la
numeración de carreras (el contador vive aquí, no en `Carrera`, para no
compartir estado global entre instancias). Construye cada `Carrera`
inyectándole la tarifa, los relojes y el id siguiente.

**El mecanismo de "congelar" — evita cobrar el tiempo de pensar:** cuando
el conductor pulsa FINALIZAR (o Ctrl+C, o la ✕ de la ventana), la interfaz
llama a **`congelar()`**, que guarda una `Congelacion` (una foto: qué
carrera, qué lectura del reloj, qué importe había en ese instante) sin
tocar la carrera todavía. Si se confirma, **`finalizar_carrera()`** cierra
la carrera *en el instante congelado*, no en el momento de la respuesta —
así el pasajero no paga los segundos que tarda el conductor en confirmar.
Si se cancela, **`descongelar()`** tira la foto y la carrera sigue
corriendo sin más — el tiempo de la pregunta sí se cobra esta vez, porque
el taxi seguía ocupado.

**`finalizar_carrera()`** cierra la carrera *antes* de intentar guardarla
en el histórico: si el disco falla, la carrera ya está cerrada y su total
ya está congelado en memoria — el cobro nunca se pierde por un problema de
E/S, solo el registro en el CSV (que la interfaz avisa aparte).
**`cambiar_tarifa()`** guarda primero en disco y solo si eso funciona
cambia la tarifa en memoria, para que fichero y taxímetro nunca discrepen;
falla con `CarreraActivaError` si hay una carrera en curso, porque al
pasajero se le cobra la tarifa que estaba vigente al empezar.

### `servicio_taximetro.py`

La clase **`ServicioTaximetro`**: la fachada — el único objeto del dominio
que el CLI y la GUI conocen. No tiene lógica propia de tarifas ni de
carreras; traduce cada intención de la interfaz (`iniciar_carrera`,
`cambiar_estado`, `congelar_importe`, `finalizar_carrera`,
`cambiar_tarifas`, `resumen_del_dia`, `comprobar_contrasena`) en una
llamada a `Taximetro` (o a `Auth`) y devuelve **datos**, nunca un objeto
vivo: **`InstantaneaCarrera`** (una foto de la carrera: id, estado,
importe, hora de inicio, duración), **`CarreraCerrada`** (el total más si
quedó guardado en el histórico), **`TarifasVigentes`**. Publica también las
excepciones del contrato (`CarreraActivaError`, `SinCarreraError`,
`TarifaInvalidaError`, y su propio **`AlmacenamientoError`**, que envuelve
cualquier `OSError` de disco) — las interfaces las importan de aquí, nunca
de los módulos de dominio.

**`por_defecto()`** (classmethod) monta el servicio real: `Taximetro` con
`ConfigTarifas()` y `Historial()` (rutas por defecto) y un `Auth()`. Es el
único sitio donde se conecta el dominio de verdad — lo llaman los dos
puntos de entrada (`__main__.py` y `taximetro_app.py`), así que ninguna
interfaz decide cómo se monta el dominio.

### `taximetro_app.py`

La clase **`TaximetroApp`**: el CLI, un bucle de menús numerados sobre
`ServicioTaximetro`. Arranca en un menú de perfil (Conductor /
Administrador / Salir); Conductor es el bucle de carreras (iniciar,
cambiar/parar-arrancar, ver importe, finalizar, ayuda), Administrador pide
contraseña y da acceso a cambiar tarifas y ver el histórico.

Puntos de diseño reutilizables en cualquier CLI de menú:

- **Los menús son tuplas** (`OPCIONES_INICIO`, `OPCIONES_CON_CARRERA`…);
  la posición decide el número (índice + 1). `_opcion()` traduce lo
  tecleado a una opción válida o `None` — cualquier cosa que no sea un
  número del menú actual da el mismo mensaje de error.
- **`cambiar` es una sola opción con dos caras** (PARAR/ARRANCAR): el menú
  siempre ofrece la acción *contraria* al estado actual, así el conductor
  no tiene que saber en qué estado está para saber qué pulsar.
- **`entrada`/`salida`/`entrada_oculta` se inyectan** en el constructor
  (por defecto `input`/`print`/`leer_contrasena`), así los tests pueden
  guionizar una sesión completa (una lista de respuestas dentro, las
  líneas impresas fuera) sin tocar stdin/stdout de verdad.
  **`leer_contrasena()`** usa `getpass` en una terminal real, pero cae a
  `input()` normal si la entrada está redirigida (un pipe, un fichero) —
  necesario en Windows, donde `getpass` ignora la entrada redirigida y se
  quedaría esperando una tecla que nunca llega.
- **Ctrl+C y EOF se gestionan distinto según haya o no carrera activa.**
  Sin carrera, Ctrl+C sale limpio (no hay importe que perder). Con carrera,
  Ctrl+C pide confirmación (`_confirmar_salida`, con el mismo mecanismo de
  "congelar" que la GUI); un segundo Ctrl+C durante la pregunta cuenta como
  "No" (para que un doble toque nervioso no cierre la carrera). EOF nunca
  es reintentable, así que con carrera activa cierra directamente en vez
  de reintentar un bucle infinito.
- **La foto de la carrera (`InstantaneaCarrera`) se pide de nuevo tras
  cada entrada del usuario**, nunca se reutiliza la de antes de esperar el
  `input()`: si no, el importe mostrado sería el de antes de que el
  conductor tecleara, no el actual.

El bloque `if __name__ == "__main__":` es el único punto que configura los
logs y monta `ServicioTaximetro.por_defecto()` — el resto de la clase
nunca toca disco por sí misma, así los tests la instancian con un servicio
en memoria.

---

## `taximetro/gui/` — la interfaz táctil (tkinter)

Un módulo por pantalla, todas heredando de `Pantalla`, más un puñado de
módulos de infraestructura visual compartida (`estilo`, `tecla`, `visor`,
`franja`, `iconos`). Igual que el CLI, **todo el paquete `gui/` solo habla
con `ServicioTaximetro`** — nunca con `Carrera`, `Taximetro`, etc.

### `__init__.py`

Solo el docstring del subpaquete: un módulo por pantalla, `app.App` es la
ventana que las muestra de una en una.

### `estilo.py`

El "CSS" del proyecto: tkinter no tiene hojas de estilo, así que todas las
medidas, colores y fuentes viven aquí y ninguna pantalla lleva un valor
suelto. Las medidas son píxeles de la resolución de referencia (1280×800,
una tablet de 10" en horizontal): márgenes, tamaño mínimo de zona táctil
(`ZONA_TACTIL_MIN = 88`, ≈15 mm a un brazo de distancia), alturas de cada
tecla, tamaño del visor, etc. Los colores están agrupados por función
(fondo, paneles, texto, los rojos del LED, verde/ámbar de
movimiento/parado) y cada estado del vehículo tiene **color y texto a la
vez** (`AspectoEstado`) — nunca solo color, por daltonismo o un vistazo de
reojo. **`fuente(px, negrita)`** construye una tupla de fuente de tkinter y
**rechaza cualquier tamaño por debajo de `TEXTO_MIN` (24 px)** con una
excepción: la regla del texto mínimo no se puede romper sin que algo
falle de inmediato. `aclarar(color)` mezcla un color con blanco (para el
efecto "pulsado" de una tecla).

### `iconos.py`

**`dibujar(lienzo, nombre, tamano, color)`** dibuja iconos (taxi, candado,
tarifas, histórico) a mano con primitivas de `Canvas` (líneas, arcos,
rectángulos) sobre una rejilla de 24×24 que se escala al tamaño pedido —
tkinter no sabe cargar SVG, y así no hace falta ningún fichero de imagen
en el repositorio.

### `tecla.py`

La clase **`Tecla`**: el botón táctil grande y plano de toda la interfaz.
Un `tk.Button` normal no sirve — mide su alto en líneas de texto y solo
admite una fuente — así que `Tecla` es un `tk.Frame` con una etiqueta de
título y otra de subtítulo más pequeño, con un alto fijo en píxeles
(nunca por debajo de `estilo.ZONA_TACTIL_MIN`, si no levanta `ValueError`).

Dos mecanismos notables:

- **Actúa al soltar, no al pulsar** (`_al_soltar` comprueba con
  `_contiene()` que el dedo sigue dentro del rectángulo de la tecla): quien
  pone el dedo y se arrepiente puede deslizarlo fuera antes de soltar,
  como en un botón físico. Mientras está pulsada se aclara (`_pintar`).
- **El texto se ajusta solo al ancho real de la tecla** (`_ajustar`, ligado
  al evento `<Configure>`): la fuente del sistema cambia de una máquina a
  otra (DejaVu Sans en Linux es más ancha que Segoe UI en Windows), y una
  etiqueta de tkinter no envuelve ni encoge su texto sola — lo cortaría
  sin avisar. La función suelta **`cabe()`** prueba tamaños de fuente de
  mayor a menor hasta encontrar el más grande que entra en el ancho
  disponible, sin bajar nunca de `TEXTO_MIN`.

### `visor.py`

La clase **`Visor`**: el importe en dígitos de 7 segmentos rojos, como un
taxímetro de verdad — con los segmentos **apagados también visibles**
(rojo muy oscuro), no invisibles, para que se lea como un display real.
Cada dígito es 7 polígonos (`FORMAS`) coloreados según qué segmentos
enciende cada carácter (`SEGMENTOS`). **`mostrar(importe)`** se llama
varias veces por segundo desde `PantallaTaximetro`, así que **nunca
redibuja**: solo recolorea los polígonos ya existentes
(`itemconfigure(..., fill=...)`), y solo reconstruye el dibujo entero si
cambia el número de cifras enteras — al pasar de 999,99 € a 1.000,00 € el
visor pasa de 3 a 4 cifras enteras **sin cambiar de ancho total**: los
dígitos se estrechan para caber, una decisión explícita registrada al
programarlo. Las cifras siempre salen de `formato_euros()`, así el visor
redondea exactamente igual que el CLI y el histórico.

### `franja.py`

La clase **`Franja`**: la cabecera negra en estilo visor (título en rojo
LED a la izquierda, texto secundario a la derecha) que usan las pantallas
de Inicio y Administrador. El texto de la derecha se ajusta
(`wraplength`) al ancho que deja libre el título, calculado en cada
`<Configure>` porque ese ancho depende de la fuente del sistema.

### `pantalla.py`

La clase base **`Pantalla`** (hereda de `tk.Frame`): lo que comparten
todas las pantallas.

- **`columnas()`** monta el esqueleto común a toda la interfaz: una
  columna principal y una lateral fija de 240 px a la derecha (donde
  siempre están Volver/Ayuda/Salir), para que esas acciones estén siempre
  en el mismo sitio en cualquier pantalla.
- **`servicio`** (propiedad) es el único acceso al dominio que tiene una
  pantalla — lo pide a `app.servicio`.
- **`programar(ms, funcion)`** envuelve `after()` de tkinter llevando la
  cuenta de los temporizadores activos; **`destroy()`** los cancela todos
  antes de destruir la pantalla. Sin esto, un refresco programado (el
  importe cada 200 ms) podría dispararse sobre widgets ya destruidos tras
  cambiar de pantalla.
- **`al_cerrar_ventana()`** por defecto no hace nada especial (devuelve
  `False`, "ciérrate"); `PantallaTaximetro` la sobreescribe para poder
  preguntar antes si hay una carrera en curso.

### `confirmacion.py`

La clase **`Confirmacion`**: el panel SÍ/NO a pantalla completa
(FINALIZAR, o cerrar la ventana con una carrera en curso). Tapa toda la
pantalla mientras está abierto (nada más se puede pulsar). **SÍ va a la
izquierda y NO a la derecha, justo donde estaba la tecla FINALIZAR**: un
doble toque accidental sobre FINALIZAR cae encima de NO, no de SÍ —
decisión de diseño explícita contra el toque accidental. `abrir()` recibe
la pregunta, el importe ya formateado y qué hace cada tecla; el propio
panel no sabe nada de carreras ni de importes, solo pinta lo que le pasan.

### `app.py`

La clase **`App`**: la ventana de tkinter y el cambio de pantalla. Solo
ella conoce la ventana real; las pantallas se piden unas a otras a través
de **`mostrar(tipo, **datos)`**, que destruye la pantalla actual
(cancelando sus temporizadores) y monta la nueva. Arranca siempre en
`Inicio`.

- **`al_cerrar_ventana()`** (ligada al protocolo `WM_DELETE_WINDOW`, la ✕
  de la ventana) delega primero en la pantalla actual
  (`pantalla.al_cerrar_ventana()`) — si esta devuelve `True` (tiene algo
  que preguntar), no cierra nada; si no, cierra el programa.
- **`error_en_callback`** está enganchada a `report_callback_exception`
  del intérprete Tk: **tkinter por diseño traga las excepciones dentro de
  un botón o un `after()`**, las imprime por consola y sigue como si nada.
  Sin este enganche, "registra cualquier error" (US-06) fallaría en
  silencio para toda la interfaz gráfica. Aquí se registra con su traza
  completa y se muestra un aviso corto al conductor (`avisar()`); el
  programa sigue vivo — una carrera en curso no se pierde por un fallo al
  pintar un widget.
- **`ejecutar()`** usa `wait_window()`, no `mainloop()`: con la ventana
  real hacen lo mismo, pero `wait_window()` también devuelve el control al
  cerrarse una ventana `Toplevel`, que es la que usan los tests (`raiz` se
  inyecta para poder pasarles una ventana oculta compartida en vez de un
  `Tk()` nuevo por test).

### `inicio.py`

La clase **`Inicio`**: la primera pantalla — elegir perfil. Dos tejas
grandes (CONDUCTOR dos tercios del ancho, con icono de taxi; ADMINISTRADOR
un tercio, con candado) más Salir en el lateral. CONDUCTOR abre
`PantallaTaximetro` directamente; ADMINISTRADOR pasa primero por
`Contrasena`. Los imports de las otras pantallas están dentro de los
métodos (`abrir_taximetro`, `pedir_contrasena`), no arriba del módulo, para
evitar un import circular entre pantallas que se abren unas a otras.

### `contrasena.py`

La clase **`Contrasena`**: un campo enmascarado, ENTRAR (o Enter) y
Cancelar, sin límite de intentos. **`entrar()`** llama a
`servicio.comprobar_contrasena()` — la misma comprobación que usa el CLI —
y, si acierta, pasa a `Administrador`; si falla, limpia el campo y muestra
el mensaje en rojo con el borde del campo también en rojo. Si las
credenciales no se pueden leer del todo (`AlmacenamientoError`), el
mensaje es distinto ("avisa al equipo técnico"): no es lo mismo que una
contraseña incorrecta, y nunca se entra por defecto.

### `administrador.py`

La clase **`Administrador`**: el menú tras la contraseña, misma estructura
que `Inicio` pero con las tejas CAMBIAR TARIFAS y VER HISTÓRICO. Volver
lleva a `Inicio` sin más — para volver a entrar aquí hay que teclear la
contraseña otra vez, no queda una sesión abierta.

### `tarifas.py`

La clase **`CambiarTarifas`**: un formulario con los dos campos (parado,
en movimiento) precargados con las tarifas vigentes. **`guardar()`**
convierte lo tecleado a número (acepta coma o punto decimal), y si algo
falla —no es un número, la `Tarifa` no es válida
(`TarifaInvalidaError`, con el mensaje de dominio tal cual), o no se pudo
escribir el fichero (`AlmacenamientoError`)— **no cambia nada** y marca en
rojo el campo culpable. Las reglas de qué es una tarifa válida son
enteramente del dominio (`Tarifa._validar`); esta pantalla solo traduce
texto a número y pinta el resultado.

### `historico.py`

La clase **`Historico`**: la tabla del día (Nº, Inicio, Fin, Importe) en
filas grandes, con ▲/▼ en el lateral para paginar (`estilo.FILAS_HISTORICO`
filas a la vez) — una barra de scroll normal es demasiado fina para un
dedo. El total del día se pinta en rojo LED en una caja aparte. `_cargar()`
pide `resumen_del_dia()` al servicio; si el histórico no se puede leer,
muestra un aviso en vez de la tabla.

### `taximetro.py` (clase `PantallaTaximetro`)

La pantalla principal — el taxímetro que ve el conductor, en estado LIBRE
u OCUPADO. Se llama `PantallaTaximetro` (no `Taximetro`, que ya es la clase
de dominio) para no confundir las dos. Es el fichero más largo del
proyecto porque reúne visor, teclas, lateral, panel de ayuda y el panel de
confirmación en una sola pantalla que cambia de aspecto según haya o no
carrera activa.

- **El refresco en vivo:** con carrera activa, `_pintar()` programa
  `_refrescar()` cada `REFRESCO_MS` (200 ms — a la tarifa más alta,
  0,05 €/s, un céntimo tarda exactamente 200 ms en aparecer, así el visor
  nunca se salta uno visualmente). `_refrescar()` vuelve a pedir
  `estado_actual()` al servicio (nunca reutiliza el dato de antes) y se
  reprograma sola; en cuanto no hay carrera, deja de reprogramarse — no
  hace falta pararla desde fuera.
- **FINALIZAR usa el mismo mecanismo de "congelar" que el Ctrl+C del CLI:**
  `pedir_finalizar()` llama a `congelar_importe()` *antes* de abrir el
  panel de confirmación, así el importe que se muestra y el que se cobrará
  si se confirma son el mismo, congelado en el instante de la pulsación —
  no el que haya cuando el conductor termine de leer la pregunta.
  `seguir()` (NO, SEGUIR) descongela y la carrera sigue corriendo sin más.
- **La ✕ de la ventana** (`al_cerrar_ventana`, llamada desde `App`) sigue
  la misma lógica: sin carrera se cierra sin preguntar; con carrera abre el
  mismo panel de confirmación (reutilizando `Confirmacion`), y si el panel
  ya estaba abierto por otro motivo, la ✕ cuenta como "NO, SEGUIR" — un
  clic nervioso repetido nunca cierra una carrera sin querer.
- **"SÍ, FINALIZAR Y SALIR"** (confirmar la ✕ con carrera activa) cierra la
  carrera pero **no cierra la ventana en el acto**: deja el total a la
  vista en el visor con una única tecla, CERRAR — cerrar de golpe
  escondería el importe antes de que el pasajero llegue a verlo.

---

## Fuera del código: `tests/`, `config/`, `data/`, `logs/`

No forman parte de "la app" en el sentido de lógica de negocio, pero
completan el cuadro:

- **`tests/`** — un fichero de test por módulo de `taximetro/` (mismo
  nombre, `test_` delante), más `tests/gui/` para las pantallas.
  `conftest.py` da los relojes falsos que evitan que los tests tengan que
  dormir tiempo real. `test_estructura.py` es el único que no comprueba
  comportamiento: comprueba la forma del código (qué importa cada capa,
  qué parámetros son inyectables) para que un cambio que rompa esas
  reglas falle de inmediato y no se note meses después.
- **`config/`** — `tarifas.example.json` (el formato, versionado) y
  `tarifas.json`/`credenciales.json` (el estado real; el primero está en
  `.gitignore`, el segundo se versiona porque solo lleva sal y hash).
- **`data/`** — `historial.csv`, generado en marcha; no se versiona.
- **`logs/`** — `taximetro.log` y sus rotaciones; tampoco se versiona.

---

## Cómo se conecta todo: una carrera de principio a fin

1. `python -m taximetro` (GUI) o `python -m taximetro.taximetro_app` (CLI)
   configura los logs y llama a **`ServicioTaximetro.por_defecto()`**, que
   monta un `Taximetro` con `ConfigTarifas()` (lee `config/tarifas.json`) y
   `Historial()` (apunta a `data/historial.csv`), más un `Auth()`.
2. El conductor pulsa Iniciar/INICIAR CARRERA → la interfaz llama a
   `servicio.iniciar_carrera()` → `Taximetro.iniciar_carrera()` crea una
   **`Carrera`** nueva, en movimiento, con la tarifa vigente y los relojes
   inyectados.
3. Cada cambio de estado o consulta de importe pasa por
   `Carrera.cambiar_estado()` / `importe_actual()`, que acumulan usando
   `Tarifa.calcular_importe()` y el reloj monótono — nunca un bucle en
   segundo plano.
4. Al pedir el cierre (FINALIZAR, Ctrl+C, la ✕), la interfaz llama a
   `servicio.congelar_importe()` → `Taximetro.congelar()` toma una foto del
   instante. Si se confirma, `servicio.finalizar_carrera()` →
   `Taximetro.finalizar_carrera()` cierra la `Carrera` en ese instante
   congelado y la pasa a `Historial.registrar()` (que añade una fila a
   `data/historial.csv`). Si se cancela, `seguir_carrera()` descarta la
   foto y la carrera sigue.
5. El total se muestra con `formato_euros()` — el único sitio que
   redondea — igual en el CLI, en el visor de 7 segmentos y en la tabla
   del histórico.
