"""Tarifa: cálculo del importe según el estado del vehículo y el tiempo transcurrido."""

from __future__ import annotations

from taximetro.carrera import Estado

# Tope de cordura, en €/s: una tarifa por encima casi siempre es un despiste
# (euros por minuto tecleados en un campo de euros por segundo).
TARIFA_MAXIMA = 1.0


class TarifaInvalidaError(ValueError):
    """Se lanza al construir una `Tarifa` con valores que no se pueden cobrar."""


class Tarifa:
    """Tarifas vigentes por segundo, según el estado del vehículo.

    Por defecto, las de la zona EMT Madrid (junio 2025), ver
    `docs/project-brief.md`. Desde la Fase 2 (US-07) pueden venir de
    `config/tarifas.json`: quien las carga es `ConfigTarifas`, y quien las
    aplica es `Taximetro`, que construye la `Tarifa` y se la inyecta a cada
    `Carrera`. El taxímetro cobra por tiempo en ambos estados, nunca por
    distancia.

    Una `Tarifa` se valida al construirse, así que no puede existir una con
    valores imposibles: el fichero editado a mano y el menú de Administrador
    pasan por la misma comprobación.
    """

    # Euros por segundo.
    TARIFAS: dict[Estado, float] = {
        Estado.PARADO: 0.02,
        Estado.EN_MOVIMIENTO: 0.05,
    }

    def __init__(
        self,
        parado: float = TARIFAS[Estado.PARADO],
        en_movimiento: float = TARIFAS[Estado.EN_MOVIMIENTO],
    ) -> None:
        """Crea la tarifa con los €/s de cada estado. Falla si no son válidos."""
        self._validar(parado, en_movimiento)
        self._tarifas = {Estado.PARADO: parado, Estado.EN_MOVIMIENTO: en_movimiento}

    @staticmethod
    def _validar(parado: float, en_movimiento: float) -> None:
        """Comprueba las reglas de `docs/decisions-fase2.md` (US-07, Validation)."""
        for valor in (parado, en_movimiento):
            # `bool` es subclase de `int`: un `true` en el JSON no es una tarifa.
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise TarifaInvalidaError("La tarifa debe ser un número.")
            # También descarta NaN, que no es ni mayor ni menor que nada.
            if not 0 < valor <= TARIFA_MAXIMA:
                raise TarifaInvalidaError(
                    "Cada tarifa debe ser mayor que 0 y como máximo 1,00 €/s."
                )
            # La tarifa se anuncia con dos decimales: con más, lo que se ve en
            # pantalla no sería lo que se cobra.
            if round(valor, 2) != valor:
                raise TarifaInvalidaError("Cada tarifa admite como máximo 2 decimales.")
        if parado > en_movimiento:
            raise TarifaInvalidaError(
                "La tarifa parado no puede ser mayor que la de en movimiento."
            )

    @property
    def parado(self) -> float:
        """€/s con el taxi parado o a menos de 20 km/h."""
        return self._tarifas[Estado.PARADO]

    @property
    def en_movimiento(self) -> float:
        """€/s con el taxi en movimiento."""
        return self._tarifas[Estado.EN_MOVIMIENTO]

    def calcular_importe(self, estado: Estado, segundos: float) -> float:
        """Devuelve el importe correspondiente a `segundos` transcurridos en `estado`."""
        return self._tarifas[estado] * segundos
