"""Fixtures compartidas por toda la batería de tests.

El dominio recibe sus dos relojes por inyección (ver
`docs/decisions-fase1-scaffold.md`), así que los tests nunca necesitan dormir
tiempo real ni parchear el módulo `time`: avanzan el reloj a mano.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import pytest


class RelojFalso:
    """Reloj monótono controlado por el test, en segundos.

    Sustituye a `time.monotonic` en la acumulación del importe: el test decide
    cuántos segundos han pasado en cada tramo.
    """

    def __init__(self, inicio: float = 0.0) -> None:
        """Arranca el reloj en `inicio` segundos."""
        self._ahora = inicio

    def __call__(self) -> float:
        """Devuelve el instante actual, como haría `time.monotonic()`."""
        return self._ahora

    def avanzar(self, segundos: float) -> None:
        """Adelanta el reloj `segundos`, sin esperar en tiempo real."""
        self._ahora += segundos


class CalendarioFalso:
    """Calendario determinista que sustituye a `datetime.now`.

    Cada llamada devuelve un instante fijo, salvo que el test lo adelante.
    """

    def __init__(self, inicio: datetime | None = None) -> None:
        """Arranca el calendario en `inicio` (por defecto, una fecha fija)."""
        self._ahora = inicio or datetime(2025, 6, 1, 8, 0, 0)

    def __call__(self) -> datetime:
        """Devuelve la fecha y hora actuales, como haría `datetime.now()`."""
        return self._ahora

    def avanzar(self, segundos: float) -> None:
        """Adelanta el calendario `segundos`."""
        self._ahora += timedelta(seconds=segundos)


@pytest.fixture
def reloj() -> RelojFalso:
    """Reloj monótono falso para medir tramos sin esperar."""
    return RelojFalso()


@pytest.fixture
def calendario() -> CalendarioFalso:
    """Calendario falso para sellar hora_inicio / hora_fin de forma estable."""
    return CalendarioFalso()


@pytest.fixture
def eventos(caplog):
    """Lee los logs de operación del paquete (US-06).

    Activa la captura desde INFO para los loggers `taximetro.*` y devuelve una
    función que da los mensajes de un nivel, en orden. Hay que pedir este
    fixture antes que los que ya generan eventos al crearse.
    """
    caplog.set_level(logging.INFO, logger="taximetro")

    def _eventos(nivel: int = logging.INFO) -> list[str]:
        return [
            registro.getMessage()
            for registro in caplog.records
            if registro.name.startswith("taximetro") and registro.levelno == nivel
        ]

    return _eventos
