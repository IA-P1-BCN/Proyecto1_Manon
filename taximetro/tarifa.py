"""Tarifa: cálculo del importe según el estado del vehículo y el tiempo transcurrido."""

from __future__ import annotations

from taximetro.carrera import Estado


class Tarifa:
    """Tarifas vigentes por segundo, según el estado del vehículo."""

    def calcular_importe(self, estado: Estado, segundos: float) -> float:
        """Devuelve el importe correspondiente a `segundos` transcurridos en `estado`."""
