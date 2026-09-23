"""Iconos de la interfaz, dibujados con trazos en un `Canvas` (T9.7).

Los mismos de la maqueta aprobada (taxi, candado, tarifas, histórico), en una
cuadrícula de 24 × 24 que se escala al tamaño pedido. Con trazos y no con
imágenes: tkinter no dibuja SVG, y así no hay ficheros que cargar.
"""

from __future__ import annotations

import tkinter as tk

GROSOR = 1.8  # grosor del trazo en la cuadrícula de 24


def dibujar(lienzo: tk.Canvas, nombre: str, tamano: int, color: str) -> None:
    """Dibuja el icono `nombre` ocupando `tamano` × `tamano` px desde la esquina (0, 0)."""
    escala = tamano / 24
    grosor = max(1.0, GROSOR * escala)

    def puntos(*coordenadas: float) -> list[float]:
        return [c * escala for c in coordenadas]

    def linea(*coordenadas: float) -> None:
        lienzo.create_line(*puntos(*coordenadas), fill=color, width=grosor, joinstyle=tk.MITER)

    def rectangulo(x1: float, y1: float, x2: float, y2: float) -> None:
        lienzo.create_rectangle(*puntos(x1, y1, x2, y2), outline=color, width=grosor)

    if nombre == "taxi":
        linea(3, 16, 3, 12, 5, 7, 19, 7, 21, 12, 21, 16, 3, 16)
        linea(3, 12, 21, 12)
        linea(9, 7, 10, 4, 14, 4, 15, 7)
        for cx in (7, 17):
            lienzo.create_oval(*puntos(cx - 1.8, 14.7, cx + 1.8, 18.3), outline=color, width=grosor)
    elif nombre == "candado":
        rectangulo(5, 11, 19, 21)
        linea(8, 11, 8, 7)
        linea(16, 7, 16, 11)
        lienzo.create_arc(*puntos(8, 3, 16, 11), start=0, extent=180, style=tk.ARC, outline=color, width=grosor)
    elif nombre == "tarifas":
        linea(4, 6, 14, 6)
        linea(18, 6, 20, 6)
        rectangulo(14, 4, 18, 8)
        linea(4, 12, 7, 12)
        linea(11, 12, 20, 12)
        rectangulo(7, 10, 11, 14)
        linea(4, 18, 16, 18)
        rectangulo(16, 16, 20, 20)
    elif nombre == "historico":
        rectangulo(4, 3, 20, 21)
        linea(8, 8, 16, 8)
        linea(8, 12, 16, 12)
        linea(8, 16, 13, 16)
    else:
        raise ValueError(f"Icono desconocido: {nombre!r}")


NOMBRES = ("taxi", "candado", "tarifas", "historico")
