"""Visor: el importe en dígitos de 7 segmentos, como un taxímetro clásico (T9.6)."""

from __future__ import annotations

import tkinter as tk

from taximetro.gui import estilo
from taximetro.utils import formato_euros

# Qué segmentos se encienden en cada cifra. Nombres clásicos:
#
#      a
#    f   b
#      g
#    e   c
#      d
SEGMENTOS = {
    "0": "abcdef",
    "1": "bc",
    "2": "abdeg",
    "3": "abcdg",
    "4": "bcfg",
    "5": "acdfg",
    "6": "acdefg",
    "7": "abc",
    "8": "abcdefg",
    "9": "abcdfg",
    " ": "",  # posición sin cifra: todos los segmentos apagados, pero visibles
}

# Formas de los segmentos en una celda de 60 × 110, las de la maqueta aprobada.
FORMAS = {
    "a": ((8, 6), (13, 1), (47, 1), (52, 6), (47, 11), (13, 11)),
    "b": ((54, 9), (59, 14), (59, 47), (54, 52), (49, 47), (49, 14)),
    "c": ((54, 58), (59, 63), (59, 96), (54, 101), (49, 96), (49, 63)),
    "d": ((8, 104), (13, 99), (47, 99), (52, 104), (47, 109), (13, 109)),
    "e": ((6, 58), (11, 63), (11, 96), (6, 101), (1, 96), (1, 63)),
    "f": ((6, 9), (11, 14), (11, 47), (6, 52), (1, 47), (1, 14)),
    "g": ((8, 55), (13, 50), (47, 50), (52, 55), (47, 60), (13, 60)),
}
CELDA_ANCHO, CELDA_ALTO = 60, 110

# Medidas en pantalla (px), las de la maqueta.
DIGITO_ANCHO, DIGITO_ALTO = 80, 147
HUECO = 10  # entre cifra y cifra
COMA_ANCHO = 24
EURO_ANCHO = 56
CIFRAS_ENTERAS = 3  # hasta 999,99 €; a partir de 1.000 € se añade una cuarta
DECIMALES = 2

# El ancho no cambia al pasar a 4 cifras: los dígitos se estrechan para caber.
ANCHO = (
    (CIFRAS_ENTERAS + DECIMALES) * DIGITO_ANCHO
    + (CIFRAS_ENTERAS + DECIMALES + 1) * HUECO
    + COMA_ANCHO
    + EURO_ANCHO
)
ALTO = DIGITO_ALTO


class Visor(tk.Canvas):
    """El importe en dígitos de 7 segmentos rojos, con los apagados visibles.

    Las cifras salen de `formato_euros()`: el visor redondea igual que el CLI,
    el histórico y el resto de la interfaz, porque no redondea él.

    `mostrar()` se llama cinco veces por segundo, así que no redibuja nada:
    solo recolorea los segmentos. Solo rehace el dibujo si cambia el número de
    cifras enteras (3 ↔ 4).
    """

    def __init__(self, padre: tk.Misc) -> None:
        """Crea el visor mostrando 0,00 €."""
        super().__init__(
            padre, width=ANCHO, height=ALTO, bg=estilo.VISOR_FONDO, highlightthickness=0
        )
        self._cifras: list[dict[str, int]] = []  # por posición: segmento → id del polígono
        self._texto = ""
        self._enteras = 0
        self.mostrar(0)

    @property
    def texto(self) -> str:
        """Lo que se lee en el visor, p. ej. '12,34 €' (tests y lectores de pantalla)."""
        return self._texto

    def mostrar(self, importe: float) -> None:
        """Pone `importe` en el visor."""
        texto = formato_euros(importe)
        enteros, decimales = texto.removesuffix(" €").split(",")
        enteras = max(CIFRAS_ENTERAS, len(enteros))
        if enteras != self._enteras:
            self._dibujar(enteras)
        caracteres = enteros.rjust(enteras) + decimales
        for segmentos, caracter in zip(self._cifras, caracteres):
            encendidos = SEGMENTOS[caracter]
            for nombre, poligono in segmentos.items():
                color = estilo.LED_ROJO if nombre in encendidos else estilo.LED_ROJO_APAGADO
                self.itemconfigure(poligono, fill=color)
        self._texto = texto

    def encendidos(self, posicion: int) -> str:
        """Los segmentos encendidos en la cifra `posicion` (0 = la de más a la izquierda)."""
        return "".join(
            nombre
            for nombre, poligono in self._cifras[posicion].items()
            if self.itemcget(poligono, "fill") == estilo.LED_ROJO
        )

    def _dibujar(self, enteras: int) -> None:
        """Dibuja de cero `enteras` cifras enteras, la coma, los decimales y el €."""
        self.delete(tk.ALL)
        self._cifras = []
        self._enteras = enteras
        total = enteras + DECIMALES
        # Lo que no son cifras ocupa siempre lo mismo; las cifras se reparten el resto.
        fijo = (total + 1) * HUECO + COMA_ANCHO + EURO_ANCHO
        ancho_cifra = (ANCHO - fijo) / total
        x = 0.0
        for posicion in range(total):
            if posicion == enteras:
                self._coma(x)
                x += COMA_ANCHO + HUECO
            self._cifras.append(self._cifra(x, ancho_cifra))
            x += ancho_cifra + HUECO
        self.create_text(
            ANCHO,
            ALTO,
            text="€",
            anchor=tk.SE,
            fill=estilo.LED_ROJO,
            font=estilo.fuente(72, negrita=True),
        )

    def _cifra(self, x: float, ancho: float) -> dict[str, int]:
        """Los 7 polígonos de una cifra con su esquina en (x, 0), apagados."""
        escala_x, escala_y = ancho / CELDA_ANCHO, DIGITO_ALTO / CELDA_ALTO
        return {
            nombre: self.create_polygon(
                *[coordenada for px, py in puntos for coordenada in (x + px * escala_x, py * escala_y)],
                fill=estilo.LED_ROJO_APAGADO,
                outline="",
            )
            for nombre, puntos in FORMAS.items()
        }

    def _coma(self, x: float) -> None:
        """La coma decimal, siempre encendida, abajo como en la maqueta."""
        escala = DIGITO_ALTO / CELDA_ALTO
        punto = ((4, 94), (14, 94), (14, 104), (4, 104))
        cola = ((9, 104), (14, 104), (10, 110), (6, 110))
        for forma in (punto, cola):
            self.create_polygon(
                *[c for px, py in forma for c in (x + px * escala, py * escala)],
                fill=estilo.LED_ROJO,
                outline="",
            )
