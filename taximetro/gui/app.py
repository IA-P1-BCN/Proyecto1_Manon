"""App: la ventana de la interfaz gráfica y el cambio de pantalla (US-09)."""

from __future__ import annotations

import tkinter as tk
from typing import Any

from taximetro.gui import estilo
from taximetro.gui.inicio import Inicio
from taximetro.gui.pantalla import Pantalla
from taximetro.servicio_taximetro import ServicioTaximetro


class App:
    """La ventana del taxímetro: muestra una `Pantalla` cada vez.

    Es la única que conoce la ventana de tkinter. Las pantallas se piden unas a
    otras con `mostrar()`, y todas hablan con el mismo `servicio`, el que
    también usa el CLI (`docs/decisions-fase3.md`, *Structural refactor*).

    `raiz` se inyecta para los tests: crean una ventana oculta y procesan los
    eventos con `update()`, sin entrar en `mainloop()`.
    """

    def __init__(self, servicio: ServicioTaximetro, raiz: tk.Tk | None = None) -> None:
        """Prepara la ventana con el tamaño de la tablet y abre la pantalla de inicio."""
        self.servicio = servicio
        self.raiz = raiz if raiz is not None else tk.Tk()
        self.raiz.title(estilo.TITULO)
        self.raiz.geometry(f"{estilo.ANCHO}x{estilo.ALTO}")
        self.raiz.minsize(estilo.ANCHO, estilo.ALTO)
        self.raiz.configure(bg=estilo.FONDO)
        self.raiz.protocol("WM_DELETE_WINDOW", self.al_cerrar_ventana)
        self.pantalla: Pantalla | None = None
        self.mostrar(Inicio)

    def mostrar(self, tipo: type[Pantalla], **datos: Any) -> Pantalla:
        """Sustituye la pantalla actual por una nueva de `tipo` y la devuelve.

        La anterior se destruye, con sus temporizadores: solo hay una pantalla
        viva cada vez. `datos` se pasa al constructor de la nueva.
        """
        if self.pantalla is not None:
            self.pantalla.destroy()
        self.pantalla = tipo(self, **datos)
        self.pantalla.pack(fill=tk.BOTH, expand=True)
        return self.pantalla

    def al_cerrar_ventana(self) -> None:
        """El ✕ de la ventana.

        De momento cierra sin más. Con una carrera en curso tendrá que
        preguntar antes (T9.8, `docs/flujo-fase3.md`).
        """
        self.cerrar()

    def cerrar(self) -> None:
        """Termina el programa: destruye la ventana y sale de `mainloop()`."""
        if self.pantalla is not None:
            self.pantalla.destroy()
            self.pantalla = None
        self.raiz.destroy()

    def ejecutar(self) -> None:
        """Muestra la ventana y atiende eventos hasta que se cierra."""
        self.raiz.mainloop()
