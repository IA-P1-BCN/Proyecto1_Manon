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

import logging
from dataclasses import dataclass
from datetime import datetime

from taximetro.auth import Auth, CredencialesError
from taximetro.carrera import Carrera, Estado
from taximetro.config_tarifas import ConfigTarifas
from taximetro.historial import Historial, RegistroCarrera, ResumenDia
from taximetro.logs import campos
from taximetro.tarifa import Tarifa, TarifaInvalidaError
from taximetro.taximetro import CarreraActivaError, SinCarreraError, Taximetro

logger = logging.getLogger(__name__)

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
    """No se pudo leer o escribir un fichero (tarifas, histórico o credenciales).

    Envuelve el `OSError` original (disponible en `__cause__`), que ya quedó
    registrado en el log por el módulo que hizo la E/S.
    """


@dataclass(frozen=True)
class InstantaneaCarrera:
    """Una foto de la carrera en un momento dado: lo que muestra la pantalla.

    `duracion` son los segundos desde `hora_inicio` hasta ahora, o hasta el
    final si la carrera ya se cerró.
    """

    id: int
    estado: Estado
    importe: float
    hora_inicio: datetime
    duracion: float


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
    interfaz a una llamada a `Taximetro` (o a `Auth`, para la contraseña) y
    devuelve el resultado como datos.
    """

    def __init__(self, taximetro: Taximetro, auth: Auth | None = None) -> None:
        """Envuelve un `Taximetro` ya construido (con sus relojes y ficheros).

        Sin `auth` no hay credenciales que comprobar y el acceso de
        Administrador se deniega siempre: nunca se lee un fichero que no se ha
        pedido, y ante la duda la puerta queda cerrada.
        """
        self._taximetro = taximetro
        self._auth = auth

    @classmethod
    def por_defecto(cls) -> ServicioTaximetro:
        """El servicio del programa real: tarifas e histórico en sus ficheros.

        Lo usan los dos puntos de entrada (CLI e interfaz gráfica), así que el
        montaje del dominio está en un solo sitio y ninguna interfaz lo conoce.
        Lee `config/tarifas.json` y `data/historial.csv` al crearse, y
        `config/credenciales.json` en cada comprobación de contraseña.
        """
        return cls(Taximetro(config=ConfigTarifas(), historial=Historial()), Auth())

    def comprobar_contrasena(self, contrasena: str) -> bool:
        """True si `contrasena` abre el Administrador (US-08).

        La interfaz decide qué hacer con la respuesta; aquí se registra el
        intento, para que las dos interfaces usen los mismos eventos. Lanza
        `AlmacenamientoError` si las credenciales no se pueden leer: no es una
        contraseña incorrecta y la pantalla lo dice de otra forma. La
        contraseña tecleada no se registra nunca, ni siquiera si es incorrecta.
        """
        try:
            if self._auth is None:
                raise CredencialesError("No hay credenciales configuradas.")
            correcta = self._auth.comprobar(contrasena)
        except CredencialesError as error:
            logger.warning(
                "acceso_admin_denegado %s", campos(motivo="credenciales_ilegibles")
            )
            raise AlmacenamientoError(
                "No se pudieron leer las credenciales."
            ) from error
        if correcta:
            logger.info("acceso_admin_concedido")
        else:
            logger.warning(
                "acceso_admin_denegado %s", campos(motivo="contrasena_incorrecta")
            )
        return correcta

    def iniciar_carrera(self) -> InstantaneaCarrera:
        """Inicia una carrera. Lanza `CarreraActivaError` si ya hay una."""
        return self._instantanea(self._taximetro.iniciar_carrera())

    def cambiar_estado(self, estado: Estado) -> InstantaneaCarrera:
        """Pasa la carrera activa a `estado`. Lanza `SinCarreraError` si no hay.

        Descarta un cierre pedido y no confirmado: después de cambiar de estado
        ya no se puede cerrar en aquel instante.
        """
        carrera = self._carrera_activa()
        self._taximetro.descongelar()
        carrera.cambiar_estado(estado)
        return self._instantanea(carrera)

    def estado_actual(self) -> InstantaneaCarrera | None:
        """La carrera en curso con su importe al instante, o None si está libre."""
        carrera = self._taximetro.carrera_activa
        return None if carrera is None else self._instantanea(carrera)

    def congelar_importe(self) -> InstantaneaCarrera:
        """Pide cerrar la carrera: la foto de este instante, que es lo que se cobrará.

        Se llama al pulsar FINALIZAR (o al pedir salir con una carrera en
        curso), antes de preguntar. Si se confirma, `finalizar_carrera()` cobra
        este importe y no el del momento de la respuesta; si no,
        `seguir_carrera()`. Lanza `SinCarreraError` si no hay carrera.
        """
        congelacion = self._taximetro.congelar()
        carrera = congelacion.carrera
        return InstantaneaCarrera(
            id=carrera.id,
            estado=carrera.estado,
            importe=congelacion.importe,
            hora_inicio=carrera.hora_inicio,
            duracion=carrera.duracion(hasta=congelacion.hora),
        )

    def seguir_carrera(self) -> None:
        """NO, SEGUIR: descarta el cierre pedido y la carrera sigue como si nada.

        El tiempo de la pregunta también se cobra: el taxi seguía ocupado.
        """
        self._taximetro.descongelar()

    def finalizar_carrera(self) -> CarreraCerrada:
        """Cierra la carrera activa y la guarda en el histórico.

        Si antes se llamó a `congelar_importe()`, cobra el importe de aquel
        instante.

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
            id=carrera.id,
            estado=carrera.estado,
            importe=carrera.importe_actual(),
            hora_inicio=carrera.hora_inicio,
            duracion=carrera.duracion(),
        )

    @staticmethod
    def _vigentes(tarifa: Tarifa) -> TarifasVigentes:
        """Copia en datos las dos tarifas."""
        return TarifasVigentes(parado=tarifa.parado, en_movimiento=tarifa.en_movimiento)
