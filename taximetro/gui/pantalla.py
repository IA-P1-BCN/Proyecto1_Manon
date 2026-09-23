"""Pantalla: la base de cada pantalla de la interfaz gráfica."""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Callable

from taximetro.gui import estilo

if TYPE_CHECKING:
    from taximetro.gui.app import App
    from taximetro.servicio_taximetro import ServicioTaximetro


class Pantalla(tk.Frame):
    """Una pantalla completa. `App` muestra una cada vez y destruye la anterior.

    Da a cada pantalla la `app` (para cambiar de pantalla) y el `servicio`
    (para todo lo demás). Sus temporizadores se programan con `programar()` y
    se cancelan solos al salir: si no, el refresco del importe seguiría
    llamando a widgets ya destruidos.
    """

    def __init__(self, app: App) -> None:
        """Crea la pantalla vacía, del tamaño de la ventana."""
        super().__init__(app.raiz, bg=estilo.FONDO)
        self.app = app
        self._temporizadores: set[str] = set()

    @property
    def servicio(self) -> ServicioTaximetro:
        """El servicio del taxímetro: lo único del dominio que ve la pantalla."""
        return self.app.servicio

    def programar(self, milisegundos: int, funcion: Callable[[], None]) -> str:
        """Llama a `funcion` dentro de `milisegundos`, en el hilo de la interfaz.

        Devuelve el identificador de `after()`. Si la pantalla se cierra antes,
        la llamada no llega a hacerse.
        """

        def disparar() -> None:
            self._temporizadores.discard(identificador)
            funcion()

        identificador = self.after(milisegundos, disparar)
        self._temporizadores.add(identificador)
        return identificador

    def destroy(self) -> None:
        """Cancela los temporizadores pendientes y destruye la pantalla."""
        for identificador in self._temporizadores:
            self.after_cancel(identificador)
        self._temporizadores.clear()
        super().destroy()
