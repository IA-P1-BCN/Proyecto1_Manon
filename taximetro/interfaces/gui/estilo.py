"""El tema de la interfaz gráfica: medidas, colores y fuentes.

tkinter no tiene CSS: este módulo hace su papel. Todos los valores salen de la
maqueta aprobada y de `docs/diseno-interfaz-fase3.md`, y ninguna pantalla lleva
colores ni tamaños sueltos.

**Se adapta al tamaño de la ventana.** Las medidas base son píxeles de una
resolución de referencia y hay dos disposiciones: la horizontal (1280 × 800,
tablet de 10") y la vertical (720 × 1280, tablet en vertical o ventana
estrecha). `aplicar(ancho, alto)` elige la que mejor aprovecha la ventana,
calcula la escala y recalcula las medidas y las fuentes: por eso `MARGEN`,
`TEJA`, `FUENTE_TITULO`… son variables del módulo que cambian. Las pantallas
las leen al construirse (`estilo.MARGEN`, nunca `from estilo import MARGEN`,
que se quedaría con una copia vieja). Ni las zonas táctiles (88 px) ni el
texto (24 px) bajan nunca de su mínimo, sea cual sea la escala.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from taximetro.application.servicio_taximetro import Estado

TITULO = "Taxímetro TTX-247"

HORIZONTAL, VERTICAL = "horizontal", "vertical"

ANCHO, ALTO = 1280, 800  # referencia horizontal
ANCHO_VERTICAL, ALTO_VERTICAL = 720, 1280  # referencia vertical
ESCALA_MIN, ESCALA_MAX, PASO_ESCALA = 0.75, 2.5, 0.05  # por debajo de 0,75 los mínimos de 24 y 88 px no caben
# La ventana más pequeña en la que todo cabe, según la disposición (ancho, alto): una ventana
# no puede ser a la vez estrecha (vertical) y baja (horizontal), así que `App` cambia el mínimo
# con la disposición.
TAMANO_MIN = {HORIZONTAL: (960, 640), VERTICAL: (560, 1000)}

ZONA_TACTIL_MIN = 88  # ≈ 15 mm en una tablet de 10", a un brazo de distancia
TEXTO_MIN = 24  # nada más pequeño en ninguna pantalla, ni siquiera la ayuda
SEPARACION_MIN = 24  # entre teclas: evita pulsar FINALIZAR queriendo PARAR
LATERAL_MIN = 208  # ancho mínimo de la columna lateral: cabe «Coma o punto:» a 24 px

# Medidas a escala 1, con el mínimo que nunca se rebasa: (base, mínimo).
_MEDIDAS = {
    "MARGEN": (24, 12),  # borde de la ventana
    "SEPARACION": (24, SEPARACION_MIN),  # entre teclas y bloques
    "TECLA_PRINCIPAL_MIN": (120, 120),  # Iniciar, Parar/Arrancar, Finalizar
    "TECLA_LATERAL": (96, ZONA_TACTIL_MIN),
    "TECLA_CONFIRMAR": (220, ZONA_TACTIL_MIN),  # SÍ, FINALIZAR / NO, SEGUIR
    "TECLA_ENTRAR": (160, ZONA_TACTIL_MIN),
    "TECLA_GUARDAR": (120, ZONA_TACTIL_MIN),
    "CAMPO": (96, ZONA_TACTIL_MIN),  # alto de los campos de texto
    "LAMPARA": (72, 48),  # alto de las lámparas OCUPADO / LIBRE
    "FILA": (64, 44),  # filas del histórico
    "DATOS": (112, 88),  # fila con Carrera / Tiempo / Inicio (solo vertical)
}

# Lo que cambia de una disposición a otra, a escala 1.
_POR_DISPOSICION = {
    HORIZONTAL: {
        "LATERAL": 240,  # ancho de la columna de la derecha (Ayuda, Volver, Salir…)
        "VISOR": 420,  # alto del visor del taxímetro
        "FRANJA": 108,  # alto de la franja superior de Inicio y Administrador
        "AYUDA_ANCHO": 780,  # panel de ayuda
        "CONFIRMACION_ANCHO": 1040,  # panel SÍ / NO
    },
    VERTICAL: {
        "LATERAL": 96,  # alto de la fila de abajo (Ayuda, Volver, Salir…)
        "VISOR": 500,
        "FRANJA": 156,  # título y tarifas en dos líneas
        "AYUDA_ANCHO": 672,
        "CONFIRMACION_ANCHO": 672,
    },
}
FILAS_POR_DISPOSICION = {HORIZONTAL: 6, VERTICAL: 8}  # filas del histórico a la vez; ▲ ▼ para el resto

DISPOSICION = HORIZONTAL
ESCALA = 1.0
VERTICAL_ACTIVA = False  # True si `DISPOSICION` es la vertical (para las pantallas)


def decidir(ancho: int, alto: int) -> tuple[str, float]:
    """La disposición y la escala que mejor aprovechan una ventana de `ancho` × `alto`.

    Cada disposición da la escala a la que cabe su referencia entera; gana la
    que da la mayor y, en un empate, la horizontal. La escala se redondea hacia
    abajo a pasos de `PASO_ESCALA`, para que nunca sobre contenido, y se limita
    a `ESCALA_MIN`–`ESCALA_MAX`.
    """
    horizontal = min(ancho / ANCHO, alto / ALTO)
    vertical = min(ancho / ANCHO_VERTICAL, alto / ALTO_VERTICAL)
    disposicion, escala = (VERTICAL, vertical) if vertical > horizontal else (HORIZONTAL, horizontal)
    escala = min(max(escala, ESCALA_MIN), ESCALA_MAX)
    return disposicion, round(int(escala / PASO_ESCALA + 1e-9) * PASO_ESCALA, 2)


def tamano_minimo() -> tuple[int, int]:
    """La ventana más pequeña (ancho, alto) en la que cabe todo, en la disposición activa."""
    return TAMANO_MIN[DISPOSICION]


def px(valor: float) -> int:
    """`valor` (píxeles a escala 1) a la escala actual, nunca menos de 1 px."""
    return max(1, round(valor * ESCALA))


def _calcular_medidas(disposicion: str, escala: float) -> dict[str, int]:
    """Todas las medidas en píxeles para una disposición y una escala."""
    medidas = {
        nombre: max(minimo, round(base * escala)) for nombre, (base, minimo) in _MEDIDAS.items()
    }
    medidas.update({n: max(1, round(v * escala)) for n, v in _POR_DISPOSICION[disposicion].items()})
    medidas["FILAS_HISTORICO"] = FILAS_POR_DISPOSICION[disposicion]
    margen, separacion = medidas["MARGEN"], medidas["SEPARACION"]
    visor, franja, lateral = medidas["VISOR"], medidas["FRANJA"], medidas["LATERAL"]
    principal = medidas["TECLA_PRINCIPAL_MIN"]

    if disposicion == HORIZONTAL:
        medidas["LATERAL"] = max(medidas["LATERAL"], LATERAL_MIN)  # el texto no baja de 24 px
        alto = round(ALTO * escala)
        medidas["TECLA_TAXIMETRO"] = max(principal, alto - 2 * margen - visor - separacion)
        teja = max(principal, alto - 2 * margen - franja - separacion)
        medidas["TEJA"] = medidas["TEJA_PRINCIPAL"] = medidas["TEJA_SECUNDARIA"] = teja
    else:
        alto = round(ALTO_VERTICAL * escala)
        lateral = medidas["LATERAL"] = max(medidas["TECLA_LATERAL"], lateral)  # una tecla cabe
        sin_lateral = alto - 2 * margen - lateral - separacion  # queda encima de la fila de abajo
        teclas = sin_lateral - visor - separacion - medidas["DATOS"] - separacion
        medidas["TECLA_TAXIMETRO"] = max(principal, (teclas - separacion) // 2)
        tejas = sin_lateral - franja - separacion - separacion  # dos tejas y lo que las separa
        medidas["TEJA"] = max(principal, tejas // 2)
        medidas["TEJA_PRINCIPAL"] = max(principal, tejas * 2 // 3)
        medidas["TEJA_SECUNDARIA"] = max(principal, tejas - medidas["TEJA_PRINCIPAL"])
    return medidas


FONDO = "#1c1c1c"  # oscuro: no deslumbra de noche
PANEL = "#141414"  # recuadros del lateral y pantallas de Administrador
PANEL_BORDE = "#2f2f2f"
VISOR_FONDO = "#070707"
VISOR_BORDE = "#3b3b3b"
FILA_ALTERNA = "#1a1a1a"  # sombreado alterno del histórico

TEXTO = "#f0f0f0"
TEXTO_SECUNDARIO = "#cfcfcf"
TEXTO_ETIQUETA = "#9a9a9a"  # «Carrera», «Tiempo»… encima del dato
TEXTO_ROTULO = "#8a8a8a"  # IMPORTE / TOTAL A COBRAR bajo los dígitos

LED_ROJO = "#ff2a1a"  # dígitos del importe
LED_ROJO_APAGADO = "#260806"  # segmentos apagados, visibles como en un LED real
LED_VERDE = "#3ddc6e"  # en movimiento
LED_AMBAR = "#ffb020"  # parado

MENSAJE_ERROR = "#ff6b5e"
MENSAJE_OK = LED_VERDE
CAMPO_BORDE = "#4a4a4a"
CAMPO_BORDE_ERROR = "#c0392b"


@dataclass(frozen=True)
class Lampara:
    """Una lámpara del visor (OCUPADO / LIBRE), encendida o apagada."""

    fondo: str
    texto: str


OCUPADO_ENCENDIDA = Lampara(fondo="#c62828", texto="#ffffff")
OCUPADO_APAGADA = Lampara(fondo="#2b1111", texto="#6b3a3a")
LIBRE_ENCENDIDA = Lampara(fondo="#1e7a3c", texto="#ffffff")
LIBRE_APAGADA = Lampara(fondo="#0f2615", texto="#3f6b4a")


@dataclass(frozen=True)
class AspectoEstado:
    """Cómo se ve un estado del vehículo: siempre color **y** texto.

    El color solo no basta (daltonismo, un vistazo de reojo): el nombre del
    estado va siempre al lado.
    """

    color: str
    texto: str


ESTADOS = {
    Estado.EN_MOVIMIENTO: AspectoEstado(color=LED_VERDE, texto="EN MOVIMIENTO"),
    Estado.PARADO: AspectoEstado(color=LED_AMBAR, texto="PARADO"),
}


@dataclass(frozen=True)
class Variante:
    """Los colores de una tecla: fondo, borde y el color de su subtítulo."""

    fondo: str
    borde: str
    subtitulo: str

    @property
    def pulsada(self) -> str:
        """El fondo mientras se tiene pulsada: un poco más claro."""
        return aclarar(self.fondo)


VERDE = Variante(fondo="#1e6b37", borde="#2e8b4e", subtitulo="#d6eedd")  # Iniciar, Entrar…
ROJA = Variante(fondo="#8e1b17", borde="#c0392b", subtitulo="#f3d6d4")  # Finalizar
GRIS = Variante(fondo="#2d2d2d", borde="#4a4a4a", subtitulo=TEXTO_SECUNDARIO)
LATERAL_TECLA = Variante(fondo="#262626", borde="#4a4a4a", subtitulo=TEXTO_SECUNDARIO)


def aclarar(color: str, cuanto: float = 0.18) -> str:
    """`color` (#rrggbb) mezclado con blanco en la proporción `cuanto`."""
    rgb = [int(color[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(c + (255 - c) * cuanto):02x}" for c in rgb)


# Las del sistema, como la maqueta: tkinter no carga fuentes propias con
# facilidad. Si falta, Tk pone la suya por defecto.
FAMILIA = "Segoe UI" if sys.platform == "win32" else "DejaVu Sans"

Fuente = tuple[str, int, str]


def fuente(px: int, negrita: bool = False) -> Fuente:
    """Una fuente de `px` píxeles de alto a escala 1, para la opción `font=` de tkinter.

    El tamaño va en negativo porque así tkinter lo toma como píxeles y no como
    puntos: coincide con las medidas de la maqueta sea cual sea la pantalla.
    Se escala con la ventana, pero nunca baja de `TEXTO_MIN`; y rechaza pedir
    menos de `TEXTO_MIN` desde el principio, para que la regla del texto
    mínimo no se pueda romper sin darse cuenta.
    """
    if px < TEXTO_MIN:
        raise ValueError(f"Texto de {px} px: el mínimo de la interfaz es {TEXTO_MIN} px.")
    return (FAMILIA, -max(TEXTO_MIN, round(px * ESCALA)), "bold" if negrita else "normal")


# nombre → (px a escala 1, negrita)
_FUENTES = {
    "FUENTE_TITULO": (48, True),  # «Administrador», «Cambiar tarifas»
    "FUENTE_TECLA": (56, True),  # PARAR, FINALIZAR, INICIAR CARRERA, ENTRAR
    "FUENTE_TECLA_SUBTITULO": (26, False),  # «Termina y muestra el total»
    "FUENTE_TECLA_LATERAL": (28, True),  # Ayuda, Volver, Salir
    "FUENTE_LAMPARA": (30, True),  # OCUPADO / LIBRE
    "FUENTE_ESTADO": (34, True),  # EN MOVIMIENTO / PARADO
    "FUENTE_TARIFA": (28, False),  # 0,05 €/s
    "FUENTE_ETIQUETA": (24, False),  # «Carrera», «Tiempo»; IMPORTE
    "FUENTE_DATO": (34, True),  # «Nº 7», «00:04:12»
    "FUENTE_TEXTO": (28, False),  # ayuda, tabla del histórico
    "FUENTE_MENSAJE": (26, True),  # errores y confirmaciones
    "FUENTE_CAMPO": (44, True),  # campos de tarifas y contraseña
    "FUENTE_MARCA": (40, True),  # «TTX-247» en la franja superior
    "FUENTE_TECLA_CONFIRMAR": (48, True),  # SÍ, FINALIZAR / NO, SEGUIR
    "FUENTE_DETALLE": (30, False),  # «Importe a cobrar:» en el panel de confirmación
    "FUENTE_DETALLE_IMPORTE": (30, True),
    "FUENTE_TEJA_PRINCIPAL": (64, True),  # CONDUCTOR
    "FUENTE_TEJA": (48, True),  # CAMBIAR TARIFAS, VER HISTÓRICO
    # ADMINISTRADOR, en una teja de un tercio. El tamaño de la maqueta: si no cabe
    # (a 40 px mide 339 px con Segoe UI y la teja tiene 309), `Tecla` lo reduce.
    "FUENTE_TEJA_ESTRECHA": (40, True),
    "FUENTE_CONTRASENA": (40, False),  # el campo enmascarado
    "FUENTE_ETIQUETA_CAMPO": (30, False),  # «Parado o < 20 km/h», «€/s»
    "FUENTE_TITULO_HISTORICO": (44, True),
    "FUENTE_TOTAL": (56, True),  # total del día, en rojo LED
}


def aplicar(ancho: int, alto: int, forzar: bool = False) -> bool:
    """Adapta el tema a una ventana de `ancho` × `alto`; True si algo cambió.

    Recalcula las medidas y las fuentes. Si la disposición y la escala son las
    que ya había, no hace nada, salvo con `forzar` (p. ej. si cambió `FAMILIA`).
    """
    global DISPOSICION, ESCALA, VERTICAL_ACTIVA
    disposicion, escala = decidir(ancho, alto)
    if not forzar and (disposicion, escala) == (DISPOSICION, ESCALA):
        return False
    DISPOSICION, ESCALA, VERTICAL_ACTIVA = disposicion, escala, disposicion == VERTICAL
    globals().update(_calcular_medidas(disposicion, escala))
    globals().update({nombre: fuente(px_, negrita) for nombre, (px_, negrita) in _FUENTES.items()})
    return True


aplicar(ANCHO, ALTO, forzar=True)
