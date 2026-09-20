"""Tests de `taximetro.utils.formato_euros` (US-03 / T3.2, TP.5).

Es lo último que ve el conductor antes de cobrar, así que se comprueba el
formato exacto: coma decimal, dos decimales y espacio antes del símbolo.
"""

from __future__ import annotations

import pytest

from taximetro.utils import formato_euros


class TestFormatoEspanol:
    """Uso español: coma decimal y espacio antes del €."""

    def test_usa_coma_decimal(self) -> None:
        assert formato_euros(12.34) == "12,34 €"

    def test_nunca_deja_un_punto_decimal(self) -> None:
        # El andamiaje original escribía '12.34€'; el conductor lee precios con
        # coma. Ver docs/decisions-fase1-scaffold.md.
        assert "." not in formato_euros(1234.5)

    def test_lleva_el_simbolo_del_euro_al_final(self) -> None:
        assert formato_euros(5).endswith(" €")


class TestDosDecimales:
    """Siempre dos decimales, redondeando solo al mostrar."""

    @pytest.mark.parametrize(
        ("importe", "esperado"),
        [
            (0, "0,00 €"),
            (0.02, "0,02 €"),
            (2, "2,00 €"),
            (12.3, "12,30 €"),
            (7.5, "7,50 €"),
            (1234.5, "1234,50 €"),
        ],
    )
    def test_formatea_con_dos_decimales(self, importe: float, esperado: str) -> None:
        assert formato_euros(importe) == esperado

    def test_redondea_la_precision_sobrante(self) -> None:
        # El importe se acumula con toda su precisión durante la carrera y solo
        # se redondea aquí, para no arrastrar error tramo a tramo.
        assert formato_euros(12.3456) == "12,35 €"

    def test_un_importe_largo_no_pierde_los_centimos(self) -> None:
        assert formato_euros(0.020000000000000004) == "0,02 €"
