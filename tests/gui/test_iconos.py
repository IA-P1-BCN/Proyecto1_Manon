"""Tests de `taximetro.gui.iconos` y de la franja superior (T9.7)."""

from __future__ import annotations

import tkinter as tk

import pytest

from taximetro.gui import estilo, iconos
from taximetro.gui.franja import Franja
from taximetro.gui.tecla import Tecla


@pytest.mark.parametrize("nombre", iconos.NOMBRES)
def test_cada_icono_se_dibuja_dentro_de_su_cuadro(raiz, nombre: str) -> None:
    lienzo = tk.Canvas(raiz, width=96, height=96)
    iconos.dibujar(lienzo, nombre, 96, "#ffffff")
    x1, y1, x2, y2 = lienzo.bbox(tk.ALL)
    assert lienzo.find_all()
    assert x1 >= 0 and y1 >= 0 and x2 <= 96 + 4 and y2 <= 96 + 4


def test_un_icono_desconocido_es_un_error(raiz) -> None:
    with pytest.raises(ValueError):
        iconos.dibujar(tk.Canvas(raiz), "cohete", 24, "#ffffff")


def test_una_tecla_con_icono_lo_pinta_del_color_de_su_fondo(raiz) -> None:
    tecla = Tecla(raiz, "CONDUCTOR", lambda: None, variante=estilo.VERDE, icono="taxi")
    assert tecla._icono.cget("bg") == estilo.VERDE.fondo


def test_la_franja_parte_el_texto_en_lo_que_deja_el_titulo(raiz) -> None:
    raiz.geometry("968x200+0+0")
    raiz.deiconify()
    franja = Franja(raiz, "ADMINISTRADOR", icono="candado")
    franja.texto.configure(text="Tarifas vigentes: parado 0,02 €/s · en movimiento 0,05 €/s")
    franja.pack(fill=tk.X)
    raiz.update()
    libre = int(franja.texto.cget("wraplength"))
    assert 0 < libre < 968 - franja.titulo.winfo_width()
    assert int(franja.cget("height")) == estilo.FRANJA
