"""Tests de `taximetro.tarifa.Tarifa` (US-02 / T2.2).

Las tarifas son el dinero que paga el pasajero: se comprueban contra los
valores del briefing, no contra lo que diga el código.
"""

from __future__ import annotations

import pytest

from taximetro.carrera import Estado
from taximetro.tarifa import Tarifa


@pytest.fixture
def tarifa() -> Tarifa:
    """Las tarifas vigentes."""
    return Tarifa()


class TestTarifasVigentes:
    """Los valores de la zona EMT Madrid (docs/project-brief.md)."""

    def test_parado_cuesta_dos_centimos_por_segundo(self, tarifa: Tarifa) -> None:
        assert tarifa.calcular_importe(Estado.PARADO, 1) == pytest.approx(0.02)

    def test_en_movimiento_cuesta_cinco_centimos_por_segundo(self, tarifa: Tarifa) -> None:
        assert tarifa.calcular_importe(Estado.EN_MOVIMIENTO, 1) == pytest.approx(0.05)

    def test_moverse_es_mas_caro_que_estar_parado(self, tarifa: Tarifa) -> None:
        # "Cuando el taxi está parado el contador sigue corriendo pero más
        # despacio. En marcha, corre más rápido." (briefing del cliente)
        un_minuto_parado = tarifa.calcular_importe(Estado.PARADO, 60)
        un_minuto_en_marcha = tarifa.calcular_importe(Estado.EN_MOVIMIENTO, 60)
        assert un_minuto_en_marcha > un_minuto_parado


class TestCalculoPorTiempo:
    """El importe es proporcional a los segundos, no a la distancia."""

    @pytest.mark.parametrize(
        ("estado", "segundos", "esperado"),
        [
            (Estado.PARADO, 0, 0.0),
            (Estado.PARADO, 60, 1.20),
            (Estado.PARADO, 150, 3.00),
            (Estado.EN_MOVIMIENTO, 0, 0.0),
            (Estado.EN_MOVIMIENTO, 60, 3.00),
            (Estado.EN_MOVIMIENTO, 150, 7.50),
        ],
    )
    def test_importe_por_estado_y_segundos(
        self, tarifa: Tarifa, estado: Estado, segundos: float, esperado: float
    ) -> None:
        assert tarifa.calcular_importe(estado, segundos) == pytest.approx(esperado)

    def test_los_segundos_fraccionarios_tambien_cuentan(self, tarifa: Tarifa) -> None:
        # La acumulación es continua: no se redondea a segundos enteros ni se
        # cobra por tramos fijos.
        assert tarifa.calcular_importe(Estado.PARADO, 0.5) == pytest.approx(0.01)

    def test_el_calculo_es_lineal(self, tarifa: Tarifa) -> None:
        diez = tarifa.calcular_importe(Estado.EN_MOVIMIENTO, 10)
        veinte = tarifa.calcular_importe(Estado.EN_MOVIMIENTO, 20)
        assert veinte == pytest.approx(diez * 2)


class TestTarifaSinEstado:
    """Un estado que no existe es un error de programación, no un importe cero."""

    def test_un_estado_desconocido_falla(self, tarifa: Tarifa) -> None:
        with pytest.raises(KeyError):
            tarifa.calcular_importe("parado", 60)  # type: ignore[arg-type]
