"""Tests de `taximetro.gui.visor.Visor`: el importe en 7 segmentos (T9.6)."""

from __future__ import annotations

import pytest

from taximetro.gui import estilo
from taximetro.gui import visor as modulo
from taximetro.gui.visor import Visor
from taximetro.utils import formato_euros


@pytest.fixture
def visor(raiz) -> Visor:
    visor = Visor(raiz)
    visor.pack()
    return visor


def cifras(visor: Visor) -> list[str]:
    """Los segmentos encendidos de cada posición, de izquierda a derecha."""
    return [visor.encendidos(i) for i in range(len(visor._cifras))]


class TestSegmentos:
    """Cada cifra enciende los segmentos de un 7 segmentos clásico."""

    @pytest.mark.parametrize(
        "cifra, esperados",
        [("0", "abcdef"), ("1", "bc"), ("2", "abdeg"), ("3", "abcdg"), ("4", "bcfg"),
         ("5", "acdfg"), ("6", "acdefg"), ("7", "abc"), ("8", "abcdefg"), ("9", "abcdfg")],
    )
    def test_cada_cifra(self, visor: Visor, cifra: str, esperados: str) -> None:
        visor.mostrar(float(f"0.0{cifra}"))
        assert cifras(visor)[-1] == esperados

    def test_los_apagados_se_ven_en_tono_oscuro(self, visor: Visor) -> None:
        # Como un LED real: el segmento apagado no desaparece.
        visor.mostrar(1)
        apagado = visor._cifras[2]["a"]  # el 1 no enciende el segmento a
        assert visor.itemcget(apagado, "fill") == estilo.LED_ROJO_APAGADO


class TestImporte:
    def test_arranca_a_cero(self, visor: Visor) -> None:
        assert visor.texto == "0,00 €"
        assert cifras(visor) == ["", "", "abcdef", "abcdef", "abcdef"]

    def test_las_posiciones_sin_cifra_quedan_apagadas(self, visor: Visor) -> None:
        visor.mostrar(5)
        assert cifras(visor) == ["", "", "acdfg", "abcdef", "abcdef"]

    def test_tres_cifras_enteras(self, visor: Visor) -> None:
        visor.mostrar(999.99)
        assert visor.texto == "999,99 €"
        assert cifras(visor) == ["abcdfg"] * 5

    @pytest.mark.parametrize("importe", [0.004, 0.005, 1.235, 12.345, 64.37, 100.0])
    def test_redondea_igual_que_formato_euros(self, visor: Visor, importe: float) -> None:
        # Una sola regla de redondeo en todo el programa: la de formato_euros.
        visor.mostrar(importe)
        assert visor.texto == formato_euros(importe)


class TestCuartaCifra:
    """A partir de 1.000 € el visor pasa a 4 cifras enteras, en el mismo ancho."""

    def test_mil_euros(self, visor: Visor) -> None:
        visor.mostrar(1000)
        assert visor.texto == "1000,00 €"
        assert len(visor._cifras) == 6
        assert cifras(visor)[:4] == ["bc", "abcdef", "abcdef", "abcdef"]

    def test_el_visor_no_crece(self, visor: Visor) -> None:
        visor.mostrar(1234.56)
        assert int(visor.cget("width")) == modulo.ANCHO
        derecha = max(visor.bbox(p)[2] for p in visor._cifras[-1].values())
        assert derecha <= modulo.ANCHO - modulo.EURO_ANCHO

    def test_vuelve_a_tres_cifras(self, visor: Visor) -> None:
        # Tras una carrera de más de 1.000 €, la siguiente empieza en 0,00.
        visor.mostrar(1000)
        visor.mostrar(0)
        assert len(visor._cifras) == 5
        assert visor.texto == "0,00 €"


class TestRefresco:
    """Se llama cinco veces por segundo: recolorea, no redibuja."""

    def test_no_crea_poligonos_nuevos_al_cambiar_el_importe(self, visor: Visor) -> None:
        antes = visor.find_all()
        for centimos in range(0, 500, 7):
            visor.mostrar(centimos / 100)
        assert visor.find_all() == antes

    def test_las_cifras_caben_en_su_sitio(self, visor: Visor) -> None:
        visor.mostrar(888.88)
        for segmentos in visor._cifras:
            for poligono in segmentos.values():
                x1, y1, x2, y2 = visor.bbox(poligono)
                assert 0 <= x1 and x2 <= modulo.ANCHO and 0 <= y1 and y2 <= modulo.ALTO + 1
