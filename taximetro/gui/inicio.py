"""Inicio: la primera pantalla (elección de perfil).

PROVISIONAL (esqueleto de la US-09): solo el título y Salir, para que la
ventana abra con algo. La pantalla aprobada (tejas CONDUCTOR y ADMINISTRADOR,
franja de tarifas) llega con la tarea T9.7; ver `docs/diseno-interfaz-fase3.md`,
*1. Pantalla de inicio*.
"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from taximetro.gui import estilo
from taximetro.gui.pantalla import Pantalla
from taximetro.gui.tecla import Tecla

if TYPE_CHECKING:
    from taximetro.gui.app import App


class Inicio(Pantalla):
    """Pantalla de inicio (provisional)."""

    def __init__(self, app: App) -> None:
        """Construye el título y la tecla Salir en el lateral."""
        super().__init__(app)
        lateral = tk.Frame(self, bg=estilo.FONDO, width=estilo.LATERAL)
        lateral.pack(side=tk.RIGHT, fill=tk.Y, padx=estilo.MARGEN, pady=estilo.MARGEN)
        lateral.pack_propagate(False)
        self.salir = Tecla(
            lateral,
            "Salir",
            app.cerrar,
            variante=estilo.LATERAL_TECLA,
            alto=estilo.TECLA_LATERAL,
            fuente=estilo.FUENTE_TECLA_LATERAL,
        )
        self.salir.pack(side=tk.BOTTOM, fill=tk.X)
        self.titulo = tk.Label(
            self, text=estilo.TITULO, bg=estilo.FONDO, fg=estilo.LED_ROJO,
            font=estilo.FUENTE_MARCA,
        )
        self.titulo.pack(expand=True)
