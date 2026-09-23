"""Tests de `taximetro.gui.inicio.Inicio`: elección de perfil (T9.7)."""

from __future__ import annotations

from taximetro.gui import estilo
from taximetro.gui.app import App
from taximetro.gui.contrasena import Contrasena
from taximetro.gui.inicio import Inicio
from taximetro.gui.taximetro import PantallaTaximetro


def test_la_franja_ensena_las_tarifas_vigentes(app: App) -> None:
    inicio = app.pantalla
    assert inicio.franja.titulo.cget("text") == "TTX-247"
    assert inicio.franja.texto.cget("text") == (
        "Tarifas vigentes: parado 0,02 €/s · en movimiento 0,05 €/s"
    )


def test_conductor_ocupa_dos_tercios(app: App) -> None:
    # La acción diaria, más grande: pesos 2 y 1 en la misma rejilla.
    tejas = app.pantalla.conductor.master
    assert tejas.grid_columnconfigure(0)["weight"] == 2
    assert tejas.grid_columnconfigure(1)["weight"] == 1


def test_conductor_abre_el_taximetro_sin_contrasena(app: App) -> None:
    app.pantalla.conductor.invoke()
    assert isinstance(app.pantalla, PantallaTaximetro)


def test_administrador_pide_la_contrasena(app: App) -> None:
    app.pantalla.administrador.invoke()
    assert isinstance(app.pantalla, Contrasena)


def test_las_tejas_dicen_que_hacen(app: App) -> None:
    inicio: Inicio = app.pantalla
    assert inicio.conductor.subtitulo == "Abrir el taxímetro"
    assert inicio.administrador.subtitulo == "Tarifas e histórico\ncon contraseña"
    assert inicio.administrador.cget("height") and int(inicio.administrador.cget("height")) == estilo.TEJA


def test_salir_cierra_el_programa(app: App, cerrada) -> None:
    app.pantalla.salir.invoke()
    assert cerrada(app.raiz)
