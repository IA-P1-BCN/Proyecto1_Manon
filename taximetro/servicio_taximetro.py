"""ServicioTaximetro: el único objeto con el que hablan las interfaces.

La interfaz gráfica y el CLI llaman a este servicio y a nada más del dominio.
Todo lo que devuelve son datos (instantáneas congeladas, números,
`ResumenDia`), nunca un `Carrera` o una `Tarifa` vivos: en la Fase 4 se
sustituye por un cliente HTTP con los mismos métodos, y un cliente HTTP solo
puede devolver datos. Ver `docs/decisions-fase3.md`, *Structural refactor*.

Las excepciones que pueden salir de sus métodos forman parte del contrato y se
importan desde aquí, igual que `Estado`, `ResumenDia` y `RegistroCarrera`.
"""

from __future__ import annotations

from dataclasses import dataclass

from taximetro.carrera import Carrera, Estado
from taximetro.historial import RegistroCarrera, ResumenDia
from taximetro.tarifa import Tarifa, TarifaInvalidaError
from taximetro.taximetro import CarreraActivaError, SinCarreraError, Taximetro

__all__ = [
    "AlmacenamientoError",
    "CarreraActivaError",
    "CarreraCerrada",
    "Estado",
    "InstantaneaCarrera",
    "RegistroCarrera",
    "ResumenDia",
    "ServicioTaximetro",
    "SinCarreraError",
    "TarifaInvalidaError",
    "TarifasVigentes",
]


class AlmacenamientoError(Exception):
    """No se pudo leer o escribir un fichero (tarifas o histórico).

    Envuelve el `OSError` original (disponible en `__cause__`), que ya quedó
    registrado en el log por el módulo que hizo la E/S.
    """


@dataclass(frozen=True)
class InstantaneaCarrera:
    """Una foto de la carrera en un momento dado: lo que muestra la pantalla."""

    id: int
    estado: Estado
    importe: float


@dataclass(frozen=True)
class CarreraCerrada:
    """El resultado de finalizar: el total, y si quedó guardado en el histórico.

    Cerrar la carrera y cobrarla nunca falla por el disco. Si el histórico no
    se pudo escribir, `guardada` es False y la interfaz avisa, pero el total
    se muestra igual.
    """

    carrera: InstantaneaCarrera
    guardada: bool


@dataclass(frozen=True)
class TarifasVigentes:
    """Las tarifas en €/s que se aplicarán a la próxima carrera."""

    parado: float
    en_movimiento: float


class ServicioTaximetro:
    """Fachada del taxímetro para la interfaz gráfica y el CLI.

    No tiene lógica de tarifas ni de carreras: traduce cada intención de la
    interfaz a una llamada a `Taximetro` y devuelve el resultado como datos.
    """

    def __init__(self, taximetro: Taximetro) -> None:
        """Envuelve un `Taximetro` ya construido (con sus relojes y ficheros)."""
        self._taximetro = taximetro

    def iniciar_carrera(self) -> InstantaneaCarrera:
        """Inicia una carrera. Lanza `CarreraActivaError` si ya hay una."""
        return self._instantanea(self._taximetro.iniciar_carrera())

    def cambiar_estado(self, estado: Estado) -> InstantaneaCarrera:
        """Pasa la carrera activa a `estado`. Lanza `SinCarreraError` si no hay."""
        carrera = self._carrera_activa()
        carrera.cambiar_estado(estado)
        return self._instantanea(carrera)

    def estado_actual(self) -> InstantaneaCarrera | None:
        """La carrera en curso con su importe al instante, o None si está libre."""
        carrera = self._taximetro.carrera_activa
        return None if carrera is None else self._instantanea(carrera)

    def finalizar_carrera(self) -> CarreraCerrada:
        """Cierra la carrera activa y la guarda en el histórico.

        Lanza `SinCarreraError` si no hay carrera. Un fallo al guardar no se
        lanza: la carrera ya está cerrada y su total congelado, así que se
        devuelve con `guardada=False`.
        """
        # Sin carrera, es `Taximetro` quien lanza `SinCarreraError` y lo registra.
        carrera = self._taximetro.carrera_activa
        try:
            self._taximetro.finalizar_carrera()
            guardada = True
        except OSError:
            # Ya lo registró Historial, con su traza.
            guardada = False
        return CarreraCerrada(carrera=self._instantanea(carrera), guardada=guardada)

    def tarifas(self) -> TarifasVigentes:
        """Las tarifas vigentes."""
        return self._vigentes(self._taximetro.tarifa)

    def cambiar_tarifas(self, parado: float, en_movimiento: float) -> TarifasVigentes:
        """Valida, guarda y aplica tarifas nuevas desde la próxima carrera.

        Lanza `TarifaInvalidaError` si no son válidas, `CarreraActivaError` si
        hay una carrera en curso y `AlmacenamientoError` si no se pueden
        guardar; en los tres casos las tarifas vigentes no cambian.
        """
        tarifa = Tarifa(parado=parado, en_movimiento=en_movimiento)
        try:
            self._taximetro.cambiar_tarifa(tarifa)
        except OSError as error:
            raise AlmacenamientoError("No se pudieron guardar las tarifas.") from error
        return self._vigentes(tarifa)

    def resumen_del_dia(self) -> ResumenDia:
        """Las carreras terminadas hoy y su total.

        Lanza `AlmacenamientoError` si el histórico no se puede leer.
        """
        try:
            return self._taximetro.resumen_del_dia()
        except OSError as error:
            raise AlmacenamientoError("No se pudo leer el histórico.") from error

    def _carrera_activa(self) -> Carrera:
        """La carrera en curso, o `SinCarreraError`."""
        carrera = self._taximetro.carrera_activa
        if carrera is None:
            raise SinCarreraError("No hay ninguna carrera activa.")
        return carrera

    @staticmethod
    def _instantanea(carrera: Carrera) -> InstantaneaCarrera:
        """Copia en datos lo que la interfaz necesita de una carrera."""
        return InstantaneaCarrera(
            id=carrera.id, estado=carrera.estado, importe=carrera.importe_actual()
        )

    @staticmethod
    def _vigentes(tarifa: Tarifa) -> TarifasVigentes:
        """Copia en datos las dos tarifas."""
        return TarifasVigentes(parado=tarifa.parado, en_movimiento=tarifa.en_movimiento)
