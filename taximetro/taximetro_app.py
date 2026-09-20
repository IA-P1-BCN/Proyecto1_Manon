"""TaximetroApp: bucle CLI que orquesta el uso del Taximetro."""

from __future__ import annotations

import sys
from typing import Callable

from taximetro.carrera import Carrera, Estado
from taximetro.taximetro import Taximetro
from taximetro.utils import formato_euros

SIN_CARRERA = ("iniciar", "ayuda", "salir")
CON_CARRERA = ("parado", "movimiento", "importe", "finalizar", "ayuda")

SIN_CARRERA_ACTIVA = "No hay ninguna carrera activa."
YA_HAY_CARRERA = "Ya hay una carrera activa."
NO_RECONOCIDO = "Comando no reconocido."
SALIR_CON_CARRERA = "Para salir, finaliza la carrera."


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
        self._taximetro = taximetro or Taximetro()
        self._entrada = entrada
        self._salida = salida

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------

    def ejecutar(self) -> None:
        """Muestra las instrucciones de uso y arranca el bucle principal de comandos."""
        self._salida(self._banner())

        while True:
            carrera = self._taximetro.carrera_activa
            self._salida(self._menu(carrera))

            try:
                comando = self._entrada("> ").strip().lower()
            except KeyboardInterrupt:
                # Sin carrera no hay nada que perder; con carrera activa, salir
                # a destiempo perdería el importe del pasajero.
                if carrera is None:
                    return
                self._salida(SALIR_CON_CARRERA)
                continue
            except EOFError:
                # EOF no es reintentable: volver a leer sería un bucle infinito,
                # así que se cierra la carrera en vez de avisar y reintentar.
                if carrera is not None:
                    self._salida(self._cerrar(carrera))
                return

            if self._despachar(comando, carrera) is False:
                return

    def _despachar(self, comando: str, carrera: Carrera | None) -> bool:
        """Ejecuta un comando. Devuelve False cuando hay que salir del bucle."""
        if comando == "ayuda":
            self._salida(self._banner())
        elif carrera is None:
            self._sin_carrera(comando)
        else:
            self._con_carrera(comando, carrera)

        return not (comando == "salir" and carrera is None)

    def _sin_carrera(self, comando: str) -> None:
        """Comandos válidos con el taxímetro libre."""
        if comando == "iniciar":
            nueva = self._taximetro.iniciar_carrera()
            self._salida(
                f"Carrera nº {nueva.id} iniciada · {self._legible(nueva.estado)} · "
                f"{self._tarifa_por_segundo(nueva.estado)}/s"
            )
        elif comando == "salir":
            pass  # el bucle termina al volver de _despachar
        elif comando in CON_CARRERA:
            self._salida(SIN_CARRERA_ACTIVA)
        else:
            self._salida(NO_RECONOCIDO)

    def _con_carrera(self, comando: str, carrera: Carrera) -> None:
        """Comandos válidos durante una carrera."""
        if comando in ("parado", "movimiento"):
            estado = Estado.PARADO if comando == "parado" else Estado.EN_MOVIMIENTO
            carrera.cambiar_estado(estado)
            self._salida(
                f"{self._legible(carrera.estado)} · "
                f"{formato_euros(carrera.importe_actual())} acumulado"
            )
        elif comando == "importe":
            self._salida(
                f"Carrera nº {carrera.id} · {self._legible(carrera.estado)} · "
                f"{formato_euros(carrera.importe_actual())} acumulado"
            )
        elif comando == "finalizar":
            self._salida(self._cerrar(carrera))
        elif comando == "iniciar":
            self._salida(YA_HAY_CARRERA)
        else:
            # Incluye `salir`, que no se ofrece con una carrera abierta: una
            # carrera solo termina de forma deliberada, con `finalizar`.
            self._salida(NO_RECONOCIDO)

    def _cerrar(self, carrera: Carrera) -> str:
        """Finaliza la carrera y devuelve la línea del total a cobrar."""
        total = carrera.finalizar()
        return f"TOTAL A COBRAR: {formato_euros(total)}"

    # ------------------------------------------------------------------
    # Presentación
    # ------------------------------------------------------------------

    def _menu(self, carrera: Carrera | None) -> str:
        """Los comandos válidos en este momento."""
        if carrera is None:
            return "Sin carrera · Comandos: " + " · ".join(SIN_CARRERA)
        return (
            f"Carrera nº {carrera.id} en curso ({self._legible(carrera.estado)})"
            " · Comandos: " + " · ".join(CON_CARRERA)
        )

    def _banner(self) -> str:
        """Instrucciones de uso y tarifas vigentes."""
        raya = "=" * 54
        return "\n".join(
            [
                raya,
                "  TAXÍMETRO TTX-247 · TaxiTech Solutions",
                raya,
                "Calcula el importe de la carrera según el tiempo que pasa",
                "en cada estado del vehículo.",
                "",
                "Tarifas vigentes:",
                f"  Parado o < 20 km/h ... {self._tarifa_por_segundo(Estado.PARADO)}/s",
                f"  En movimiento ........ "
                f"{self._tarifa_por_segundo(Estado.EN_MOVIMIENTO)}/s",
                "",
                "Comandos:",
                "  iniciar      empieza una carrera nueva",
                "  parado       el taxi está detenido",
                "  movimiento   el taxi circula",
                "  importe      muestra el importe acumulado",
                "  finalizar    cierra la carrera y muestra el total",
                "  ayuda        vuelve a mostrar estas instrucciones",
                "  salir        cierra el programa",
                "",
                "En cada momento solo se ofrecen los comandos válidos.",
                raya,
            ]
        )

    def _tarifa_por_segundo(self, estado: Estado) -> str:
        """La tarifa del estado, formateada — el importe de un solo segundo."""
        return formato_euros(self._taximetro.tarifa.calcular_importe(estado, 1))

    def _legible(self, estado: Estado) -> str:
        """El estado tal y como se muestra al conductor: 'EN MOVIMIENTO'."""
        return estado.value.replace("_", " ").upper()


if __name__ == "__main__":
    # La salida lleva €, ñ y ·. En una consola con codificación heredada
    # (cp437, cp850) un print podría abortar con UnicodeEncodeError a mitad de
    # carrera; con `replace` se degradan los símbolos pero el taxímetro sigue.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    TaximetroApp().ejecutar()
