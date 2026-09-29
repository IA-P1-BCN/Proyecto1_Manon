"""Nada se recorta ni se sale de su sitio, en ninguna pantalla ni a ningún tamaño.

Una etiqueta de tkinter no ajusta su texto: si no cabe, se corta sin avisar.
Los tests de comportamiento no lo ven, porque el texto sigue ahí. Este test
muestra cada pantalla en una rejilla de tamaños de ventana (la tablet de
1280 × 800, más grandes, más pequeñas y en vertical) y mira la geometría que
calcula Tk: ningún widget más ancho que su texto pide, ninguno fuera de su
padre, y ninguna pantalla que pida más sitio del que tiene la ventana.
Encontró «SÍ, FINALIZAR Y SALIR», que en una línea no cabía en su tecla.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

import pytest

from taximetro.interfaces.gui import estilo
from taximetro.interfaces.gui.administrador import Administrador
from taximetro.interfaces.gui.app import App
from taximetro.interfaces.gui.contrasena import Contrasena
from taximetro.interfaces.gui.historico import Historico
from taximetro.interfaces.gui.inicio import Inicio
from taximetro.interfaces.gui.tarifas import CambiarTarifas
from taximetro.interfaces.gui.taximetro import PantallaTaximetro
from taximetro.infrastructure.historial import Historial
from taximetro.application.servicio_taximetro import ServicioTaximetro
from taximetro.application.taximetro import Taximetro


ANCHAS = ("Verdana", "DejaVu Sans")  # más anchas que Segoe UI: lo que cabe con ellas, cabe

# Tamaños de ventana (ancho, alto): la tablet, mayores, menores y en vertical.
TAMANOS = [
    (1280, 800), (1600, 1000), (1920, 1080), (1024, 660), estilo.TAMANO_MIN[estilo.HORIZONTAL],
    (720, 1280), (800, 1000), (640, 1100), estilo.TAMANO_MIN[estilo.VERTICAL],
]


@pytest.fixture(params=TAMANOS, ids=lambda t: f"{t[0]}x{t[1]}")
def tamano(request) -> tuple[int, int]:
    return request.param


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
def app(raiz, fuente, tamano, tmp_path: Path, reloj, calendario) -> App:
    """Una App visible, al tamaño que toque, con 9 carreras en el histórico."""
    taximetro = Taximetro(historial=Historial(tmp_path / "h.csv"), reloj=reloj, calendario=calendario)
    servicio = ServicioTaximetro(taximetro)
    for _ in range(9):
        servicio.iniciar_carrera()
        servicio.finalizar_carrera()
    aplicacion = App(servicio, raiz=raiz)
    raiz.maxsize(4000, 4000)  # por defecto, Windows no deja pasar del tamaño de la pantalla
    raiz.geometry(f"{tamano[0]}x{tamano[1]}+0+0")
    raiz.deiconify()
    raiz.update()
    # Lo que la ventana mide de verdad: si el sistema no la dejó crecer, se prueba a ese tamaño.
    aplicacion.adaptar(raiz.winfo_width(), raiz.winfo_height())
    return aplicacion


def desbordes(app: App) -> list[str]:
    """Lo que se recorta o se sale de su padre en la pantalla actual."""
    app.raiz.update()
    problemas: list[str] = []
    pantalla = app.pantalla
    if pantalla.winfo_reqwidth() > app.raiz.winfo_width() + 1 or pantalla.winfo_reqheight() > app.raiz.winfo_height() + 1:
        problemas.append(
            f"la pantalla pide {pantalla.winfo_reqwidth()}x{pantalla.winfo_reqheight()} "
            f"y la ventana mide {app.raiz.winfo_width()}x{app.raiz.winfo_height()}"
        )

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
