"""App: la ventana de la interfaz gráfica y el cambio de pantalla (US-09)."""

from __future__ import annotations

import logging
import tkinter as tk
from types import TracebackType
from typing import Any

from taximetro.gui import estilo
from taximetro.gui.inicio import Inicio
from taximetro.gui.pantalla import Pantalla
from taximetro.gui.tecla import Tecla
from taximetro.logs import campos
from taximetro.servicio_taximetro import ServicioTaximetro

# Nombre fijo, no `__name__`, igual que en el CLI: un logger bajo `taximetro`
# llega al fichero de logs también cuando el módulo se ejecuta como `__main__`.
logger = logging.getLogger("taximetro.gui")

ERROR_INESPERADO = "Ha ocurrido un error inesperado. Si se repite, avisa al equipo técnico."


class App:
    """La ventana del taxímetro: muestra una `Pantalla` cada vez.

    Es la única que conoce la ventana de tkinter. Las pantallas se piden unas a
    otras con `mostrar()`, y todas hablan con el mismo `servicio`, el que
    también usa el CLI (`docs/decisions-fase3.md`, *Structural refactor*).

    `raiz` se inyecta para los tests: le dan una ventana `Toplevel` oculta de
    un único intérprete Tk para toda la sesión, y procesan los eventos con
    `update()`. Crear un `Tk()` por test hacía que Tk 9 en Windows abortara
    de vez en cuando (ver `tests/gui/conftest.py`).
    """

    def __init__(
        self, servicio: ServicioTaximetro, raiz: tk.Tk | tk.Toplevel | None = None
    ) -> None:
        """Prepara la ventana con el tamaño de la tablet y abre la pantalla de inicio."""
        self.servicio = servicio
        self.raiz = raiz if raiz is not None else tk.Tk()
        self.raiz.title(estilo.TITULO)
        self.raiz.geometry(f"{estilo.ANCHO}x{estilo.ALTO}")
        self.raiz.minsize(estilo.ANCHO, estilo.ALTO)
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
                justify=tk.LEFT, anchor=tk.W, wraplength=estilo.CONFIRMACION_ANCHO - 96,
            )
            self.texto_aviso.pack(fill=tk.X, padx=48, pady=(48, 32))
            self.cerrar_aviso = Tecla(
                panel, "Cerrar", self._aviso.place_forget, variante=estilo.GRIS,
                alto=estilo.TECLA_LATERAL, fuente=estilo.FUENTE_TECLA_LATERAL,
            )
            self.cerrar_aviso.pack(fill=tk.X, padx=48, pady=(0, 48))
        self.texto_aviso.configure(text=texto)
        self._aviso.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._aviso.lift()
