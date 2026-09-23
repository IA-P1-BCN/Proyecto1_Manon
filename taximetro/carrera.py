"""Carrera: estado y datos de una carrera individual de taxi."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Callable

from taximetro.logs import campos

if TYPE_CHECKING:
    # Solo para anotaciones: `tarifa.py` importa `Estado` de este módulo, así que
    # importar `Tarifa` aquí en tiempo de ejecución crearía un import circular.
    # Con `from __future__ import annotations` las anotaciones no se evalúan,
    # por lo que basta con importarla bajo TYPE_CHECKING.
    from taximetro.tarifa import Tarifa

logger = logging.getLogger(__name__)


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
        id: int,
        tarifa: Tarifa,
        reloj: Callable[[], float] = time.monotonic,
        calendario: Callable[[], datetime] = datetime.now,
    ) -> None:
        """Crea una carrera nueva en estado EN_MOVIMIENTO, con el importe a cero.

        El número de carrera (`id`) lo asigna quien la crea — en la práctica,
        `Taximetro` —, no un contador global de la clase.
        """
        self.id = id
        self.estado = Estado.EN_MOVIMIENTO
        self.importe = 0.0
        self.distancia = 0.0
        self.hora_inicio = calendario()
        self.hora_fin: datetime | None = None

        self._tarifa = tarifa
        self._reloj = reloj
        self._calendario = calendario
        # Instante en que empezó el tramo actual. Se reinicia en cada cambio de
        # estado, y es lo que se resta para saber cuántos segundos cobrar.
        self._inicio_tramo = reloj()
        logger.info(
            "carrera_iniciada %s",
            campos(
                carrera=self.id,
                estado=self.estado.value,
                tarifa=tarifa.calcular_importe(self.estado, 1),
            ),
        )

    @property
    def finalizada(self) -> bool:
        """True si la carrera ya está cerrada y no admite más cambios."""
        return self.hora_fin is not None

    def duracion(self) -> float:
        """Segundos desde `hora_inicio` hasta `hora_fin`, o hasta ahora si sigue en curso.

        Se mide con el calendario, igual que la `duracion_s` del log de
        `carrera_finalizada`: es un dato para mostrar, no para cobrar (el
        importe se acumula con el reloj monótono).
        """
        fin = self.hora_fin if self.hora_fin is not None else self._calendario()
        return (fin - self.hora_inicio).total_seconds()

    def _segundos_en_curso(self) -> float:
        """Segundos transcurridos en el tramo actual, sin cerrarlo."""
        return self._reloj() - self._inicio_tramo

    def _cerrar_tramo(self) -> None:
        """Acumula el tramo en curso en el importe y reinicia la marca."""
        # El reloj se lee una sola vez a propósito: con dos lecturas, los
        # microsegundos que pasan entre una y otra se perderían sin cobrar.
        ahora = self._reloj()
        segundos = ahora - self._inicio_tramo
        self.importe += self._tarifa.calcular_importe(self.estado, segundos)
        self._inicio_tramo = ahora

    def cambiar_estado(self, nuevo_estado: Estado) -> None:
        """Acumula el importe del tramo en curso y cambia de estado.

        Repetir el estado actual no hace nada: el importe sigue acumulándose a
        la misma tarifa. Sobre una carrera finalizada lanza
        `CarreraFinalizadaError`.
        """
        if self.finalizada:
            logger.warning("cambio_rechazado %s", campos(carrera=self.id, motivo="finalizada"))
            raise CarreraFinalizadaError(
                f"La carrera nº {self.id} ya está finalizada."
            )
        if nuevo_estado is self.estado:
            return

        anterior = self.estado
        self._cerrar_tramo()
        self.estado = nuevo_estado
        logger.info(
            "estado_cambiado %s",
            campos(
                carrera=self.id,
                de=anterior.value,
                a=nuevo_estado.value,
                acumulado=self.importe,
            ),
        )

    def importe_actual(self) -> float:
        """Devuelve el importe acumulado más el tramo en curso, sin mutar nada.

        Sobre una carrera ya finalizada devuelve el total congelado.
        """
        if self.finalizada:
            return self.importe
        return self.importe + self._tarifa.calcular_importe(
            self.estado, self._segundos_en_curso()
        )

    def finalizar(self) -> float:
        """Cierra la carrera, acumula el último tramo y devuelve el importe total.

        Sobre una carrera ya finalizada lanza `CarreraFinalizadaError`: el
        total ya se cobró y no puede recalcularse.
        """
        if self.finalizada:
            logger.warning(
                "finalizar_rechazado %s", campos(carrera=self.id, motivo="finalizada")
            )
            raise CarreraFinalizadaError(
                f"La carrera nº {self.id} ya está finalizada."
            )

        self._cerrar_tramo()
        self.hora_fin = self._calendario()
        logger.info(
            "carrera_finalizada %s",
            campos(
                carrera=self.id,
                importe=self.importe,
                duracion_s=int((self.hora_fin - self.hora_inicio).total_seconds()),
            ),
        )
        return self.importe
