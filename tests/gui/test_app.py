"""Tests de `taximetro.gui.app.App`: la ventana y el cambio de pantalla (T9.3)."""

from __future__ import annotations

import pytest

from taximetro.gui import estilo
from taximetro.gui.app import App
from taximetro.gui.inicio import Inicio
from taximetro.gui.pantalla import Pantalla


class PantallaA(Pantalla):
    """Una pantalla de prueba."""


class PantallaConDatos(Pantalla):
    """Una pantalla de prueba que recibe datos al crearse."""

    def __init__(self, app: App, numero: int) -> None:
        super().__init__(app)
        self.numero = numero


class TestVentana:
    """La ventana con el tamaño de una tablet de 10" en horizontal."""

    def test_lleva_el_titulo_del_taximetro(self, app: App) -> None:
        assert app.raiz.title() == estilo.TITULO

    def test_nunca_es_mas_pequena_que_la_tablet(self, app: App) -> None:
        assert app.raiz.minsize() == (estilo.ANCHO, estilo.ALTO)

    def test_arranca_en_la_pantalla_de_inicio(self, app: App) -> None:
        assert isinstance(app.pantalla, Inicio)


class TestMostrar:
    """Una sola pantalla viva cada vez."""

    def test_sustituye_la_pantalla_actual(self, app: App) -> None:
        anterior = app.pantalla
        nueva = app.mostrar(PantallaA)
        assert app.pantalla is nueva
        assert isinstance(nueva, PantallaA)
        assert not anterior.winfo_exists()

    def test_pasa_los_datos_a_la_nueva(self, app: App) -> None:
        assert app.mostrar(PantallaConDatos, numero=7).numero == 7

    def test_todas_usan_el_mismo_servicio(self, app: App) -> None:
        # El mismo que el CLI: la interfaz no duplica el dominio (US-09).
        assert app.mostrar(PantallaA).servicio is app.servicio


class TestCerrar:
    """Salir del programa."""

    def test_el_aspa_de_la_ventana_cierra(self, app: App, cerrada) -> None:
        # Invoca lo que tkinter tiene enganchado al ✕ (WM_DELETE_WINDOW).
        app.raiz.tk.call(app.raiz.protocol("WM_DELETE_WINDOW"))
        assert cerrada(app.raiz)

    def test_cerrar_destruye_la_pantalla_y_la_ventana(self, app: App, cerrada) -> None:
        app.cerrar()
        assert app.pantalla is None
        assert cerrada(app.raiz)

    def test_ejecutar_vuelve_al_cerrar_la_ventana(self, app: App, cerrada) -> None:
        app.raiz.after(0, app.cerrar)
        app.ejecutar()  # si no volviera, el test se quedaría colgado
        assert cerrada(app.raiz)


class TestSinRaizInyectada:
    def test_crea_su_propia_ventana(self, raiz, reloj, calendario) -> None:
        # El programa real no inyecta la ventana: la crea la App.
        from taximetro.servicio_taximetro import ServicioTaximetro
        from taximetro.taximetro import Taximetro

        app = App(ServicioTaximetro(Taximetro(reloj=reloj, calendario=calendario)))
        try:
            assert app.raiz is not raiz
            assert app.raiz.title() == estilo.TITULO
        finally:
            app.cerrar()


@pytest.mark.parametrize("tipo", [Inicio, PantallaA])
def test_las_pantallas_ocupan_toda_la_ventana(app: App, tipo) -> None:
    pantalla = app.mostrar(tipo)
    assert pantalla.pack_info()["fill"] == "both"
    assert pantalla.pack_info()["expand"] in (True, 1, "1")
