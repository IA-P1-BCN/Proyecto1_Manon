"""Confirmacion: el panel SÍ / NO que tapa la pantalla (T9.8)."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from taximetro.gui import estilo
from taximetro.gui.tecla import Tecla


class Confirmacion(tk.Frame):
    """Una pregunta a pantalla completa, con el importe que se cobrará y dos teclas.

    **SÍ a la izquierda y NO a la derecha**, justo donde estaba FINALIZAR: un
    doble toque sin querer sobre FINALIZAR cae en NO y no cierra nada
    (`docs/diseno-interfaz-fase3.md`, *Confirmación al finalizar*). Tapa toda
    la pantalla, así que mientras está abierta no se puede pulsar nada más.
    """

    def __init__(self, padre: tk.Misc) -> None:
        """Crea el panel, cerrado."""
        super().__init__(padre, bg=estilo.VISOR_FONDO)
        panel = tk.Frame(
            self, bg=estilo.PANEL, highlightthickness=3, highlightbackground=estilo.ROJA.borde
        )
        panel.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=estilo.CONFIRMACION_ANCHO)
        margen = 48
        self.pregunta = tk.Label(
            panel, font=estilo.FUENTE_TITULO, bg=estilo.PANEL, fg=estilo.TEXTO,
            anchor=tk.W, justify=tk.LEFT, wraplength=estilo.CONFIRMACION_ANCHO - 2 * margen,
        )
        self.pregunta.pack(fill=tk.X, padx=margen, pady=(margen, estilo.SEPARACION))
        fila = tk.Frame(panel, bg=estilo.PANEL)
        fila.pack(fill=tk.X, padx=margen)
        tk.Label(
            fila, text="Importe a cobrar:", font=estilo.FUENTE_DETALLE,
            bg=estilo.PANEL, fg=estilo.TEXTO_SECUNDARIO,
        ).pack(side=tk.LEFT)
        self.importe = tk.Label(
            fila, font=estilo.FUENTE_DETALLE_IMPORTE, bg=estilo.PANEL, fg=estilo.LED_ROJO
        )
        self.importe.pack(side=tk.LEFT, padx=(12, 0))

        teclas = tk.Frame(panel, bg=estilo.PANEL)
        teclas.pack(fill=tk.X, padx=margen, pady=(40, margen))
        comunes = {"alto": estilo.TECLA_CONFIRMAR, "fuente": estilo.FUENTE_TECLA_CONFIRMAR}
        self.si = Tecla(teclas, "SÍ", lambda: None, variante=estilo.ROJA, **comunes)
        self.si.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, estilo.SEPARACION // 2))
        self.no = Tecla(teclas, "NO, SEGUIR", lambda: None, variante=estilo.GRIS, **comunes)
        self.no.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(estilo.SEPARACION // 2, 0))

    @property
    def abierta(self) -> bool:
        """True mientras el panel está en pantalla."""
        return self.winfo_manager() == "place"

    def abrir(
        self,
        pregunta: str,
        importe: str,
        si: str,
        al_si: Callable[[], None],
        al_no: Callable[[], None],
    ) -> None:
        """Muestra la pregunta con el importe (ya formateado) y las acciones de cada tecla."""
        self.pregunta.configure(text=pregunta)
        self.importe.configure(text=importe)
        self.si.configurar(titulo=si)
        self.si.comando = al_si
        self.no.comando = al_no
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()

    def cerrar(self) -> None:
        """Quita el panel."""
        self.place_forget()
