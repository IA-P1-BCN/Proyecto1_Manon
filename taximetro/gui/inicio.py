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

if TYPE_CHECKING:
    from taximetro.gui.app import App


class Inicio(Pantalla):
    """Pantalla de inicio (provisional)."""

    def __init__(self, app: App) -> None:
        """Construye el título y la tecla Salir."""
        super().__init__(app)
        self.titulo = tk.Label(
            self, text=estilo.TITULO, bg=estilo.FONDO, fg=estilo.TEXTO, font=("", 40)
        )
        self.titulo.pack(expand=True)
        self.salir = tk.Button(self, text="Salir", font=("", 24), command=app.cerrar)
        self.salir.pack(pady=40)
