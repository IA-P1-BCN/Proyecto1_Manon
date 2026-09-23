"""Nada se recorta ni se sale de su sitio, en ninguna pantalla (T9.7).

Una etiqueta de tkinter no ajusta su texto: si no cabe, se corta sin avisar.
Los tests de comportamiento no lo ven, porque el texto sigue ahí. Este test
muestra cada pantalla a 1280 × 800 y mira la geometría que calcula Tk: ningún
widget más ancho que su texto pide, y ninguno fuera de su padre. Encontró
«SÍ, FINALIZAR Y SALIR», que en una línea no cabía en su tecla.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

import pytest

from taximetro.gui import estilo
from taximetro.gui.administrador import Administrador
from taximetro.gui.app import App
from taximetro.gui.contrasena import Contrasena
from taximetro.gui.historico import Historico
from taximetro.gui.inicio import Inicio
from taximetro.gui.tarifas import CambiarTarifas
from taximetro.gui.taximetro import PantallaTaximetro
from taximetro.historial import Historial
from taximetro.servicio_taximetro import ServicioTaximetro
from taximetro.taximetro import Taximetro


ANCHAS = ("Verdana", "DejaVu Sans")  # más anchas que Segoe UI: lo que cabe con ellas, cabe


@pytest.fixture(params=["sistema", "ancha"])
def fuente(request, interprete, monkeypatch: pytest.MonkeyPatch) -> str:
    """Cada test corre con la fuente del sistema y con la más ancha disponible.

    La fuente cambia de una máquina a otra (en el CI, DejaVu Sans; en Windows,
    Segoe UI): el diseño tiene que caber con cualquiera.
    """
    if request.param == "sistema":
        return estilo.FAMILIA
    disponibles = set(tkfont.families(interprete))
    ancha = next((familia for familia in ANCHAS if familia in disponibles), None)
    if ancha is None:
        pytest.skip("no hay ninguna fuente ancha instalada")
    monkeypatch.setattr(estilo, "FAMILIA", ancha)
    for nombre, valor in list(vars(estilo).items()):
        if nombre.startswith("FUENTE_"):
            monkeypatch.setattr(estilo, nombre, (ancha, *valor[1:]))
    return ancha


@pytest.fixture
def app(raiz, fuente, tmp_path: Path, reloj, calendario) -> App:
    """Una App visible, a tamaño de tablet, con 9 carreras en el histórico."""
    taximetro = Taximetro(historial=Historial(tmp_path / "h.csv"), reloj=reloj, calendario=calendario)
    servicio = ServicioTaximetro(taximetro)
    for _ in range(9):
        servicio.iniciar_carrera()
        servicio.finalizar_carrera()
    raiz.geometry(f"{estilo.ANCHO}x{estilo.ALTO}+0+0")
    raiz.deiconify()
    return App(servicio, raiz=raiz)


def desbordes(app: App) -> list[str]:
    """Lo que se recorta o se sale de su padre en la pantalla actual."""
    app.raiz.update()
    problemas: list[str] = []

    def recorrer(widget: tk.Misc) -> None:
        if not widget.winfo_ismapped():
            return
        texto = widget.cget("text") if isinstance(widget, tk.Label) else ""
        if texto and widget.winfo_reqwidth() > widget.winfo_width() + 1:
            problemas.append(f"recortado: {texto!r}")
        padre = widget.master
        if widget is not app.pantalla and padre is not None:
            fuera = (
                widget.winfo_rootx() < padre.winfo_rootx() - 1
                or widget.winfo_rooty() < padre.winfo_rooty() - 1
                or widget.winfo_rootx() + widget.winfo_width() > padre.winfo_rootx() + padre.winfo_width() + 1
                or widget.winfo_rooty() + widget.winfo_height() > padre.winfo_rooty() + padre.winfo_height() + 1
            )
            if fuera:
                problemas.append(
                    f"se sale de su padre: {widget.winfo_class()} {texto!r} "
                    f"{widget.winfo_width()}x{widget.winfo_height()} en "
                    f"{padre.winfo_width()}x{padre.winfo_height()}"
                )
        for hijo in widget.winfo_children():
            recorrer(hijo)

    recorrer(app.pantalla)
    return problemas


def test_inicio(app: App) -> None:
    app.mostrar(Inicio)
    assert desbordes(app) == []


def test_contrasena_con_su_mensaje_mas_largo(app: App) -> None:
    pantalla = app.mostrar(Contrasena)
    pantalla.campo.insert(0, "x")
    pantalla.entrar()  # sin Auth: «No se puede comprobar la contraseña…»
    assert desbordes(app) == []


def test_administrador(app: App) -> None:
    app.mostrar(Administrador)
    assert desbordes(app) == []


@pytest.mark.parametrize("parado", ["0,06", "0,02"], ids=["error-mas-largo", "guardadas"])
def test_tarifas_con_sus_mensajes(app: App, parado: str) -> None:
    pantalla = app.mostrar(CambiarTarifas)
    pantalla.campos["parado"].delete(0, tk.END)
    pantalla.campos["parado"].insert(0, parado)
    pantalla.guardar()
    assert desbordes(app) == []


def test_historico_lleno(app: App) -> None:
    app.mostrar(Historico)
    assert desbordes(app) == []


def test_taximetro_en_todos_sus_estados(app: App) -> None:
    pantalla = app.mostrar(PantallaTaximetro)
    assert desbordes(app) == [], "libre"
    pantalla.iniciar()
    assert desbordes(app) == [], "ocupado"
    pantalla.pedir_finalizar()
    assert desbordes(app) == [], "confirmar FINALIZAR"
    pantalla.confirmacion.si.invoke()
    assert desbordes(app) == [], "total a cobrar"
    pantalla.abrir_ayuda()
    assert desbordes(app) == [], "ayuda"
    pantalla.cerrar_ayuda()
    pantalla.iniciar()
    app.al_cerrar_ventana()
    assert desbordes(app) == [], "confirmar salir"


def test_el_detector_ve_un_texto_que_no_cabe(app: App) -> None:
    # Sin esto, un detector roto daría todas las pantallas por buenas.
    hueco = tk.Frame(app.mostrar(Inicio), width=100, height=100)
    hueco.place(x=0, y=0)
    hueco.pack_propagate(False)
    tk.Label(hueco, text="un texto demasiado largo para su sitio").pack()
    assert any(problema.startswith("recortado") for problema in desbordes(app))
