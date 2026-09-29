"""Historial: registro persistente de las carreras finalizadas (US-05)."""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from taximetro.infrastructure.logs import campos

if TYPE_CHECKING:
    from taximetro.domain.carrera import Carrera

logger = logging.getLogger(__name__)

# Relativa al directorio desde el que se lanza el programa, igual que
# `config/tarifas.json`.
RUTA_POR_DEFECTO = Path("data") / "historial.csv"

COLUMNAS = ("carrera", "hora_inicio", "hora_fin", "importe", "distancia")


@dataclass(frozen=True)
class RegistroCarrera:
    """Una fila del histórico: una carrera ya cobrada."""

    carrera: int
    hora_inicio: datetime
    hora_fin: datetime
    importe: float
    distancia: float


@dataclass(frozen=True)
class ResumenDia:
    """Las carreras de un día y la caja que suman."""

    fecha: date
    carreras: tuple[RegistroCarrera, ...]

    @property
    def total(self) -> float:
        """Suma de los importes cobrados ese día."""
        return round(sum(registro.importe for registro in self.carreras), 2)


class Historial:
    """El histórico de carreras en un CSV, una fila por carrera finalizada.

    Se escribe añadiendo una fila por carrera, nunca reescribiendo el fichero:
    un cierre inesperado no puede corromper las carreras anteriores, y el
    fichero se abre en una hoja de cálculo para cuadrar caja. Se conservan
    todas las carreras; la migración a base de datos es cosa de la Fase 4.
    """

    def __init__(self, ruta: Path = RUTA_POR_DEFECTO) -> None:
        """Apunta al fichero del histórico, sin leerlo todavía."""
        self._ruta = Path(ruta)

    @property
    def ruta(self) -> Path:
        """Dónde está el fichero."""
        return self._ruta

    def registrar(self, carrera: Carrera) -> None:
        """Añade una carrera finalizada al final del fichero.

        Se guarda el importe redondeado a céntimos, que es lo que se cobró al
        pasajero: así el total del día es la suma exacta de los tickets.
        """
        if carrera.hora_fin is None:
            raise ValueError(f"La carrera nº {carrera.id} no está finalizada.")

        try:
            self._anadir_fila(carrera)
        except OSError:
            logger.error(
                "carrera_no_guardada %s",
                campos(carrera=carrera.id, importe=carrera.importe, ruta=self._ruta),
                exc_info=True,
            )
            raise
        logger.info(
            "carrera_guardada %s",
            campos(carrera=carrera.id, importe=carrera.importe, ruta=self._ruta),
        )

    def _anadir_fila(self, carrera: Carrera) -> None:
        """Escribe la fila de la carrera; si el fichero es nuevo, antes la cabecera."""
        nuevo = not self._ruta.exists()
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        with self._ruta.open("a", encoding="utf-8", newline="") as fichero:
            escritor = csv.writer(fichero)
            if nuevo:
                escritor.writerow(COLUMNAS)
            escritor.writerow(_fila_csv(carrera))

    def registros(self) -> list[RegistroCarrera]:
        """Todas las carreras guardadas, en el orden en que se cerraron.

        Sin fichero, lista vacía. Las filas ilegibles (editadas a mano, o una
        escritura cortada a medias) se saltan: una fila rota no puede impedir
        ver el resto del día.
        """
        if not self._ruta.exists():
            return []

        registros = []
        with self._ruta.open(encoding="utf-8", newline="") as fichero:
            lector = csv.DictReader(fichero)
            for fila in lector:
                try:
                    registros.append(_leer_registro(fila))
                except (KeyError, TypeError, ValueError):
                    logger.warning(
                        "fila_ilegible %s", campos(ruta=self._ruta, linea=lector.line_num)
                    )
                    continue
        return registros

    def resumen_del_dia(self, fecha: date) -> ResumenDia:
        """Las carreras que terminaron en `fecha` y su total.

        Cuenta la hora de fin: una carrera que empieza antes de medianoche y
        termina después se cobra, y por tanto se cuadra, al día siguiente.
        """
        del_dia = tuple(r for r in self.registros() if r.hora_fin.date() == fecha)
        return ResumenDia(fecha=fecha, carreras=del_dia)

    def ultimo_numero(self) -> int:
        """El número de la última carrera guardada, o 0 si no hay ninguna."""
        return max((registro.carrera for registro in self.registros()), default=0)


def _fila_csv(carrera: Carrera) -> tuple[object, ...]:
    """La carrera como fila del CSV, en el orden de `COLUMNAS`."""
    return (
        carrera.id,
        carrera.hora_inicio.isoformat(timespec="seconds"),
        carrera.hora_fin.isoformat(timespec="seconds"),
        f"{carrera.importe:.2f}",
        f"{carrera.distancia:.2f}",
    )


def _leer_registro(fila: dict[str, str]) -> RegistroCarrera:
    """Una fila del CSV como registro; lanza si la fila está rota."""
    return RegistroCarrera(
        carrera=int(fila["carrera"]),
        hora_inicio=datetime.fromisoformat(fila["hora_inicio"]),
        hora_fin=datetime.fromisoformat(fila["hora_fin"]),
        importe=float(fila["importe"]),
        distancia=float(fila["distancia"]),
    )
