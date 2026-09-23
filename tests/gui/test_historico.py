"""Tests de `taximetro.gui.historico.Historico`: la pantalla 8 (T9.7)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from taximetro.gui import estilo
from taximetro.gui.administrador import Administrador
from taximetro.gui.app import App
from taximetro.gui.historico import ILEGIBLE, SIN_CARRERAS, Historico
from taximetro.historial import Historial
from taximetro.servicio_taximetro import ServicioTaximetro
from taximetro.taximetro import Taximetro


@pytest.fixture
def con_carreras(raiz, tmp_path: Path, reloj, calendario):
    """Una App cuyo histórico tiene `n` carreras de 60 s (3,00 € cada una)."""

    def _con(n: int) -> Historico:
        taximetro = Taximetro(historial=Historial(tmp_path / "h.csv"), reloj=reloj, calendario=calendario)
        servicio = ServicioTaximetro(taximetro)
        for _ in range(n):
            servicio.iniciar_carrera()
            reloj.avanzar(60)
            calendario.avanzar(60)
            servicio.finalizar_carrera()
        return App(servicio, raiz=raiz).mostrar(Historico)

    return _con


def test_titulo_con_la_fecha(con_carreras) -> None:
    assert con_carreras(1).titulo.cget("text") == "Histórico de hoy · 01/06/2025"


def test_una_fila_por_carrera_con_las_columnas_del_cli(con_carreras) -> None:
    historico = con_carreras(2)
    assert historico.filas_visibles == [
        ["1", "08:00:00", "08:01:00", "3,00 €"],
        ["2", "08:01:00", "08:02:00", "3,00 €"],
    ]


def test_total_del_dia(con_carreras) -> None:
    historico = con_carreras(2)
    assert historico.resumen.cget("text") == "2 carreras · Total del día"
    assert historico.total.cget("text") == "6,00 €"
    assert historico.total.cget("fg") == estilo.LED_ROJO


def test_una_carrera_en_singular(con_carreras) -> None:
    assert con_carreras(1).resumen.cget("text") == "1 carrera · Total del día"


def test_sin_carreras(con_carreras) -> None:
    historico = con_carreras(0)
    assert historico.filas_visibles == []
    assert historico.mensaje.cget("text") == SIN_CARRERAS
    assert historico.total.cget("text") == "0,00 €"


class TestDesplazar:
    """▲ ▼ de página en página cuando no caben todas."""

    def test_solo_una_pagina_a_la_vista(self, con_carreras) -> None:
        historico = con_carreras(estilo.FILAS_HISTORICO + 3)
        assert len(historico.filas_visibles) == estilo.FILAS_HISTORICO
        assert historico.filas_visibles[0][0] == "1"

    def test_bajar_y_subir(self, con_carreras) -> None:
        historico = con_carreras(estilo.FILAS_HISTORICO + 3)
        historico.bajar.invoke()
        # La última página se llena hasta el final, sin huecos.
        assert historico.filas_visibles[-1][0] == str(estilo.FILAS_HISTORICO + 3)
        assert len(historico.filas_visibles) == estilo.FILAS_HISTORICO
        historico.bajar.invoke()  # ya al final: no se mueve
        assert historico.filas_visibles[-1][0] == str(estilo.FILAS_HISTORICO + 3)
        historico.subir.invoke()
        historico.subir.invoke()  # ya al principio: no se mueve
        assert historico.filas_visibles[0][0] == "1"


class HistorialIlegible:
    def ultimo_numero(self) -> int:
        return 0

    def resumen_del_dia(self, fecha: date):
        raise PermissionError("sin permiso")


def test_si_no_se_puede_leer(raiz) -> None:
    servicio = ServicioTaximetro(Taximetro(historial=HistorialIlegible()))
    historico = App(servicio, raiz=raiz).mostrar(Historico)
    assert historico.mensaje.cget("text") == ILEGIBLE
    assert historico.filas_visibles == []


def test_volver_al_menu(con_carreras) -> None:
    historico = con_carreras(0)
    historico.volver.invoke()
    assert isinstance(historico.app.pantalla, Administrador)
