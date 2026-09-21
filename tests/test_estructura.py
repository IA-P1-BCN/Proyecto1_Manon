"""Tests de estructura: el contrato de diseño acordado antes de implementar.

No comprueban comportamiento (eso es cosa de US-01 a US-04), sino que la API
pública es la que se decidió en `docs/decisions-fase1-scaffold.md`. Si alguien
renombra un método, le quita un parámetro inyectable o vuelve a poner el reloj
de pared, estos tests fallan y la decisión se revisa a conciencia en vez de
erosionarse sin querer.
"""

from __future__ import annotations

import inspect
import time
from datetime import datetime

from taximetro.carrera import Carrera, CarreraFinalizadaError, Estado
from taximetro.tarifa import Tarifa
from taximetro.taximetro import CarreraActivaError, Taximetro
from taximetro.taximetro_app import TaximetroApp
from taximetro.utils import formato_euros


def parametros(funcion) -> dict[str, inspect.Parameter]:
    """Devuelve los parámetros de `funcion` indexados por nombre."""
    return dict(inspect.signature(funcion).parameters)


class TestEstado:
    """El estado del vehículo es un Enum, no cadenas sueltas."""

    def test_tiene_los_dos_estados_del_briefing(self) -> None:
        assert Estado.PARADO.value == "parado"
        assert Estado.EN_MOVIMIENTO.value == "en_movimiento"


class TestCarrera:
    """Contrato de `Carrera` (US-01 a US-03, TD.4)."""

    def test_expone_la_api_acordada(self) -> None:
        assert callable(Carrera.cambiar_estado)
        assert callable(Carrera.finalizar)
        assert callable(Carrera.importe_actual), "TD.4: accesor de solo lectura"

    def test_recibe_la_tarifa_inyectada(self) -> None:
        assert "tarifa" in parametros(Carrera.__init__)

    def test_acumula_con_un_reloj_monotono(self) -> None:
        # Un reloj de pared puede retroceder (NTP, cambio manual) y restar
        # importe en silencio: el tramo se mide siempre con time.monotonic.
        reloj = parametros(Carrera.__init__)["reloj"]
        assert reloj.default is time.monotonic
        assert reloj.default is not time.time

    def test_sella_las_horas_con_un_calendario_aparte(self) -> None:
        calendario = parametros(Carrera.__init__)["calendario"]
        assert calendario.default == datetime.now


class TestTarifa:
    """Contrato de `Tarifa` (US-02)."""

    def test_calcula_por_estado_y_segundos(self) -> None:
        assert set(parametros(Tarifa.calcular_importe)) >= {"estado", "segundos"}


class TestTaximetro:
    """Contrato de `Taximetro` (US-01, US-04)."""

    def test_es_el_dueno_de_la_tarifa_y_los_relojes(self) -> None:
        esperados = {"tarifa", "reloj", "calendario"}
        assert esperados <= set(parametros(Taximetro.__init__))

    def test_inicia_carreras(self) -> None:
        assert callable(Taximetro.iniciar_carrera)

    def test_carga_y_cambia_tarifas_desde_la_configuracion(self) -> None:
        # US-07: la configuración entra por `Taximetro`, nunca por `Carrera`.
        assert "config" in parametros(Taximetro.__init__)
        assert "config" not in parametros(Carrera.__init__)
        assert callable(Taximetro.cambiar_tarifa)

    def test_cierra_carreras_y_resume_el_dia(self) -> None:
        # US-05: el histórico entra por `Taximetro`, que es quien cierra las
        # carreras; así ningún camino de cierre se queda sin guardar.
        assert "historial" in parametros(Taximetro.__init__)
        assert callable(Taximetro.finalizar_carrera)
        assert callable(Taximetro.resumen_del_dia)


class TestTaximetroApp:
    """Contrato de la capa CLI (US-04, EPIC D)."""

    def test_acepta_entrada_y_salida_inyectables(self) -> None:
        # Sin esta costura no se pueden testear los menús, los mensajes de
        # error ni Ctrl+C (TD.9).
        params = parametros(TaximetroApp.__init__)
        assert {"entrada", "salida"} <= set(params)
        assert params["entrada"].default is input
        assert params["salida"].default is print

    def test_tiene_bucle_principal(self) -> None:
        assert callable(TaximetroApp.ejecutar)


class TestExcepcionesDelDominio:
    """Las garantías del dominio son excepciones propias, no genéricas."""

    def test_son_excepciones_propias(self) -> None:
        assert issubclass(CarreraActivaError, Exception)
        assert issubclass(CarreraFinalizadaError, Exception)


class TestUtils:
    """Contrato del formateo de euros (T3.2)."""

    def test_existe_el_helper_de_formato(self) -> None:
        assert callable(formato_euros)
        assert "importe" in parametros(formato_euros)
