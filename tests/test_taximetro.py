"""Tests de `taximetro.taximetro.Taximetro`.

Cubre el inicio de carreras y la validación de "no hay carrera activa"
(US-01 / T1.2, T1.4).
"""

from __future__ import annotations

from datetime import datetime

import pytest

from taximetro.carrera import Carrera, Estado
from taximetro.taximetro import CarreraActivaError, Taximetro


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
        assert carrera.estado is Estado.PARADO

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
