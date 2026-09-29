"""Pantalla: la base de cada pantalla de la interfaz gráfica."""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Any, Callable

from taximetro.interfaces.gui import estilo
from taximetro.interfaces.gui.tecla import Tecla
from taximetro.utils import formato_euros

if TYPE_CHECKING:
    from taximetro.interfaces.gui.app import App
    from taximetro.application.servicio_taximetro import ServicioTaximetro


class Pantalla(tk.Frame):
    """Una pantalla completa. `App` muestra una cada vez y destruye la anterior.

    Da a cada pantalla la `app` (para cambiar de pantalla) y el `servicio`
    (para todo lo demás). Sus temporizadores se programan con `programar()` y
    se cancelan solos al salir: si no, el refresco del importe seguiría
    llamando a widgets ya destruidos.
    """

    def __init__(self, app: App) -> None:
        """Crea la pantalla vacía, del tamaño de la ventana."""
        super().__init__(app.raiz, bg=estilo.FONDO)
        self.app = app
        self._temporizadores: set[str] = set()

    @property
    def servicio(self) -> ServicioTaximetro:
        """El servicio del taxímetro: lo único del dominio que ve la pantalla."""
        return self.app.servicio

    def columnas(self) -> tuple[tk.Frame, tk.Frame]:
        """El esqueleto común: la zona principal y el lateral con las acciones secundarias.

        En horizontal, el lateral es una columna de 240 px a la derecha; en
        vertical, una fila de teclas debajo. Todas las pantallas lo comparten,
        para que Volver, Ayuda, Salir… estén siempre en el mismo sitio. Las
        teclas del lateral se colocan con `colocar_lateral()`.
        """
        if estilo.VERTICAL_ACTIVA:
            return self._columnas_verticales()
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, minsize=estilo.LATERAL)
        self.rowconfigure(0, weight=1)
        principal = tk.Frame(self, bg=estilo.FONDO)
        principal.grid(row=0, column=0, sticky="nsew", padx=(estilo.MARGEN, 0), pady=estilo.MARGEN)
        lateral = tk.Frame(self, bg=estilo.FONDO, width=estilo.LATERAL)
        lateral.grid(row=0, column=1, sticky="ns", padx=estilo.MARGEN, pady=estilo.MARGEN)
        lateral.pack_propagate(False)
        return principal, lateral

    def _columnas_verticales(self) -> tuple[tk.Frame, tk.Frame]:
        """La zona principal arriba y, debajo, la fila del lateral."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        principal = tk.Frame(self, bg=estilo.FONDO)
        principal.grid(row=0, column=0, sticky="nsew", padx=estilo.MARGEN, pady=(estilo.MARGEN, 0))
        lateral = tk.Frame(self, bg=estilo.FONDO, height=estilo.LATERAL)
        lateral.grid(row=1, column=0, sticky="ew", padx=estilo.MARGEN, pady=estilo.MARGEN)
        lateral.pack_propagate(False)
        lateral.grid_propagate(False)
        return principal, lateral

    def colocar_lateral(self, tecla: Tecla, **empaquetado: Any) -> None:
        """Coloca una tecla del lateral: en una columna (`empaquetado`, como `pack`) o en la fila.

        En horizontal se apila con las opciones de `pack` que pasa cada pantalla.
        En vertical las teclas se reparten la fila de abajo a partes iguales,
        de izquierda a derecha en el orden en que se colocan.
        """
        if not estilo.VERTICAL_ACTIVA:
            tecla.pack(**empaquetado)
            return
        fila = tecla.master
        columna = len(fila.grid_slaves())
        fila.columnconfigure(columna, weight=1, uniform="lateral")
        tecla.grid(row=0, column=columna, sticky="nsew", padx=(estilo.SEPARACION if columna else 0, 0))

    @staticmethod
    def ajustar_al_ancho(etiqueta: tk.Label) -> None:
        """Hace que el texto de `etiqueta` salte de línea al llegar al borde de su hueco.

        Una etiqueta de tkinter no parte sola el texto: se sale de la pantalla
        o lo corta. Así el mensaje más largo cabe en cualquier ancho de ventana.
        La etiqueta pide solo un carácter de ancho (si no, pediría el del texto
        entero y ensancharía a su padre antes de que nadie lo partiera) y ocupa
        el hueco que le den: colócala con `fill=tk.X`.
        """
        etiqueta.configure(width=1)
        etiqueta.bind(
            "<Configure>",
            lambda evento: etiqueta.configure(wraplength=max(1, evento.width - 8)),
            add="+",
        )

    def guardar_ui(self) -> dict[str, Any]:
        """Lo que la pantalla tiene que recordar si la ventana cambia de tamaño y se rehace.

        Lo que vive en el servicio (la carrera, el importe congelado, las tarifas)
        no se guarda aquí: sigue donde estaba. Solo lo que hay en los widgets:
        lo tecleado, un aviso, un panel abierto. Por defecto, nada.
        """
        return {}

    def restaurar_ui(self, estado: dict[str, Any]) -> None:
        """Vuelve a poner en la pantalla nueva lo que devolvió `guardar_ui()` en la vieja."""

    def panel(self, principal: tk.Frame, padx: int, pady: int) -> tk.Frame:
        """El panel con borde de la columna principal; devuelve su interior.

        `padx` y `pady` son los márgenes a escala 1: aquí se escalan.
        """
        marco = tk.Frame(
            principal, bg=estilo.PANEL, highlightthickness=3, highlightbackground=estilo.VISOR_BORDE
        )
        marco.pack(fill=tk.BOTH, expand=True)
        interior = tk.Frame(marco, bg=estilo.PANEL)
        interior.pack(fill=tk.BOTH, expand=True, padx=estilo.px(padx), pady=estilo.px(pady))
        return interior

    def tecla_lateral(self, padre: tk.Misc, texto: str, comando: Callable[[], None]) -> Tecla:
        """Una tecla del lateral (Volver, Ayuda, Salir…), sin colocar."""
        return Tecla(
            padre, texto, comando, variante=estilo.LATERAL_TECLA,
            alto=estilo.TECLA_LATERAL, fuente=estilo.FUENTE_TECLA_LATERAL,
        )

    def resumen_tarifas(self) -> str:
        """Las tarifas vigentes en una línea: 'parado 0,02 €/s · en movimiento 0,05 €/s'."""
        tarifas = self.servicio.tarifas()
        return (
            f"parado {formato_euros(tarifas.parado)}/s · "
            f"en movimiento {formato_euros(tarifas.en_movimiento)}/s"
        )

    def programar(self, milisegundos: int, funcion: Callable[[], None]) -> str:
        """Llama a `funcion` dentro de `milisegundos`, en el hilo de la interfaz.

        Devuelve el identificador de `after()`. Si la pantalla se cierra antes,
        la llamada no llega a hacerse.
        """

        def disparar() -> None:
            self._temporizadores.discard(identificador)
            funcion()

        identificador = self.after(milisegundos, disparar)
        self._temporizadores.add(identificador)
        return identificador

    def al_cerrar_ventana(self) -> bool:
        """El ✕ de la ventana, antes de cerrar el programa.

        Devuelve True si la pantalla se ocupa (p. ej. pregunta porque hay una
        carrera en curso) y el programa no debe cerrarse todavía. Por defecto,
        False: se cierra.
        """
        return False

    def destroy(self) -> None:
        """Cancela los temporizadores pendientes y destruye la pantalla."""
        for identificador in self._temporizadores:
            self.after_cancel(identificador)
        self._temporizadores.clear()
        super().destroy()
