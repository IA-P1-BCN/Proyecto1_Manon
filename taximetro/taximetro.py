"""Taximetro: orquesta el ciclo de vida de la carrera activa."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from taximetro.carrera import Carrera
from taximetro.tarifa import Tarifa


class CarreraActivaError(Exception):
    """Se lanza al intentar iniciar una carrera mientras otra sigue activa."""


class Taximetro:
    """Gestiona la carrera activa: inicio, cambios de estado y finalización.

    Es el dueño de la `Tarifa` y de los dos relojes, y se los inyecta a cada
    `Carrera` que crea. Así, cuando la Fase 2 cargue las tarifas de un fichero
    de configuración (US-07), el cambio se queda aquí y `Carrera` no se toca.
    """

    def __init__(
        self,
        tarifa: Tarifa | None = None,
        reloj: Callable[[], float] = time.monotonic,
        calendario: Callable[[], datetime] = datetime.now,
    ) -> None:
        """Inicializa el taxímetro sin ninguna carrera activa."""

    def iniciar_carrera(self) -> Carrera:
        """Crea y activa una nueva carrera. Falla si ya hay una en curso."""
