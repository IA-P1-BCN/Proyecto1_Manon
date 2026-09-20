"""TaximetroApp: bucle CLI que orquesta el uso del Taximetro."""

from __future__ import annotations

from typing import Callable

from taximetro.taximetro import Taximetro


class TaximetroApp:
    """Capa CLI: interpreta los comandos del taxista y llama al Taximetro.

    `entrada` y `salida` se inyectan para que los tests puedan guionizar una
    sesión completa (lista de comandos dentro, lista de líneas fuera) sin
    parchear `input`/`print` ni leer de stdout. El comportamiento del bucle
    está definido en `docs/flujo-fase1.md`.
    """

    def __init__(
        self,
        taximetro: Taximetro | None = None,
        entrada: Callable[[str], str] = input,
        salida: Callable[[str], None] = print,
    ) -> None:
        """Inicializa la app con un Taximetro nuevo y los canales de E/S."""

    def ejecutar(self) -> None:
        """Muestra las instrucciones de uso y arranca el bucle principal de comandos."""


if __name__ == "__main__":
    TaximetroApp().ejecutar()
