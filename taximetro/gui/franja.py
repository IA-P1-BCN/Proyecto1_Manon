"""Franja: la cabecera en estilo visor de Inicio y Administrador (T9.7)."""

from __future__ import annotations

import tkinter as tk

from taximetro.gui import estilo, iconos


class Franja(tk.Frame):
    """Franja negra con el título en rojo LED a la izquierda y un texto a la derecha.

    El texto (las tarifas vigentes) se ajusta a `ancho_texto` px, partiéndose
    en líneas si no cabe: una etiqueta de tkinter no se ajusta sola.
    """

    def __init__(
        self, padre: tk.Misc, titulo: str, icono: str | None = None, ancho_texto: int = 700
    ) -> None:
        """Crea la franja; `icono` es un nombre de `iconos.NOMBRES`."""
        super().__init__(
            padre, bg=estilo.VISOR_FONDO, height=estilo.FRANJA,
            highlightthickness=3, highlightbackground=estilo.VISOR_BORDE,
        )
        self.pack_propagate(False)
        if icono is not None:
            lienzo = tk.Canvas(self, width=44, height=44, bg=estilo.VISOR_FONDO, highlightthickness=0)
            iconos.dibujar(lienzo, icono, 44, estilo.LED_ROJO)
            lienzo.pack(side=tk.LEFT, padx=(32, 0))
        self.titulo = tk.Label(
            self, text=titulo, font=estilo.FUENTE_MARCA, bg=estilo.VISOR_FONDO, fg=estilo.LED_ROJO
        )
        self.titulo.pack(side=tk.LEFT, padx=(16 if icono else 32, 0))
        self.texto = tk.Label(
            self, font=estilo.FUENTE_ETIQUETA, bg=estilo.VISOR_FONDO, fg=estilo.TEXTO_SECUNDARIO,
            justify=tk.RIGHT, wraplength=ancho_texto,
        )
        self.texto.pack(side=tk.RIGHT, padx=32)
