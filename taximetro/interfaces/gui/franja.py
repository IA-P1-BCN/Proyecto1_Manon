"""Franja: la cabecera en estilo visor de Inicio y Administrador."""

from __future__ import annotations

import tkinter as tk

from taximetro.interfaces.gui import estilo, iconos
from taximetro.interfaces.gui.pantalla import Pantalla

MARGEN_LATERAL = 32  # a los lados de la franja y entre el título y lo que lo rodea (a escala 1)
TAMANO_ICONO = 44
HUECO_ICONO = 16  # entre el icono y el título


class Franja(tk.Frame):
    """Franja negra con el título en rojo LED y, junto a él, las tarifas vigentes.

    En horizontal el título va a la izquierda y el texto a la derecha; en
    vertical, el título arriba y el texto debajo. El texto se parte en líneas
    para caber en lo que queda: una etiqueta de tkinter no se ajusta sola y
    cortaría el texto.
    """

    def __init__(self, padre: tk.Misc, titulo: str, icono: str | None = None) -> None:
        """Crea la franja; `icono` es un nombre de `iconos.NOMBRES`."""
        super().__init__(
            padre, bg=estilo.VISOR_FONDO, height=estilo.FRANJA,
            highlightthickness=3, highlightbackground=estilo.VISOR_BORDE,
        )
        self.pack_propagate(False)
        margen = estilo.px(MARGEN_LATERAL)
        cabecera = self._montar_cabecera(icono, titulo, margen)
        self.texto = tk.Label(
            self, font=estilo.FUENTE_ETIQUETA, bg=estilo.VISOR_FONDO, fg=estilo.TEXTO_SECUNDARIO,
        )
        if estilo.VERTICAL_ACTIVA:
            self.texto.configure(justify=tk.LEFT, anchor=tk.W)
            Pantalla.ajustar_al_ancho(self.texto)
            self.texto.pack(fill=tk.X, padx=margen)
            return
        self.texto.configure(justify=tk.RIGHT)
        self.texto.pack(side=tk.RIGHT, padx=margen)
        self._izquierda = margen + (estilo.px(TAMANO_ICONO + HUECO_ICONO) if icono is not None else 0)
        self.bind("<Configure>", lambda _evento: self._ajustar(), add="+")

    def _montar_cabecera(self, icono: str | None, titulo: str, margen: int) -> tk.Frame:
        """El icono (si lo hay) y el título; en vertical, en una fila propia arriba."""
        if estilo.VERTICAL_ACTIVA:
            cabecera = tk.Frame(self, bg=estilo.VISOR_FONDO)
            cabecera.pack(fill=tk.X, padx=margen, pady=(estilo.px(12), 0))
            destino, izquierda = cabecera, 0
        else:
            destino, izquierda = self, margen
        hueco = estilo.px(HUECO_ICONO)
        if icono is not None:
            tamano = estilo.px(TAMANO_ICONO)
            lienzo = tk.Canvas(
                destino, width=tamano, height=tamano, bg=estilo.VISOR_FONDO, highlightthickness=0,
            )
            iconos.dibujar(lienzo, icono, tamano, estilo.LED_ROJO)
            lienzo.pack(side=tk.LEFT, padx=(izquierda, 0))
        self.titulo = tk.Label(
            destino, text=titulo, font=estilo.FUENTE_MARCA, bg=estilo.VISOR_FONDO, fg=estilo.LED_ROJO
        )
        self.titulo.pack(side=tk.LEFT, padx=(hueco if icono else izquierda, 0))
        return destino

    def _ajustar(self) -> None:
        """El ancho del texto: lo que queda a la derecha del título."""
        libre = (
            self.winfo_width() - 2 * int(self.cget("highlightthickness"))
            - self._izquierda - self.titulo.winfo_reqwidth() - 2 * estilo.px(MARGEN_LATERAL)
            - estilo.SEPARACION
        )
        if libre > 0:
            self.texto.configure(wraplength=libre)
