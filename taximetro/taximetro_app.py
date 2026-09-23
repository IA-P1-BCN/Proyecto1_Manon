"""TaximetroApp: bucle CLI sobre el ServicioTaximetro."""

from __future__ import annotations

import logging
import sys
from typing import Callable

from taximetro.logs import campos, configurar_logs
from taximetro.servicio_taximetro import (
    AlmacenamientoError,
    Estado,
    InstantaneaCarrera,
    ResumenDia,
    ServicioTaximetro,
    TarifaInvalidaError,
    TarifasVigentes,
)
from taximetro.utils import formato_euros

# Nombre fijo, no `__name__`: con `python -m taximetro.taximetro_app` este
# módulo se llama `__main__`, y su logger quedaría fuera de `taximetro`, sin
# el handler del fichero. Sus WARNING acabarían en la consola del conductor.
logger = logging.getLogger("taximetro.taximetro_app")

# Cada menú es una tupla de opciones y la posición manda: el número que se
# teclea es el índice + 1. Reordenar una tupla renumera ese menú.
OPCIONES_INICIO = ("conductor", "administrador", "salir")
OPCIONES_SIN_CARRERA = ("iniciar", "ayuda", "volver")
OPCIONES_CON_CARRERA = ("cambiar", "importe", "finalizar", "ayuda")
OPCIONES_ADMINISTRADOR = ("tarifas", "historico", "volver")
OPCIONES_CONFIRMAR_SALIDA = ("confirmar", "seguir")

ETIQUETAS = {
    "conductor": "Conductor",
    "administrador": "Administrador",
    "iniciar": "Iniciar carrera",
    "tarifas": "Cambiar tarifas",
    "historico": "Ver histórico",
    "importe": "Ver importe",
    "finalizar": "Finalizar carrera",
    "ayuda": "Ayuda",
    "volver": "Volver",
    "salir": "Salir",
    "confirmar": "Sí, finalizar la carrera y salir",
    "seguir": "No, seguir con la carrera",
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
        ("Cambiar tarifas", "fija los €/s de cada estado, desde la próxima carrera"),
        ("Ver histórico", "carreras terminadas hoy y total de caja"),
        ("Volver", "vuelve al menú de inicio"),
    ),
}

OPCION_NO_VALIDA = "Opción no válida. Elige un número del menú."
NADA_GUARDADO = "No se ha guardado nada."
HISTORICO_NO_GUARDADO = (
    "Aviso: no se pudo guardar la carrera en el histórico. Anota el total."
)


class TaximetroApp:
    """Capa CLI: muestra los menús numerados y llama al ServicioTaximetro.

    Arranca en el menú de inicio, donde se elige perfil: Conductor (el bucle de
    carreras de la Fase 1) o Administrador (las funciones de la Fase 2). Ver
    `docs/decisions-fase2.md`.

    Del dominio solo usa el servicio, el mismo que la interfaz gráfica
    (`docs/decisions-fase3.md`, *Structural refactor*). Recibe datos, nunca
    objetos vivos: para saber el importe de ahora hay que volver a preguntar.

    `entrada` y `salida` se inyectan para que los tests puedan guionizar una
    sesión completa (lista de opciones dentro, lista de líneas fuera) sin
    parchear `input`/`print` ni leer de stdout.
    """

    def __init__(
        self,
        servicio: ServicioTaximetro,
        entrada: Callable[[str], str] = input,
        salida: Callable[[str], None] = print,
    ) -> None:
        """Inicializa la app con el servicio y los canales de E/S."""
        self._servicio = servicio
        self._entrada = entrada
        self._salida = salida

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------

    def ejecutar(self) -> None:
        """Muestra las instrucciones de uso y arranca en el menú de inicio.

        Registra el arranque y el cierre, con el motivo del cierre (US-06). Un
        error inesperado queda en el log con su traza antes de propagarse.
        """
        tarifa = self._servicio.tarifas()
        logger.info(
            "aplicacion_iniciada %s",
            campos(parado=tarifa.parado, movimiento=tarifa.en_movimiento),
        )
        try:
            motivo = self._bucle()
        except Exception:
            logger.exception("error_inesperado")
            raise
        logger.info("aplicacion_cerrada %s", campos(motivo=motivo))

    def _bucle(self) -> str:
        """El menú de inicio, hasta que el programa termina; devuelve el motivo."""
        self._salida(self._banner())

        try:
            while True:
                opcion = self._leer("Menú de inicio", OPCIONES_INICIO)
                if opcion == "salir":
                    return "salir"
                logger.info("perfil_elegido %s", campos(perfil=opcion))
                if opcion == "administrador":
                    self._administrador()
                else:
                    motivo = self._conductor()
                    if motivo is not None:
                        return motivo
        except KeyboardInterrupt:
            # Solo llegan aquí desde fuera de una carrera: no hay importe que
            # perder, así que se sale limpiamente. Con carrera activa, los
            # atiende `_conductor`.
            return "ctrl_c"
        except EOFError:
            return "eof"

    def _leer(
        self,
        cabecera: str,
        opciones: tuple[str, ...],
        carrera: InstantaneaCarrera | None = None,
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

    def _conductor(self) -> str | None:
        """El bucle de carreras. None al volver al menú de inicio; si el
        programa debe cerrarse, el motivo.

        `Volver` solo existe sin carrera: con una carrera abierta no se puede
        llegar al Administrador, y por tanto las tarifas no cambian a mitad de
        carrera.
        """
        while True:
            carrera = self._servicio.estado_actual()
            try:
                opcion = self._leer(
                    self._cabecera(carrera), self._opciones(carrera), carrera
                )
            except KeyboardInterrupt:
                if carrera is None:
                    raise
                if self._confirmar_salida(carrera):
                    self._cerrar()
                    return "ctrl_c_con_carrera"
                continue
            except EOFError:
                if carrera is None:
                    raise
                # EOF no es reintentable: volver a leer sería un bucle infinito,
                # así que se cierra la carrera en vez de avisar y reintentar.
                self._cerrar()
                return "eof_con_carrera"

            if opcion == "volver":
                return None
            self._aplicar(opcion, carrera)

    def _confirmar_salida(self, carrera: InstantaneaCarrera) -> bool:
        """Ctrl+C con carrera activa: pregunta antes de cerrar el programa (T7.7).

        El taxímetro sigue contando mientras se pregunta: el importe se calcula
        con marcas de tiempo, así que no hay nada que pausar. Un segundo Ctrl+C
        cuenta como «No», para que un doble toque nervioso no termine la
        carrera; EOF cuenta como «Sí», porque no es reintentable.
        """
        cabecera = f"Vas a salir del programa con la carrera nº {carrera.id} en curso."
        logger.info("salida_solicitada %s", campos(carrera=carrera.id))
        try:
            confirmada = self._leer(cabecera, OPCIONES_CONFIRMAR_SALIDA) == "confirmar"
        except KeyboardInterrupt:
            confirmada = False
        except EOFError:
            confirmada = True
        logger.info(
            "salida_%s %s",
            "confirmada" if confirmada else "cancelada",
            campos(carrera=carrera.id),
        )
        return confirmada

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

    def _aplicar(self, opcion: str, carrera: InstantaneaCarrera | None) -> None:
        """Ejecuta una opción ya validada contra el menú del modo actual."""
        if opcion == "ayuda":
            self._salida(self._banner())
        elif carrera is None:
            self._iniciar()  # la única opción que queda sin carrera activa
        else:
            self._con_carrera(opcion, carrera)

    def _iniciar(self) -> None:
        """Abre una carrera nueva y anuncia su número, estado y tarifa."""
        nueva = self._servicio.iniciar_carrera()
        self._salida(
            f"Carrera nº {nueva.id} iniciada · {self._legible(nueva.estado)} · "
            f"{self._tarifa_por_segundo(nueva.estado)}/s"
        )

    def _con_carrera(self, opcion: str, carrera: InstantaneaCarrera) -> None:
        """Opciones disponibles durante una carrera.

        `carrera` es la foto tomada antes de esperar la opción: vale para saber
        el estado, pero el importe se vuelve a pedir, o saldría el de antes de
        que el conductor tecleara.
        """
        if opcion == "cambiar":
            ahora = self._servicio.cambiar_estado(self._contrario(carrera.estado))
            self._salida(
                f"{self._legible(ahora.estado)} · {formato_euros(ahora.importe)} acumulado"
            )
        elif opcion == "importe":
            ahora = self._servicio.estado_actual()
            self._salida(
                f"Carrera nº {ahora.id} · {self._legible(ahora.estado)} · "
                f"{formato_euros(ahora.importe)} acumulado"
            )
        else:  # finalizar
            self._cerrar()

    def _cerrar(self) -> None:
        """Finaliza la carrera, la guarda en el histórico y muestra el total.

        Si el histórico no se puede escribir, la carrera ya está cerrada y el
        total se muestra igualmente: el cobro al pasajero no depende del disco.
        """
        cerrada = self._servicio.finalizar_carrera()
        self._salida(f"TOTAL A COBRAR: {formato_euros(cerrada.carrera.importe)}")
        if not cerrada.guardada:
            self._salida(HISTORICO_NO_GUARDADO)

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
            if opcion == "historico":
                self._ver_historico()
            else:
                self._cambiar_tarifas()

    def _ver_historico(self) -> None:
        """Las carreras terminadas hoy y el total de caja (US-05 / T5.3)."""
        try:
            resumen = self._servicio.resumen_del_dia()
        except AlmacenamientoError:
            logger.error("historico_ilegible", exc_info=True)
            self._salida("No se pudo leer el histórico.")
            return
        logger.info(
            "historico_consultado %s",
            campos(fecha=resumen.fecha, carreras=len(resumen.carreras), total=resumen.total),
        )
        self._salida(self._tabla_historico(resumen))

    def _cambiar_tarifas(self) -> None:
        """Pide las dos tarifas nuevas y se las pasa al servicio (T7.6).

        Las reglas de qué es una tarifa válida son del dominio; aquí solo se
        traduce lo tecleado a número. Cualquier fallo vuelve al menú de
        Administrador sin haber cambiado nada. Ctrl+C a mitad cancela; EOF
        sube hasta `ejecutar` y cierra el programa, también sin cambiar nada.
        """
        self._salida(f"Tarifas vigentes: {self._resumen(self._servicio.tarifas())}")
        try:
            parado = self._leer_tarifa("Nueva tarifa parado (€/s): ")
            if parado is None:
                return
            en_movimiento = self._leer_tarifa("Nueva tarifa en movimiento (€/s): ")
            if en_movimiento is None:
                return
        except KeyboardInterrupt:
            logger.info("cambio_tarifas_cancelado")
            self._salida(f"Cambio cancelado. {NADA_GUARDADO}")
            return

        try:
            tarifa = self._servicio.cambiar_tarifas(parado, en_movimiento)
        except TarifaInvalidaError as error:
            logger.warning(
                "tarifa_rechazada %s",
                campos(parado=parado, movimiento=en_movimiento, motivo=repr(str(error))),
            )
            self._salida(f"{error} {NADA_GUARDADO}")
            return
        except AlmacenamientoError:
            # El detalle ya lo registró ConfigTarifas.
            self._salida(f"No se pudo escribir el fichero de tarifas. {NADA_GUARDADO}")
            return

        self._salida(
            f"Tarifas guardadas: {self._resumen(tarifa)}. "
            "Se aplican desde la próxima carrera."
        )

    def _leer_tarifa(self, pregunta: str) -> float | None:
        """Lee una tarifa en €/s; acepta coma o punto decimal. None si no es un número."""
        tecleado = self._entrada(pregunta).strip()
        try:
            return float(tecleado.replace(",", "."))
        except ValueError:
            logger.warning(
                "tarifa_rechazada %s", campos(tecleado=repr(tecleado), motivo="no_numerica")
            )
            self._salida(
                f"«{tecleado}» no es un número. Escribe, por ejemplo, 0,03. "
                f"{NADA_GUARDADO}"
            )
            return None

    # ------------------------------------------------------------------
    # Presentación
    # ------------------------------------------------------------------

    def _opciones(self, carrera: InstantaneaCarrera | None) -> tuple[str, ...]:
        """El menú vigente: el número tecleado se resuelve contra esta tupla."""
        return OPCIONES_SIN_CARRERA if carrera is None else OPCIONES_CON_CARRERA

    def _contrario(self, estado: Estado) -> Estado:
        """El estado opuesto: lo que hace la opción de cambio."""
        if estado is Estado.EN_MOVIMIENTO:
            return Estado.PARADO
        return Estado.EN_MOVIMIENTO

    def _etiqueta(self, opcion: str, carrera: InstantaneaCarrera | None) -> str:
        """El texto de una opción; el de `cambiar` depende del estado actual."""
        if opcion == "cambiar" and carrera is not None:
            return ETIQUETAS_CAMBIO[self._contrario(carrera.estado)]
        return ETIQUETAS[opcion]

    def _cabecera(self, carrera: InstantaneaCarrera | None) -> str:
        """La situación del conductor, encima de su menú."""
        if carrera is None:
            return "Sin carrera"
        return f"Carrera nº {carrera.id} en curso ({self._legible(carrera.estado)})"

    def _menu(
        self,
        cabecera: str,
        opciones: tuple[str, ...],
        carrera: InstantaneaCarrera | None = None,
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

    def _tabla_historico(self, resumen: ResumenDia) -> str:
        """El histórico del día en columnas, con el total al pie."""
        lineas = [f"Histórico de hoy · {resumen.fecha:%d/%m/%Y}"]
        if not resumen.carreras:
            lineas.append("No hay carreras terminadas hoy.")
            return "\n".join(lineas)

        lineas.append(f"  {'Nº':>4}  {'Inicio':<8}  {'Fin':<8}  {'Importe':>10}")
        lineas += [
            f"  {r.carrera:>4}  {r.hora_inicio:%H:%M:%S}  {r.hora_fin:%H:%M:%S}  "
            f"{formato_euros(r.importe):>10}"
            for r in resumen.carreras
        ]
        cuantas = len(resumen.carreras)
        lineas.append(
            f"  {cuantas} {'carrera' if cuantas == 1 else 'carreras'} · "
            f"Total del día: {formato_euros(resumen.total)}"
        )
        return "\n".join(lineas)

    def _resumen(self, tarifa: TarifasVigentes) -> str:
        """Las dos tarifas en una línea: 'parado 0,02 €/s · en movimiento 0,05 €/s'."""
        return (
            f"parado {formato_euros(tarifa.parado)}/s · "
            f"en movimiento {formato_euros(tarifa.en_movimiento)}/s"
        )

    def _tarifa_por_segundo(self, estado: Estado) -> str:
        """La tarifa del estado en €/s, formateada."""
        tarifa = self._servicio.tarifas()
        return formato_euros(
            tarifa.parado if estado is Estado.PARADO else tarifa.en_movimiento
        )

    def _legible(self, estado: Estado) -> str:
        """El estado tal y como se muestra al conductor: 'EN MOVIMIENTO'."""
        return estado.value.replace("_", " ").upper()


if __name__ == "__main__":
    # La salida lleva €, ñ y ·. En una consola con codificación heredada
    # (cp437, cp850) un print podría abortar con UnicodeEncodeError a mitad de
    # carrera; con `replace` se degradan los símbolos pero el taxímetro sigue.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    # Solo el programa real lee y escribe config/tarifas.json,
    # data/historial.csv y logs/taximetro.log; los tests usan un Taximetro en
    # memoria o rutas temporales. Los logs se configuran primero para que
    # también quede registrada la carga de las tarifas.
    configurar_logs()
    TaximetroApp(ServicioTaximetro.por_defecto()).ejecutar()
