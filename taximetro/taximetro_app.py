"""TaximetroApp: bucle CLI que orquesta el uso del Taximetro."""

from __future__ import annotations

from taximetro.taximetro import Taximetro


class TaximetroApp:
    """Capa CLI: interpreta los comandos del taxista y llama al Taximetro."""

    def __init__(self) -> None:
        """Inicializa la app con un Taximetro nuevo."""

    def ejecutar(self) -> None:
        """Muestra las instrucciones de uso y arranca el bucle principal de comandos."""


if __name__ == "__main__":
    TaximetroApp().ejecutar()
