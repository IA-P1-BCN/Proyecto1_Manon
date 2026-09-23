"""Tecla: la tecla táctil de la interfaz gráfica (T9.5)."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from taximetro.gui import estilo, iconos
from taximetro.gui.estilo import Variante


class Tecla(tk.Frame):
    """Una tecla grande, plana y rectangular, como las de un taxímetro.

    Un `tk.Button` no sirve: mide el alto en líneas de texto y lleva una sola
    fuente, y aquí hacen falta un alto fijo en píxeles y un subtítulo más
    pequeño («FINALIZAR» / «Termina y muestra el total»).

    Actúa al **soltar** encima, como un botón real: quien pone el dedo y se
    arrepiente puede deslizarlo fuera. Mientras se pulsa se aclara. Nunca mide
    menos de `estilo.ZONA_TACTIL_MIN` de alto.
    """

    def __init__(
        self,
        padre: tk.Misc,
        titulo: str,
        comando: Callable[[], None],
        variante: Variante = estilo.GRIS,
        alto: int = estilo.TECLA_PRINCIPAL_MIN,
        subtitulo: str = "",
        fuente: estilo.Fuente = estilo.FUENTE_TECLA,
        icono: str | None = None,
        tamano_icono: int = 96,
    ) -> None:
        """Crea la tecla; `alto` en píxeles, nunca por debajo de la zona táctil mínima.

        Con `icono` (un nombre de `iconos.NOMBRES`) es una teja: icono encima
        del título, como CONDUCTOR y ADMINISTRADOR en la pantalla de inicio.
        """
        if alto < estilo.ZONA_TACTIL_MIN:
            raise ValueError(
                f"Tecla de {alto} px: la zona táctil mínima es {estilo.ZONA_TACTIL_MIN} px."
            )
        super().__init__(padre, height=alto, highlightthickness=3, cursor="hand2")
        self.pack_propagate(False)  # el alto lo decide la tecla, no su texto
        self.comando = comando
        self._pulsada = False

        # Un marco interior centra título y subtítulo en vertical.
        self._centro = tk.Frame(self)
        self._centro.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self._icono: tk.Canvas | None = None
        if icono is not None:
            self._icono = tk.Canvas(
                self._centro, width=tamano_icono, height=tamano_icono, highlightthickness=0
            )
            iconos.dibujar(self._icono, icono, tamano_icono, "#ffffff")
            self._icono.pack(pady=(0, 16))
        self._titulo = tk.Label(self._centro, font=fuente, justify=tk.CENTER)
        self._titulo.pack()
        self._subtitulo = tk.Label(
            self._centro, font=estilo.FUENTE_TECLA_SUBTITULO, justify=tk.CENTER
        )

        widgets = [self, self._centro, self._titulo, self._subtitulo]
        if self._icono is not None:
            widgets.append(self._icono)
        for widget in widgets:
            widget.bind("<ButtonPress-1>", self._al_pulsar)
            widget.bind("<ButtonRelease-1>", self._al_soltar)

        self.configurar(titulo=titulo, subtitulo=subtitulo, variante=variante)

    @property
    def titulo(self) -> str:
        """El texto grande de la tecla."""
        return self._titulo.cget("text")

    @property
    def subtitulo(self) -> str:
        """El texto pequeño bajo el título, o '' si no tiene."""
        return self._subtitulo.cget("text")

    def configurar(
        self,
        titulo: str | None = None,
        subtitulo: str | None = None,
        variante: Variante | None = None,
    ) -> None:
        """Cambia el texto o los colores (p. ej. PARAR ↔ ARRANCAR) sin rehacer la tecla."""
        if variante is not None:
            self._variante = variante
        if titulo is not None:
            self._titulo.configure(text=titulo)
        if subtitulo is not None:
            self._subtitulo.configure(text=subtitulo)
            if subtitulo:
                self._subtitulo.pack(pady=(8, 0))
            else:
                self._subtitulo.pack_forget()
        self._pintar()

    def invoke(self) -> None:
        """Ejecuta el comando, como una pulsación completa (lo usan Enter y los tests)."""
        self.comando()

    def _pintar(self) -> None:
        """Aplica los colores de la variante, más claros mientras se pulsa."""
        variante = self._variante
        fondo = variante.pulsada if self._pulsada else variante.fondo
        self.configure(bg=fondo, highlightbackground=variante.borde, highlightcolor=variante.borde)
        self._centro.configure(bg=fondo)
        if self._icono is not None:
            self._icono.configure(bg=fondo)
        self._titulo.configure(bg=fondo, fg="#ffffff")
        self._subtitulo.configure(bg=fondo, fg=variante.subtitulo)

    def _al_pulsar(self, _evento: tk.Event) -> None:
        self._pulsada = True
        self._pintar()

    def _al_soltar(self, evento: tk.Event) -> None:
        """Solo actúa si el dedo se levanta encima de la tecla."""
        if not self._pulsada:
            return
        self._pulsada = False
        self._pintar()
        if self._contiene(evento.x_root, evento.y_root):
            self.comando()

    def _contiene(self, x: int, y: int) -> bool:
        """True si el punto de la pantalla (x, y) cae dentro del rectángulo de la tecla.

        Se mira la geometría y no `winfo_containing`, que pregunta qué ventana
        hay de verdad en ese punto del escritorio y falla si otra la tapa.
        """
        izquierda, arriba = self.winfo_rootx(), self.winfo_rooty()
        return (
            izquierda <= x < izquierda + self.winfo_width()
            and arriba <= y < arriba + self.winfo_height()
        )
