"""Inicio: la primera pantalla, elección de perfil.

Pantalla 1 de `docs/diseno-interfaz-fase3.md`: franja con las tarifas
vigentes, teja CONDUCTOR (la acción diaria, dos tercios del ancho) y teja
ADMINISTRADOR (con candado: pide contraseña). Salir, en el lateral.
"""

from __future__ import annotations

import logging
import tkinter as tk
from typing import TYPE_CHECKING

from taximetro.interfaces.gui import estilo
from taximetro.interfaces.gui.franja import Franja
from taximetro.interfaces.gui.pantalla import Pantalla
from taximetro.interfaces.gui.tecla import Tecla
from taximetro.infrastructure.logs import campos

if TYPE_CHECKING:
    from taximetro.interfaces.gui.app import App

logger = logging.getLogger("taximetro.interfaces.gui")


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
        self.conductor = Tecla(
            tejas, "CONDUCTOR", self.abrir_taximetro, variante=estilo.VERDE,
            alto=estilo.TEJA_PRINCIPAL, subtitulo="Abrir el taxímetro",
            fuente=estilo.FUENTE_TEJA_PRINCIPAL, icono="taxi",
        )
        self.administrador = Tecla(
            tejas, "ADMINISTRADOR", self.pedir_contrasena, variante=estilo.GRIS,
            alto=estilo.TEJA_SECUNDARIA, subtitulo="Tarifas e histórico\ncon contraseña",
            fuente=estilo.FUENTE_TEJA_ESTRECHA, icono="candado", tamano_icono=estilo.px(72),
        )
        self._colocar_tejas(tejas)

        self.salir = self.tecla_lateral(lateral, "Salir", app.cerrar)
        self.colocar_lateral(self.salir, side=tk.BOTTOM, fill=tk.X)

    def _colocar_tejas(self, tejas: tk.Frame) -> None:
        """CONDUCTOR (dos tercios) y ADMINISTRADOR (uno): lado a lado, o apiladas en vertical."""
        mitad = estilo.SEPARACION // 2
        if estilo.VERTICAL_ACTIVA:
            tejas.columnconfigure(0, weight=1)
            tejas.rowconfigure(0, weight=2)  # sin `uniform`: obligaría a sumar más de lo que se pide
            tejas.rowconfigure(1, weight=1)
            self.conductor.grid(row=0, column=0, sticky="nsew", pady=(0, mitad))
            self.administrador.grid(row=1, column=0, sticky="nsew", pady=(mitad, 0))
            return
        # Con la ventana pequeña, «ADMINISTRADOR» (24 px como mínimo) no cabe en un tercio.
        peso_conductor, peso_administrador = (2, 1) if estilo.ESCALA >= 1 else (3, 2)
        tejas.columnconfigure(0, weight=peso_conductor, uniform="teja")
        tejas.columnconfigure(1, weight=peso_administrador, uniform="teja")
        self.conductor.grid(row=0, column=0, sticky="ew", padx=(0, mitad))
        self.administrador.grid(row=0, column=1, sticky="ew", padx=(mitad, 0))

    def abrir_taximetro(self) -> None:
        """CONDUCTOR: el taxímetro, sin contraseña."""
        from taximetro.interfaces.gui.taximetro import PantallaTaximetro

        logger.info("perfil_elegido %s", campos(perfil="conductor"))
        self.app.mostrar(PantallaTaximetro)

    def pedir_contrasena(self) -> None:
        """ADMINISTRADOR: primero la contraseña (US-08)."""
        from taximetro.interfaces.gui.contrasena import Contrasena

        logger.info("perfil_elegido %s", campos(perfil="administrador"))
        self.app.mostrar(Contrasena)
