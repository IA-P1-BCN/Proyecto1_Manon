"""Tests de `taximetro.taximetro.Taximetro`.

Cubre el inicio de carreras y la validación de "no hay carrera activa"
(US-01 / T1.2, T1.4).
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pytest

from taximetro.carrera import Carrera, Estado
from taximetro.config_tarifas import ConfigTarifas
from taximetro.historial import Historial
from taximetro.tarifa import Tarifa
from taximetro.taximetro import CarreraActivaError, SinCarreraError, Taximetro


@pytest.fixture
def taximetro(reloj, calendario) -> Taximetro:
    """Un taxímetro libre, con relojes deterministas."""
    return Taximetro(reloj=reloj, calendario=calendario)


class TestTaximetroLibre:
    """Estado de partida: sin ninguna carrera."""

    def test_arranca_sin_carrera_activa(self, taximetro: Taximetro) -> None:
        assert taximetro.carrera_activa is None


class TestIniciarCarrera:
    """US-01: iniciar una carrera con un solo comando."""

    def test_devuelve_una_carrera_nueva(self, taximetro: Taximetro) -> None:
        carrera = taximetro.iniciar_carrera()
        assert isinstance(carrera, Carrera)
        assert carrera.estado is Estado.EN_MOVIMIENTO

    def test_la_carrera_queda_activa(self, taximetro: Taximetro) -> None:
        carrera = taximetro.iniciar_carrera()
        assert taximetro.carrera_activa is carrera

    def test_el_cobro_empieza_en_el_momento_del_arranque(
        self, taximetro: Taximetro, calendario
    ) -> None:
        carrera = taximetro.iniciar_carrera()
        assert carrera.hora_inicio == calendario()

    def test_propaga_los_relojes_inyectados(self, reloj, calendario) -> None:
        # Si el taxímetro no pasara sus relojes a la carrera, esta usaría la
        # hora real y los tests de tarifas dependerían del reloj de la máquina.
        taximetro = Taximetro(reloj=reloj, calendario=calendario)
        carrera = taximetro.iniciar_carrera()
        assert carrera.hora_inicio == datetime(2025, 6, 1, 8, 0, 0)


class TestNumeracionDeCarreras:
    """El contador vive en el taxímetro, no en la clase Carrera."""

    def test_la_primera_carrera_es_la_numero_uno(self, taximetro: Taximetro) -> None:
        assert taximetro.iniciar_carrera().id == 1

    def test_las_carreras_se_numeran_en_orden(self, taximetro: Taximetro) -> None:
        primera = taximetro.iniciar_carrera()
        primera.finalizar()

        segunda = taximetro.iniciar_carrera()
        assert (primera.id, segunda.id) == (1, 2)

    def test_cada_taximetro_numera_sus_propias_carreras(self, reloj, calendario) -> None:
        # Con un contador de clase, el segundo taxímetro empezaría en 2 y los
        # tests se contaminarían entre sí.
        primero = Taximetro(reloj=reloj, calendario=calendario)
        segundo = Taximetro(reloj=reloj, calendario=calendario)

        assert primero.iniciar_carrera().id == 1
        assert segundo.iniciar_carrera().id == 1


class TestCarreraDuplicada:
    """US-01: el sistema impide iniciar una carrera si ya hay una activa."""

    def test_iniciar_dos_veces_lanza_carrera_activa_error(
        self, taximetro: Taximetro
    ) -> None:
        taximetro.iniciar_carrera()
        with pytest.raises(CarreraActivaError):
            taximetro.iniciar_carrera()

    def test_el_intento_fallido_no_toca_la_carrera_en_curso(
        self, taximetro: Taximetro
    ) -> None:
        # Lo importante no es solo que falle, sino que el pasajero que ya va a
        # bordo no pierda su carrera ni su importe.
        en_curso = taximetro.iniciar_carrera()

        with pytest.raises(CarreraActivaError):
            taximetro.iniciar_carrera()

        assert taximetro.carrera_activa is en_curso
        assert en_curso.id == 1

    def test_se_puede_iniciar_otra_cuando_la_anterior_se_cierra(
        self, taximetro: Taximetro
    ) -> None:
        # Base de US-04: encadenar servicios sin cerrar el programa.
        primera = taximetro.iniciar_carrera()
        primera.finalizar()

        segunda = taximetro.iniciar_carrera()
        assert taximetro.carrera_activa is segunda

    def test_la_carrera_finalizada_deja_de_estar_activa(
        self, taximetro: Taximetro
    ) -> None:
        carrera = taximetro.iniciar_carrera()
        carrera.finalizar()
        assert taximetro.carrera_activa is None


class TestTarifasDesdeConfiguracion:
    """US-07 / T7.3: `Taximetro` carga las tarifas del fichero y guarda los cambios."""

    def test_sin_configuracion_usa_las_tarifas_por_defecto(self, taximetro) -> None:
        assert taximetro.tarifa.parado == 0.02

    def test_carga_las_tarifas_del_fichero(self, tmp_path: Path, reloj) -> None:
        ruta = tmp_path / "tarifas.json"
        ruta.write_text('{"parado": 0.03, "en_movimiento": 0.06}', encoding="utf-8")
        taximetro = Taximetro(config=ConfigTarifas(ruta), reloj=reloj)
        assert taximetro.tarifa.en_movimiento == 0.06

    def test_una_tarifa_explicita_manda_sobre_el_fichero(self, tmp_path: Path) -> None:
        ruta = tmp_path / "tarifas.json"
        ruta.write_text('{"parado": 0.03, "en_movimiento": 0.06}', encoding="utf-8")
        taximetro = Taximetro(tarifa=Tarifa(0.01, 0.01), config=ConfigTarifas(ruta))
        assert taximetro.tarifa.parado == 0.01


class TestCambiarTarifa:
    """T7.6 en el dominio: la tarifa nueva se aplica desde la próxima carrera."""

    def test_la_proxima_carrera_cobra_la_tarifa_nueva(self, taximetro, reloj) -> None:
        taximetro.cambiar_tarifa(Tarifa(parado=0.03, en_movimiento=0.10))
        carrera = taximetro.iniciar_carrera()
        reloj.avanzar(10)
        assert carrera.importe_actual() == pytest.approx(1.00)

    def test_la_carrera_ya_cerrada_conserva_su_tarifa(self, taximetro, reloj) -> None:
        carrera = taximetro.iniciar_carrera()
        reloj.avanzar(10)
        carrera.finalizar()
        taximetro.cambiar_tarifa(Tarifa(parado=0.03, en_movimiento=0.10))
        assert carrera.importe_actual() == pytest.approx(0.50)

    def test_con_una_carrera_activa_falla(self, taximetro) -> None:
        taximetro.iniciar_carrera()
        with pytest.raises(CarreraActivaError):
            taximetro.cambiar_tarifa(Tarifa(parado=0.03, en_movimiento=0.10))
        assert taximetro.tarifa.parado == 0.02

    def test_guarda_la_tarifa_en_el_fichero(self, tmp_path: Path) -> None:
        config = ConfigTarifas(tmp_path / "tarifas.json")
        Taximetro(config=config).cambiar_tarifa(Tarifa(0.03, 0.10))
        assert ConfigTarifas(config.ruta).cargar().en_movimiento == 0.10

    def test_si_no_se_puede_guardar_no_la_aplica(self, tmp_path: Path) -> None:
        # Fichero y taxímetro nunca discrepan: sin guardar, no hay cambio.
        (tmp_path / "config").write_text("", encoding="utf-8")  # bloquea mkdir
        taximetro = Taximetro(config=ConfigTarifas(tmp_path / "config" / "t.json"))
        with pytest.raises(OSError):
            taximetro.cambiar_tarifa(Tarifa(0.03, 0.10))
        assert taximetro.tarifa.parado == 0.02


class TestFinalizarCarrera:
    """US-05 / T5.1: toda carrera cerrada por el Taximetro se guarda."""

    @pytest.fixture
    def historial(self, tmp_path: Path) -> Historial:
        return Historial(tmp_path / "historial.csv")

    def test_devuelve_el_total_y_cierra_la_carrera(self, taximetro, reloj) -> None:
        carrera = taximetro.iniciar_carrera()
        reloj.avanzar(60)
        assert taximetro.finalizar_carrera() == pytest.approx(3.00)
        assert carrera.finalizada
        assert taximetro.carrera_activa is None

    def test_sin_carrera_activa_falla(self, taximetro) -> None:
        with pytest.raises(SinCarreraError):
            taximetro.finalizar_carrera()

    def test_guarda_la_carrera_en_el_historial(
        self, historial, reloj, calendario
    ) -> None:
        taximetro = Taximetro(historial=historial, reloj=reloj, calendario=calendario)
        taximetro.iniciar_carrera()
        reloj.avanzar(60)
        taximetro.finalizar_carrera()
        assert [r.importe for r in historial.registros()] == [3.00]

    def test_si_no_se_puede_guardar_el_cobro_no_se_pierde(
        self, tmp_path: Path, reloj
    ) -> None:
        (tmp_path / "data").write_text("", encoding="utf-8")  # bloquea mkdir
        taximetro = Taximetro(historial=Historial(tmp_path / "data" / "h.csv"), reloj=reloj)
        carrera = taximetro.iniciar_carrera()
        reloj.avanzar(60)
        with pytest.raises(OSError):
            taximetro.finalizar_carrera()
        assert carrera.finalizada
        assert carrera.importe == pytest.approx(3.00)
        assert taximetro.carrera_activa is None

    def test_la_numeracion_sigue_desde_el_historial(
        self, historial, reloj, calendario
    ) -> None:
        # Un reinicio del programa no repite números en el histórico del día.
        primera_sesion = Taximetro(historial=historial, reloj=reloj, calendario=calendario)
        for _ in range(2):
            primera_sesion.iniciar_carrera()
            primera_sesion.finalizar_carrera()
        segunda_sesion = Taximetro(historial=historial, reloj=reloj, calendario=calendario)
        assert segunda_sesion.iniciar_carrera().id == 3


class TestResumenDelDia:
    """US-05: el Taximetro pide al histórico las carreras de hoy."""

    def test_sin_historial_el_resumen_esta_vacio(self, taximetro) -> None:
        resumen = taximetro.resumen_del_dia()
        assert resumen.carreras == ()
        assert resumen.fecha == datetime(2025, 6, 1).date()

    def test_hoy_lo_dice_el_calendario(self, tmp_path: Path, reloj, calendario) -> None:
        historial = Historial(tmp_path / "historial.csv")
        taximetro = Taximetro(historial=historial, reloj=reloj, calendario=calendario)
        taximetro.iniciar_carrera()
        taximetro.finalizar_carrera()
        assert len(taximetro.resumen_del_dia().carreras) == 1
        calendario.avanzar(24 * 3600)
        assert taximetro.resumen_del_dia().carreras == ()


class TestLogs:
    """US-06 / T6.2: los rechazos del taxímetro y los cambios de tarifa."""

    def test_iniciar_dos_veces_es_warning(self, eventos, taximetro) -> None:
        taximetro.iniciar_carrera()
        with pytest.raises(CarreraActivaError):
            taximetro.iniciar_carrera()
        assert eventos(logging.WARNING) == [
            "inicio_rechazado carrera_activa=1 motivo=carrera_activa"
        ]

    def test_finalizar_sin_carrera_es_warning(self, eventos, taximetro) -> None:
        with pytest.raises(SinCarreraError):
            taximetro.finalizar_carrera()
        assert eventos(logging.WARNING) == ["finalizar_rechazado motivo=sin_carrera"]

    def test_registra_el_cambio_de_tarifa(self, eventos, taximetro) -> None:
        taximetro.cambiar_tarifa(Tarifa(parado=0.03, en_movimiento=0.10))
        assert eventos() == [
            "tarifa_cambiada parado_antes=0.02 movimiento_antes=0.05 "
            "parado=0.03 movimiento=0.10"
        ]

    def test_cambiar_tarifa_con_carrera_es_warning(self, eventos, taximetro) -> None:
        taximetro.iniciar_carrera()
        with pytest.raises(CarreraActivaError):
            taximetro.cambiar_tarifa(Tarifa(0.03, 0.10))
        assert eventos(logging.WARNING) == ["cambio_tarifa_rechazado motivo=carrera_activa"]
