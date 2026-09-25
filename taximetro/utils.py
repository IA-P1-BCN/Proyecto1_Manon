"""Utilidades genéricas de formato para el taxímetro."""

from __future__ import annotations


def formato_euros(importe: float) -> str:
    """Formatea un importe en euros al uso español: 12.3456 -> '12,35 €'.

    Coma decimal y espacio antes del símbolo. El redondeo a dos decimales
    ocurre solo aquí, al mostrar: el importe se guarda con toda su precisión
    para no arrastrar error de redondeo tramo a tramo durante la carrera.

    No usa el módulo `locale`: haría depender el formato de que la
    configuración regional esté instalada en la máquina, y el resultado
    cambiaría entre el equipo de desarrollo, el runner de CI y el portátil de
    la demo.
    """
    return f"{importe:.2f} €".replace(".", ",")
