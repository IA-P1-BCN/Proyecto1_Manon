"""Inicio: la primera pantalla, elección de perfil (T9.7).

Pantalla 1 de `docs/diseno-interfaz-fase3.md`: franja con las tarifas
vigentes, teja CONDUCTOR (la acción diaria, dos tercios del ancho) y teja
ADMINISTRADOR (con candado: pide contraseña). Salir, en el lateral.
"""

from __future__ import annotations

import logging
import tkinter as tk
from typing import TYPE_CHECKING

from taximetro.gui import estilo
from taximetro.gui.franja import Franja
from taximetro.gui.pantalla import Pantalla
from taximetro.gui.tecla import Tecla
from taximetro.logs import campos

if TYPE_CHECKING:
    from taximetro.gui.app import App

logger = logging.getLogger("taximetro.gui")


class Inicio(Pantalla):
    """Elección de perfil: Conductor o Administrador."""

    def __init__(self, app: App) -> None:
        """Monta la franja, las dos tejas y Salir."""
        super().__init__(app)
        principal, lateral = self.columnas()

        self.franja = Franja(principal, "TTX-247")
        self.franja.texto.configure(text=f"Tarifas vigentes: {self.resumen_tarifas()}")
        self.franja.pack(fill=tk.X)

        tejas = tk.Frame(principal, bg=estilo.FONDO)
        tejas.pack(fill=tk.BOTH, expand=True, pady=(estilo.SEPARACION, 0))
        tejas.columnconfigure(0, weight=2, uniform="teja")
        tejas.columnconfigure(1, weight=1, uniform="teja")
        self.conductor = Tecla(
            tejas, "CONDUCTOR", self.abrir_taximetro, variante=estilo.VERDE,
            alto=estilo.TEJA, subtitulo="Abrir el taxímetro",
            fuente=estilo.FUENTE_TEJA_PRINCIPAL, icono="taxi",
        )
        self.conductor.grid(row=0, column=0, sticky="ew", padx=(0, estilo.SEPARACION // 2))
        self.administrador = Tecla(
            tejas, "ADMINISTRADOR", self.pedir_contrasena, variante=estilo.GRIS,
            alto=estilo.TEJA, subtitulo="Tarifas e histórico\ncon contraseña",
            fuente=estilo.FUENTE_TEJA_ESTRECHA, icono="candado", tamano_icono=72,
        )
        self.administrador.grid(row=0, column=1, sticky="ew", padx=(estilo.SEPARACION // 2, 0))

        self.salir = self.tecla_lateral(lateral, "Salir", app.cerrar)
        self.salir.pack(side=tk.BOTTOM, fill=tk.X)

    def abrir_taximetro(self) -> None:
        """CONDUCTOR: el taxímetro, sin contraseña."""
        from taximetro.gui.taximetro import PantallaTaximetro

        logger.info("perfil_elegido %s", campos(perfil="conductor"))
        self.app.mostrar(PantallaTaximetro)

    def pedir_contrasena(self) -> None:
        """ADMINISTRADOR: primero la contraseña (US-08)."""
        from taximetro.gui.contrasena import Contrasena

        logger.info("perfil_elegido %s", campos(perfil="administrador"))
        self.app.mostrar(Contrasena)
