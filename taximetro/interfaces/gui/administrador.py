"""Administrador: el menú de gestión.

Pantalla 6 de `docs/diseno-interfaz-fase3.md`: la misma estructura que Inicio,
con las tejas CAMBIAR TARIFAS y VER HISTÓRICO. Solo se llega tras la
contraseña; Volver lleva a Inicio, y para entrar otra vez hay que teclearla.
"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from taximetro.interfaces.gui import estilo
from taximetro.interfaces.gui.franja import Franja
from taximetro.interfaces.gui.pantalla import Pantalla
from taximetro.interfaces.gui.tecla import Tecla

if TYPE_CHECKING:
    from taximetro.interfaces.gui.app import App


class Administrador(Pantalla):
    """Menú de Administrador: tarifas e histórico."""

    def __init__(self, app: App) -> None:
        """Monta la franja, las dos tejas y Volver."""
        super().__init__(app)
        principal, lateral = self.columnas()

        self.franja = Franja(principal, "ADMINISTRADOR", icono="candado")
        self.franja.texto.configure(text=f"Tarifas vigentes: {self.resumen_tarifas()}")
        self.franja.pack(fill=tk.X)

        tejas = tk.Frame(principal, bg=estilo.FONDO)
        tejas.pack(fill=tk.BOTH, expand=True, pady=(estilo.SEPARACION, 0))
        comunes = {"variante": estilo.GRIS, "alto": estilo.TEJA, "fuente": estilo.FUENTE_TEJA,
                   "tamano_icono": estilo.px(80)}
        self.tarifas = Tecla(
            tejas, "CAMBIAR TARIFAS", self.abrir_tarifas, icono="tarifas",
            subtitulo="Los €/s de cada estado,\ndesde la próxima carrera", **comunes,
        )
        self.historico = Tecla(
            tejas, "VER HISTÓRICO", self.abrir_historico, icono="historico",
            subtitulo="Carreras terminadas hoy\ny total de caja", **comunes,
        )
        self._colocar_tejas(tejas)

        self.volver = self.tecla_lateral(lateral, "Volver", self.volver_a_inicio)
        self.colocar_lateral(self.volver, side=tk.BOTTOM, fill=tk.X)

    def _colocar_tejas(self, tejas: tk.Frame) -> None:
        """Las dos tejas a partes iguales: una junto a otra, o una encima de otra en vertical."""
        mitad = estilo.SEPARACION // 2
        if estilo.VERTICAL_ACTIVA:
            tejas.columnconfigure(0, weight=1)
            tejas.rowconfigure((0, 1), weight=1, uniform="teja")
            self.tarifas.grid(row=0, column=0, sticky="nsew", pady=(0, mitad))
            self.historico.grid(row=1, column=0, sticky="nsew", pady=(mitad, 0))
            return
        tejas.columnconfigure((0, 1), weight=1, uniform="teja")
        self.tarifas.grid(row=0, column=0, sticky="ew", padx=(0, mitad))
        self.historico.grid(row=0, column=1, sticky="ew", padx=(mitad, 0))

    def abrir_tarifas(self) -> None:
        """CAMBIAR TARIFAS: al formulario de tarifas."""
        from taximetro.interfaces.gui.tarifas import CambiarTarifas

        self.app.mostrar(CambiarTarifas)

    def abrir_historico(self) -> None:
        """VER HISTÓRICO: a la tabla de las carreras de hoy."""
        from taximetro.interfaces.gui.historico import Historico

        self.app.mostrar(Historico)

    def volver_a_inicio(self) -> None:
        """Volver: a Inicio. Para volver aquí hay que teclear otra vez la contraseña."""
        from taximetro.interfaces.gui.inicio import Inicio

        self.app.mostrar(Inicio)
