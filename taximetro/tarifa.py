"""Tarifa: cálculo del importe según el estado del vehículo y el tiempo transcurrido."""

from __future__ import annotations

from taximetro.carrera import Estado


class Tarifa:
    """Tarifas vigentes por segundo, según el estado del vehículo.

    Tarifas de la zona EMT Madrid (junio 2025), ver `docs/project-brief.md`.
    El taxímetro cobra por tiempo en ambos estados, nunca por distancia.
    """

    # Euros por segundo. En la Fase 2 estos valores vendrán de un fichero de
    # configuración (US-07); el cambio se quedará en `Taximetro`, que es quien
    # construye la `Tarifa` y se la inyecta a cada `Carrera`.
    TARIFAS: dict[Estado, float] = {
        Estado.PARADO: 0.02,
        Estado.EN_MOVIMIENTO: 0.05,
    }

    def calcular_importe(self, estado: Estado, segundos: float) -> float:
        """Devuelve el importe correspondiente a `segundos` transcurridos en `estado`."""
        return self.TARIFAS[estado] * segundos
