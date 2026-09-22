"""Tests de `taximetro.historial.Historial` (US-05 / T5.1, T5.2, T5.4).

Cada test escribe en su propia carpeta temporal (`tmp_path`): ninguno toca el
`data/historial.csv` del repo.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path

import pytest

from taximetro.carrera import Carrera
from taximetro.historial import COLUMNAS, RUTA_POR_DEFECTO, Historial
from taximetro.tarifa import Tarifa
from taximetro.utils import formato_euros

HOY = date(2025, 6, 1)  # la fecha de CalendarioFalso


@pytest.fixture
def historial(tmp_path: Path) -> Historial:
    """Un histórico vacío, en una carpeta que aún no existe."""
    return Historial(tmp_path / "data" / "historial.csv")


@pytest.fixture
def cerrar(reloj, calendario):
    """Crea y finaliza una carrera de `segundos` en movimiento (0,05 €/s)."""
    numero = 0

    def _cerrar(segundos: float) -> Carrera:
        nonlocal numero
        numero += 1
        carrera = Carrera(numero, Tarifa(), reloj=reloj, calendario=calendario)
        reloj.avanzar(segundos)
        calendario.avanzar(segundos)
        carrera.finalizar()
        return carrera

    return _cerrar


class TestRegistrar:
    def test_crea_el_fichero_con_cabecera(self, historial, cerrar) -> None:
        historial.registrar(cerrar(60))
        lineas = historial.ruta.read_text(encoding="utf-8").splitlines()
        assert lineas[0] == ",".join(COLUMNAS)
        assert lineas[1] == "1,2025-06-01T08:00:00,2025-06-01T08:01:00,3.00,0.00"

    def test_anade_una_fila_por_carrera_sin_reescribir(self, historial, cerrar) -> None:
        historial.registrar(cerrar(60))
        primera = historial.ruta.read_text(encoding="utf-8")
        historial.registrar(cerrar(20))
        contenido = historial.ruta.read_text(encoding="utf-8")
        assert contenido.startswith(primera)
        assert len(contenido.splitlines()) == 3  # cabecera + 2 carreras

    def test_guarda_el_importe_cobrado_en_centimos(self, historial, cerrar) -> None:
        # 10,26 s a 0,05 €/s = 0,513 €: se cobran 0,51 €, y eso es lo que se guarda.
        historial.registrar(cerrar(10.26))
        assert historial.registros()[0].importe == 0.51

    @pytest.mark.parametrize("segundos", [10.26, 12.5, 12.7, 59.99])
    def test_guarda_lo_mismo_que_se_mostro(self, historial, cerrar, segundos) -> None:
        # El redondeo es el de `formato_euros`, también en los medios céntimos
        # (0,625 € se muestra 0,62 €): el histórico nunca contradice el ticket.
        carrera = cerrar(segundos)
        historial.registrar(carrera)
        guardado = historial.registros()[0].importe
        assert formato_euros(guardado) == formato_euros(carrera.importe)

    def test_una_carrera_abierta_no_se_registra(self, historial, reloj) -> None:
        with pytest.raises(ValueError, match="no está finalizada"):
            historial.registrar(Carrera(1, Tarifa(), reloj=reloj))
        assert not historial.ruta.exists()


class TestLeer:
    def test_sin_fichero_no_hay_registros(self, historial) -> None:
        assert historial.registros() == []
        assert historial.ultimo_numero() == 0

    def test_lo_registrado_se_vuelve_a_leer(self, historial, cerrar) -> None:
        historial.registrar(cerrar(60))
        registro = Historial(historial.ruta).registros()[0]
        assert registro.carrera == 1
        assert registro.hora_inicio == datetime(2025, 6, 1, 8, 0, 0)
        assert registro.hora_fin == datetime(2025, 6, 1, 8, 1, 0)
        assert registro.importe == 3.00
        assert registro.distancia == 0.0

    def test_salta_las_filas_ilegibles(self, historial, cerrar) -> None:
        historial.registrar(cerrar(60))
        with historial.ruta.open("a", encoding="utf-8") as fichero:
            fichero.write("roto,,,\n")
            fichero.write("2,2025-06-01T09:00:00\n")  # escritura cortada
        historial.registrar(cerrar(20))
        assert [r.carrera for r in historial.registros()] == [1, 2]

    def test_ultimo_numero(self, historial, cerrar) -> None:
        for _ in range(3):
            historial.registrar(cerrar(10))
        assert historial.ultimo_numero() == 3


class TestResumenDelDia:
    """US-05: listado del día y total de caja."""

    def test_suma_las_carreras_del_dia(self, historial, cerrar) -> None:
        historial.registrar(cerrar(60))  # 3,00 €
        historial.registrar(cerrar(20))  # 1,00 €
        resumen = historial.resumen_del_dia(HOY)
        assert [r.carrera for r in resumen.carreras] == [1, 2]
        assert resumen.total == 4.00

    def test_el_total_es_la_suma_de_los_tickets(self, historial, cerrar) -> None:
        # 0,513 € + 0,513 € = 1,026 € (1,03 €) sin redondear, pero se cobraron
        # dos tickets de 0,51 €: la caja tiene 1,02 €.
        historial.registrar(cerrar(10.26))
        historial.registrar(cerrar(10.26))
        assert historial.resumen_del_dia(HOY).total == 1.02

    def test_un_dia_sin_carreras(self, historial) -> None:
        resumen = historial.resumen_del_dia(HOY)
        assert resumen.carreras == ()
        assert resumen.total == 0
        assert resumen.fecha == HOY

    def test_solo_cuenta_las_del_dia_pedido(self, historial, cerrar, calendario) -> None:
        historial.registrar(cerrar(60))
        calendario.avanzar(24 * 3600)
        historial.registrar(cerrar(60))
        assert len(historial.resumen_del_dia(HOY).carreras) == 1

    def test_cuenta_el_dia_en_que_termina(self, historial, reloj) -> None:
        # Empieza el 1 a las 23:59:30 y termina el 2 a las 00:00:30.
        horas = iter([datetime(2025, 6, 1, 23, 59, 30), datetime(2025, 6, 2, 0, 0, 30)])
        carrera = Carrera(1, Tarifa(), reloj=reloj, calendario=lambda: next(horas))
        reloj.avanzar(60)
        carrera.finalizar()
        historial.registrar(carrera)
        assert historial.resumen_del_dia(HOY).carreras == ()
        assert len(historial.resumen_del_dia(date(2025, 6, 2)).carreras) == 1


class TestRuta:
    def test_por_defecto_es_data_historial_csv(self) -> None:
        assert Historial().ruta == RUTA_POR_DEFECTO == Path("data/historial.csv")


class TestLogs:
    """US-06 / T6.2: cada carrera guardada, y cada fallo, queda en el log."""

    def test_registra_la_carrera_guardada(self, eventos, historial, cerrar) -> None:
        historial.registrar(cerrar(60))
        assert (
            f"carrera_guardada carrera=1 importe=3.00 ruta={historial.ruta}" in eventos()
        )

    def test_no_poder_guardar_es_error(self, eventos, tmp_path: Path, cerrar) -> None:
        (tmp_path / "data").write_text("", encoding="utf-8")  # bloquea mkdir
        historial = Historial(tmp_path / "data" / "historial.csv")
        with pytest.raises(OSError):
            historial.registrar(cerrar(60))
        assert eventos(logging.ERROR) == [
            f"carrera_no_guardada carrera=1 importe=3.00 ruta={historial.ruta}"
        ]

    def test_una_fila_ilegible_es_warning_con_su_linea(
        self, eventos, historial, cerrar
    ) -> None:
        historial.registrar(cerrar(60))
        with historial.ruta.open("a", encoding="utf-8") as fichero:
            fichero.write("roto,,,\n")
        historial.registros()
        assert eventos(logging.WARNING) == [
            f"fila_ilegible ruta={historial.ruta} linea=3"
        ]
