"""`python -m taximetro`: arranca la interfaz gráfica (Fase 3, US-09).

El CLI sigue disponible con `python -m taximetro.interfaces.taximetro_app`.
"""

from taximetro.interfaces.gui.app import App
from taximetro.infrastructure.logs import configurar_logs
from taximetro.application.servicio_taximetro import ServicioTaximetro


def main() -> None:
    """Configura los logs, monta el servicio real y abre la ventana."""
    # Los logs primero, para que también quede registrada la carga de tarifas.
    configurar_logs()
    App(ServicioTaximetro.por_defecto()).ejecutar()


if __name__ == "__main__":
    main()
