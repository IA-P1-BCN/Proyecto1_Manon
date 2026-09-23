"""CambiarTarifas: los €/s de cada estado, desde la próxima carrera (T9.7).

Pantalla 7 de `docs/diseno-interfaz-fase3.md`. Las reglas de qué es una
tarifa válida son del dominio (`Tarifa`), no de la pantalla; aquí solo se
traduce lo tecleado a número y se enseñan los mismos mensajes que en el CLI.
"""

from __future__ import annotations

import logging
import tkinter as tk
from typing import TYPE_CHECKING

from taximetro.gui import estilo
from taximetro.gui.pantalla import Pantalla
from taximetro.gui.tecla import Tecla
from taximetro.logs import campos
from taximetro.servicio_taximetro import AlmacenamientoError, TarifaInvalidaError

if TYPE_CHECKING:
    from taximetro.gui.app import App

logger = logging.getLogger("taximetro.gui")

NADA_GUARDADO = "No se ha guardado nada."
NO_ESCRITO = f"No se pudo escribir el fichero de tarifas. {NADA_GUARDADO}"


def a_texto(tarifa: float) -> str:
    """0.02 → '0,02', como se teclea."""
    return f"{tarifa:.2f}".replace(".", ",")


class CambiarTarifas(Pantalla):
    """Dos campos rellenos con las tarifas vigentes, GUARDAR (o Enter) y Volver."""

    def __init__(self, app: App) -> None:
        """Monta el formulario con las tarifas vigentes ya escritas."""
        super().__init__(app)
        principal, lateral = self.columnas()
        panel = tk.Frame(
            principal, bg=estilo.PANEL, highlightthickness=3, highlightbackground=estilo.VISOR_BORDE
        )
        panel.pack(fill=tk.BOTH, expand=True)
        interior = tk.Frame(panel, bg=estilo.PANEL)
        interior.pack(fill=tk.BOTH, expand=True, padx=56, pady=40)

        tk.Label(
            interior, text="Cambiar tarifas", font=estilo.FUENTE_TITULO,
            bg=estilo.PANEL, fg=estilo.TEXTO, anchor=tk.W,
        ).pack(fill=tk.X)
        self.vigentes = tk.Label(
            interior, font=estilo.FUENTE_TECLA_SUBTITULO, bg=estilo.PANEL,
            fg=estilo.TEXTO_SECUNDARIO, anchor=tk.W,
        )
        self.vigentes.pack(fill=tk.X, pady=(estilo.SEPARACION, 0))

        formulario = tk.Frame(interior, bg=estilo.PANEL)
        formulario.pack(fill=tk.X, pady=(32, 0))
        tarifas = self.servicio.tarifas()
        self.campos: dict[str, tk.Entry] = {}
        self._marcos: dict[str, tk.Frame] = {}
        filas = (
            ("parado", "Parado o < 20 km/h", tarifas.parado, estilo.LED_AMBAR),
            ("en_movimiento", "En movimiento", tarifas.en_movimiento, estilo.LED_VERDE),
        )
        for fila, (nombre, etiqueta, valor, color) in enumerate(filas):
            tk.Label(
                formulario, text=etiqueta, font=estilo.FUENTE_ETIQUETA_CAMPO,
                bg=estilo.PANEL, fg=estilo.TEXTO, anchor=tk.W, width=18,
            ).grid(row=fila, column=0, sticky="w", pady=10)
            marco = tk.Frame(
                formulario, width=260, height=estilo.CAMPO, bg=estilo.VISOR_FONDO,
                highlightthickness=3, highlightbackground=estilo.CAMPO_BORDE,
            )
            marco.grid(row=fila, column=1, padx=estilo.SEPARACION, pady=10)
            marco.pack_propagate(False)
            # El color del estado que representa, como en el taxímetro.
            campo = tk.Entry(
                marco, font=estilo.FUENTE_CAMPO, justify=tk.RIGHT, relief=tk.FLAT,
                bg=estilo.VISOR_FONDO, fg=color, insertbackground=color,
            )
            campo.insert(0, a_texto(valor))
            campo.pack(fill=tk.BOTH, expand=True, padx=24)
            campo.bind("<Return>", lambda _evento: self.guardar())
            campo.bind("<Key>", self._al_teclear)
            tk.Label(
                formulario, text="€/s", font=estilo.FUENTE_ETIQUETA_CAMPO,
                bg=estilo.PANEL, fg=estilo.TEXTO_SECUNDARIO,
            ).grid(row=fila, column=2, sticky="w")
            self.campos[nombre] = campo
            self._marcos[nombre] = marco

        self.mensaje = tk.Label(
            interior, font=estilo.FUENTE_MENSAJE, bg=estilo.PANEL, anchor=tk.W,
            justify=tk.LEFT, wraplength=820,
        )
        self.mensaje.pack(fill=tk.X, pady=(estilo.SEPARACION, 0))
        self.guardar_tecla = Tecla(
            interior, "GUARDAR", self.guardar, variante=estilo.VERDE, alto=estilo.TECLA_GUARDAR
        )
        self.guardar_tecla.pack(side=tk.BOTTOM, fill=tk.X)

        ayuda = tk.Frame(lateral, bg=estilo.PANEL, highlightthickness=2, highlightbackground=estilo.PANEL_BORDE)
        ayuda.pack(fill=tk.X)
        tk.Label(
            ayuda, text="Coma o punto:\n0,03 o 0.03", font=estilo.FUENTE_ETIQUETA,
            bg=estilo.PANEL, fg=estilo.TEXTO_SECUNDARIO, justify=tk.LEFT, anchor=tk.W,
        ).pack(fill=tk.X, padx=16, pady=16)
        self.volver = self.tecla_lateral(lateral, "Volver", self.volver_a_administrador)
        self.volver.pack(side=tk.BOTTOM, fill=tk.X)

        self._pintar_vigentes()
        self.campos["parado"].focus_set()

    def guardar(self) -> None:
        """GUARDAR o Enter: valida, guarda y aplica. Si algo falla, no cambia nada."""
        valores: dict[str, float] = {}
        for nombre, campo in self.campos.items():
            tecleado = campo.get().strip()
            try:
                valores[nombre] = float(tecleado.replace(",", "."))
            except ValueError:
                logger.warning(
                    "tarifa_rechazada %s", campos(tecleado=repr(tecleado), motivo="no_numerica")
                )
                self._error(
                    f"«{tecleado}» no es un número. Escribe, por ejemplo, 0,03. {NADA_GUARDADO}",
                    (nombre,),
                )
                return
        try:
            nuevas = self.servicio.cambiar_tarifas(valores["parado"], valores["en_movimiento"])
        except TarifaInvalidaError as error:
            logger.warning(
                "tarifa_rechazada %s",
                campos(
                    parado=valores["parado"],
                    movimiento=valores["en_movimiento"],
                    motivo=repr(str(error)),
                ),
            )
            self._error(f"{error} {NADA_GUARDADO}", error.campos)
            return
        except AlmacenamientoError:
            # El detalle ya lo registró ConfigTarifas, donde ocurrió la escritura.
            self._error(NO_ESCRITO, ())
            return
        self._pintar_vigentes()
        self.mensaje.configure(
            text=(
                f"Tarifas guardadas: parado {a_texto(nuevas.parado)} €/s · "
                f"en movimiento {a_texto(nuevas.en_movimiento)} €/s. "
                "Se aplican desde la próxima carrera."
            ),
            fg=estilo.MENSAJE_OK,
        )

    def volver_a_administrador(self) -> None:
        """Volver: al menú de Administrador, sin guardar."""
        from taximetro.gui.administrador import Administrador

        self.app.mostrar(Administrador)

    def _pintar_vigentes(self) -> None:
        self.vigentes.configure(text=f"Tarifas vigentes: {self.resumen_tarifas()}")

    def _error(self, texto: str, culpables: tuple[str, ...]) -> None:
        """Mensaje en rojo y el borde de los campos culpables en rojo."""
        self.mensaje.configure(text=texto, fg=estilo.MENSAJE_ERROR)
        for nombre, marco in self._marcos.items():
            color = estilo.CAMPO_BORDE_ERROR if nombre in culpables else estilo.CAMPO_BORDE
            marco.configure(highlightbackground=color)

    def _al_teclear(self, evento: tk.Event) -> None:
        """Al volver a escribir, el aviso anterior sobra."""
        if evento.keysym != "Return":
            self.mensaje.configure(text="")
            for marco in self._marcos.values():
                marco.configure(highlightbackground=estilo.CAMPO_BORDE)
