"""Confirmacion: el panel SÍ / NO que tapa la pantalla."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from taximetro.interfaces.gui import estilo
from taximetro.interfaces.gui.pantalla import Pantalla
from taximetro.interfaces.gui.tecla import Tecla


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
        margen = estilo.px(48)
        self.pregunta = tk.Label(
            panel, font=estilo.FUENTE_TITULO, bg=estilo.PANEL, fg=estilo.TEXTO,
            anchor=tk.W, justify=tk.LEFT,
        )
        Pantalla.ajustar_al_ancho(self.pregunta)
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
        self.importe.pack(side=tk.LEFT, padx=(estilo.px(12), 0))

        teclas = tk.Frame(panel, bg=estilo.PANEL)
        teclas.pack(fill=tk.X, padx=margen, pady=(estilo.px(40), margen))
        comunes = {"alto": estilo.TECLA_CONFIRMAR, "fuente": estilo.FUENTE_TECLA_CONFIRMAR}
        self.si = Tecla(teclas, "SÍ", lambda: None, variante=estilo.ROJA, **comunes)
        self.no = Tecla(teclas, "NO, SEGUIR", lambda: None, variante=estilo.GRIS, **comunes)
        mitad = estilo.SEPARACION // 2
        if estilo.VERTICAL_ACTIVA:  # sin ancho para dos teclas grandes: SÍ arriba y NO abajo
            self.si.pack(fill=tk.X, pady=(0, mitad))
            self.no.pack(fill=tk.X, pady=(mitad, 0))
        else:
            self.si.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, mitad))
            self.no.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(mitad, 0))

    @property
    def abierta(self) -> bool:
        """True mientras el panel está en pantalla."""
        return self.winfo_manager() == "place"

    def abrir(
        self,
        pregunta: str,
        importe: str,
        texto_si: str,
        al_si: Callable[[], None],
        al_no: Callable[[], None],
    ) -> None:
        """Muestra la pregunta con el importe (ya formateado) y las acciones de cada tecla."""
        self.pregunta.configure(text=pregunta)
        self.importe.configure(text=importe)
        self.si.configurar(titulo=texto_si)
        self.si.comando = al_si
        self.no.comando = al_no
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()

    def cerrar(self) -> None:
        """Quita el panel."""
        self.place_forget()
