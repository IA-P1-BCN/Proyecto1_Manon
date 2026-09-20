"""Taximetro: orquesta el ciclo de vida de la carrera activa."""

from __future__ import annotations

from taximetro.carrera import Carrera


class CarreraActivaError(Exception):
    """Se lanza al intentar iniciar una carrera mientras otra sigue activa."""


class Taximetro:
    """Gestiona la carrera activa: inicio, cambios de estado y finalización."""

    def __init__(self) -> None:
        """Inicializa el taxímetro sin ninguna carrera activa."""

    def iniciar_carrera(self) -> Carrera:
        """Crea y activa una nueva carrera. Falla si ya hay una en curso."""
