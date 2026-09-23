"""Administrador: el menú de gestión (T9.7).

Pantalla 6 de `docs/diseno-interfaz-fase3.md`: la misma estructura que Inicio,
con las tejas CAMBIAR TARIFAS y VER HISTÓRICO. Solo se llega tras la
contraseña; Volver lleva a Inicio, y para entrar otra vez hay que teclearla.
"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from taximetro.gui import estilo
from taximetro.gui.franja import Franja
from taximetro.gui.pantalla import Pantalla
from taximetro.gui.tecla import Tecla

if TYPE_CHECKING:
    from taximetro.gui.app import App


class Administrador(Pantalla):
    """Menú de Administrador: tarifas e histórico."""

    def __init__(self, app: App) -> None:
        """Monta la franja, las dos tejas y Volver."""
        super().__init__(app)
        principal, lateral = self.columnas()

        # Con candado y título, a las tarifas les queda menos sitio: dos líneas.
        self.franja = Franja(principal, "ADMINISTRADOR", icono="candado", ancho_texto=460)
        self.franja.texto.configure(text=f"Tarifas vigentes: {self.resumen_tarifas()}")
        self.franja.pack(fill=tk.X)

        tejas = tk.Frame(principal, bg=estilo.FONDO)
        tejas.pack(fill=tk.BOTH, expand=True, pady=(estilo.SEPARACION, 0))
        tejas.columnconfigure((0, 1), weight=1, uniform="teja")
        comunes = {"variante": estilo.GRIS, "alto": estilo.TEJA, "fuente": estilo.FUENTE_TEJA,
                   "tamano_icono": 80}
        self.tarifas = Tecla(
            tejas, "CAMBIAR TARIFAS", self.abrir_tarifas, icono="tarifas",
            subtitulo="Los €/s de cada estado,\ndesde la próxima carrera", **comunes,
        )
        self.tarifas.grid(row=0, column=0, sticky="ew", padx=(0, estilo.SEPARACION // 2))
        self.historico = Tecla(
            tejas, "VER HISTÓRICO", self.abrir_historico, icono="historico",
            subtitulo="Carreras terminadas hoy\ny total de caja", **comunes,
        )
        self.historico.grid(row=0, column=1, sticky="ew", padx=(estilo.SEPARACION // 2, 0))

        self.volver = self.tecla_lateral(lateral, "Volver", self.volver_a_inicio)
        self.volver.pack(side=tk.BOTTOM, fill=tk.X)

    def abrir_tarifas(self) -> None:
        from taximetro.gui.tarifas import CambiarTarifas

        self.app.mostrar(CambiarTarifas)

    def abrir_historico(self) -> None:
        from taximetro.gui.historico import Historico

        self.app.mostrar(Historico)

    def volver_a_inicio(self) -> None:
        """Volver: a Inicio. Para volver aquí hay que teclear otra vez la contraseña."""
        from taximetro.gui.inicio import Inicio

        self.app.mostrar(Inicio)
