"""El tema de la interfaz gráfica: medidas, colores y fuentes (T9.5).

tkinter no tiene CSS: este módulo hace su papel. Todos los valores salen de la
maqueta aprobada y de `docs/diseno-interfaz-fase3.md`, y ninguna pantalla lleva
colores ni tamaños sueltos. Las medidas son píxeles de la resolución de
referencia, 1280 × 800 (tablet de 10" en horizontal).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from taximetro.servicio_taximetro import Estado

TITULO = "Taxímetro TTX-247"

# ----------------------------------------------------------------------
# Medidas (px)
# ----------------------------------------------------------------------

ANCHO, ALTO = 1280, 800
MARGEN = 24  # borde de la ventana
SEPARACION = 24  # entre teclas y bloques: evita pulsar FINALIZAR queriendo PARAR
LATERAL = 240  # columna de la derecha (Ayuda, Volver, Salir…)

ZONA_TACTIL_MIN = 88  # ≈ 15 mm en una tablet de 10", a un brazo de distancia
TECLA_PRINCIPAL_MIN = 120  # Iniciar, Parar/Arrancar, Finalizar
TECLA_LATERAL = 96
TECLA_CONFIRMAR = 220  # SÍ, FINALIZAR / NO, SEGUIR
TECLA_ENTRAR = 160
TECLA_GUARDAR = 150
CAMPO = 96  # alto de los campos de texto
VISOR = 420  # alto del visor del taxímetro
TECLA_TAXIMETRO = ALTO - 2 * MARGEN - VISOR - SEPARACION  # lo que queda bajo el visor: 308
LAMPARA = 72  # alto de las lámparas OCUPADO / LIBRE
AYUDA_ANCHO = 780  # panel de ayuda

TEXTO_MIN = 24  # nada más pequeño en ninguna pantalla, ni siquiera la ayuda

# ----------------------------------------------------------------------
# Colores
# ----------------------------------------------------------------------

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


# ----------------------------------------------------------------------
# Fuentes
# ----------------------------------------------------------------------

# Las del sistema, como la maqueta: tkinter no carga fuentes propias con
# facilidad. Si falta, Tk pone la suya por defecto.
FAMILIA = "Segoe UI" if sys.platform == "win32" else "DejaVu Sans"

Fuente = tuple[str, int, str]


def fuente(px: int, negrita: bool = False) -> Fuente:
    """Una fuente de `px` píxeles de alto, para la opción `font=` de tkinter.

    El tamaño va en negativo porque así tkinter lo toma como píxeles y no como
    puntos: coincide con las medidas de la maqueta sea cual sea la pantalla.
    Rechaza cualquier tamaño por debajo de `TEXTO_MIN`, para que la regla del
    texto mínimo no se pueda romper sin darse cuenta.
    """
    if px < TEXTO_MIN:
        raise ValueError(f"Texto de {px} px: el mínimo de la interfaz es {TEXTO_MIN} px.")
    return (FAMILIA, -px, "bold" if negrita else "normal")


FUENTE_TITULO = fuente(48, negrita=True)  # «Administrador», «Cambiar tarifas»
FUENTE_TECLA = fuente(56, negrita=True)  # PARAR, FINALIZAR, INICIAR CARRERA, ENTRAR
FUENTE_TECLA_SUBTITULO = fuente(26)  # «Termina y muestra el total»
FUENTE_TECLA_LATERAL = fuente(28, negrita=True)  # Ayuda, Volver, Salir
FUENTE_LAMPARA = fuente(30, negrita=True)  # OCUPADO / LIBRE
FUENTE_ESTADO = fuente(34, negrita=True)  # EN MOVIMIENTO / PARADO
FUENTE_TARIFA = fuente(28)  # 0,05 €/s
FUENTE_ETIQUETA = fuente(24)  # «Carrera», «Tiempo»; IMPORTE
FUENTE_DATO = fuente(34, negrita=True)  # «Nº 7», «00:04:12»
FUENTE_TEXTO = fuente(28)  # ayuda, tabla del histórico
FUENTE_MENSAJE = fuente(26, negrita=True)  # errores y confirmaciones
FUENTE_CAMPO = fuente(44, negrita=True)  # campos de tarifas y contraseña
FUENTE_MARCA = fuente(40, negrita=True)  # «TTX-247» en la franja superior
