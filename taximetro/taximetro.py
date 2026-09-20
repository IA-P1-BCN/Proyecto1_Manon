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

    También numera las carreras: el contador vive en el taxímetro, no en la
    clase `Carrera`, para no compartir estado global entre instancias.
    """

    def __init__(
        self,
        tarifa: Tarifa | None = None,
        reloj: Callable[[], float] = time.monotonic,
        calendario: Callable[[], datetime] = datetime.now,
    ) -> None:
        """Inicializa el taxímetro sin ninguna carrera activa."""
        self._tarifa = tarifa or Tarifa()
        self._reloj = reloj
        self._calendario = calendario
        self._carrera: Carrera | None = None
        self._siguiente_id = 1

    @property
    def carrera_activa(self) -> Carrera | None:
        """La carrera en curso, o None si el taxímetro está libre.

        Una carrera deja de estar activa en cuanto se finaliza, que es lo que
        marca `hora_fin`.
        """
        if self._carrera is None or self._carrera.hora_fin is not None:
            return None
        return self._carrera

    def iniciar_carrera(self) -> Carrera:
        """Crea y activa una nueva carrera. Falla si ya hay una en curso."""
        if self.carrera_activa is not None:
            raise CarreraActivaError("Ya hay una carrera activa.")

        self._carrera = Carrera(
            id=self._siguiente_id,
            tarifa=self._tarifa,
            reloj=self._reloj,
            calendario=self._calendario,
        )
        self._siguiente_id += 1
        return self._carrera
