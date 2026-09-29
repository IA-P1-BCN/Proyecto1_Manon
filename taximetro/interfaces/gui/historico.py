"""Historico: las carreras terminadas hoy y el total de caja.

Pantalla 8 de `docs/diseno-interfaz-fase3.md`: las columnas del CLI (Nº,
Inicio, Fin, Importe) en filas grandes, con ▲ ▼ en el lateral cuando no caben
todas (una barra de desplazamiento es demasiado fina para un dedo).
"""

from __future__ import annotations

import logging
import tkinter as tk
from typing import TYPE_CHECKING, Any

from taximetro.interfaces.gui import estilo
from taximetro.interfaces.gui.pantalla import Pantalla
from taximetro.infrastructure.logs import campos
from taximetro.application.servicio_taximetro import AlmacenamientoError, RegistroCarrera
from taximetro.utils import formato_euros

if TYPE_CHECKING:
    from taximetro.interfaces.gui.app import App

logger = logging.getLogger("taximetro.interfaces.gui")

SIN_CARRERAS = "No hay carreras terminadas hoy."
ILEGIBLE = "No se pudo leer el histórico."
COLUMNAS = (("Nº", tk.E, 4), ("Inicio", tk.W, 8), ("Fin", tk.W, 8), ("Importe", tk.E, 9))


class Historico(Pantalla):
    """Tabla del día, total en rojo LED, ▲ ▼ y Volver."""

    def __init__(self, app: App) -> None:
        """Lee el histórico del día y lo enseña desde la primera carrera."""
        super().__init__(app)
        principal, lateral = self.columnas()
        margen = 16 if estilo.VERTICAL_ACTIVA else 40  # a escala 1: en vertical sobra menos ancho
        self._montar_tabla(self.panel(principal, padx=margen, pady=32))
        self._montar_lateral(lateral)
        self._carreras: tuple[RegistroCarrera, ...] = ()
        self.desde = 0  # primera fila a la vista
        self._cargar()

    def _montar_tabla(self, interior: tk.Frame) -> None:
        """El título, el hueco de las filas, el aviso y la caja del total."""
        self.titulo = tk.Label(
            interior, font=estilo.FUENTE_TITULO_HISTORICO, bg=estilo.PANEL,
            fg=estilo.TEXTO, anchor=tk.W, justify=tk.LEFT,
        )
        self.ajustar_al_ancho(self.titulo)
        self.titulo.pack(fill=tk.X, pady=(0, estilo.px(20)))
        self._tabla = tk.Frame(interior, bg=estilo.PANEL)
        self._tabla.pack(fill=tk.X)
        self.mensaje = tk.Label(
            interior, font=estilo.FUENTE_TEXTO, bg=estilo.PANEL, fg=estilo.TEXTO_SECUNDARIO, anchor=tk.W
        )

        self._caja = tk.Frame(
            interior, bg=estilo.VISOR_FONDO, highlightthickness=3, highlightbackground=estilo.VISOR_BORDE
        )
        self.resumen = tk.Label(
            self._caja, font=estilo.FUENTE_TEXTO, bg=estilo.VISOR_FONDO, fg=estilo.TEXTO_SECUNDARIO
        )
        self.total = tk.Label(self._caja, font=estilo.FUENTE_TOTAL, bg=estilo.VISOR_FONDO, fg=estilo.LED_ROJO)
        lado, hueco = estilo.px(28), estilo.px(20)
        if estilo.VERTICAL_ACTIVA:  # sin sitio para los dos a la vez: uno encima del otro
            self.resumen.pack(anchor=tk.W, padx=lado, pady=(hueco, 0))
            self.total.pack(anchor=tk.E, padx=lado, pady=(0, hueco))
        else:
            self.resumen.pack(side=tk.LEFT, padx=lado, pady=hueco)
            self.total.pack(side=tk.RIGHT, padx=lado)

    def _montar_lateral(self, lateral: tk.Frame) -> None:
        """Las teclas ▲ ▼ y Volver."""
        self.subir = self.tecla_lateral(lateral, "▲", self.subir_filas)
        self.colocar_lateral(self.subir, fill=tk.X, pady=(0, estilo.SEPARACION))
        self.bajar = self.tecla_lateral(lateral, "▼", self.bajar_filas)
        self.colocar_lateral(self.bajar, fill=tk.X)
        self.volver = self.tecla_lateral(lateral, "Volver", self.volver_a_administrador)
        self.colocar_lateral(self.volver, side=tk.BOTTOM, fill=tk.X)

    def guardar_ui(self) -> dict[str, Any]:
        """La primera fila a la vista, para no volver a la primera página al cambiar de tamaño."""
        return {"desde": self.desde}

    def restaurar_ui(self, estado: dict[str, Any]) -> None:
        """Vuelve a la página en la que se estaba, sin pasar de la última fila."""
        self.desde = min(estado["desde"], max(0, len(self._carreras) - estilo.FILAS_HISTORICO))
        self._pintar_filas()

    def subir_filas(self) -> None:
        """▲: una página hacia arriba."""
        self.desde = max(0, self.desde - estilo.FILAS_HISTORICO)
        self._pintar_filas()

    def bajar_filas(self) -> None:
        """▼: una página hacia abajo, sin pasar de la última fila."""
        ultima_pagina = max(0, len(self._carreras) - estilo.FILAS_HISTORICO)
        self.desde = min(ultima_pagina, self.desde + estilo.FILAS_HISTORICO)
        self._pintar_filas()

    def volver_a_administrador(self) -> None:
        """Volver: al menú de Administrador."""
        from taximetro.interfaces.gui.administrador import Administrador

        self.app.mostrar(Administrador)

    def _cargar(self) -> None:
        """Pide el resumen del día al servicio y lo pinta."""
        try:
            resumen = self.servicio.resumen_del_dia()
        except AlmacenamientoError:
            logger.error("historico_ilegible", exc_info=True)
            self.titulo.configure(text="Histórico de hoy")
            self.mensaje.configure(text=ILEGIBLE, fg=estilo.MENSAJE_ERROR)
            self.mensaje.pack(fill=tk.X, pady=(estilo.SEPARACION, 0))
            return
        logger.info(
            "historico_consultado %s",
            campos(fecha=resumen.fecha, carreras=len(resumen.carreras), total=resumen.total),
        )
        self.titulo.configure(text=f"Histórico de hoy · {resumen.fecha:%d/%m/%Y}")
        self._carreras = resumen.carreras
        cuantas = len(resumen.carreras)
        self.resumen.configure(text=f"{cuantas} {'carrera' if cuantas == 1 else 'carreras'} · Total del día")
        self.total.configure(text=formato_euros(resumen.total))
        self._caja.pack(side=tk.BOTTOM, fill=tk.X)
        if not resumen.carreras:
            self.mensaje.configure(text=SIN_CARRERAS)
            self.mensaje.pack(fill=tk.X, pady=(estilo.SEPARACION, 0))
        self._pintar_filas()

    def _pintar_filas(self) -> None:
        """Cabecera y las filas de la página actual, con sombreado alterno."""
        for hijo in self._tabla.winfo_children():
            hijo.destroy()
        self._fila(
            [nombre for nombre, _, _ in COLUMNAS], estilo.PANEL, estilo.FUENTE_ETIQUETA,
            estilo.TEXTO_ETIQUETA, alto=estilo.px(56),
        )
        pagina = self._carreras[self.desde : self.desde + estilo.FILAS_HISTORICO]
        for i, registro in enumerate(pagina):
            fondo = estilo.FILA_ALTERNA if (self.desde + i) % 2 else estilo.PANEL
            self._fila(
                [
                    str(registro.carrera),
                    f"{registro.hora_inicio:%H:%M:%S}",
                    f"{registro.hora_fin:%H:%M:%S}",
                    formato_euros(registro.importe),
                ],
                fondo, estilo.FUENTE_TEXTO, estilo.TEXTO, alto=estilo.FILA,
            )

    def _fila(self, textos: list[str], fondo: str, fuente, color: str, alto: int) -> None:
        fila = tk.Frame(self._tabla, bg=fondo, height=alto)
        fila.pack(fill=tk.X)
        fila.pack_propagate(False)
        for (_, ancla, ancho), texto in zip(COLUMNAS, textos):
            tk.Label(
                fila, text=texto, font=fuente, bg=fondo, fg=color, anchor=ancla, width=ancho
            ).pack(side=tk.LEFT, fill=tk.Y, padx=estilo.px(4 if estilo.VERTICAL_ACTIVA else 24))

    @property
    def filas_visibles(self) -> list[list[str]]:
        """Los textos de las filas a la vista, sin la cabecera (para los tests)."""
        filas = self._tabla.winfo_children()[1:]
        return [[celda.cget("text") for celda in fila.winfo_children()] for fila in filas]
