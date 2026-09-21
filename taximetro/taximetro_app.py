"""TaximetroApp: bucle CLI que orquesta el uso del Taximetro."""

from __future__ import annotations

import sys
from typing import Callable

from taximetro.carrera import Carrera, Estado
from taximetro.taximetro import Taximetro
from taximetro.utils import formato_euros

# Cada menú es una tupla de opciones y la posición manda: el número que teclea
# el conductor es el índice + 1. Reordenar una tupla renumera ese menú.
OPCIONES_SIN_CARRERA = ("iniciar", "ayuda", "salir")
OPCIONES_CON_CARRERA = ("cambiar", "importe", "finalizar", "ayuda")

ETIQUETAS = {
    "iniciar": "Iniciar carrera",
    "importe": "Ver importe",
    "finalizar": "Finalizar carrera",
    "ayuda": "Ayuda",
    "salir": "Salir",
}

# `cambiar` es una sola opción con dos caras: el menú ofrece siempre la acción
# contraria al estado actual, nunca el estado en el que ya se está. Así el
# conductor no tiene que leer en qué estado está para saber qué pulsar.
# Indexado por el estado de DESTINO, igual que la acción que ejecuta.
ETIQUETAS_CAMBIO = {
    Estado.EN_MOVIMIENTO: "Arrancar",
    Estado.PARADO: "Parar",
}

# Para el banner: qué hace cada opción. Sin números, porque una misma opción
# lleva un número distinto en cada menú (Ayuda es la 2 sin carrera y la 4 con
# carrera); los números solo son ciertos en el menú que está en pantalla.
DESCRIPCIONES = (
    ("Iniciar carrera", "empieza una carrera nueva y cobra desde ese segundo"),
    ("Arrancar", "el taxi se pone en movimiento"),
    ("Parar", "el taxi se detiene"),
    ("Ver importe", "muestra el importe acumulado"),
    ("Finalizar carrera", "cierra la carrera y muestra el total"),
    ("Ayuda", "vuelve a mostrar estas instrucciones"),
    ("Salir", "cierra el programa"),
)

OPCION_NO_VALIDA = "Opción no válida. Elige un número del menú."
SALIR_CON_CARRERA = "Para salir, finaliza la carrera."


class TaximetroApp:
    """Capa CLI: muestra el menú numerado y llama al Taximetro.

    `entrada` y `salida` se inyectan para que los tests puedan guionizar una
    sesión completa (lista de opciones dentro, lista de líneas fuera) sin
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
        """Muestra las instrucciones de uso y arranca el bucle principal del menú."""
        self._salida(self._banner())

        while True:
            carrera = self._taximetro.carrera_activa
            self._salida(self._menu(carrera))

            try:
                eleccion = self._entrada("> ").strip()
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

            opcion = self._opcion(eleccion, carrera)
            if opcion is None:
                self._salida(OPCION_NO_VALIDA)
            elif opcion == "salir":
                return
            else:
                self._aplicar(opcion, carrera)

    def _opcion(self, eleccion: str, carrera: Carrera | None) -> str | None:
        """Traduce lo tecleado a una opción del menú actual, o None si no lo es."""
        opciones = self._opciones(carrera)
        try:
            numero = int(eleccion)
        except ValueError:
            # Cubre la línea vacía, las palabras y los dígitos exóticos ('²'),
            # que `isdigit()` daría por buenos y luego `int()` rechazaría.
            return None

        if 1 <= numero <= len(opciones):
            return opciones[numero - 1]
        return None

    def _aplicar(self, opcion: str, carrera: Carrera | None) -> None:
        """Ejecuta una opción ya validada contra el menú del modo actual."""
        if opcion == "ayuda":
            self._salida(self._banner())
        elif carrera is None:
            self._iniciar()  # la única opción que queda sin carrera activa
        else:
            self._con_carrera(opcion, carrera)

    def _iniciar(self) -> None:
        """Abre una carrera nueva y anuncia su número, estado y tarifa."""
        nueva = self._taximetro.iniciar_carrera()
        self._salida(
            f"Carrera nº {nueva.id} iniciada · {self._legible(nueva.estado)} · "
            f"{self._tarifa_por_segundo(nueva.estado)}/s"
        )

    def _con_carrera(self, opcion: str, carrera: Carrera) -> None:
        """Opciones disponibles durante una carrera."""
        if opcion == "cambiar":
            carrera.cambiar_estado(self._contrario(carrera.estado))
            self._salida(
                f"{self._legible(carrera.estado)} · "
                f"{formato_euros(carrera.importe_actual())} acumulado"
            )
        elif opcion == "importe":
            self._salida(
                f"Carrera nº {carrera.id} · {self._legible(carrera.estado)} · "
                f"{formato_euros(carrera.importe_actual())} acumulado"
            )
        else:  # finalizar
            self._salida(self._cerrar(carrera))

    def _cerrar(self, carrera: Carrera) -> str:
        """Finaliza la carrera y devuelve la línea del total a cobrar."""
        total = carrera.finalizar()
        return f"TOTAL A COBRAR: {formato_euros(total)}"

    # ------------------------------------------------------------------
    # Presentación
    # ------------------------------------------------------------------

    def _opciones(self, carrera: Carrera | None) -> tuple[str, ...]:
        """El menú vigente: el número tecleado se resuelve contra esta tupla."""
        return OPCIONES_SIN_CARRERA if carrera is None else OPCIONES_CON_CARRERA

    def _contrario(self, estado: Estado) -> Estado:
        """El estado opuesto: lo que hace la opción de cambio."""
        if estado is Estado.EN_MOVIMIENTO:
            return Estado.PARADO
        return Estado.EN_MOVIMIENTO

    def _etiqueta(self, opcion: str, carrera: Carrera | None) -> str:
        """El texto de una opción; el de `cambiar` depende del estado actual."""
        if opcion == "cambiar" and carrera is not None:
            return ETIQUETAS_CAMBIO[self._contrario(carrera.estado)]
        return ETIQUETAS[opcion]

    def _menu(self, carrera: Carrera | None) -> str:
        """La situación actual y, numeradas, las opciones válidas ahora mismo.

        Abre con una línea en blanco para separarlo de lo que se acaba de
        imprimir: el conductor busca el menú de un vistazo, no leyendo.
        """
        if carrera is None:
            lineas = ["", "Sin carrera"]
        else:
            lineas = [
                "",
                f"Carrera nº {carrera.id} en curso ({self._legible(carrera.estado)})",
            ]

        lineas += [
            f"  {numero}) {self._etiqueta(opcion, carrera)}"
            for numero, opcion in enumerate(self._opciones(carrera), start=1)
        ]
        return "\n".join(lineas)

    def _banner(self) -> str:
        """Instrucciones de uso y tarifas vigentes."""
        raya = "=" * 54
        ancho = max(len(etiqueta) for etiqueta, _ in DESCRIPCIONES)
        return "\n".join(
            [
                raya,
                "  TAXÍMETRO TTX-247 · TaxiTech Solutions",
                raya,
                "Tarifas vigentes:",
                f"  Parado o < 20 km/h ... {self._tarifa_por_segundo(Estado.PARADO)}/s",
                f"  En movimiento ........ "
                f"{self._tarifa_por_segundo(Estado.EN_MOVIMIENTO)}/s",
                "",
                "Escribe el número de la opción que quieras y pulsa Intro.",
                "",
                "Opciones:",
                *(
                    f"  {etiqueta:<{ancho}}  {descripcion}"
                    for etiqueta, descripcion in DESCRIPCIONES
                ),
                "",
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
