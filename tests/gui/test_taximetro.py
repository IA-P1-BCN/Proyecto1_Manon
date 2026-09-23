"""Tests de `taximetro.gui.taximetro.PantallaTaximetro` (T9.13).

Pantallas 3 y 4 de `docs/diseno-interfaz-fase3.md`: el taxímetro en LIBRE y
en OCUPADO. El reloj y el calendario son falsos y se adelantan juntos; el
refresco de 200 ms se deja correr con `procesar()`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from taximetro.gui import estilo
from taximetro.gui.app import App
from taximetro.gui.inicio import Inicio
from taximetro.gui.taximetro import NO_GUARDADA, REFRESCO_MS, PantallaTaximetro, tiempo
from taximetro.historial import Historial
from taximetro.servicio_taximetro import Estado, ServicioTaximetro
from taximetro.taximetro import Taximetro


@pytest.fixture
def pasar(reloj, calendario):
    """Adelanta a la vez el reloj del importe y el calendario del lateral."""

    def _pasar(segundos: float) -> None:
        reloj.avanzar(segundos)
        calendario.avanzar(segundos)

    return _pasar


@pytest.fixture
def pantalla(app: App) -> PantallaTaximetro:
    return app.mostrar(PantallaTaximetro)


def visible(widget) -> bool:
    """True si el widget está colocado en la pantalla (pack, grid o place)."""
    return widget.winfo_manager() != ""


def lampara_encendida(pantalla: PantallaTaximetro) -> str:
    if pantalla.lampara_ocupado.cget("bg") == estilo.OCUPADO_ENCENDIDA.fondo:
        assert pantalla.lampara_libre.cget("bg") == estilo.LIBRE_APAGADA.fondo
        return "OCUPADO"
    assert pantalla.lampara_libre.cget("bg") == estilo.LIBRE_ENCENDIDA.fondo
    assert pantalla.lampara_ocupado.cget("bg") == estilo.OCUPADO_APAGADA.fondo
    return "LIBRE"


class TestLibreAlEntrar:
    """Primer arranque: visor a 0,00, LIBRE encendida, INICIAR CARRERA."""

    def test_libre_a_cero(self, pantalla: PantallaTaximetro) -> None:
        assert lampara_encendida(pantalla) == "LIBRE"
        assert pantalla.visor.texto == "0,00 €"
        assert pantalla.rotulo.cget("text") == "IMPORTE"
        assert pantalla.dato_carrera.cget("text") == "—"

    def test_solo_iniciar_carrera_con_volver_y_ayuda(self, pantalla: PantallaTaximetro) -> None:
        assert visible(pantalla.tecla_iniciar)
        assert not visible(pantalla.tecla_cambiar)
        assert not visible(pantalla.tecla_finalizar)
        assert visible(pantalla.tecla_volver) and visible(pantalla.tecla_ayuda)

    def test_iniciar_anuncia_la_tarifa_en_movimiento(self, pantalla: PantallaTaximetro) -> None:
        assert pantalla.tecla_iniciar.subtitulo == "Empieza en movimiento · 0,05 €/s"

    def test_con_una_carrera_en_curso_entra_ocupado(self, app: App) -> None:
        app.servicio.iniciar_carrera()
        assert lampara_encendida(app.mostrar(PantallaTaximetro)) == "OCUPADO"


class TestOcupado:
    """US-01 y US-02 en la pantalla: iniciar y cambiar de estado."""

    def test_iniciar_pasa_a_ocupado_en_movimiento(self, pantalla: PantallaTaximetro) -> None:
        pantalla.tecla_iniciar.invoke()
        assert lampara_encendida(pantalla) == "OCUPADO"
        assert pantalla.estado.cget("text") == "EN MOVIMIENTO"
        assert pantalla.estado.cget("fg") == estilo.LED_VERDE
        assert pantalla.tarifa.cget("text") == "0,05 €/s"
        assert pantalla.dato_carrera.cget("text") == "Nº 1"
        assert pantalla.dato_inicio.cget("text") == "08:00"

    def test_teclas_parar_y_finalizar_sin_volver(self, pantalla: PantallaTaximetro) -> None:
        pantalla.tecla_iniciar.invoke()
        assert pantalla.tecla_cambiar.titulo == "PARAR"
        assert visible(pantalla.tecla_cambiar) and visible(pantalla.tecla_finalizar)
        assert not visible(pantalla.tecla_iniciar)
        # Sin Volver con carrera: al Administrador (tarifas) no se llega a mitad de carrera.
        assert not visible(pantalla.tecla_volver)

    def test_parar_y_arrancar(self, pantalla: PantallaTaximetro) -> None:
        pantalla.tecla_iniciar.invoke()
        pantalla.tecla_cambiar.invoke()
        assert pantalla.servicio.estado_actual().estado is Estado.PARADO
        assert pantalla.estado.cget("text") == "PARADO"
        assert pantalla.estado.cget("fg") == estilo.LED_AMBAR
        assert pantalla.tarifa.cget("text") == "0,02 €/s"
        assert pantalla.tecla_cambiar.titulo == "ARRANCAR"
        pantalla.tecla_cambiar.invoke()
        assert pantalla.tecla_cambiar.titulo == "PARAR"

    def test_cambiar_sin_carrera_no_hace_nada(self, pantalla: PantallaTaximetro) -> None:
        pantalla.cambiar_estado()
        assert pantalla.servicio.estado_actual() is None


class TestRefresco:
    """El importe y el tiempo se actualizan solos cada 200 ms."""

    def test_el_visor_y_el_tiempo_avanzan_solos(
        self, pantalla: PantallaTaximetro, pasar, procesar
    ) -> None:
        pantalla.tecla_iniciar.invoke()
        pasar(10)
        procesar(REFRESCO_MS / 1000 * 2)
        assert pantalla.visor.texto == "0,50 €"
        assert pantalla.dato_tiempo.cget("text") == "00:00:10"

    def test_una_pulsacion_repinta_sin_esperar(self, pantalla: PantallaTaximetro, pasar) -> None:
        pantalla.tecla_iniciar.invoke()
        pasar(10)
        pantalla.tecla_cambiar.invoke()
        assert pantalla.visor.texto == "0,50 €"

    def test_un_solo_temporizador_aunque_se_encadenen_carreras(
        self, pantalla: PantallaTaximetro, procesar
    ) -> None:
        for _ in range(3):
            pantalla.tecla_iniciar.invoke()
            pantalla.tecla_cambiar.invoke()
            pantalla.tecla_finalizar.invoke()
        pantalla.tecla_iniciar.invoke()
        procesar(0.05)
        assert len(pantalla._temporizadores) == 1

    def test_libre_no_refresca(self, pantalla: PantallaTaximetro, procesar) -> None:
        pantalla.tecla_iniciar.invoke()
        pantalla.tecla_finalizar.invoke()
        procesar(REFRESCO_MS / 1000 * 2)
        assert pantalla._temporizadores == set()


class TestFinalizar:
    """US-03: el total se queda en el visor hasta la siguiente carrera."""

    def test_carrera_finalizada_cabe_en_su_columna(self, pantalla: PantallaTaximetro) -> None:
        # Pasa a dos líneas en vez de cortarse contra el visor.
        pantalla.tecla_iniciar.invoke()
        pantalla.tecla_finalizar.invoke()
        assert int(pantalla.estado.cget("wraplength")) == 300

    def test_deja_el_total_a_cobrar(self, pantalla: PantallaTaximetro, pasar) -> None:
        pantalla.tecla_iniciar.invoke()
        pasar(60)
        pantalla.tecla_finalizar.invoke()
        assert lampara_encendida(pantalla) == "LIBRE"
        assert pantalla.visor.texto == "3,00 €"
        assert pantalla.rotulo.cget("text") == "TOTAL A COBRAR"
        assert pantalla.estado.cget("text") == "CARRERA FINALIZADA"
        assert pantalla.tarifa.cget("text") == "Cobrar al pasajero"

    def test_el_lateral_sigue_con_la_carrera_terminada(
        self, pantalla: PantallaTaximetro, pasar
    ) -> None:
        pantalla.tecla_iniciar.invoke()
        pasar(252)
        pantalla.tecla_finalizar.invoke()
        pasar(600)
        assert pantalla.dato_carrera.cget("text") == "Nº 1"
        assert pantalla.dato_tiempo.cget("text") == "00:04:12"

    def test_el_total_no_sigue_contando(
        self, pantalla: PantallaTaximetro, pasar, procesar
    ) -> None:
        pantalla.tecla_iniciar.invoke()
        pasar(60)
        pantalla.tecla_finalizar.invoke()
        pasar(60)
        procesar(REFRESCO_MS / 1000 * 2)
        assert pantalla.visor.texto == "3,00 €"

    def test_vuelve_a_iniciar_carrera(self, pantalla: PantallaTaximetro, pasar) -> None:
        pantalla.tecla_iniciar.invoke()
        pasar(60)
        pantalla.tecla_finalizar.invoke()
        assert visible(pantalla.tecla_iniciar) and visible(pantalla.tecla_volver)
        pantalla.tecla_iniciar.invoke()
        assert pantalla.dato_carrera.cget("text") == "Nº 2"
        assert pantalla.visor.texto == "0,00 €"
        assert pantalla.rotulo.cget("text") == "IMPORTE"

    def test_si_el_historico_no_se_guarda_avisa_y_cobra_igual(
        self, raiz, tmp_path: Path, reloj, calendario, pasar
    ) -> None:
        (tmp_path / "data").write_text("", encoding="utf-8")  # bloquea la carpeta
        historial = Historial(tmp_path / "data" / "historial.csv")
        servicio = ServicioTaximetro(Taximetro(historial=historial, reloj=reloj, calendario=calendario))
        pantalla = App(servicio, raiz=raiz).mostrar(PantallaTaximetro)
        pantalla.tecla_iniciar.invoke()
        pasar(60)
        pantalla.tecla_finalizar.invoke()
        assert pantalla.visor.texto == "3,00 €"
        assert pantalla.tarifa.cget("text") == NO_GUARDADA


class TestLateral:
    def test_volver_va_encima_de_ayuda_y_separado(self, pantalla: PantallaTaximetro) -> None:
        # Como en la maqueta: Volver arriba, Ayuda abajo, 24 px entre ellas.
        # La ventana se muestra: oculta no calcula posiciones.
        pantalla.app.raiz.geometry(f"{estilo.ANCHO}x{estilo.ALTO}+0+0")
        pantalla.app.raiz.deiconify()
        pantalla.update()
        volver, ayuda = pantalla.tecla_volver, pantalla.tecla_ayuda
        hueco = ayuda.winfo_y() - (volver.winfo_y() + volver.winfo_height())
        assert hueco == estilo.SEPARACION

    def test_volver_a_inicio(self, app: App, pantalla: PantallaTaximetro) -> None:
        pantalla.tecla_volver.invoke()
        assert isinstance(app.pantalla, Inicio)

    def test_volver_y_entrar_otra_vez_arranca_a_cero(self, app: App, pasar) -> None:
        pantalla = app.mostrar(PantallaTaximetro)
        pantalla.tecla_iniciar.invoke()
        pasar(60)
        pantalla.tecla_finalizar.invoke()
        pantalla.tecla_volver.invoke()
        assert app.mostrar(PantallaTaximetro).visor.texto == "0,00 €"

    def test_ayuda_se_abre_y_se_cierra(self, pantalla: PantallaTaximetro) -> None:
        pantalla.tecla_ayuda.invoke()
        assert pantalla._ayuda.winfo_manager() == "place"
        assert pantalla._tarifas_ayuda.cget("text") == (
            "Tarifas: parado 0,02 €/s · en movimiento 0,05 €/s"
        )
        pantalla.tecla_cerrar_ayuda.invoke()
        assert not visible(pantalla._ayuda)


@pytest.mark.parametrize(
    "segundos, esperado",
    [(0, "00:00:00"), (9.9, "00:00:09"), (252, "00:04:12"), (3600, "01:00:00"), (20000, "05:33:20")],
)
def test_tiempo_como_un_cronometro(segundos: float, esperado: str) -> None:
    assert tiempo(segundos) == esperado
