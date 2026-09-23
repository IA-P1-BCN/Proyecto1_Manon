"""Fixtures de la interfaz gráfica: una ventana oculta y la App sobre ella.

Los tests no entran en `mainloop()`: llaman a los métodos y procesan los
eventos pendientes con `update()`. tkinter necesita una pantalla; en el CI
(Linux sin pantalla) la pone `xvfb-run` (T9.14).
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


@pytest.fixture
def raiz():
    """Una ventana de tkinter oculta, destruida al terminar el test.

    Sin pantalla, el test se salta en local, pero en el CI falla: allí tiene
    que haberla, y un salto escondería que los tests de la interfaz no corren.
    """
    try:
        ventana = tk.Tk()
    except tk.TclError as error:
        if os.environ.get("CI"):
            raise
        pytest.skip(f"tkinter no tiene pantalla: {error}")
    ventana.withdraw()
    yield ventana
    try:
        ventana.destroy()
    except tk.TclError:
        pass  # el propio test ya la cerró (Salir, ✕)


@pytest.fixture
def app(raiz, reloj, calendario) -> App:
    """La interfaz sobre un taxímetro en memoria y con relojes falsos."""
    return App(ServicioTaximetro(Taximetro(reloj=reloj, calendario=calendario)), raiz=raiz)


@pytest.fixture
def procesar(raiz) -> Callable[[float], None]:
    """Deja pasar `segundos` de tiempo real atendiendo los eventos de la ventana."""

    def _procesar(segundos: float = 0.0) -> None:
        limite = time.monotonic() + segundos
        raiz.update()
        while time.monotonic() < limite:
            time.sleep(0.005)
            raiz.update()

    return _procesar


@pytest.fixture
def cerrada() -> Callable[[tk.Tk], bool]:
    """Pregunta si una ventana ya se destruyó (Salir, ✕)."""

    def _cerrada(ventana: tk.Tk) -> bool:
        try:
            ventana.winfo_exists()
        except tk.TclError:
            return True
        return False

    return _cerrada
