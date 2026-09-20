"""Carrera: estado y datos de una carrera individual de taxi."""

from __future__ import annotations

import time
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    # Solo para anotaciones: `tarifa.py` importa `Estado` de este módulo, así que
    # importar `Tarifa` aquí en tiempo de ejecución crearía un import circular.
    # Con `from __future__ import annotations` las anotaciones no se evalúan,
    # por lo que basta con importarla bajo TYPE_CHECKING.
    from taximetro.tarifa import Tarifa


class Estado(Enum):
    """Estados posibles del vehículo durante una carrera."""

    PARADO = "parado"
    EN_MOVIMIENTO = "en_movimiento"


class CarreraFinalizadaError(Exception):
    """Se lanza al intentar modificar una carrera ya finalizada."""


class Carrera:
    """Una carrera de taxi, desde el inicio hasta la finalización.

    Atributos: `id`, `hora_inicio`, `hora_fin` (None hasta finalizar), `estado`,
    `distancia` (0.0, reservado para fases futuras) e `importe`.

    Usa dos relojes distintos, ambos inyectables: `reloj` mide el tiempo
    transcurrido para acumular el importe (monótono, nunca retrocede) y
    `calendario` sella `hora_inicio` / `hora_fin`. Ver
    `docs/decisions-fase1-scaffold.md`.
    """

    def __init__(
        self,
        tarifa: Tarifa,
        reloj: Callable[[], float] = time.monotonic,
        calendario: Callable[[], datetime] = datetime.now,
    ) -> None:
        """Crea una carrera nueva en estado PARADO, con el importe a cero."""

    def cambiar_estado(self, nuevo_estado: Estado) -> None:
        """Acumula el importe del tramo en curso y cambia de estado."""

    def importe_actual(self) -> float:
        """Devuelve el importe acumulado más el tramo en curso, sin mutar nada.

        Sobre una carrera ya finalizada devuelve el total congelado.
        """

    def finalizar(self) -> float:
        """Cierra la carrera, acumula el último tramo y devuelve el importe total."""
