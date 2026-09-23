"""Pantalla: la base de cada pantalla de la interfaz gráfica."""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Callable

from taximetro.gui import estilo
from taximetro.gui.tecla import Tecla
from taximetro.utils import formato_euros

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

    def columnas(self) -> tuple[tk.Frame, tk.Frame]:
        """El esqueleto común: columna principal y lateral de 240 px a la derecha.

        Todas las pantallas lo comparten, para que las acciones secundarias
        (Volver, Ayuda, Salir…) estén siempre en el mismo sitio.
        """
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, minsize=estilo.LATERAL)
        self.rowconfigure(0, weight=1)
        principal = tk.Frame(self, bg=estilo.FONDO)
        principal.grid(row=0, column=0, sticky="nsew", padx=(estilo.MARGEN, 0), pady=estilo.MARGEN)
        lateral = tk.Frame(self, bg=estilo.FONDO, width=estilo.LATERAL)
        lateral.grid(row=0, column=1, sticky="ns", padx=estilo.MARGEN, pady=estilo.MARGEN)
        lateral.pack_propagate(False)
        return principal, lateral

    def tecla_lateral(self, padre: tk.Misc, texto: str, comando: Callable[[], None]) -> Tecla:
        """Una tecla del lateral (Volver, Ayuda, Salir…), sin colocar."""
        return Tecla(
            padre, texto, comando, variante=estilo.LATERAL_TECLA,
            alto=estilo.TECLA_LATERAL, fuente=estilo.FUENTE_TECLA_LATERAL,
        )

    def resumen_tarifas(self) -> str:
        """Las tarifas vigentes en una línea: 'parado 0,02 €/s · en movimiento 0,05 €/s'."""
        tarifas = self.servicio.tarifas()
        return (
            f"parado {formato_euros(tarifas.parado)}/s · "
            f"en movimiento {formato_euros(tarifas.en_movimiento)}/s"
        )

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

    def al_cerrar_ventana(self) -> bool:
        """El ✕ de la ventana, antes de cerrar el programa.

        Devuelve True si la pantalla se ocupa (p. ej. pregunta porque hay una
        carrera en curso) y el programa no debe cerrarse todavía. Por defecto,
        False: se cierra.
        """
        return False

    def destroy(self) -> None:
        """Cancela los temporizadores pendientes y destruye la pantalla."""
        for identificador in self._temporizadores:
            self.after_cancel(identificador)
        self._temporizadores.clear()
        super().destroy()
