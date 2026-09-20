"""Utilidades genéricas de formato para el taxímetro."""

from __future__ import annotations


def formato_euros(importe: float) -> str:
    """Formatea un importe en euros al uso español: 12.3456 -> '12,34 €'.

    Coma decimal y espacio antes del símbolo. No usa el módulo `locale`: haría
    depender el formato de que la configuración regional esté instalada en la
    máquina, y el resultado cambiaría entre el equipo de desarrollo, el runner
    de CI y el portátil de la demo.
    """
