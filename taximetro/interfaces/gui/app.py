"""App: la ventana de la interfaz gráfica y el cambio de pantalla (US-09)."""

from __future__ import annotations

import logging
import tkinter as tk
from types import TracebackType
from typing import Any

from taximetro.interfaces.gui import estilo
from taximetro.interfaces.gui.inicio import Inicio
from taximetro.interfaces.gui.pantalla import Pantalla
from taximetro.interfaces.gui.tecla import Tecla
from taximetro.infrastructure.logs import campos
from taximetro.application.servicio_taximetro import ServicioTaximetro

# Nombre fijo, no `__name__`, igual que en el CLI: un logger bajo `taximetro`
# llega al fichero de logs también cuando el módulo se ejecuta como `__main__`.
logger = logging.getLogger("taximetro.interfaces.gui")

TAMANO_SIN_PINTAR = 200  # una ventana que mide menos que esto aún no se ha colocado
REAJUSTE_MS = 150  # lo que se espera tras el último cambio de tamaño antes de rehacer la pantalla
ERROR_INESPERADO = "Ha ocurrido un error inesperado. Si se repite, avisa al equipo técnico."


class App:
    """La ventana del taxímetro: muestra una `Pantalla` cada vez.

    Es la única que conoce la ventana de tkinter. Las pantallas se piden unas a
    otras con `mostrar()`, y todas hablan con el mismo `servicio`, el que
    también usa el CLI.

    `raiz` se inyecta para los tests: le dan una ventana `Toplevel` oculta de
    un único intérprete Tk para toda la sesión, y procesan los eventos con
    `update()`. Crear un `Tk()` por test hacía que Tk 9 en Windows abortara
    de vez en cuando (ver `tests/gui/conftest.py`).
    """

    def __init__(
        self, servicio: ServicioTaximetro, raiz: tk.Tk | tk.Toplevel | None = None
    ) -> None:
        """Prepara la ventana y abre la pantalla de inicio.

        Una ventana propia se abre al tamaño de la tablet, o al de la pantalla
        si esta es más pequeña. Una inyectada (los tests) se deja al tamaño
        de referencia. En los dos casos el tema se adapta a ese tamaño.
        """
        self.servicio = servicio
        propia = raiz is None
        self.raiz = tk.Tk() if propia else raiz
        self.raiz.title(estilo.TITULO)
        ancho, alto = self._tamano_inicial() if propia else (estilo.ANCHO, estilo.ALTO)
        estilo.aplicar(ancho, alto, forzar=True)
        self.raiz.geometry(f"{ancho}x{alto}")
        self.raiz.minsize(*estilo.tamano_minimo())
        self._pendiente: str | None = None  # el reajuste al tamaño nuevo, esperando a que se calme
        self.raiz.bind("<Configure>", self._al_configurar, add="+")
        self.raiz.configure(bg=estilo.FONDO)
        self.raiz.protocol("WM_DELETE_WINDOW", self.al_cerrar_ventana)
        # tkinter no deja salir las excepciones de un botón o un temporizador:
        # las imprime en la consola y sigue. Sin esto, «cualquier error» (US-06)
        # faltaría en el log. Vive en el intérprete Tk, no en la ventana.
        self.raiz._root().report_callback_exception = self.error_en_callback
        self.pantalla: Pantalla | None = None
        self._aviso: tk.Frame | None = None
        self.mostrar(Inicio)

    def mostrar(self, tipo: type[Pantalla], **datos: Any) -> Pantalla:
        """Sustituye la pantalla actual por una nueva de `tipo` y la devuelve.

        La anterior se destruye, con sus temporizadores: solo hay una pantalla
        viva cada vez. `datos` se pasa al constructor de la nueva.
        """
        if self.pantalla is not None:
            self.pantalla.destroy()
        self.pantalla = tipo(self, **datos)
        self.pantalla.pack(fill=tk.BOTH, expand=True)
        return self.pantalla

    def _tamano_inicial(self) -> tuple[int, int]:
        """El tamaño de la tablet, o el de la pantalla si esta es más pequeña.

        En una pantalla apaisada, el de referencia horizontal; en una vertical,
        el de referencia vertical. Se dejan unos píxeles para la barra de
        tareas y la del título.
        """
        util_ancho = self.raiz.winfo_screenwidth() - 2 * estilo.MARGEN
        util_alto = self.raiz.winfo_screenheight() - 100
        if util_alto > util_ancho:
            return min(estilo.ANCHO_VERTICAL, util_ancho), min(estilo.ALTO_VERTICAL, util_alto)
        return min(estilo.ANCHO, util_ancho), min(estilo.ALTO, util_alto)

    def _al_configurar(self, evento: tk.Event) -> None:
        """La ventana cambió de tamaño: se reajusta cuando deja de moverse.

        Arrastrar el borde dispara decenas de eventos por segundo; rehacer la
        pantalla en cada uno parpadearía y gastaría CPU sin necesidad.
        """
        if evento.widget is not self.raiz:
            return  # los eventos de los widgets de dentro también llegan hasta aquí
        if self._pendiente is not None:
            self.raiz.after_cancel(self._pendiente)
        self._pendiente = self.raiz.after(
            REAJUSTE_MS, lambda: self.adaptar(self.raiz.winfo_width(), self.raiz.winfo_height())
        )

    def adaptar(self, ancho: int, alto: int) -> None:
        """Adapta el tema a `ancho` × `alto` y, si cambió, rehace la pantalla actual.

        Una ventana sin pintar aún mide 1 × 1: se ignora. Lo que hay en la
        pantalla (lo tecleado, un panel abierto…) pasa a la nueva. La carrera y
        el importe no dependen de esto: viven en el servicio. El tamaño mínimo
        de la ventana sigue a la disposición.
        """
        self._pendiente = None
        if ancho < TAMANO_SIN_PINTAR or alto < TAMANO_SIN_PINTAR:
            return
        if estilo.aplicar(ancho, alto):
            self.raiz.minsize(*estilo.tamano_minimo())
            self._rehacer_pantalla()

    def _rehacer_pantalla(self) -> None:
        """Vuelve a construir la pantalla y el aviso abiertos, con el tema recién aplicado."""
        aviso = self._texto_del_aviso()
        if self._aviso is not None:
            self._aviso.destroy()
            self._aviso = None
        if self.pantalla is not None:
            estado = self.pantalla.guardar_ui()
            self.mostrar(type(self.pantalla)).restaurar_ui(estado)
        if aviso is not None:
            self.avisar(aviso)

    def _texto_del_aviso(self) -> str | None:
        """El texto del aviso si está a la vista; None si no."""
        if self._aviso is None or not self._aviso.winfo_exists() or self._aviso.winfo_manager() != "place":
            return None
        return self.texto_aviso.cget("text")

    def al_cerrar_ventana(self) -> None:
        """El ✕ de la ventana: cierra, salvo que la pantalla tenga algo que preguntar.

        Con una carrera en curso, la pantalla del taxímetro pregunta antes
        (`docs/flujo-fase3.md`, *Cerrar la ventana con una carrera en curso*).
        """
        if self.pantalla is not None and self.pantalla.al_cerrar_ventana():
            return
        self.cerrar("ventana")

    def cerrar(self, motivo: str = "salir") -> None:
        """Termina el programa y registra por qué (`salir`, `ventana`…), como el CLI."""
        logger.info("aplicacion_cerrada %s", campos(motivo=motivo))
        if self._pendiente is not None:
            self.raiz.after_cancel(self._pendiente)
            self._pendiente = None
        if self.pantalla is not None:
            self.pantalla.destroy()
            self.pantalla = None
        self.raiz.destroy()

    def ejecutar(self) -> None:
        """Muestra la ventana y atiende eventos hasta que se cierra.

        `wait_window()` y no `mainloop()`: con la ventana principal hacen lo
        mismo, pero `wait_window()` también vuelve al cerrar un `Toplevel`,
        que es lo que usan los tests.
        """
        tarifas = self.servicio.tarifas()
        logger.info(
            "aplicacion_iniciada %s",
            campos(parado=tarifas.parado, movimiento=tarifas.en_movimiento),
        )
        self.raiz.wait_window()

    def error_en_callback(
        self, tipo: type[BaseException], valor: BaseException, traza: TracebackType | None
    ) -> None:
        """Un error dentro de un botón o un temporizador: al log con su traza, y un aviso.

        El programa sigue: una carrera en curso no se pierde por un fallo al
        pintar. El conductor ve un aviso corto; el detalle es para el técnico.
        """
        logger.error("error_inesperado", exc_info=(tipo, valor, traza))
        try:
            self.avisar(ERROR_INESPERADO)
        except tk.TclError:
            pass  # la ventana ya no existe: basta con el log

    def avisar(self, texto: str) -> None:
        """Un aviso encima de la pantalla actual, con una tecla Cerrar."""
        if self._aviso is None or not self._aviso.winfo_exists():
            self._aviso = tk.Frame(self.raiz, bg=estilo.VISOR_FONDO)
            panel = tk.Frame(
                self._aviso, bg=estilo.PANEL, highlightthickness=3,
                highlightbackground=estilo.CAMPO_BORDE_ERROR,
            )
            panel.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=estilo.CONFIRMACION_ANCHO)
            self.texto_aviso = tk.Label(
                panel, font=estilo.FUENTE_DETALLE, bg=estilo.PANEL, fg=estilo.TEXTO,
                justify=tk.LEFT, anchor=tk.W,
            )
            Pantalla.ajustar_al_ancho(self.texto_aviso)
            self.texto_aviso.pack(fill=tk.X, padx=estilo.px(48), pady=(estilo.px(48), estilo.px(32)))
            self.cerrar_aviso = Tecla(
                panel, "Cerrar", self._aviso.place_forget, variante=estilo.GRIS,
                alto=estilo.TECLA_LATERAL, fuente=estilo.FUENTE_TECLA_LATERAL,
            )
            self.cerrar_aviso.pack(fill=tk.X, padx=estilo.px(48), pady=(0, estilo.px(48)))
        self.texto_aviso.configure(text=texto)
        self._aviso.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._aviso.lift()
