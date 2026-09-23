"""Tests de `taximetro.gui.tecla.Tecla`: la tecla táctil (T9.5)."""

from __future__ import annotations

import re
import tkinter as tk
from types import SimpleNamespace

import pytest

from taximetro.gui import estilo
from taximetro.gui.tecla import Tecla


@pytest.fixture
def pulsaciones() -> list[str]:
    return []


@pytest.fixture
def tecla(raiz, pulsaciones) -> Tecla:
    """Una FINALIZAR roja con subtítulo, en una ventana visible.

    Visible porque su tamaño y su posición en pantalla (lo que decide si el
    dedo se levantó encima) solo existen con la ventana mostrada.
    """
    raiz.geometry("600x400+0+0")
    raiz.deiconify()
    tecla = Tecla(
        raiz,
        "FINALIZAR",
        lambda: pulsaciones.append("finalizar"),
        variante=estilo.ROJA,
        alto=300,
        subtitulo="Termina y muestra el total",
    )
    tecla.pack(fill=tk.X)
    raiz.update()
    return tecla


def punto(widget: tk.Misc, dentro: bool = True) -> SimpleNamespace:
    """Un evento de ratón con coordenadas de pantalla, dentro o fuera de `widget`."""
    x = widget.winfo_rootx() + widget.winfo_width() // 2
    y = widget.winfo_rooty() + widget.winfo_height() // 2
    return SimpleNamespace(x_root=x if dentro else -1000, y_root=y if dentro else -1000)


class TestMedidas:
    def test_rechaza_una_tecla_por_debajo_de_la_zona_tactil(self, raiz) -> None:
        with pytest.raises(ValueError, match="88 px"):
            Tecla(raiz, "Ayuda", lambda: None, alto=87)

    def test_mide_el_alto_pedido_sea_cual_sea_el_texto(self, tecla: Tecla) -> None:
        assert tecla.winfo_height() == 300

    def test_por_defecto_mide_lo_de_una_tecla_principal(self, raiz) -> None:
        assert int(Tecla(raiz, "PARAR", lambda: None).cget("height")) == estilo.TECLA_PRINCIPAL_MIN


class TestTexto:
    def test_titulo_y_subtitulo(self, tecla: Tecla) -> None:
        assert (tecla.titulo, tecla.subtitulo) == ("FINALIZAR", "Termina y muestra el total")

    def test_sin_subtitulo_no_ocupa_sitio(self, raiz) -> None:
        tecla = Tecla(raiz, "PARAR", lambda: None)
        assert tecla.subtitulo == ""
        assert not tecla._subtitulo.winfo_ismapped()

    def test_configurar_cambia_texto_y_colores(self, tecla: Tecla) -> None:
        # PARAR ↔ ARRANCAR sin rehacer la tecla.
        tecla.configurar(titulo="ARRANCAR", subtitulo="", variante=estilo.GRIS)
        assert (tecla.titulo, tecla.subtitulo) == ("ARRANCAR", "")
        assert tecla.cget("bg") == estilo.GRIS.fondo


class TestColores:
    def test_usa_los_de_su_variante(self, tecla: Tecla) -> None:
        assert tecla.cget("bg") == estilo.ROJA.fondo
        assert tecla.cget("highlightbackground") == estilo.ROJA.borde
        assert tecla._subtitulo.cget("fg") == estilo.ROJA.subtitulo

    def test_se_aclara_mientras_se_pulsa(self, tecla: Tecla) -> None:
        tecla._al_pulsar(punto(tecla))
        assert tecla.cget("bg") == estilo.ROJA.pulsada
        tecla._al_soltar(punto(tecla))
        assert tecla.cget("bg") == estilo.ROJA.fondo


class TestPulsar:
    def test_actua_al_soltar_encima(self, tecla: Tecla, pulsaciones) -> None:
        tecla._al_pulsar(punto(tecla))
        assert pulsaciones == []  # todavía no: solo al soltar
        tecla._al_soltar(punto(tecla))
        assert pulsaciones == ["finalizar"]

    def test_soltar_fuera_no_hace_nada(self, tecla: Tecla, pulsaciones) -> None:
        # El dedo se arrepiente y se desliza fuera de la tecla.
        tecla._al_pulsar(punto(tecla))
        tecla._al_soltar(punto(tecla, dentro=False))
        assert pulsaciones == []
        assert tecla.cget("bg") == estilo.ROJA.fondo

    def test_soltar_sin_haber_pulsado_no_hace_nada(self, tecla: Tecla, pulsaciones) -> None:
        tecla._al_soltar(punto(tecla))
        assert pulsaciones == []

    def test_pulsar_sobre_el_texto_tambien_cuenta(self, tecla: Tecla, pulsaciones) -> None:
        tecla._al_pulsar(punto(tecla._titulo))
        tecla._al_soltar(punto(tecla._titulo))
        assert pulsaciones == ["finalizar"]

    def test_invoke_ejecuta_el_comando(self, tecla: Tecla, pulsaciones) -> None:
        tecla.invoke()
        assert pulsaciones == ["finalizar"]


class TestAjustarTexto:
    """Si el texto no cabe con su fuente, baja de tamaño; nunca por debajo de 24 px."""

    @staticmethod
    def px(etiqueta: tk.Label) -> int:
        """El tamaño en píxeles de la fuente de `etiqueta` ('{Segoe UI} -40 bold' → 40)."""
        return -int(re.search(r"-\d+", str(etiqueta.cget("font"))).group())

    @staticmethod
    def colocar(raiz, ancho: int, titulo: str, **opciones) -> Tecla:
        raiz.geometry(f"{ancho}x300+0+0")
        raiz.deiconify()
        tecla = Tecla(raiz, titulo, lambda: None, **opciones)
        tecla.pack(fill=tk.X)
        raiz.update()
        return tecla

    def test_si_cabe_no_cambia(self, raiz) -> None:
        tecla = self.colocar(raiz, 900, "PARAR")
        assert self.px(tecla._titulo) == -estilo.FUENTE_TECLA[1]

    def test_si_no_cabe_baja_lo_justo(self, raiz) -> None:
        tecla = self.colocar(raiz, 300, "ADMINISTRADOR", fuente=estilo.fuente(40, negrita=True))
        assert estilo.TEXTO_MIN <= self.px(tecla._titulo) < 40
        assert tecla._titulo.winfo_reqwidth() <= tecla.winfo_width()

    def test_nunca_por_debajo_del_minimo(self, raiz) -> None:
        tecla = self.colocar(raiz, 120, "UN TÍTULO LARGUÍSIMO QUE NO CABE")
        assert self.px(tecla._titulo) == estilo.TEXTO_MIN

    def test_se_reajusta_al_cambiar_el_texto(self, raiz) -> None:
        tecla = self.colocar(raiz, 300, "PARAR")
        tecla.configurar(titulo="ARRANCAR DE NUEVO")  # a 56 px no cabe; a menos, sí
        raiz.update()
        assert tecla._titulo.winfo_reqwidth() <= tecla.winfo_width()
