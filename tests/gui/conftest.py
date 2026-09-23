"""Fixtures de la interfaz gráfica: una ventana oculta y la App sobre ella.

Los tests no entran en el bucle de eventos: llaman a los métodos y procesan
los eventos pendientes con `update()`. tkinter necesita una pantalla; en el CI
(Linux sin pantalla) la pone `xvfb-run` (T9.14).

**Un solo intérprete Tk para toda la sesión.** Crear y destruir un `Tk()` por
test hacía que Tk 9.0 en Windows abortara de vez en cuando al crear el
siguiente (`Windows fatal exception: code 0x80000003`, a veces matando el
proceso). Cada test recibe en su lugar una ventana `Toplevel` nueva de ese
intérprete, que se destruye al terminar.
"""

from __future__ import annotations

import os
import time
import tkinter as tk
from typing import Callable

import pytest

from taximetro.gui.app import App
from taximetro.servicio_taximetro import ServicioTaximetro
from taximetro.taximetro import Taximetro


@pytest.fixture(scope="session")
def interprete():
    """El único `Tk` de la sesión, oculto: nunca se muestra ni se cierra en un test.

    Sin pantalla, los tests de la interfaz se saltan en local, pero en el CI
    fallan: allí tiene que haberla, y un salto escondería que no corren.
    """
    try:
        tk_raiz = tk.Tk()
    except tk.TclError as error:
        if os.environ.get("CI"):
            raise
        pytest.skip(f"tkinter no tiene pantalla: {error}")
    tk_raiz.withdraw()
    yield tk_raiz
    tk_raiz.destroy()


@pytest.fixture
def raiz(interprete):
    """Una ventana oculta, nueva en cada test y destruida al terminar."""
    ventana = tk.Toplevel(interprete)
    ventana.withdraw()
    # La App instala su gestor de errores en el intérprete, que es de toda la
    # sesión: se deja como estaba para que ningún test herede el de otro.
    gestor = interprete.report_callback_exception
    yield ventana
    interprete.report_callback_exception = gestor
    if ventana.winfo_exists():  # el propio test puede haberla cerrado (Salir, ✕)
        ventana.destroy()


@pytest.fixture
def app(raiz, reloj, calendario) -> App:
    """La interfaz sobre un taxímetro en memoria y con relojes falsos."""
    return App(ServicioTaximetro(Taximetro(reloj=reloj, calendario=calendario)), raiz=raiz)


@pytest.fixture
def procesar(interprete) -> Callable[[float], None]:
    """Deja pasar `segundos` de tiempo real atendiendo los eventos de la ventana."""

    def _procesar(segundos: float = 0.0) -> None:
        limite = time.monotonic() + segundos
        interprete.update()
        while time.monotonic() < limite:
            time.sleep(0.005)
            interprete.update()

    return _procesar


@pytest.fixture
def cerrada() -> Callable[[tk.Misc], bool]:
    """Pregunta si una ventana ya se destruyó (Salir, ✕)."""

    def _cerrada(ventana: tk.Misc) -> bool:
        return not ventana.winfo_exists()

    return _cerrada
