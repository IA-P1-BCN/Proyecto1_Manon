"""Tests de `taximetro.gui.administrador.Administrador`: el menú (T9.7)."""

from __future__ import annotations

import pytest

from taximetro.gui.administrador import Administrador
from taximetro.gui.app import App
from taximetro.gui.historico import Historico
from taximetro.gui.inicio import Inicio
from taximetro.gui.tarifas import CambiarTarifas


@pytest.fixture
def menu(app: App) -> Administrador:
    return app.mostrar(Administrador)


def test_franja_con_candado_y_tarifas(menu: Administrador) -> None:
    assert menu.franja.titulo.cget("text") == "ADMINISTRADOR"
    assert "parado 0,02 €/s" in menu.franja.texto.cget("text")


def test_cambiar_tarifas(menu: Administrador) -> None:
    menu.tarifas.invoke()
    assert isinstance(menu.app.pantalla, CambiarTarifas)


def test_ver_historico(menu: Administrador) -> None:
    menu.historico.invoke()
    assert isinstance(menu.app.pantalla, Historico)


def test_volver_a_inicio(menu: Administrador) -> None:
    # Para volver a entrar hay que teclear otra vez la contraseña.
    menu.volver.invoke()
    assert isinstance(menu.app.pantalla, Inicio)
