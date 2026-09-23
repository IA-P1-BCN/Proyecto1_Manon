"""Tests de `taximetro.carrera.Carrera`.

Cubre el estado inicial de una carrera (US-01 / T1.1), la acumulación por tramos
al cambiar de estado (US-02 / T2.1, T2.3) y la lectura del importe bajo demanda
(TD.4). El cierre de la carrera llega con US-03.
"""

from __future__ import annotations

import logging
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

    def test_empieza_en_movimiento(self, carrera: Carrera) -> None:
        # La carrera se inicia cuando el taxi arranca con el pasajero dentro,
        # así que nace EN_MOVIMIENTO y cobra a la tarifa alta desde el primer
        # segundo. Si el taxi arranca detenido, el conductor pulsa `Parar`.
        assert carrera.estado is Estado.EN_MOVIMIENTO

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
        reloj.avanzar(100)  # 100 s en movimiento a 0,05 €/s
        carrera.cambiar_estado(Estado.PARADO)
        assert carrera.importe == pytest.approx(5.00)

    def test_repetir_el_mismo_estado_no_interrumpe_la_acumulacion(
        self, carrera: Carrera, reloj
    ) -> None:
        # Decisión registrada: repetir estado es un no-op silencioso, pensado
        # para el conductor que pulsa dos veces el mismo comando.
        reloj.avanzar(50)
        carrera.cambiar_estado(Estado.EN_MOVIMIENTO)  # ya está en movimiento
        reloj.avanzar(50)
        carrera.cambiar_estado(Estado.PARADO)

        # Los 100 s se cobran enteros a tarifa de movimiento, sin perder el
        # primer tramo ni cobrarlo dos veces.
        assert carrera.importe == pytest.approx(5.00)

    def test_una_carrera_finalizada_no_admite_cambios(self, carrera: Carrera) -> None:
        carrera.finalizar()
        with pytest.raises(CarreraFinalizadaError):
            carrera.cambiar_estado(Estado.EN_MOVIMIENTO)


class TestAcumulacionContinua:
    """US-02 / T2.3: el importe se acumula tramo a tramo según el estado."""

    def test_suma_tramos_a_tarifas_distintas(self, carrera: Carrera, reloj) -> None:
        reloj.avanzar(100)  # 100 s en movimiento -> 5,00 €
        carrera.cambiar_estado(Estado.PARADO)
        reloj.avanzar(60)  # 60 s parado          -> 1,20 €
        carrera.cambiar_estado(Estado.EN_MOVIMIENTO)

        assert carrera.importe == pytest.approx(6.20)

    def test_cambiar_de_estado_no_reinicia_el_importe(
        self, carrera: Carrera, reloj
    ) -> None:
        # Criterio de aceptación de US-02: "cambiar de estado no interrumpe el
        # cálculo acumulado del importe".
        reloj.avanzar(100)
        carrera.cambiar_estado(Estado.PARADO)
        acumulado = carrera.importe

        carrera.cambiar_estado(Estado.EN_MOVIMIENTO)
        assert carrera.importe >= acumulado

    def test_un_semaforo_no_cobra_como_una_avenida(
        self, carrera: Carrera, reloj
    ) -> None:
        reloj.avanzar(60)
        carrera.cambiar_estado(Estado.PARADO)
        en_marcha = carrera.importe

        reloj.avanzar(60)
        carrera.cambiar_estado(Estado.EN_MOVIMIENTO)
        parado = carrera.importe - en_marcha

        assert en_marcha == pytest.approx(parado * 2.5)


class TestImporteActual:
    """TD.4: total acumulado bajo demanda, sin efectos secundarios."""

    def test_incluye_el_tramo_en_curso(self, carrera: Carrera, reloj) -> None:
        reloj.avanzar(30)
        assert carrera.importe_actual() == pytest.approx(1.50)

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

        leida.cambiar_estado(Estado.PARADO)
        intacta.cambiar_estado(Estado.PARADO)

        assert leida.importe == pytest.approx(intacta.importe)
        assert leida.importe == pytest.approx(4.00)  # 80 s a 0,05 €/s

    def test_sobre_una_carrera_cerrada_devuelve_el_total_congelado(
        self, carrera: Carrera, reloj
    ) -> None:
        # TP.2: sin esto, el total "final" de una carrera cerrada seguiría
        # creciendo mientras el programa siga abierto.
        reloj.avanzar(100)
        total = carrera.finalizar()

        reloj.avanzar(500)
        assert carrera.importe_actual() == pytest.approx(total)


class TestCarreraFinalizadaFlag:
    """`hora_fin` es la marca de carrera cerrada."""

    def test_una_carrera_nueva_no_esta_finalizada(self, carrera: Carrera) -> None:
        assert carrera.finalizada is False

    def test_tras_finalizar_queda_cerrada(self, carrera: Carrera) -> None:
        carrera.finalizar()
        assert carrera.finalizada is True


class TestDuracion:
    """Tiempo transcurrido, para mostrarlo en pantalla (Fase 3, T9.13)."""

    def test_una_carrera_recien_iniciada_dura_cero(self, carrera: Carrera) -> None:
        assert carrera.duracion() == 0

    def test_en_curso_cuenta_hasta_ahora(self, carrera: Carrera, calendario) -> None:
        calendario.avanzar(252)
        assert carrera.duracion() == 252

    def test_finalizada_se_queda_en_su_hora_de_fin(self, carrera: Carrera, calendario) -> None:
        calendario.avanzar(60)
        carrera.finalizar()
        calendario.avanzar(600)
        assert carrera.duracion() == 60


class TestCerrarEnUnInstanteAnterior:
    """Cobrar lo que había al pulsar FINALIZAR, no al confirmar (Fase 3, T9.8)."""

    def test_importe_en_un_instante_anterior(self, carrera: Carrera, reloj) -> None:
        reloj.avanzar(10)
        pulsacion = reloj()
        reloj.avanzar(50)
        assert carrera.importe_actual(en=pulsacion) == pytest.approx(0.50)
        assert carrera.importe_actual() == pytest.approx(3.00)

    def test_finalizar_en_un_instante_anterior(self, carrera: Carrera, reloj, calendario) -> None:
        reloj.avanzar(10)
        calendario.avanzar(10)
        pulsacion, hora = reloj(), calendario()
        reloj.avanzar(50)  # lo que se tarda en confirmar
        calendario.avanzar(50)
        assert carrera.finalizar(en=pulsacion, hora_fin=hora) == pytest.approx(0.50)
        assert carrera.hora_fin == hora
        assert carrera.duracion() == 10

    def test_nunca_antes_del_ultimo_cambio_de_estado(self, carrera: Carrera, reloj) -> None:
        # Ese tramo ya se cobró a otra tarifa: cerrar antes restaría importe.
        antes = reloj()
        reloj.avanzar(10)
        carrera.cambiar_estado(Estado.PARADO)
        with pytest.raises(ValueError):
            carrera.finalizar(en=antes)
        with pytest.raises(ValueError):
            carrera.importe_actual(en=antes)
        assert not carrera.finalizada

    def test_duracion_hasta_un_instante(self, carrera: Carrera, calendario) -> None:
        calendario.avanzar(10)
        hasta = calendario()
        calendario.avanzar(50)
        assert carrera.duracion(hasta=hasta) == 10


class TestFinalizar:
    """US-03 / T3.1: cerrar la carrera y devolver el total a cobrar."""

    def test_devuelve_el_total_con_el_ultimo_tramo_incluido(
        self, carrera: Carrera, reloj
    ) -> None:
        reloj.avanzar(100)  # 100 s en movimiento -> 5,00 €
        carrera.cambiar_estado(Estado.PARADO)
        reloj.avanzar(60)  # 60 s parado          -> 1,20 €

        # El último tramo no se ha cerrado con ningún cambio de estado: si
        # finalizar() no lo cobrase, la última espera del taxi saldría gratis.
        assert carrera.finalizar() == pytest.approx(6.20)

    def test_sella_la_hora_de_fin(self, carrera: Carrera, calendario) -> None:
        carrera.finalizar()
        assert carrera.hora_fin == calendario()

    def test_la_carrera_queda_cerrada(self, carrera: Carrera) -> None:
        carrera.finalizar()
        assert carrera.finalizada is True

    def test_no_admite_cambios_de_estado_despues(self, carrera: Carrera) -> None:
        carrera.finalizar()
        with pytest.raises(CarreraFinalizadaError):
            carrera.cambiar_estado(Estado.EN_MOVIMIENTO)

    def test_no_se_puede_finalizar_dos_veces(self, carrera: Carrera) -> None:
        carrera.finalizar()
        with pytest.raises(CarreraFinalizadaError):
            carrera.finalizar()

    def test_el_total_deja_de_crecer(self, carrera: Carrera, reloj) -> None:
        reloj.avanzar(100)
        total = carrera.finalizar()

        reloj.avanzar(3600)  # el taxi pasa una hora parado con el programa abierto
        assert carrera.importe_actual() == pytest.approx(total)
        assert carrera.importe == pytest.approx(total)

    def test_consultar_el_importe_no_altera_el_total_final(
        self, reloj, calendario
    ) -> None:
        # TD.5 en su forma completa, ahora que finalizar() existe: dos lecturas
        # seguidas y luego finalizar deben dar lo mismo que finalizar a secas.
        consultada = Carrera(id=1, tarifa=Tarifa(), reloj=reloj, calendario=calendario)
        intacta = Carrera(id=2, tarifa=Tarifa(), reloj=reloj, calendario=calendario)

        reloj.avanzar(45)
        consultada.importe_actual()
        consultada.importe_actual()
        reloj.avanzar(45)

        assert consultada.finalizar() == pytest.approx(intacta.finalizar())


class TestLogs:
    """US-06 / T6.2: la carrera deja rastro de su ciclo de vida."""

    def test_registra_el_inicio(self, eventos, reloj, calendario) -> None:
        Carrera(id=7, tarifa=Tarifa(), reloj=reloj, calendario=calendario)
        assert eventos() == ["carrera_iniciada carrera=7 estado=en_movimiento tarifa=0.05"]

    def test_registra_el_cambio_de_estado(self, eventos, carrera, reloj) -> None:
        reloj.avanzar(60)
        carrera.cambiar_estado(Estado.PARADO)
        assert (
            "estado_cambiado carrera=1 de=en_movimiento a=parado acumulado=3.00"
            in eventos()
        )

    def test_repetir_el_estado_no_registra_nada(self, eventos, carrera) -> None:
        antes = len(eventos())
        carrera.cambiar_estado(Estado.EN_MOVIMIENTO)
        assert len(eventos()) == antes

    def test_registra_el_final_con_importe_y_duracion(
        self, eventos, carrera, reloj, calendario
    ) -> None:
        reloj.avanzar(90)
        calendario.avanzar(90)
        carrera.finalizar()
        assert "carrera_finalizada carrera=1 importe=4.50 duracion_s=90" in eventos()

    def test_los_cambios_rechazados_son_warning(self, eventos, carrera) -> None:
        carrera.finalizar()
        with pytest.raises(CarreraFinalizadaError):
            carrera.cambiar_estado(Estado.PARADO)
        with pytest.raises(CarreraFinalizadaError):
            carrera.finalizar()
        assert eventos(logging.WARNING) == [
            "cambio_rechazado carrera=1 motivo=finalizada",
            "finalizar_rechazado carrera=1 motivo=finalizada",
        ]
