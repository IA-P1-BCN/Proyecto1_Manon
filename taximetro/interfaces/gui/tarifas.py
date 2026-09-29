"""CambiarTarifas: los €/s de cada estado, desde la próxima carrera.

Pantalla 7 de `docs/diseno-interfaz-fase3.md`. Las reglas de qué es una
tarifa válida son del dominio (`Tarifa`), no de la pantalla; aquí solo se
traduce lo tecleado a número y se enseñan los mismos mensajes que en el CLI.
"""

from __future__ import annotations

import logging
import tkinter as tk
from typing import TYPE_CHECKING, Any

from taximetro.interfaces.gui import estilo
from taximetro.interfaces.gui.pantalla import Pantalla
from taximetro.interfaces.gui.tecla import Tecla
from taximetro.infrastructure.logs import campos
from taximetro.application.servicio_taximetro import AlmacenamientoError, TarifaInvalidaError

if TYPE_CHECKING:
    from taximetro.interfaces.gui.app import App

logger = logging.getLogger("taximetro.interfaces.gui")

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
        # El aviso a la vista (texto, campos culpables, si es de «guardado»), o None.
        self._aviso_actual: tuple[str, tuple[str, ...], bool] | None = None
        principal, lateral = self.columnas()
        interior = self.panel(principal, padx=56, pady=28)
        self._montar_titulo(interior)
        self._montar_campos(interior)
        self._montar_mensaje_y_guardar(interior)
        self._montar_ayuda(interior, lateral)
        self._pintar_vigentes()
        self.campos["parado"].focus_set()

    def _montar_titulo(self, interior: tk.Frame) -> None:
        """El título y la línea con las tarifas vigentes."""
        tk.Label(
            interior, text="Cambiar tarifas", font=estilo.FUENTE_TITULO,
            bg=estilo.PANEL, fg=estilo.TEXTO, anchor=tk.W,
        ).pack(fill=tk.X)
        self.vigentes = tk.Label(
            interior, font=estilo.FUENTE_TECLA_SUBTITULO, bg=estilo.PANEL,
            fg=estilo.TEXTO_SECUNDARIO, anchor=tk.W, justify=tk.LEFT,
        )
        self.ajustar_al_ancho(self.vigentes)
        self.vigentes.pack(fill=tk.X, pady=(estilo.SEPARACION, 0))

    def _montar_campos(self, interior: tk.Frame) -> None:
        """Una fila por estado: etiqueta, campo con la tarifa vigente y «€/s»."""
        formulario = tk.Frame(interior, bg=estilo.PANEL)
        formulario.pack(fill=tk.X, pady=(estilo.px(20), 0))
        tarifas = self.servicio.tarifas()
        self.campos: dict[str, tk.Entry] = {}
        self._marcos: dict[str, tk.Frame] = {}
        filas = (
            ("parado", "Parado o < 20 km/h", tarifas.parado, estilo.LED_AMBAR),
            ("en_movimiento", "En movimiento", tarifas.en_movimiento, estilo.LED_VERDE),
        )
        for fila, (nombre, etiqueta, valor, color) in enumerate(filas):
            self._montar_fila(formulario, fila, nombre, etiqueta, valor, color)

    def _montar_fila(
        self, formulario: tk.Frame, fila: int, nombre: str, etiqueta: str, valor: float, color: str
    ) -> None:
        """Una fila del formulario; deja el campo y su marco en `campos` y `_marcos`.

        En horizontal, la etiqueta va a la izquierda del campo; en vertical no
        hay sitio para eso y va encima.
        """
        vertical = estilo.VERTICAL_ACTIVA
        pady = estilo.px(6)
        etiqueta_campo = tk.Label(
            formulario, text=etiqueta, font=estilo.FUENTE_ETIQUETA_CAMPO,
            bg=estilo.PANEL, fg=estilo.TEXTO, anchor=tk.W, width=0 if vertical else 18,
        )
        # Vertical: dos filas por campo (etiqueta y campo); horizontal: una.
        fila_etiqueta, fila_campo = (2 * fila, 2 * fila + 1) if vertical else (fila, fila)
        etiqueta_campo.grid(row=fila_etiqueta, column=0, columnspan=2 if vertical else 1,
                            sticky="w", pady=(pady, 0) if vertical else pady)
        marco = tk.Frame(
            formulario, width=estilo.px(260), height=estilo.CAMPO, bg=estilo.VISOR_FONDO,
            highlightthickness=3, highlightbackground=estilo.CAMPO_BORDE,
        )
        marco.grid(row=fila_campo, column=0 if vertical else 1,
                   padx=(0 if vertical else estilo.SEPARACION, estilo.SEPARACION), pady=pady)
        marco.pack_propagate(False)
        # El color del estado que representa, como en el taxímetro.
        campo = tk.Entry(
            marco, font=estilo.FUENTE_CAMPO, justify=tk.RIGHT, relief=tk.FLAT,
            bg=estilo.VISOR_FONDO, fg=color, insertbackground=color,
        )
        campo.insert(0, a_texto(valor))
        campo.pack(fill=tk.BOTH, expand=True, padx=estilo.px(24))
        campo.bind("<Return>", lambda _evento: self.guardar())
        campo.bind("<Key>", self._al_teclear)
        tk.Label(
            formulario, text="€/s", font=estilo.FUENTE_ETIQUETA_CAMPO,
            bg=estilo.PANEL, fg=estilo.TEXTO_SECUNDARIO,
        ).grid(row=fila_campo, column=1 if vertical else 2, sticky="w")
        self.campos[nombre] = campo
        self._marcos[nombre] = marco

    def _montar_mensaje_y_guardar(self, interior: tk.Frame) -> None:
        """La línea de avisos y la tecla GUARDAR."""
        self.mensaje = tk.Label(
            interior, font=estilo.FUENTE_MENSAJE, bg=estilo.PANEL, anchor=tk.W,
            justify=tk.LEFT,
        )
        self.ajustar_al_ancho(self.mensaje)
        self.mensaje.pack(fill=tk.X, pady=(estilo.SEPARACION, 0))
        self.guardar_tecla = Tecla(
            interior, "GUARDAR", self.guardar, variante=estilo.VERDE, alto=estilo.TECLA_GUARDAR
        )
        self.guardar_tecla.pack(side=tk.BOTTOM, fill=tk.X)

    def _montar_ayuda(self, interior: tk.Frame, lateral: tk.Frame) -> None:
        """Cómo escribir el número (en el lateral; en vertical, sobre GUARDAR) y la tecla Volver."""
        if estilo.VERTICAL_ACTIVA:
            ayuda = tk.Frame(interior, bg=estilo.PANEL, highlightthickness=2, highlightbackground=estilo.PANEL_BORDE)
            ayuda.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, estilo.SEPARACION))
        else:
            ayuda = tk.Frame(lateral, bg=estilo.PANEL, highlightthickness=2, highlightbackground=estilo.PANEL_BORDE)
            ayuda.pack(fill=tk.X)
        # En una columna estrecha el salto de línea ayuda; en vertical, sobra: ocuparía otra línea.
        nota = tk.Label(
            ayuda, text="Coma o punto: 0,03 o 0.03" if estilo.VERTICAL_ACTIVA else "Coma o punto:\n0,03 o 0.03",
            font=estilo.FUENTE_ETIQUETA,
            bg=estilo.PANEL, fg=estilo.TEXTO_SECUNDARIO, justify=tk.LEFT, anchor=tk.W,
        )
        self.ajustar_al_ancho(nota)
        nota.pack(fill=tk.X, padx=estilo.px(16), pady=estilo.px(16))
        self.volver = self.tecla_lateral(lateral, "Volver", self.volver_a_administrador)
        self.colocar_lateral(self.volver, side=tk.BOTTOM, fill=tk.X)

    def guardar(self) -> None:
        """GUARDAR o Enter: valida, guarda y aplica. Si algo falla, no cambia nada."""
        valores = self._leer_valores()
        if valores is not None:
            self._aplicar(valores)

    def _leer_valores(self) -> dict[str, float] | None:
        """Los números tecleados, o None (con el error ya mostrado) si alguno no lo es."""
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
                return None
        return valores

    def _aplicar(self, valores: dict[str, float]) -> None:
        """Pide al servicio el cambio y enseña el resultado o el error."""
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
        self._avisar_guardado(
            f"Tarifas guardadas: parado {a_texto(nuevas.parado)} €/s · "
            f"en movimiento {a_texto(nuevas.en_movimiento)} €/s. "
            "Se aplican desde la próxima carrera."
        )

    def _avisar_guardado(self, texto: str) -> None:
        """Mensaje en verde: las tarifas nuevas ya están en uso."""
        self._aviso_actual = (texto, (), True)
        self.mensaje.configure(text=texto, fg=estilo.MENSAJE_OK)

    def guardar_ui(self) -> dict[str, Any]:
        """Lo tecleado y el aviso que se ve, para que sobrevivan a un cambio de tamaño."""
        return {
            "valores": {nombre: campo.get() for nombre, campo in self.campos.items()},
            "aviso": self._aviso_actual,
        }

    def restaurar_ui(self, estado: dict[str, Any]) -> None:
        """Vuelve a poner lo tecleado y el aviso, con los campos culpables marcados."""
        for nombre, valor in estado["valores"].items():
            self.campos[nombre].delete(0, tk.END)
            self.campos[nombre].insert(0, valor)
        if estado["aviso"] is None:
            return
        texto, culpables, guardado = estado["aviso"]
        if guardado:
            self._avisar_guardado(texto)
        else:
            self._error(texto, culpables)

    def volver_a_administrador(self) -> None:
        """Volver: al menú de Administrador, sin guardar."""
        from taximetro.interfaces.gui.administrador import Administrador

        self.app.mostrar(Administrador)

    def _pintar_vigentes(self) -> None:
        self.vigentes.configure(text=f"Tarifas vigentes: {self.resumen_tarifas()}")

    def _error(self, texto: str, culpables: tuple[str, ...]) -> None:
        """Mensaje en rojo y el borde de los campos culpables en rojo."""
        self._aviso_actual = (texto, culpables, False)
        self.mensaje.configure(text=texto, fg=estilo.MENSAJE_ERROR)
        for nombre, marco in self._marcos.items():
            color = estilo.CAMPO_BORDE_ERROR if nombre in culpables else estilo.CAMPO_BORDE
            marco.configure(highlightbackground=color)

    def _al_teclear(self, evento: tk.Event) -> None:
        """Al volver a escribir, el aviso anterior sobra."""
        if evento.keysym != "Return":
            self._aviso_actual = None
            self.mensaje.configure(text="")
            for marco in self._marcos.values():
                marco.configure(highlightbackground=estilo.CAMPO_BORDE)
