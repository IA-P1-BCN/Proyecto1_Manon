"""Taximetro: orquesta el ciclo de vida de la carrera activa."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from taximetro.carrera import Carrera
from taximetro.config_tarifas import ConfigTarifas
from taximetro.historial import Historial, ResumenDia
from taximetro.tarifa import Tarifa


class CarreraActivaError(Exception):
    """Se lanza al intentar iniciar una carrera mientras otra sigue activa."""


class SinCarreraError(Exception):
    """Se lanza al intentar finalizar cuando no hay ninguna carrera activa."""


class Taximetro:
    """Gestiona la carrera activa: inicio, cambios de estado y finalización.

    Es el dueño de la `Tarifa` y de los dos relojes, y se los inyecta a cada
    `Carrera` que crea. Las tarifas pueden venir de un fichero de
    configuración (US-07): el cambio se queda aquí y `Carrera` no se toca.
    Cada carrera se queda con la tarifa que había al iniciarse.

    También numera las carreras: el contador vive en el taxímetro, no en la
    clase `Carrera`, para no compartir estado global entre instancias. Con
    histórico, la numeración sigue desde la última carrera guardada, así un
    reinicio del programa no repite números en el histórico del día.

    Toda carrera se cierra con `finalizar_carrera()`, que la guarda en el
    histórico (US-05) venga de donde venga el cierre: el menú, EOF o Ctrl+C.
    """

    def __init__(
        self,
        tarifa: Tarifa | None = None,
        config: ConfigTarifas | None = None,
        historial: Historial | None = None,
        reloj: Callable[[], float] = time.monotonic,
        calendario: Callable[[], datetime] = datetime.now,
    ) -> None:
        """Inicializa el taxímetro sin ninguna carrera activa.

        Sin `tarifa` ni `config`, usa las tarifas por defecto y no toca el
        disco; con `config`, las carga del fichero y guarda en él cada cambio.
        Sin `historial`, las carreras no se guardan.
        """
        self._config = config
        if tarifa is None:
            tarifa = config.cargar() if config is not None else Tarifa()
        self._tarifa = tarifa
        self._reloj = reloj
        self._calendario = calendario
        self._carrera: Carrera | None = None
        self._historial = historial
        self._siguiente_id = 1 + (historial.ultimo_numero() if historial else 0)

    @property
    def tarifa(self) -> Tarifa:
        """Las tarifas vigentes, para que la capa CLI pueda mostrarlas."""
        return self._tarifa

    def cambiar_tarifa(self, tarifa: Tarifa) -> None:
        """Aplica una tarifa nueva desde la próxima carrera y la guarda.

        Se guarda antes de aplicarla: si el fichero no se puede escribir, sale
        el `OSError` y la tarifa en uso no cambia, así fichero y taxímetro
        nunca discrepan. Falla con una carrera activa, porque al pasajero se le
        cobra la tarifa anunciada al empezar.
        """
        if self.carrera_activa is not None:
            raise CarreraActivaError("No se cambian las tarifas con una carrera activa.")
        if self._config is not None:
            self._config.guardar(tarifa)
        self._tarifa = tarifa

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

    def finalizar_carrera(self) -> float:
        """Cierra la carrera activa, la guarda en el histórico y devuelve el total.

        La carrera se cierra antes de guardarla: si el fichero no se puede
        escribir, sale el `OSError` pero la carrera ya está cerrada y su total
        congelado en `carrera.importe`, así que el cobro no se pierde.
        Sin carrera activa lanza `SinCarreraError`.
        """
        carrera = self.carrera_activa
        if carrera is None:
            raise SinCarreraError("No hay ninguna carrera activa.")
        total = carrera.finalizar()
        if self._historial is not None:
            self._historial.registrar(carrera)
        return total

    def resumen_del_dia(self) -> ResumenDia:
        """Las carreras que han terminado hoy y su total (US-05).

        "Hoy" lo dice el calendario inyectado. Sin histórico, un resumen vacío.
        """
        hoy = self._calendario().date()
        if self._historial is None:
            return ResumenDia(fecha=hoy, carreras=())
        return self._historial.resumen_del_dia(hoy)
