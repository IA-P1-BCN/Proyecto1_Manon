"""Tests de `taximetro.carrera.Carrera`.

Cubre el estado inicial de una carrera (US-01 / T1.1), la acumulación por tramos
al cambiar de estado (US-02 / T2.1, T2.3) y la lectura del importe bajo demanda
(TD.4). El cierre de la carrera llega con US-03.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from taximetro.carrera import Carrera, CarreraFinalizadaError, Estado
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


class TestCambiarEstado:
    """US-02 / T2.1: el conductor indica si el vehículo está parado o en marcha."""

    def test_cambia_el_estado(self, carrera: Carrera) -> None:
        carrera.cambiar_estado(Estado.EN_MOVIMIENTO)
        assert carrera.estado is Estado.EN_MOVIMIENTO

    def test_cobra_el_tramo_anterior_al_cambiar(self, carrera: Carrera, reloj) -> None:
        reloj.avanzar(100)  # 100 s parado a 0,02 €/s
        carrera.cambiar_estado(Estado.EN_MOVIMIENTO)
        assert carrera.importe == pytest.approx(2.00)

    def test_repetir_el_mismo_estado_no_interrumpe_la_acumulacion(
        self, carrera: Carrera, reloj
    ) -> None:
        # Decisión registrada: repetir estado es un no-op silencioso, pensado
        # para el conductor que pulsa dos veces el mismo comando.
        reloj.avanzar(50)
        carrera.cambiar_estado(Estado.PARADO)
        reloj.avanzar(50)
        carrera.cambiar_estado(Estado.EN_MOVIMIENTO)

        # Los 100 s se cobran enteros a tarifa de parado, sin perder el primer
        # tramo ni cobrarlo dos veces.
        assert carrera.importe == pytest.approx(2.00)

    def test_una_carrera_finalizada_no_admite_cambios(
        self, carrera: Carrera, calendario
    ) -> None:
        carrera.hora_fin = calendario()  # cierre simulado; finalizar() es US-03
        with pytest.raises(CarreraFinalizadaError):
            carrera.cambiar_estado(Estado.EN_MOVIMIENTO)


class TestAcumulacionContinua:
    """US-02 / T2.3: el importe se acumula tramo a tramo según el estado."""

    def test_suma_tramos_a_tarifas_distintas(self, carrera: Carrera, reloj) -> None:
        reloj.avanzar(100)  # 100 s parado      -> 2,00 €
        carrera.cambiar_estado(Estado.EN_MOVIMIENTO)
        reloj.avanzar(60)  # 60 s en movimiento -> 3,00 €
        carrera.cambiar_estado(Estado.PARADO)

        assert carrera.importe == pytest.approx(5.00)

    def test_cambiar_de_estado_no_reinicia_el_importe(
        self, carrera: Carrera, reloj
    ) -> None:
        # Criterio de aceptación de US-02: "cambiar de estado no interrumpe el
        # cálculo acumulado del importe".
        reloj.avanzar(100)
        carrera.cambiar_estado(Estado.EN_MOVIMIENTO)
        acumulado = carrera.importe

        carrera.cambiar_estado(Estado.PARADO)
        assert carrera.importe >= acumulado

    def test_un_semaforo_no_cobra_como_una_avenida(
        self, carrera: Carrera, reloj
    ) -> None:
        reloj.avanzar(60)
        carrera.cambiar_estado(Estado.EN_MOVIMIENTO)
        parado = carrera.importe

        reloj.avanzar(60)
        carrera.cambiar_estado(Estado.PARADO)
        en_marcha = carrera.importe - parado

        assert en_marcha == pytest.approx(parado * 2.5)


class TestImporteActual:
    """TD.4: total acumulado bajo demanda, sin efectos secundarios."""

    def test_incluye_el_tramo_en_curso(self, carrera: Carrera, reloj) -> None:
        reloj.avanzar(30)
        assert carrera.importe_actual() == pytest.approx(0.60)

    def test_el_importe_almacenado_no_cambia_al_leer(
        self, carrera: Carrera, reloj
    ) -> None:
        reloj.avanzar(30)
        carrera.importe_actual()
        assert carrera.importe == 0.0

    def test_leer_no_reinicia_el_tramo(self, reloj, calendario) -> None:
        # TD.5, la regresión más peligrosa del modelo: si leer reiniciase la
        # marca de tiempo, cada consulta descartaría el tramo en curso y el
        # pasajero pagaría de menos, sin error en ninguna parte.
        leida = Carrera(id=1, tarifa=Tarifa(), reloj=reloj, calendario=calendario)
        intacta = Carrera(id=2, tarifa=Tarifa(), reloj=reloj, calendario=calendario)

        reloj.avanzar(40)
        leida.importe_actual()
        leida.importe_actual()
        reloj.avanzar(40)

        leida.cambiar_estado(Estado.EN_MOVIMIENTO)
        intacta.cambiar_estado(Estado.EN_MOVIMIENTO)

        assert leida.importe == pytest.approx(intacta.importe)
        assert leida.importe == pytest.approx(1.60)  # 80 s a 0,02 €/s

    def test_sobre_una_carrera_cerrada_devuelve_el_total_congelado(
        self, carrera: Carrera, reloj, calendario
    ) -> None:
        # TP.2: sin esto, el total "final" de una carrera cerrada seguiría
        # creciendo mientras el programa siga abierto.
        reloj.avanzar(100)
        carrera.importe = carrera.importe_actual()
        carrera.hora_fin = calendario()  # cierre simulado; finalizar() es US-03
        total = carrera.importe_actual()

        reloj.avanzar(500)
        assert carrera.importe_actual() == pytest.approx(total)


class TestCarreraFinalizadaFlag:
    """`hora_fin` es la marca de carrera cerrada."""

    def test_una_carrera_nueva_no_esta_finalizada(self, carrera: Carrera) -> None:
        assert carrera.finalizada is False

    def test_al_sellar_hora_fin_queda_finalizada(
        self, carrera: Carrera, calendario
    ) -> None:
        carrera.hora_fin = calendario()
        assert carrera.finalizada is True
