"""Contrasena: la contraseña antes del Administrador (US-08, T9.7).

Pantalla 2 de `docs/diseno-interfaz-fase3.md`. La comprobación es del
servicio, el mismo que usa el CLI (T8.3); aquí solo se teclea y se avisa.
"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from taximetro.gui import estilo, iconos
from taximetro.gui.pantalla import Pantalla
from taximetro.gui.tecla import Tecla
from taximetro.servicio_taximetro import AlmacenamientoError

if TYPE_CHECKING:
    from taximetro.gui.app import App

VACIA = "Escribe la contraseña."
INCORRECTA = "Contraseña incorrecta. Inténtalo de nuevo."
NO_DISPONIBLE = "No se puede comprobar la contraseña. Avisa al equipo técnico."


class Contrasena(Pantalla):
    """Campo enmascarado, ENTRAR (o Enter) y Cancelar. Sin límite de intentos."""

    def __init__(self, app: App) -> None:
        """Monta la pantalla con el cursor ya en el campo."""
        super().__init__(app)
        principal, lateral = self.columnas()
        panel = tk.Frame(
            principal, bg=estilo.PANEL, highlightthickness=3, highlightbackground=estilo.VISOR_BORDE
        )
        panel.pack(fill=tk.BOTH, expand=True)
        interior = tk.Frame(panel, bg=estilo.PANEL)
        interior.pack(fill=tk.BOTH, expand=True, padx=64, pady=56)

        cabecera = tk.Frame(interior, bg=estilo.PANEL)
        cabecera.pack(fill=tk.X)
        lienzo = tk.Canvas(cabecera, width=56, height=56, bg=estilo.PANEL, highlightthickness=0)
        iconos.dibujar(lienzo, "candado", 56, "#ffffff")
        lienzo.pack(side=tk.LEFT)
        tk.Label(
            cabecera, text="Administrador", font=estilo.FUENTE_TITULO,
            bg=estilo.PANEL, fg=estilo.TEXTO,
        ).pack(side=tk.LEFT, padx=(20, 0))

        tk.Label(
            interior, text="Contraseña", font=estilo.FUENTE_TEXTO,
            bg=estilo.PANEL, fg=estilo.TEXTO_SECUNDARIO, anchor=tk.W,
        ).pack(fill=tk.X, pady=(28, 12))
        self._marco_campo = tk.Frame(
            interior, height=estilo.CAMPO, bg=estilo.VISOR_FONDO,
            highlightthickness=3, highlightbackground=estilo.CAMPO_BORDE,
        )
        self._marco_campo.pack(fill=tk.X)
        self._marco_campo.pack_propagate(False)
        self.campo = tk.Entry(
            self._marco_campo, show="•", font=estilo.FUENTE_CONTRASENA,
            bg=estilo.VISOR_FONDO, fg="#ffffff", insertbackground="#ffffff", relief=tk.FLAT,
        )
        self.campo.pack(fill=tk.BOTH, expand=True, padx=24)
        self.campo.bind("<Return>", lambda _evento: self.entrar())
        self.campo.bind("<Key>", self._al_teclear)
        # Con ajuste de línea: el mensaje más largo no cabe en una con todas las fuentes.
        self.mensaje = tk.Label(
            interior, font=estilo.FUENTE_MENSAJE, bg=estilo.PANEL,
            fg=estilo.MENSAJE_ERROR, anchor=tk.W, justify=tk.LEFT, wraplength=820,
        )
        self.mensaje.pack(fill=tk.X, pady=(12, 0))

        self.entrar_tecla = Tecla(
            interior, "ENTRAR", self.entrar, variante=estilo.VERDE, alto=estilo.TECLA_ENTRAR
        )
        self.entrar_tecla.pack(side=tk.BOTTOM, fill=tk.X)

        self.cancelar = self.tecla_lateral(lateral, "Cancelar", self.volver_a_inicio)
        self.cancelar.pack(side=tk.BOTTOM, fill=tk.X)
        self.campo.focus_set()

    def entrar(self) -> None:
        """ENTRAR o Enter: comprueba la contraseña con el servicio."""
        contrasena = self.campo.get()
        if contrasena == "":
            self._error(VACIA)
            return
        try:
            correcta = self.servicio.comprobar_contrasena(contrasena)
        except AlmacenamientoError:
            # No se entra nunca por defecto: sin credenciales, no hay Administrador.
            self._error(NO_DISPONIBLE)
            return
        if correcta:
            from taximetro.gui.administrador import Administrador

            self.app.mostrar(Administrador)
            return
        self.campo.delete(0, tk.END)
        self._error(INCORRECTA)

    def volver_a_inicio(self) -> None:
        """Cancelar: a Inicio."""
        from taximetro.gui.inicio import Inicio

        self.app.mostrar(Inicio)

    def _error(self, texto: str) -> None:
        """Mensaje en rojo bajo el campo, y el borde del campo en rojo."""
        self.mensaje.configure(text=texto)
        self._marco_campo.configure(highlightbackground=estilo.CAMPO_BORDE_ERROR)

    def _al_teclear(self, evento: tk.Event) -> None:
        """Al volver a escribir, el aviso anterior sobra."""
        if evento.keysym != "Return":
            self.mensaje.configure(text="")
            self._marco_campo.configure(highlightbackground=estilo.CAMPO_BORDE)
