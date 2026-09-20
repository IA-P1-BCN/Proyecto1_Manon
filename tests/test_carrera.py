"""Tests de `taximetro.carrera.Carrera`.

Cubre por ahora el estado inicial de una carrera recién creada (US-01 / T1.1).
La acumulación del importe llega con US-02 y el cierre con US-03.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from taximetro.carrera import Carrera, Estado
from taximetro.tarifa import Tarifa


@pytest.fixture
def carrera(reloj, calendario) -> Carrera:
    """Una carrera nº 1 recién creada, con relojes deterministas."""
    return Carrera(id=1, tarifa=Tarifa(), reloj=reloj, calendario=calendario)


class TestCarreraNueva:
    """Estado inicial de una carrera (US-01)."""

    def test_empieza_parada(self, carrera: Carrera) -> None:
        # El taxi recoge al pasajero con el vehículo detenido, así que la
        # carrera nace en PARADO y no en movimiento.
        assert carrera.estado is Estado.PARADO

    def test_empieza_sin_importe(self, carrera: Carrera) -> None:
        assert carrera.importe == 0.0

    def test_guarda_el_numero_que_le_asignan(self, carrera: Carrera) -> None:
        assert carrera.id == 1

    def test_sella_la_hora_de_inicio_con_el_calendario(
        self, carrera: Carrera, calendario
    ) -> None:
        # El cobro empieza en el momento del arranque: la hora queda registrada
        # al crear la carrera, no al primer cambio de estado.
        assert carrera.hora_inicio == calendario()
        assert isinstance(carrera.hora_inicio, datetime)

    def test_no_tiene_hora_de_fin(self, carrera: Carrera) -> None:
        # `hora_fin` es además la marca de "carrera cerrada": mientras sea None,
        # la carrera sigue viva.
        assert carrera.hora_fin is None

    def test_la_distancia_es_un_marcador_de_posicion(self, carrera: Carrera) -> None:
        # El taxímetro cobra por tiempo, nunca por distancia. El atributo existe
        # reservado para fases futuras; ver docs/decisions-fase1-scaffold.md.
        assert carrera.distancia == 0.0


class TestRelojesInyectados:
    """Los dos relojes inyectables (TP.1)."""

    def test_usa_el_calendario_inyectado_y_no_la_hora_real(self, reloj, calendario) -> None:
        carrera = Carrera(id=1, tarifa=Tarifa(), reloj=reloj, calendario=calendario)
        assert carrera.hora_inicio == datetime(2025, 6, 1, 8, 0, 0)

    def test_el_tramo_arranca_en_el_instante_del_reloj(self, reloj, calendario) -> None:
        reloj.avanzar(100.0)  # el taxímetro lleva un rato encendido
        carrera = Carrera(id=1, tarifa=Tarifa(), reloj=reloj, calendario=calendario)
        # El tramo se mide desde que se crea la carrera. Es estado interno, pero
        # es justo lo que hace que el cobro empiece "desde el arranque" (US-01),
        # y sin comprobarlo un tramo inicial mal puesto pasaría desapercibido
        # hasta US-02.
        assert carrera._inicio_tramo == 100.0
