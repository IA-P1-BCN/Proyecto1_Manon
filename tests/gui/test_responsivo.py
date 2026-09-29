"""La interfaz se adapta al tamaño de la ventana, sin perder nada por el camino.

Dos partes. La primera prueba las reglas de `estilo` (qué disposición y qué
escala toca a cada tamaño, y que los mínimos de 88 px y 24 px no se rompen a
ninguna escala). La segunda prueba `App`: al cambiar el tamaño se rehace la
pantalla, y lo que había en ella (una carrera, el importe congelado, un panel
abierto, lo tecleado) sigue ahí. Que nada se recorte a cada tamaño lo prueba
`test_cabe.py`.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from types import SimpleNamespace

import pytest

from taximetro.application.servicio_taximetro import ServicioTaximetro
from taximetro.application.taximetro import Taximetro
from taximetro.infrastructure.historial import Historial
from taximetro.interfaces.gui import estilo
from taximetro.interfaces.gui.administrador import Administrador
from taximetro.interfaces.gui.app import REAJUSTE_MS, App
from taximetro.interfaces.gui.contrasena import Contrasena
from taximetro.interfaces.gui.historico import Historico
from taximetro.interfaces.gui.inicio import Inicio
from taximetro.interfaces.gui.tarifas import CambiarTarifas
from taximetro.interfaces.gui.tecla import Tecla
from taximetro.interfaces.gui.taximetro import REFRESCO_MS, PantallaTaximetro

HORIZONTAL_GRANDE = (1920, 1080)
VERTICAL = (720, 1280)
TAMANOS = [
    (960, 640), (1024, 660), (1280, 800), (1600, 1000), HORIZONTAL_GRANDE,
    (560, 1000), (640, 1100), (720, 1280), (800, 1300),
]


class TestDecidir:
    """Qué disposición y qué escala toca a cada tamaño de ventana."""

    def test_la_tablet_es_la_referencia(self) -> None:
        assert estilo.decidir(1280, 800) == (estilo.HORIZONTAL, 1.0)

    def test_una_ventana_mayor_escala_hacia_arriba(self) -> None:
        disposicion, escala = estilo.decidir(*HORIZONTAL_GRANDE)
        assert (disposicion, escala > 1) == (estilo.HORIZONTAL, True)

    def test_una_ventana_alta_y_estrecha_es_vertical(self) -> None:
        assert estilo.decidir(*VERTICAL) == (estilo.VERTICAL, 1.0)
        assert estilo.decidir(800, 1300)[0] == estilo.VERTICAL

    def test_en_un_empate_gana_la_horizontal(self) -> None:
        assert estilo.decidir(1000, 1000)[0] == estilo.HORIZONTAL

    def test_la_escala_se_redondea_hacia_abajo_para_que_nunca_sobre_contenido(self) -> None:
        # 1000 / 1280 = 0,78125: a 0,80 el contenido no cabría.
        assert estilo.decidir(1000, 800)[1] == 0.75

    def test_la_escala_queda_entre_el_minimo_y_el_maximo(self) -> None:
        assert estilo.decidir(100, 100)[1] == estilo.ESCALA_MIN
        assert estilo.decidir(20000, 20000)[1] == estilo.ESCALA_MAX

    @pytest.mark.parametrize("disposicion", [estilo.HORIZONTAL, estilo.VERTICAL])
    def test_el_tamano_minimo_de_cada_disposicion_es_valido_para_ella(self, disposicion: str) -> None:
        ancho, alto = estilo.TAMANO_MIN[disposicion]
        assert estilo.decidir(ancho, alto)[0] == disposicion


class TestAplicar:
    """`aplicar()` recalcula las medidas y las fuentes."""

    def test_devuelve_si_algo_cambio(self) -> None:
        assert estilo.aplicar(*HORIZONTAL_GRANDE) is True
        assert estilo.aplicar(*HORIZONTAL_GRANDE) is False, "misma escala: no hay nada que rehacer"
        assert estilo.aplicar(*VERTICAL) is True

    def test_forzar_recalcula_aunque_no_cambie_el_tamano(self) -> None:
        assert estilo.aplicar(estilo.ANCHO, estilo.ALTO) is False
        assert estilo.aplicar(estilo.ANCHO, estilo.ALTO, forzar=True) is True

    def test_a_la_escala_de_referencia_no_cambia_ninguna_medida(self) -> None:
        estilo.aplicar(*VERTICAL)
        estilo.aplicar(estilo.ANCHO, estilo.ALTO)
        assert (estilo.MARGEN, estilo.LATERAL, estilo.VISOR, estilo.TEJA, estilo.FRANJA) == (
            24, 240, 420, 620, 108,
        )
        assert estilo.FUENTE_TITULO[1] == -48

    def test_las_medidas_y_las_fuentes_crecen_con_la_ventana(self) -> None:
        pequena = (estilo.VISOR, estilo.FUENTE_TITULO[1])
        estilo.aplicar(*HORIZONTAL_GRANDE)
        assert estilo.VISOR > pequena[0]
        assert -estilo.FUENTE_TITULO[1] > -pequena[1]

    def test_px_escala_un_valor_de_la_referencia(self) -> None:
        estilo.aplicar(1600, 1000)
        assert estilo.px(100) == 125
        assert estilo.px(0) == 1, "nunca menos de 1 px"

    @pytest.mark.parametrize("tamano", TAMANOS, ids=lambda t: f"{t[0]}x{t[1]}")
    def test_ninguna_escala_rompe_los_minimos_tactiles(self, tamano: tuple[int, int]) -> None:
        estilo.aplicar(*tamano)
        for nombre in ("TECLA_LATERAL", "TECLA_CONFIRMAR", "TECLA_ENTRAR", "TECLA_GUARDAR", "CAMPO",
                       "TEJA", "TEJA_PRINCIPAL", "TEJA_SECUNDARIA", "TECLA_TAXIMETRO"):
            assert getattr(estilo, nombre) >= estilo.ZONA_TACTIL_MIN, nombre
        assert estilo.TECLA_PRINCIPAL_MIN >= 120
        assert estilo.TECLA_TAXIMETRO >= 120
        assert estilo.SEPARACION >= 24

    @pytest.mark.parametrize("tamano", TAMANOS, ids=lambda t: f"{t[0]}x{t[1]}")
    def test_ninguna_escala_baja_el_texto_de_24_px(self, tamano: tuple[int, int]) -> None:
        estilo.aplicar(*tamano)
        fuentes = {n: v for n, v in vars(estilo).items() if n.startswith("FUENTE_")}
        assert fuentes
        for nombre, (_, tamano_px, _) in fuentes.items():
            assert -tamano_px >= estilo.TEXTO_MIN, nombre

    def test_en_vertical_el_lateral_es_una_fila_con_una_tecla(self) -> None:
        estilo.aplicar(*VERTICAL)
        assert estilo.VERTICAL_ACTIVA
        assert estilo.LATERAL >= estilo.TECLA_LATERAL

    def test_el_lateral_horizontal_no_se_estrecha_por_debajo_de_su_minimo(self) -> None:
        estilo.aplicar(960, 640)
        assert estilo.LATERAL >= estilo.LATERAL_MIN


class TestValoresPorDefectoQueSiguenALaVentana:
    """Un valor por defecto se evalúa al importar el módulo: no puede quedarse con la escala vieja."""

    def test_una_tecla_sin_alto_toma_el_de_la_escala_actual(self, raiz: tk.Toplevel) -> None:
        estilo.aplicar(*HORIZONTAL_GRANDE)
        tecla = Tecla(raiz, "X", lambda: None)
        assert int(tecla.cget("height")) == estilo.TECLA_PRINCIPAL_MIN
        assert estilo.TECLA_PRINCIPAL_MIN > 120

    def test_una_tecla_sin_fuente_toma_la_de_la_escala_actual(self, raiz: tk.Toplevel) -> None:
        estilo.aplicar(*HORIZONTAL_GRANDE)
        tecla = Tecla(raiz, "X", lambda: None)
        assert tecla._fuentes["titulo"] == estilo.FUENTE_TECLA


class TestAdaptar:
    """`App.adaptar()` rehace la pantalla al nuevo tamaño."""

    def test_al_cambiar_de_disposicion_se_rehace_la_pantalla(self, app: App) -> None:
        anterior = app.pantalla
        app.adaptar(*VERTICAL)
        assert app.pantalla is not anterior
        assert isinstance(app.pantalla, Inicio), "la misma pantalla, montada de nuevo"
        assert estilo.VERTICAL_ACTIVA

    def test_la_pantalla_vieja_se_destruye(self, app: App) -> None:
        anterior = app.pantalla
        app.adaptar(*VERTICAL)
        assert not anterior.winfo_exists()

    def test_si_la_escala_no_cambia_no_se_rehace_nada(self, app: App) -> None:
        anterior = app.pantalla
        app.adaptar(estilo.ANCHO, estilo.ALTO)
        assert app.pantalla is anterior

    def test_una_ventana_sin_pintar_se_ignora(self, app: App) -> None:
        anterior = app.pantalla
        app.adaptar(1, 1)
        assert app.pantalla is anterior
        assert not estilo.VERTICAL_ACTIVA

    def test_el_tamano_minimo_de_la_ventana_sigue_a_la_disposicion(self, app: App) -> None:
        assert app.raiz.minsize() == estilo.TAMANO_MIN[estilo.HORIZONTAL]
        app.adaptar(*VERTICAL)
        assert app.raiz.minsize() == estilo.TAMANO_MIN[estilo.VERTICAL]
        app.adaptar(estilo.ANCHO, estilo.ALTO)
        assert app.raiz.minsize() == estilo.TAMANO_MIN[estilo.HORIZONTAL]

    @pytest.mark.parametrize(
        ("pantalla", "esperado"),
        [
            ((2560, 1440), (1280, 800)),  # un monitor grande: la tablet entera
            ((1366, 768), (1280, 668)),  # un portátil pequeño: cabe con la barra de tareas
            ((800, 1280), (720, 1180)),  # una tablet en vertical: la referencia vertical
        ],
        ids=["monitor", "portatil", "tablet-vertical"],
    )
    def test_una_ventana_propia_se_abre_a_un_tamano_que_cabe_en_la_pantalla(
        self, pantalla: tuple[int, int], esperado: tuple[int, int]
    ) -> None:
        # Sin crear un `Tk` más (ver `conftest.py`): una pantalla simulada basta.
        falsa = SimpleNamespace(
            raiz=SimpleNamespace(winfo_screenwidth=lambda: pantalla[0], winfo_screenheight=lambda: pantalla[1])
        )
        ancho, alto = App._tamano_inicial(falsa)
        assert (ancho, alto) == esperado
        disposicion, _ = estilo.decidir(ancho, alto)
        minimo_ancho, minimo_alto = estilo.TAMANO_MIN[disposicion]
        assert ancho >= minimo_ancho and alto >= minimo_alto, "cabe en la disposición que le toca"

    def test_cambiar_el_tamano_de_la_ventana_reajusta_cuando_deja_de_moverse(
        self, app: App, raiz: tk.Toplevel, procesar
    ) -> None:
        raiz.maxsize(4000, 4000)
        raiz.geometry("1600x1000+0+0")
        raiz.deiconify()
        procesar(0.02)
        assert estilo.ESCALA == 1.0, "aún esperando: no se reajusta en cada evento"
        procesar(REAJUSTE_MS / 1000 + 0.3)
        assert estilo.ESCALA == 1.25

    def test_varios_cambios_seguidos_solo_rehacen_una_vez(self, app: App, raiz: tk.Toplevel, procesar) -> None:
        raiz.maxsize(4000, 4000)
        raiz.deiconify()
        rehechas = []
        original = app._rehacer_pantalla
        app._rehacer_pantalla = lambda: (rehechas.append(1), original())
        for ancho in (1300, 1400, 1500, 1600):
            raiz.geometry(f"{ancho}x1000+0+0")
            raiz.update()
        procesar(REAJUSTE_MS / 1000 + 0.3)
        assert len(rehechas) == 1


class TestSeConservaLaCarreraAlCambiarDeTamano:
    """Cambiar de tamaño nunca toca la carrera, el importe ni lo que el conductor tiene delante."""

    @pytest.fixture
    def pantalla(self, app: App) -> PantallaTaximetro:
        return app.mostrar(PantallaTaximetro)

    def test_la_carrera_sigue_y_el_importe_no_se_altera(self, app: App, pantalla, reloj, calendario) -> None:
        pantalla.iniciar()
        reloj.avanzar(10)
        calendario.avanzar(10)
        app.adaptar(*VERTICAL)
        nueva = app.pantalla
        assert isinstance(nueva, PantallaTaximetro)
        assert nueva.visor.texto == "0,50 €"
        assert nueva.lampara_ocupado.cget("bg") == estilo.OCUPADO_ENCENDIDA.fondo

    def test_el_refresco_sigue_con_un_solo_temporizador(self, app: App, pantalla, procesar) -> None:
        pantalla.iniciar()
        app.adaptar(*VERTICAL)
        procesar(REFRESCO_MS / 1000 * 2)
        assert len(app.pantalla._temporizadores) == 1

    def test_el_importe_congelado_al_pedir_finalizar_no_cambia_al_redimensionar(
        self, app: App, pantalla, reloj, calendario
    ) -> None:
        pantalla.iniciar()
        reloj.avanzar(10)
        calendario.avanzar(10)
        pantalla.pedir_finalizar()  # congela 0,50 €
        reloj.avanzar(100)  # lo que se tarda en contestar, y en redimensionar
        calendario.avanzar(100)
        app.adaptar(*VERTICAL)
        nueva = app.pantalla
        assert nueva.confirmacion.abierta, "el panel SÍ / NO sigue abierto"
        assert nueva.confirmacion.importe.cget("text") == "0,50 €"
        nueva.confirmacion.si.invoke()
        assert nueva.visor.texto == "0,50 €", "SÍ cobra lo congelado, no lo que pasó después"

    def test_no_seguir_tras_redimensionar_sigue_funcionando(self, app: App, pantalla, reloj, calendario) -> None:
        pantalla.iniciar()
        pantalla.pedir_finalizar()
        app.adaptar(*VERTICAL)
        app.pantalla.confirmacion.no.invoke()
        assert not app.pantalla.confirmacion.abierta
        assert app.pantalla.servicio.estado_actual() is not None, "la carrera sigue"

    def test_el_panel_de_salida_tambien_se_conserva(self, app: App, pantalla) -> None:
        pantalla.iniciar()
        app.al_cerrar_ventana()  # la ✕ con carrera en curso
        app.adaptar(*VERTICAL)
        nueva = app.pantalla
        assert nueva.confirmacion.abierta
        assert "salir del programa" in nueva.confirmacion.pregunta.cget("text")
        nueva.confirmacion.si.invoke()
        assert nueva._saliendo
        assert nueva.tecla_cerrar.winfo_manager() != "", "solo queda CERRAR, como antes de redimensionar"

    def test_el_panel_de_ayuda_se_conserva(self, app: App, pantalla) -> None:
        pantalla.abrir_ayuda()
        app.adaptar(*VERTICAL)
        assert app.pantalla._ayuda.winfo_manager() == "place"

    def test_el_total_a_cobrar_se_conserva(self, app: App, pantalla, reloj, calendario) -> None:
        pantalla.iniciar()
        reloj.avanzar(60)
        calendario.avanzar(60)
        pantalla.tecla_finalizar.invoke()
        pantalla.confirmacion.si.invoke()
        app.adaptar(*HORIZONTAL_GRANDE)
        nueva = app.pantalla
        assert nueva.visor.texto == "3,00 €"
        assert nueva.rotulo.cget("text") == "TOTAL A COBRAR"

    def test_en_vertical_volver_solo_esta_sin_carrera(self, app: App, pantalla) -> None:
        app.adaptar(*VERTICAL)
        nueva = app.pantalla
        assert nueva.tecla_volver.winfo_manager() == "grid", "libre: Volver y Ayuda comparten la fila"
        nueva.iniciar()
        assert nueva.tecla_volver.winfo_manager() == "", "con carrera no se puede volver"
        assert nueva.tecla_ayuda.winfo_manager() == "grid"


class TestSeConservaLoTecleado:
    def test_la_contrasena_y_su_aviso(self, app: App) -> None:
        pantalla = app.mostrar(Contrasena)
        pantalla.campo.insert(0, "abc")
        pantalla.entrar()  # sin Auth: «No se puede comprobar…»
        aviso = pantalla.mensaje.cget("text")
        assert aviso
        app.adaptar(*VERTICAL)
        nueva = app.pantalla
        assert nueva.campo.get() == "abc"
        assert nueva.mensaje.cget("text") == aviso
        assert nueva._marco_campo.cget("highlightbackground") == estilo.CAMPO_BORDE_ERROR

    def test_las_tarifas_tecleadas_y_el_campo_culpable(self, app: App) -> None:
        pantalla = app.mostrar(CambiarTarifas)
        pantalla.campos["parado"].delete(0, tk.END)
        pantalla.campos["parado"].insert(0, "0,06")  # más que la de en movimiento: no vale
        pantalla.guardar()
        aviso = pantalla.mensaje.cget("text")
        app.adaptar(*VERTICAL)
        nueva = app.pantalla
        assert nueva.campos["parado"].get() == "0,06"
        assert nueva.mensaje.cget("text") == aviso
        assert nueva.mensaje.cget("fg") == estilo.MENSAJE_ERROR
        assert nueva._marcos["parado"].cget("highlightbackground") == estilo.CAMPO_BORDE_ERROR

    def test_las_tarifas_guardadas_y_su_mensaje_verde(self, app: App) -> None:
        pantalla = app.mostrar(CambiarTarifas)
        pantalla.campos["parado"].delete(0, tk.END)
        pantalla.campos["parado"].insert(0, "0,03")
        pantalla.guardar()
        app.adaptar(*VERTICAL)
        nueva = app.pantalla
        assert nueva.mensaje.cget("fg") == estilo.MENSAJE_OK
        assert "Tarifas guardadas" in nueva.mensaje.cget("text")
        assert "0,03" in nueva.vigentes.cget("text")

    def test_la_pagina_del_historico(self, raiz: tk.Toplevel, tmp_path: Path, reloj, calendario) -> None:
        servicio = ServicioTaximetro(
            Taximetro(historial=Historial(tmp_path / "h.csv"), reloj=reloj, calendario=calendario)
        )
        for _ in range(20):
            servicio.iniciar_carrera()
            servicio.finalizar_carrera()
        aplicacion = App(servicio, raiz=raiz)
        pantalla = aplicacion.mostrar(Historico)
        pantalla.bajar_filas()
        assert pantalla.desde == estilo.FILAS_HISTORICO
        aplicacion.adaptar(*HORIZONTAL_GRANDE)
        assert aplicacion.pantalla.desde == estilo.FILAS_HISTORICO, "sigue en la misma página"
        aplicacion.adaptar(*VERTICAL)
        nueva = aplicacion.pantalla
        assert nueva.desde <= len(nueva._carreras) - estilo.FILAS_HISTORICO, "sin pasar de la última fila"
        assert nueva.filas_visibles, "y se ven filas"

    def test_la_pantalla_de_administrador_no_tiene_nada_que_recordar(self, app: App) -> None:
        app.mostrar(Administrador)
        app.adaptar(*VERTICAL)
        assert isinstance(app.pantalla, Administrador)


class TestElAvisoDeErrorSeAdapta:
    def test_un_aviso_a_la_vista_se_vuelve_a_mostrar(self, app: App) -> None:
        app.avisar("Algo ha fallado.")
        app.adaptar(*VERTICAL)
        assert app.texto_aviso.cget("text") == "Algo ha fallado."
        assert app._aviso.winfo_manager() == "place"

    def test_sin_aviso_no_aparece_ninguno(self, app: App) -> None:
        app.adaptar(*VERTICAL)
        assert app._aviso is None
