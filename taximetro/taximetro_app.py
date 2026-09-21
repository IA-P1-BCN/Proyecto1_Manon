"""TaximetroApp: bucle CLI que orquesta el uso del Taximetro."""

from __future__ import annotations

import sys
from typing import Callable

from taximetro.carrera import Carrera, Estado
from taximetro.taximetro import Taximetro
from taximetro.utils import formato_euros

# Cada menú es una tupla de opciones y la posición manda: el número que se
# teclea es el índice + 1. Reordenar una tupla renumera ese menú.
OPCIONES_INICIO = ("conductor", "administrador", "salir")
OPCIONES_SIN_CARRERA = ("iniciar", "ayuda", "volver")
OPCIONES_CON_CARRERA = ("cambiar", "importe", "finalizar", "ayuda")
OPCIONES_ADMINISTRADOR = ("volver",)

ETIQUETAS = {
    "conductor": "Conductor",
    "administrador": "Administrador",
    "iniciar": "Iniciar carrera",
    "importe": "Ver importe",
    "finalizar": "Finalizar carrera",
    "ayuda": "Ayuda",
    "volver": "Volver",
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

# Para el banner: qué hace cada opción, agrupadas por perfil. Sin números,
# porque una misma opción lleva un número distinto en cada menú (Ayuda es la 2
# sin carrera y la 4 con carrera); los números solo son ciertos en el menú que
# está en pantalla.
DESCRIPCIONES = {
    "Conductor": (
        ("Iniciar carrera", "empieza una carrera nueva y cobra desde ese segundo"),
        ("Arrancar", "el taxi se pone en movimiento"),
        ("Parar", "el taxi se detiene"),
        ("Ver importe", "muestra el importe acumulado"),
        ("Finalizar carrera", "cierra la carrera y muestra el total"),
        ("Ayuda", "vuelve a mostrar estas instrucciones"),
        ("Volver", "vuelve al menú de inicio (sin carrera en curso)"),
    ),
    "Administrador": (
        ("Volver", "vuelve al menú de inicio"),
    ),
}

OPCION_NO_VALIDA = "Opción no válida. Elige un número del menú."
SALIR_CON_CARRERA = "Para salir, finaliza la carrera."


class TaximetroApp:
    """Capa CLI: muestra los menús numerados y llama al Taximetro.

    Arranca en el menú de inicio, donde se elige perfil: Conductor (el bucle de
    carreras de la Fase 1) o Administrador (las funciones de la Fase 2). Ver
    `docs/decisions-fase2.md`.

    `entrada` y `salida` se inyectan para que los tests puedan guionizar una
    sesión completa (lista de opciones dentro, lista de líneas fuera) sin
    parchear `input`/`print` ni leer de stdout.
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
        """Muestra las instrucciones de uso y arranca en el menú de inicio."""
        self._salida(self._banner())

        try:
            while True:
                opcion = self._leer("Menú de inicio", OPCIONES_INICIO)
                if opcion == "salir":
                    return
                if opcion == "administrador":
                    self._administrador()
                elif not self._conductor():
                    return
        except (KeyboardInterrupt, EOFError):
            # Solo llegan aquí desde fuera de una carrera: no hay importe que
            # perder, así que se sale limpiamente. Con carrera activa, los
            # atiende `_conductor`.
            return

    def _leer(
        self, cabecera: str, opciones: tuple[str, ...], carrera: Carrera | None = None
    ) -> str:
        """Muestra un menú y repite hasta que se teclea uno de sus números."""
        while True:
            self._salida(self._menu(cabecera, opciones, carrera))
            opcion = self._opcion(self._entrada("> ").strip(), opciones)
            if opcion is not None:
                return opcion
            self._salida(OPCION_NO_VALIDA)

    # ------------------------------------------------------------------
    # Conductor
    # ------------------------------------------------------------------

    def _conductor(self) -> bool:
        """El bucle de carreras. Devuelve False si el programa debe cerrarse.

        `Volver` solo existe sin carrera: con una carrera abierta no se puede
        llegar al Administrador, y por tanto las tarifas no cambian a mitad de
        carrera.
        """
        while True:
            carrera = self._taximetro.carrera_activa
            try:
                opcion = self._leer(
                    self._cabecera(carrera), self._opciones(carrera), carrera
                )
            except KeyboardInterrupt:
                if carrera is None:
                    raise
                self._salida(SALIR_CON_CARRERA)
                continue
            except EOFError:
                if carrera is None:
                    raise
                # EOF no es reintentable: volver a leer sería un bucle infinito,
                # así que se cierra la carrera en vez de avisar y reintentar.
                self._salida(self._cerrar(carrera))
                return False

            if opcion == "volver":
                return True
            self._aplicar(opcion, carrera)

    def _opcion(self, eleccion: str, opciones: tuple[str, ...]) -> str | None:
        """Traduce lo tecleado a una opción del menú, o None si no lo es."""
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
    # Administrador
    # ------------------------------------------------------------------

    def _administrador(self) -> None:
        """El menú de Administrador, hasta que se elige `Volver`.

        Sin contraseña en la Fase 2: la protección llega con US-08 (Fase 3),
        que solo tendrá que ponerse delante de este método.
        """
        while True:
            opcion = self._leer("Administrador", OPCIONES_ADMINISTRADOR)
            if opcion == "volver":
                return

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

    def _cabecera(self, carrera: Carrera | None) -> str:
        """La situación del conductor, encima de su menú."""
        if carrera is None:
            return "Sin carrera"
        return f"Carrera nº {carrera.id} en curso ({self._legible(carrera.estado)})"

    def _menu(
        self, cabecera: str, opciones: tuple[str, ...], carrera: Carrera | None = None
    ) -> str:
        """La cabecera y, numeradas, las opciones válidas ahora mismo.

        Abre con una línea en blanco para separarlo de lo que se acaba de
        imprimir: el menú se busca de un vistazo, no leyendo.
        """
        lineas = ["", cabecera]
        lineas += [
            f"  {numero}) {self._etiqueta(opcion, carrera)}"
            for numero, opcion in enumerate(opciones, start=1)
        ]
        return "\n".join(lineas)

    def _banner(self) -> str:
        """Instrucciones de uso y tarifas vigentes."""
        raya = "=" * 54
        ancho = max(
            len(etiqueta) for grupo in DESCRIPCIONES.values() for etiqueta, _ in grupo
        )
        perfiles: list[str] = []
        for perfil, grupo in DESCRIPCIONES.items():
            perfiles += ["", f"{perfil}:"]
            perfiles += [
                f"  {etiqueta:<{ancho}}  {descripcion}" for etiqueta, descripcion in grupo
            ]
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
                "Al empezar, elige tu perfil: Conductor o Administrador.",
                "Salir, en el menú de inicio, cierra el programa.",
                *perfiles,
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
