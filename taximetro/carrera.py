"""Carrera: estado y datos de una carrera individual de taxi."""

from __future__ import annotations

import time
from enum import Enum
from typing import Callable


class Estado(Enum):
    """Estados posibles del vehículo durante una carrera."""

    PARADO = "parado"
    EN_MOVIMIENTO = "en_movimiento"


class CarreraFinalizadaError(Exception):
    """Se lanza al intentar modificar una carrera ya finalizada."""


class Carrera:
    """Una carrera de taxi, desde el inicio hasta la finalización."""

    def __init__(self, reloj: Callable[[], float] = time.time) -> None:
        """Crea una carrera nueva en estado PARADO, con el importe a cero."""

    def cambiar_estado(self, nuevo_estado: Estado) -> None:
        """Acumula el importe del tramo actual en curso y cambia de estado."""

    def finalizar(self) -> float:
        """Cierra la carrera, acumula el último tramo y devuelve el importe total."""
