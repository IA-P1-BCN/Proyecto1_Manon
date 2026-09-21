"""Tests de `taximetro.logs` (US-06 / T6.1, T6.3, T6.4).

Cada test escribe en su propia carpeta temporal y deja el logger `taximetro`
como lo encontró: un handler olvidado seguiría escribiendo en los tests
siguientes.
"""

from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

from taximetro.logs import (
    COPIAS,
    LOGGER_RAIZ,
    RUTA_POR_DEFECTO,
    TAMANO_MAXIMO,
    campos,
    configurar_logs,
)


@pytest.fixture(autouse=True)
def logger_limpio():
    """Restaura handlers y nivel del logger del paquete al terminar."""
    raiz = logging.getLogger(LOGGER_RAIZ)
    handlers, nivel = list(raiz.handlers), raiz.level
    yield
    for handler in raiz.handlers:
        if handler not in handlers:
            handler.close()
    raiz.handlers = handlers
    raiz.setLevel(nivel)


@pytest.fixture
def ruta(tmp_path: Path) -> Path:
    return tmp_path / "logs" / "taximetro.log"


class TestConfigurarLogs:
    def test_escribe_los_eventos_del_paquete_en_el_fichero(self, ruta: Path) -> None:
        handler = configurar_logs(ruta)
        logging.getLogger("taximetro.carrera").info("carrera_iniciada carrera=1")
        handler.flush()
        linea = ruta.read_text(encoding="utf-8").strip()
        assert re.fullmatch(
            r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d INFO taximetro\.carrera carrera_iniciada carrera=1",
            linea,
        )

    def test_incluye_nivel_warning_y_error(self, ruta: Path) -> None:
        handler = configurar_logs(ruta)
        logging.getLogger("taximetro.x").warning("aviso")
        logging.getLogger("taximetro.x").error("fallo")
        handler.flush()
        contenido = ruta.read_text(encoding="utf-8")
        assert " WARNING taximetro.x aviso" in contenido
        assert " ERROR taximetro.x fallo" in contenido

    def test_no_registra_debug(self, ruta: Path) -> None:
        handler = configurar_logs(ruta)
        logging.getLogger("taximetro.x").debug("ruido")
        handler.flush()
        assert "ruido" not in ruta.read_text(encoding="utf-8")

    def test_no_escribe_lo_que_no_es_del_paquete(self, ruta: Path) -> None:
        handler = configurar_logs(ruta)
        logging.getLogger("otra_libreria").warning("ajeno")
        handler.flush()
        assert "ajeno" not in ruta.read_text(encoding="utf-8")

    def test_rota_el_fichero(self, ruta: Path) -> None:
        # T6.3: tamaño acotado, el disco del taxi no se llena.
        handler = configurar_logs(ruta)
        assert isinstance(handler, RotatingFileHandler)
        assert handler.maxBytes == TAMANO_MAXIMO == 1_000_000
        assert handler.backupCount == COPIAS == 5

    def test_llamarla_dos_veces_no_duplica_lineas(self, ruta: Path) -> None:
        configurar_logs(ruta)
        handler = configurar_logs(ruta)
        logging.getLogger("taximetro.x").info("una_vez")
        handler.flush()
        assert ruta.read_text(encoding="utf-8").count("una_vez") == 1

    def test_si_no_se_puede_abrir_el_fichero_sigue_sin_logs(self, tmp_path: Path) -> None:
        (tmp_path / "logs").write_text("", encoding="utf-8")  # bloquea mkdir
        handler = configurar_logs(tmp_path / "logs" / "taximetro.log")
        assert isinstance(handler, logging.NullHandler)
        logging.getLogger("taximetro.x").warning("no rompe nada")

    def test_ruta_por_defecto(self) -> None:
        assert RUTA_POR_DEFECTO == Path("logs/taximetro.log")


class TestCampos:
    def test_clave_valor_en_orden(self) -> None:
        assert campos(carrera=1, estado="parado") == "carrera=1 estado=parado"

    def test_los_float_salen_con_dos_decimales(self) -> None:
        assert campos(importe=3.0, tarifa=0.05) == "importe=3.00 tarifa=0.05"


class TestLoggersDelPaquete:
    """Todos los módulos escriben bajo `taximetro`, que es donde está el handler."""

    def test_lanzado_con_python_m_escribe_en_el_fichero(self, tmp_path: Path) -> None:
        # Con `python -m`, el módulo de la capa CLI se llama `__main__`, y un
        # logger con `__name__` quedaría fuera del fichero. Bajo pytest el
        # módulo se importa con su nombre normal y el fallo no se ve, así que
        # se lanza el programa real, en una carpeta temporal.
        import os
        import subprocess
        import sys

        raiz = Path(__file__).parent.parent
        entorno = {**os.environ, "PYTHONPATH": str(raiz), "PYTHONIOENCODING": "utf-8"}
        resultado = subprocess.run(
            [sys.executable, "-m", "taximetro.taximetro_app"],
            input="2\n1\nabc\n3\n3\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=tmp_path,
            env=entorno,
            timeout=30,
        )
        log = (tmp_path / "logs" / "taximetro.log").read_text(encoding="utf-8")
        assert "aplicacion_iniciada" in log
        assert "WARNING taximetro.taximetro_app tarifa_rechazada" in log
        assert "aplicacion_cerrada motivo=salir" in log
        assert "tarifa_rechazada" not in resultado.stderr  # nada en la consola
