"""Tests de `taximetro.gui.inicio.Inicio`, de momento provisional (esqueleto US-09).

La pantalla aprobada llega con T9.7 y traerá sus propios tests.
"""

from __future__ import annotations

from taximetro.gui import estilo
from taximetro.gui.app import App


def test_muestra_el_nombre_del_taximetro(app: App) -> None:
    assert app.pantalla.titulo.cget("text") == estilo.TITULO


def test_conductor_abre_el_taximetro(app: App) -> None:
    from taximetro.gui.taximetro import PantallaTaximetro

    app.pantalla.conductor.invoke()
    assert isinstance(app.pantalla, PantallaTaximetro)


def test_salir_cierra_el_programa(app: App, cerrada) -> None:
    app.pantalla.salir.invoke()
    assert cerrada(app.raiz)
