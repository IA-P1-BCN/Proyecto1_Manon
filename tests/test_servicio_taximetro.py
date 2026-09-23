"""Tests de `taximetro.servicio_taximetro.ServicioTaximetro` (T9.10).

El servicio es la fachada que comparten la interfaz gráfica y el CLI. Además
de que cada método haga lo que dice, se comprueba lo que lo hace sustituible
por un cliente HTTP en la Fase 4: devuelve datos congelados, nunca objetos
vivos del dominio, y los fallos de disco salen como excepciones del contrato.
"""

from __future__ import annotations

import dataclasses
from datetime import date
from pathlib import Path

import pytest

from taximetro.config_tarifas import ConfigTarifas
from taximetro.historial import Historial
from taximetro.servicio_taximetro import (
    AlmacenamientoError,
    CarreraActivaError,
    CarreraCerrada,
    Estado,
    InstantaneaCarrera,
    ResumenDia,
    ServicioTaximetro,
    SinCarreraError,
    TarifaInvalidaError,
    TarifasVigentes,
)
from taximetro.taximetro import Taximetro


@pytest.fixture
def servicio(reloj, calendario) -> ServicioTaximetro:
    """Un servicio sobre un taxímetro libre, en memoria y con relojes falsos."""
    return ServicioTaximetro(Taximetro(reloj=reloj, calendario=calendario))


def bloqueado(tmp_path: Path) -> Path:
    """Una ruta cuya carpeta no se puede crear, porque ya hay un fichero con su nombre."""
    (tmp_path / "bloqueo").write_text("", encoding="utf-8")
    return tmp_path / "bloqueo" / "fichero"


class TestIniciarCarrera:
    """US-01 a través del servicio."""

    def test_devuelve_una_instantanea_de_la_carrera_nueva(self, servicio) -> None:
        assert servicio.iniciar_carrera() == InstantaneaCarrera(
            id=1, estado=Estado.EN_MOVIMIENTO, importe=0.0
        )

    def test_dos_veces_lanza_carrera_activa_error(self, servicio) -> None:
        servicio.iniciar_carrera()
        with pytest.raises(CarreraActivaError):
            servicio.iniciar_carrera()


class TestEstadoActual:
    """Lo que la interfaz gráfica lee cada 200 ms."""

    def test_libre_es_none(self, servicio) -> None:
        assert servicio.estado_actual() is None

    def test_da_el_importe_al_instante(self, servicio, reloj) -> None:
        servicio.iniciar_carrera()
        reloj.avanzar(10)
        assert servicio.estado_actual().importe == pytest.approx(0.50)

    def test_leer_no_cambia_nada(self, servicio, reloj) -> None:
        # Se llama cinco veces por segundo: leer no puede acumular dos veces.
        servicio.iniciar_carrera()
        reloj.avanzar(10)
        servicio.estado_actual()
        servicio.estado_actual()
        assert servicio.estado_actual().importe == pytest.approx(0.50)

    def test_tras_finalizar_vuelve_a_estar_libre(self, servicio) -> None:
        servicio.iniciar_carrera()
        servicio.finalizar_carrera()
        assert servicio.estado_actual() is None


class TestCambiarEstado:
    """US-02 a través del servicio."""

    def test_devuelve_la_carrera_en_su_nuevo_estado(self, servicio) -> None:
        servicio.iniciar_carrera()
        assert servicio.cambiar_estado(Estado.PARADO).estado is Estado.PARADO

    def test_cada_tramo_se_cobra_a_su_tarifa(self, servicio, reloj) -> None:
        servicio.iniciar_carrera()
        reloj.avanzar(10)  # 10 s en movimiento: 0,50 €
        servicio.cambiar_estado(Estado.PARADO)
        reloj.avanzar(10)  # 10 s parado: 0,20 €
        assert servicio.estado_actual().importe == pytest.approx(0.70)

    def test_sin_carrera_lanza_sin_carrera_error(self, servicio) -> None:
        with pytest.raises(SinCarreraError):
            servicio.cambiar_estado(Estado.PARADO)


class TestFinalizarCarrera:
    """US-03 a través del servicio."""

    def test_devuelve_el_total_y_que_se_guardo(self, servicio, reloj) -> None:
        servicio.iniciar_carrera()
        reloj.avanzar(10)
        cerrada = servicio.finalizar_carrera()
        assert cerrada == CarreraCerrada(
            carrera=InstantaneaCarrera(id=1, estado=Estado.EN_MOVIMIENTO, importe=0.50),
            guardada=True,
        )

    def test_el_total_queda_congelado(self, servicio, reloj) -> None:
        servicio.iniciar_carrera()
        reloj.avanzar(10)
        cerrada = servicio.finalizar_carrera()
        reloj.avanzar(60)
        assert cerrada.carrera.importe == pytest.approx(0.50)

    def test_sin_carrera_lanza_sin_carrera_error(self, servicio) -> None:
        with pytest.raises(SinCarreraError):
            servicio.finalizar_carrera()

    def test_un_historico_que_no_se_escribe_no_impide_cobrar(
        self, tmp_path: Path, reloj, calendario
    ) -> None:
        servicio = ServicioTaximetro(
            Taximetro(historial=Historial(bloqueado(tmp_path)), reloj=reloj, calendario=calendario)
        )
        servicio.iniciar_carrera()
        reloj.avanzar(10)

        cerrada = servicio.finalizar_carrera()

        assert cerrada.guardada is False
        assert cerrada.carrera.importe == pytest.approx(0.50)
        assert servicio.estado_actual() is None


class TestTarifas:
    """US-07 a través del servicio."""

    def test_da_las_tarifas_vigentes(self, servicio) -> None:
        assert servicio.tarifas() == TarifasVigentes(parado=0.02, en_movimiento=0.05)

    def test_cambiarlas_las_aplica_a_la_proxima_carrera(self, servicio, reloj) -> None:
        assert servicio.cambiar_tarifas(0.03, 0.06) == TarifasVigentes(0.03, 0.06)
        servicio.iniciar_carrera()
        reloj.avanzar(10)
        assert servicio.estado_actual().importe == pytest.approx(0.60)

    def test_una_tarifa_invalida_no_cambia_nada(self, servicio) -> None:
        with pytest.raises(TarifaInvalidaError):
            servicio.cambiar_tarifas(-1, 0.05)
        assert servicio.tarifas() == TarifasVigentes(0.02, 0.05)

    def test_con_carrera_activa_no_se_cambian(self, servicio) -> None:
        servicio.iniciar_carrera()
        with pytest.raises(CarreraActivaError):
            servicio.cambiar_tarifas(0.03, 0.06)

    def test_si_no_se_pueden_guardar_lanza_almacenamiento_error(
        self, tmp_path: Path
    ) -> None:
        servicio = ServicioTaximetro(Taximetro(config=ConfigTarifas(bloqueado(tmp_path))))
        with pytest.raises(AlmacenamientoError) as error:
            servicio.cambiar_tarifas(0.03, 0.06)
        assert isinstance(error.value.__cause__, OSError)
        assert servicio.tarifas() == TarifasVigentes(0.02, 0.05)


class HistorialIlegible:
    """Un histórico cuyo fichero existe pero no se puede leer."""

    def ultimo_numero(self) -> int:
        return 0

    def resumen_del_dia(self, fecha: date) -> ResumenDia:
        raise PermissionError("sin permiso de lectura")


class TestResumenDelDia:
    """US-05 a través del servicio."""

    def test_da_las_carreras_de_hoy(self, tmp_path: Path, reloj, calendario) -> None:
        servicio = ServicioTaximetro(
            Taximetro(historial=Historial(tmp_path / "h.csv"), reloj=reloj, calendario=calendario)
        )
        servicio.iniciar_carrera()
        reloj.avanzar(10)
        servicio.finalizar_carrera()

        resumen = servicio.resumen_del_dia()

        assert [registro.carrera for registro in resumen.carreras] == [1]
        assert resumen.total == pytest.approx(0.50)

    def test_si_no_se_puede_leer_lanza_almacenamiento_error(self) -> None:
        servicio = ServicioTaximetro(Taximetro(historial=HistorialIlegible()))
        with pytest.raises(AlmacenamientoError):
            servicio.resumen_del_dia()


class TestSoloDatos:
    """Lo que hace posible sustituir el servicio por un cliente HTTP (Fase 4)."""

    @pytest.mark.parametrize("tipo", [InstantaneaCarrera, CarreraCerrada, TarifasVigentes])
    def test_lo_que_devuelve_esta_congelado(self, tipo) -> None:
        assert dataclasses.is_dataclass(tipo)
        assert tipo.__dataclass_params__.frozen

    def test_la_instantanea_no_sigue_a_la_carrera(self, servicio, reloj) -> None:
        # Una copia, no una vista: la pantalla repinta cuando vuelve a preguntar.
        instantanea = servicio.iniciar_carrera()
        reloj.avanzar(10)
        assert instantanea.importe == 0.0
