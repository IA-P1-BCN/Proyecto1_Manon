"""PantallaTaximetro: el taxímetro del conductor, LIBRE u OCUPADO.

Pantallas 3 y 4 de `docs/diseno-interfaz-fase3.md`, que son una sola: el
taxímetro pasa de OCUPADO a LIBRE y vuelta, como uno real. Se llama
`PantallaTaximetro` y no `Taximetro` para no confundirla con la clase del
dominio.
"""

from __future__ import annotations

import logging
import tkinter as tk
from typing import TYPE_CHECKING, Any

from taximetro.interfaces.gui import estilo
from taximetro.interfaces.gui.confirmacion import Confirmacion
from taximetro.interfaces.gui.pantalla import Pantalla
from taximetro.interfaces.gui.tecla import Tecla
from taximetro.interfaces.gui.visor import Visor
from taximetro.infrastructure.logs import campos
from taximetro.application.servicio_taximetro import CarreraCerrada, Estado, InstantaneaCarrera
from taximetro.utils import formato_euros

if TYPE_CHECKING:
    from taximetro.interfaces.gui.app import App

logger = logging.getLogger("taximetro.interfaces.gui")

REFRESCO_MS = 200  # un céntimo a 0,05 €/s: el visor nunca se salta uno
SIN_DATO = "—"
NO_GUARDADA = "No guardada en el histórico: anota el total."


class PantallaTaximetro(Pantalla):
    """El taxímetro: visor, teclas y lateral, en estado LIBRE u OCUPADO.

    Todo lo que enseña sale del servicio: la carrera en curso de
    `estado_actual()`, y la que se acaba de cerrar, del `CarreraCerrada` que
    devolvió `finalizar_carrera()`. Con carrera, el importe y el tiempo se
    refrescan cada `REFRESCO_MS`; cada pulsación repinta en el acto.
    """

    def __init__(self, app: App) -> None:
        """Monta la pantalla y la pinta en el estado en que esté el taxímetro."""
        super().__init__(app)
        self._cerrada: CarreraCerrada | None = None  # la última, mientras se cobra
        self._refrescando = False
        self._saliendo = False  # «SÍ, FINALIZAR Y SALIR»: solo queda la tecla CERRAR
        self._salida_pedida: int | None = None  # nº de carrera mientras se pregunta por el ✕
        # Lo que enseña el panel SÍ / NO abierto (modo, pregunta, importe, texto de SÍ), o None.
        self._confirmando: tuple[str, str, str, str] | None = None

        principal, lateral = self.columnas()
        self._montar_visor(principal)
        self._montar_datos(principal, lateral)
        self._montar_teclas(principal)
        self._montar_lateral(lateral)
        self._montar_ayuda()
        self.confirmacion = Confirmacion(self)  # la última: queda por encima de todo
        self._pintar()

    def iniciar(self) -> None:
        """INICIAR CARRERA: la carrera nace en movimiento, como en el CLI."""
        self.servicio.iniciar_carrera()
        self._cerrada = None
        self._pintar()

    def cambiar_estado(self) -> None:
        """PARAR / ARRANCAR: siempre la acción contraria al estado actual."""
        ahora = self.servicio.estado_actual()
        if ahora is None:
            return
        destino = Estado.PARADO if ahora.estado is Estado.EN_MOVIMIENTO else Estado.EN_MOVIMIENTO
        self.servicio.cambiar_estado(destino)
        self._pintar()

    def pedir_finalizar(self) -> None:
        """FINALIZAR: congela el importe y pregunta antes de cerrar.

        Un toque sin querer con el coche en marcha cerraría una carrera que no
        se puede reabrir. Lo que se cobra es lo de este instante, no lo que se
        tarda en contestar.
        """
        congelada = self.servicio.congelar_importe()
        self._abrir_confirmacion(
            "finalizar", f"¿Finalizar la carrera nº {congelada.id}?",
            formato_euros(congelada.importe), "SÍ, FINALIZAR",
        )

    def seguir(self) -> None:
        """NO, SEGUIR: la carrera sigue como si nada (también se cobra la pregunta)."""
        if self._salida_pedida is not None:
            logger.info("salida_cancelada %s", campos(carrera=self._salida_pedida))
            self._salida_pedida = None
        self.servicio.seguir_carrera()
        self._cerrar_confirmacion()
        self._pintar()

    def finalizar(self) -> None:
        """Cierra la carrera y deja el total en el visor hasta la siguiente.

        Si antes se pidió el cierre, se cobra el importe congelado entonces.
        """
        self._cerrada = self.servicio.finalizar_carrera()
        self._pintar()

    def al_cerrar_ventana(self) -> bool:
        """El ✕ con una carrera en curso pregunta antes de salir (`flujo-fase3.md`).

        Con el panel ya abierto, el ✕ cuenta como NO, SEGUIR: un doble clic
        nervioso nunca termina una carrera. Sin carrera, se cierra sin preguntar.
        """
        if self.confirmacion.abierta:
            self.seguir()
            return True
        if self.servicio.estado_actual() is None:
            return False
        congelada = self.servicio.congelar_importe()
        # Los mismos eventos que el Ctrl+C del CLI: un grep sirve para los dos.
        logger.info("salida_solicitada %s", campos(carrera=congelada.id))
        self._salida_pedida = congelada.id
        self._abrir_confirmacion(
            "salir", f"Vas a salir del programa con la carrera nº {congelada.id} en curso.",
            formato_euros(congelada.importe),
            # En dos líneas: en una, a 48 px, no cabe en media tecla (507 px de 457).
            "SÍ, FINALIZAR\nY SALIR",
        )
        return True

    def _abrir_confirmacion(self, modo: str, pregunta: str, importe: str, texto_si: str) -> None:
        """Abre el panel SÍ / NO; `modo` dice qué hace SÍ: `finalizar` o `salir`.

        Se recuerda lo que muestra, para volver a abrirlo igual si la ventana
        cambia de tamaño y se rehace la pantalla. El importe no se vuelve a
        congelar: sigue congelado en el servicio.
        """
        self._confirmando = (modo, pregunta, importe, texto_si)
        self.confirmacion.abrir(
            pregunta=pregunta,
            importe=importe,
            texto_si=texto_si,
            al_si=self._confirmar_finalizar if modo == "finalizar" else self._finalizar_y_salir,
            al_no=self.seguir,
        )

    def _cerrar_confirmacion(self) -> None:
        """Quita el panel SÍ / NO."""
        self._confirmando = None
        self.confirmacion.cerrar()

    def _confirmar_finalizar(self) -> None:
        self._cerrar_confirmacion()
        self.finalizar()

    def _finalizar_y_salir(self) -> None:
        """Cierra la carrera y deja el total a la vista con una sola tecla, CERRAR.

        Cerrar la ventana en el acto escondería el total antes de que el
        pasajero lo vea; el programa termina al pulsar CERRAR.
        """
        logger.info("salida_confirmada %s", campos(carrera=self._salida_pedida))
        self._salida_pedida = None
        self._cerrar_confirmacion()
        self._saliendo = True
        self.finalizar()

    def guardar_ui(self) -> dict[str, Any]:
        """Lo que hay que recordar si la ventana cambia de tamaño: total a cobrar, paneles y salida pedida."""
        return {
            "cerrada": self._cerrada,
            "saliendo": self._saliendo,
            "salida_pedida": self._salida_pedida,
            "confirmando": self._confirmando,
            "ayuda": self._ayuda.winfo_manager() == "place",
        }

    def restaurar_ui(self, estado: dict[str, Any]) -> None:
        """Repone el total a cobrar, la salida pedida y los paneles abiertos."""
        self._cerrada = estado["cerrada"]
        self._saliendo = estado["saliendo"]
        self._salida_pedida = estado["salida_pedida"]
        self._pintar()
        if estado["confirmando"] is not None:
            self._abrir_confirmacion(*estado["confirmando"])
        if estado["ayuda"]:
            self.abrir_ayuda()

    def volver(self) -> None:
        """Volver a la pantalla de inicio (solo existe sin carrera)."""
        from taximetro.interfaces.gui.inicio import Inicio  # Inicio también importa esta pantalla

        self.app.mostrar(Inicio)

    def abrir_ayuda(self) -> None:
        """Muestra el panel de ayuda encima de la pantalla."""
        self._tarifas_ayuda.configure(text=f"Tarifas: {self.resumen_tarifas()}")
        self._ayuda.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._ayuda.lift()

    def cerrar_ayuda(self) -> None:
        """Quita el panel de ayuda."""
        self._ayuda.place_forget()

    def _pintar(self) -> None:
        """Pone la pantalla en LIBRE u OCUPADO según el servicio."""
        ahora = self.servicio.estado_actual()
        if ahora is None:
            self._pintar_libre()
        else:
            self._pintar_ocupado(ahora)
            if not self._refrescando:
                self._refrescando = True
                self.programar(REFRESCO_MS, self._refrescar)

    def _pintar_ocupado(self, ahora: InstantaneaCarrera) -> None:
        self._lamparas(ocupado=True)
        aspecto = estilo.ESTADOS[ahora.estado]
        self.estado.configure(text=aspecto.texto, fg=aspecto.color)
        self.tarifa.configure(text=f"{self._tarifa_de(ahora.estado)}/s", fg=aspecto.color)
        self.rotulo.configure(text="IMPORTE")
        self._mostrar_carrera(ahora)
        accion = "PARAR" if ahora.estado is Estado.EN_MOVIMIENTO else "ARRANCAR"
        self.tecla_cambiar.configurar(titulo=accion)
        self.tecla_iniciar.pack_forget()
        self._colocar_teclas_de_carrera()
        self._ocultar_volver()

    def _colocar_teclas_de_carrera(self) -> None:
        """PARAR / ARRANCAR y FINALIZAR: lado a lado en horizontal, una encima de otra en vertical."""
        if estilo.VERTICAL_ACTIVA:
            self.tecla_cambiar.pack(fill=tk.X, expand=True, pady=(0, estilo.SEPARACION))
            self.tecla_finalizar.pack(fill=tk.X, expand=True)
            return
        self.tecla_cambiar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, estilo.SEPARACION // 2))
        self.tecla_finalizar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(estilo.SEPARACION // 2, 0))

    def _mostrar_volver(self) -> None:
        """Volver, que solo existe sin carrera: encima de Ayuda, o a su izquierda en vertical."""
        if estilo.VERTICAL_ACTIVA:
            self._ordenar_fila_lateral(con_volver=True)
            return
        # Al apilar desde abajo, lo que se empaqueta después queda más arriba.
        self.tecla_volver.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, estilo.SEPARACION), after=self.tecla_ayuda)

    def _ocultar_volver(self) -> None:
        """Quita Volver (con una carrera en curso no se puede volver a Inicio)."""
        if estilo.VERTICAL_ACTIVA:
            self._ordenar_fila_lateral(con_volver=False)
            return
        self.tecla_volver.pack_forget()

    def _ordenar_fila_lateral(self, con_volver: bool) -> None:
        """En vertical: Volver y Ayuda se reparten la fila; sin Volver, Ayuda la ocupa entera."""
        fila = self.tecla_ayuda.master
        if con_volver:
            fila.columnconfigure((0, 1), weight=1, uniform="lateral")
            self.tecla_volver.grid(row=0, column=0, sticky="nsew", padx=(0, estilo.SEPARACION))
            self.tecla_ayuda.grid(row=0, column=1, columnspan=1, sticky="nsew")
        else:
            self.tecla_volver.grid_remove()
            self.tecla_ayuda.grid(row=0, column=0, columnspan=2, sticky="nsew")

    def _pintar_libre(self) -> None:
        self._lamparas(ocupado=False)
        cerrada = self._cerrada
        if cerrada is None:
            # Primer arranque: aún no hay carrera que enseñar.
            self.estado.configure(text="", fg=estilo.TEXTO)
            self.tarifa.configure(text="", fg=estilo.TEXTO)
            self.rotulo.configure(text="IMPORTE")
            self.visor.mostrar(0)
            for dato in (self.dato_carrera, self.dato_tiempo, self.dato_inicio):
                dato.configure(text=SIN_DATO)
        else:
            self.estado.configure(text="CARRERA FINALIZADA", fg=estilo.LED_ROJO)
            if cerrada.guardada:
                self.tarifa.configure(text="Cobrar al pasajero", fg=estilo.LED_ROJO)
            else:
                self.tarifa.configure(text=NO_GUARDADA, fg=estilo.LED_AMBAR)
            self.rotulo.configure(text="TOTAL A COBRAR")
            self._mostrar_carrera(cerrada.carrera)
        self.tecla_cambiar.pack_forget()
        self.tecla_finalizar.pack_forget()
        if self._saliendo:
            self.tecla_iniciar.pack_forget()
            self._ocultar_volver()
            self.tecla_cerrar.pack(fill=tk.X, expand=True)
            return
        subtitulo = f"Empieza en movimiento · {self._tarifa_de(Estado.EN_MOVIMIENTO)}/s"
        self.tecla_iniciar.configurar(subtitulo=subtitulo)
        self.tecla_iniciar.pack(fill=tk.X, expand=True)
        self._mostrar_volver()

    def _refrescar(self) -> None:
        """Cada REFRESCO_MS con carrera: importe y tiempo. Se para sola al quedar libre."""
        ahora = self.servicio.estado_actual()
        if ahora is None:
            self._refrescando = False
            return
        self._mostrar_carrera(ahora)
        self.programar(REFRESCO_MS, self._refrescar)

    def _mostrar_carrera(self, carrera: InstantaneaCarrera) -> None:
        """El importe en el visor y los datos del lateral."""
        self.visor.mostrar(carrera.importe)
        self.dato_carrera.configure(text=f"Nº {carrera.id}")
        self.dato_tiempo.configure(text=tiempo(carrera.duracion))
        self.dato_inicio.configure(text=f"{carrera.hora_inicio:%H:%M}")

    def _lamparas(self, ocupado: bool) -> None:
        """Enciende OCUPADO o LIBRE; la otra queda apagada pero visible."""
        encendidas = {
            self.lampara_ocupado: estilo.OCUPADO_ENCENDIDA if ocupado else estilo.OCUPADO_APAGADA,
            self.lampara_libre: estilo.LIBRE_APAGADA if ocupado else estilo.LIBRE_ENCENDIDA,
        }
        for lampara, aspecto in encendidas.items():
            lampara.configure(bg=aspecto.fondo, fg=aspecto.texto)

    def _tarifa_de(self, estado: Estado) -> str:
        """La tarifa vigente de `estado`, formateada: '0,05 €'.

        Con carrera coincide con la suya: las tarifas no cambian a mitad de
        carrera (el Administrador no es accesible con una en curso).
        """
        tarifas = self.servicio.tarifas()
        return formato_euros(tarifas.parado if estado is Estado.PARADO else tarifas.en_movimiento)

    def _montar_visor(self, padre: tk.Frame) -> None:
        """El visor negro: lámparas, estado y tarifa, y el importe (a la derecha; en vertical, debajo)."""
        visor = tk.Frame(
            padre, bg=estilo.VISOR_FONDO, height=estilo.VISOR,
            highlightthickness=3, highlightbackground=estilo.VISOR_BORDE,
        )
        visor.pack(fill=tk.X)
        visor.pack_propagate(False)
        margen = estilo.px(32)

        if estilo.VERTICAL_ACTIVA:
            izquierda = tk.Frame(visor, bg=estilo.VISOR_FONDO)
            izquierda.pack(fill=tk.X, padx=margen, pady=(estilo.px(24), 0))
            lamparas = tk.Frame(izquierda, bg=estilo.VISOR_FONDO)
            lamparas.pack(fill=tk.X)
        else:
            izquierda = tk.Frame(visor, bg=estilo.VISOR_FONDO, width=estilo.px(300))
            izquierda.pack(side=tk.LEFT, fill=tk.Y, padx=margen, pady=margen)
            izquierda.pack_propagate(False)
            lamparas = izquierda
        self.lampara_ocupado = self._lampara(lamparas, "OCUPADO")
        self.lampara_libre = self._lampara(lamparas, "LIBRE")
        # Con ajuste de línea: «CARRERA FINALIZADA» no cabe en 300 px a 34 px.
        self.estado = tk.Label(
            izquierda, font=estilo.FUENTE_ESTADO, bg=estilo.VISOR_FONDO, anchor=tk.W, justify=tk.LEFT,
        )
        self.ajustar_al_ancho(self.estado)
        self.estado.pack(fill=tk.X, pady=(estilo.px(12), 0))
        self.tarifa = tk.Label(
            izquierda, font=estilo.FUENTE_TARIFA, bg=estilo.VISOR_FONDO, anchor=tk.W, justify=tk.LEFT,
        )
        self.ajustar_al_ancho(self.tarifa)
        self.tarifa.pack(fill=tk.X)

        derecha = tk.Frame(visor, bg=estilo.VISOR_FONDO)
        if estilo.VERTICAL_ACTIVA:
            derecha.pack(expand=True)
        else:
            derecha.pack(side=tk.RIGHT, padx=margen)
        self.visor = Visor(derecha)
        self.visor.pack()
        self.rotulo = tk.Label(
            derecha, font=estilo.FUENTE_ETIQUETA, bg=estilo.VISOR_FONDO, fg=estilo.TEXTO_ROTULO
        )
        self.rotulo.pack(anchor=tk.E, pady=(estilo.px(16), 0))

    def _lampara(self, padre: tk.Frame, texto: str) -> tk.Label:
        """Una lámpara: apilada en horizontal; en vertical, una junto a otra en su fila."""
        marco = tk.Frame(padre, height=estilo.LAMPARA)
        if estilo.VERTICAL_ACTIVA:
            hueco = estilo.SEPARACION if padre.pack_slaves() else 0
            marco.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(hueco, 0))
        else:
            marco.pack(fill=tk.X, pady=(0, estilo.px(20)))
        marco.pack_propagate(False)
        lampara = tk.Label(marco, text=texto, font=estilo.FUENTE_LAMPARA)
        lampara.pack(fill=tk.BOTH, expand=True)
        return lampara

    def _montar_teclas(self, padre: tk.Frame) -> None:
        """Las teclas bajo el visor; `_pintar` enseña las del estado actual."""
        teclas = tk.Frame(padre, bg=estilo.FONDO)
        teclas.pack(fill=tk.BOTH, expand=True, pady=(estilo.SEPARACION, 0))
        alto = estilo.TECLA_TAXIMETRO
        self.tecla_cambiar = Tecla(teclas, "PARAR", self.cambiar_estado, variante=estilo.GRIS, alto=alto)
        self.tecla_finalizar = Tecla(
            teclas, "FINALIZAR", self.pedir_finalizar, variante=estilo.ROJA, alto=alto,
            subtitulo="Termina y muestra el total",
        )
        self.tecla_iniciar = Tecla(teclas, "INICIAR CARRERA", self.iniciar, variante=estilo.VERDE, alto=alto)
        self.tecla_cerrar = Tecla(
            teclas, "CERRAR", lambda: self.app.cerrar("ventana_con_carrera"),
            variante=estilo.GRIS, alto=alto,
            subtitulo="Sale del programa",
        )

    def _montar_datos(self, principal: tk.Frame, lateral: tk.Frame) -> None:
        """Nº de carrera, tiempo e inicio: en el lateral; en vertical, en una fila bajo el visor."""
        padre = lateral
        if estilo.VERTICAL_ACTIVA:
            padre = tk.Frame(principal, bg=estilo.FONDO, height=estilo.DATOS)
            padre.pack(fill=tk.X, pady=(estilo.SEPARACION, 0))
            padre.pack_propagate(False)
        self.dato_carrera = self._dato(padre, "Carrera")
        self.dato_tiempo = self._dato(padre, "Tiempo")
        self.dato_inicio = self._dato(padre, "Inicio")

    def _montar_lateral(self, lateral: tk.Frame) -> None:
        """Ayuda y Volver, abajo. `_pintar` decide cuándo se ve Volver y dónde se pone."""
        self.tecla_ayuda = self.tecla_lateral(lateral, "Ayuda", self.abrir_ayuda)
        if not estilo.VERTICAL_ACTIVA:
            self.tecla_ayuda.pack(side=tk.BOTTOM, fill=tk.X)
        self.tecla_volver = self.tecla_lateral(lateral, "Volver", self.volver)

    def _dato(self, padre: tk.Frame, etiqueta: str) -> tk.Label:
        """Una cajita con la etiqueta encima del dato; en vertical se reparten la fila."""
        caja = tk.Frame(padre, bg=estilo.PANEL, highlightthickness=2, highlightbackground=estilo.PANEL_BORDE)
        vertical = estilo.VERTICAL_ACTIVA
        if vertical:
            hueco = estilo.SEPARACION if padre.pack_slaves() else 0
            caja.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(hueco, 0))
        else:
            caja.pack(fill=tk.X, pady=(0, estilo.SEPARACION))
        lado, arriba, abajo = (estilo.px(8), estilo.px(6), estilo.px(6)) if vertical else (
            estilo.px(16), estilo.px(12), estilo.px(12))
        tk.Label(caja, text=etiqueta, font=estilo.FUENTE_ETIQUETA, bg=estilo.PANEL,
                 fg=estilo.TEXTO_ETIQUETA, anchor=tk.W).pack(fill=tk.X, padx=lado, pady=(arriba, 0))
        valor = tk.Label(caja, font=estilo.FUENTE_DATO, bg=estilo.PANEL, fg=estilo.TEXTO, anchor=tk.W)
        valor.pack(fill=tk.X, padx=lado, pady=(0, abajo))
        return valor

    def _montar_ayuda(self) -> None:
        """El panel de ayuda: tapa la pantalla hasta que se pulsa Cerrar."""
        self._ayuda = tk.Frame(self, bg=estilo.VISOR_FONDO)
        panel = tk.Frame(self._ayuda, bg=estilo.PANEL, highlightthickness=3,
                         highlightbackground=estilo.CAMPO_BORDE, width=estilo.AYUDA_ANCHO)
        panel.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=estilo.AYUDA_ANCHO)
        texto = {"bg": estilo.PANEL, "fg": estilo.TEXTO, "anchor": tk.W, "justify": tk.LEFT}
        margen = estilo.px(40)
        self._etiqueta_de_ayuda(panel, "Ayuda", estilo.FUENTE_TITULO, texto).pack(
            fill=tk.X, padx=margen, pady=(margen, estilo.px(20)))
        for linea in (
            "INICIAR CARRERA: empieza una carrera nueva, en movimiento.",
            "PARAR / ARRANCAR: cambia la tarifa cuando el taxi se detiene o vuelve a moverse.",
            "FINALIZAR: termina la carrera y muestra el total a cobrar.",
        ):
            self._etiqueta_de_ayuda(panel, linea, estilo.FUENTE_TEXTO, texto).pack(
                fill=tk.X, padx=margen, pady=(0, estilo.px(12)))
        self._tarifas_ayuda = self._etiqueta_de_ayuda(
            panel, "", estilo.FUENTE_TEXTO, {**texto, "fg": estilo.TEXTO_SECUNDARIO})
        self._tarifas_ayuda.pack(fill=tk.X, padx=margen, pady=(0, estilo.px(20)))
        self.tecla_cerrar_ayuda = Tecla(
            panel, "Cerrar", self.cerrar_ayuda, variante=estilo.GRIS, alto=estilo.TECLA_LATERAL,
            fuente=estilo.FUENTE_TECLA_LATERAL,
        )
        self.tecla_cerrar_ayuda.pack(fill=tk.X, padx=margen, pady=(0, margen))

    def _etiqueta_de_ayuda(self, panel: tk.Frame, texto: str, fuente, estilos: dict) -> tk.Label:
        """Una línea del panel de ayuda, que se parte sola si no cabe."""
        etiqueta = tk.Label(panel, text=texto, font=fuente, **estilos)
        self.ajustar_al_ancho(etiqueta)
        return etiqueta


def tiempo(segundos: float) -> str:
    """Duración como en un cronómetro: 252 → '00:04:12'."""
    total = int(segundos)
    return f"{total // 3600:02d}:{total // 60 % 60:02d}:{total % 60:02d}"
