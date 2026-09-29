"""Franja: la cabecera en estilo visor de Inicio y Administrador."""

from __future__ import annotations

import tkinter as tk

from taximetro.interfaces.gui import estilo, iconos

MARGEN_LATERAL = 32  # a los lados de la franja y entre el título y lo que lo rodea
TAMANO_ICONO = 44
HUECO_ICONO = 16  # entre el icono y el título


class Franja(tk.Frame):
    """Franja negra con el título en rojo LED a la izquierda y un texto a la derecha.

    El texto (las tarifas vigentes) se parte en líneas para caber en lo que
    deja el título, que depende de la fuente del sistema: una etiqueta de
    tkinter no se ajusta sola, cortaría el texto.
    """

    def __init__(self, padre: tk.Misc, titulo: str, icono: str | None = None) -> None:
        """Crea la franja; `icono` es un nombre de `iconos.NOMBRES`."""
        super().__init__(
            padre, bg=estilo.VISOR_FONDO, height=estilo.FRANJA,
            highlightthickness=3, highlightbackground=estilo.VISOR_BORDE,
        )
        self.pack_propagate(False)
        if icono is not None:
            lienzo = tk.Canvas(
                self, width=TAMANO_ICONO, height=TAMANO_ICONO,
                bg=estilo.VISOR_FONDO, highlightthickness=0,
            )
            iconos.dibujar(lienzo, icono, TAMANO_ICONO, estilo.LED_ROJO)
            lienzo.pack(side=tk.LEFT, padx=(MARGEN_LATERAL, 0))
        self.titulo = tk.Label(
            self, text=titulo, font=estilo.FUENTE_MARCA, bg=estilo.VISOR_FONDO, fg=estilo.LED_ROJO
        )
        self.titulo.pack(side=tk.LEFT, padx=(HUECO_ICONO if icono else MARGEN_LATERAL, 0))
        self.texto = tk.Label(
            self, font=estilo.FUENTE_ETIQUETA, bg=estilo.VISOR_FONDO, fg=estilo.TEXTO_SECUNDARIO,
            justify=tk.RIGHT,
        )
        self.texto.pack(side=tk.RIGHT, padx=MARGEN_LATERAL)
        self._izquierda = MARGEN_LATERAL + (TAMANO_ICONO + HUECO_ICONO if icono is not None else 0)
        self.bind("<Configure>", lambda _evento: self._ajustar(), add="+")

    def _ajustar(self) -> None:
        """El ancho del texto: lo que queda a la derecha del título."""
        libre = (
            self.winfo_width() - 2 * int(self.cget("highlightthickness"))
            - self._izquierda - self.titulo.winfo_reqwidth() - 2 * MARGEN_LATERAL - estilo.SEPARACION
        )
        if libre > 0:
            self.texto.configure(wraplength=libre)
