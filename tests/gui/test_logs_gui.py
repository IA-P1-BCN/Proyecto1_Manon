"""Los logs de operación desde la interfaz gráfica (US-06 en la Fase 3, T9.9).

Mismos nombres de evento que el CLI, para que un `grep` del equipo técnico
sirva para las dos interfaces. Se leen con el fixture `eventos` (caplog).
"""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path

import pytest

from taximetro.gui.administrador import Administrador
from taximetro.gui.app import ERROR_INESPERADO, App
from taximetro.gui.contrasena import Contrasena
from taximetro.gui.historico import Historico
from taximetro.gui.tarifas import CambiarTarifas
from taximetro.gui.taximetro import PantallaTaximetro
from taximetro.historial import Historial
from taximetro.servicio_taximetro import ServicioTaximetro
from taximetro.taximetro import Taximetro


def aspa(app: App) -> None:
    app.raiz.tk.call(app.raiz.protocol("WM_DELETE_WINDOW"))


class TestArranqueYCierre:
    def test_arranque_con_las_tarifas(self, eventos, app: App) -> None:
        app.raiz.after(0, app.cerrar)
        app.ejecutar()
        assert "aplicacion_iniciada parado=0.02 movimiento=0.05" in eventos()

    @pytest.mark.parametrize(
        "cerrar, motivo",
        [
            (lambda app: app.pantalla.salir.invoke(), "salir"),
            (aspa, "ventana"),
        ],
        ids=["tecla-salir", "aspa-sin-carrera"],
    )
    def test_cierre_con_su_motivo(self, eventos, app: App, cerrar, motivo: str) -> None:
        cerrar(app)
        assert f"aplicacion_cerrada motivo={motivo}" in eventos()

    def test_cerrar_tras_finalizar_y_salir(self, eventos, app: App) -> None:
        pantalla = app.mostrar(PantallaTaximetro)
        pantalla.iniciar()
        aspa(app)
        pantalla.confirmacion.si.invoke()
        pantalla.tecla_cerrar.invoke()
        assert "aplicacion_cerrada motivo=ventana_con_carrera" in eventos()


class TestPerfil:
    def test_conductor(self, eventos, app: App) -> None:
        app.pantalla.conductor.invoke()
        assert "perfil_elegido perfil=conductor" in eventos()

    def test_administrador(self, eventos, app: App) -> None:
        app.pantalla.administrador.invoke()
        assert "perfil_elegido perfil=administrador" in eventos()


class TestSalirConCarrera:
    """El ✕ con carrera: los mismos eventos que el Ctrl+C del CLI."""

    def test_confirmada(self, eventos, app: App) -> None:
        pantalla = app.mostrar(PantallaTaximetro)
        pantalla.iniciar()
        aspa(app)
        pantalla.confirmacion.si.invoke()
        assert ["salida_solicitada carrera=1", "salida_confirmada carrera=1"] == [
            e for e in eventos() if e.startswith("salida_")
        ]

    def test_cancelada(self, eventos, app: App) -> None:
        pantalla = app.mostrar(PantallaTaximetro)
        pantalla.iniciar()
        aspa(app)
        aspa(app)  # el segundo ✕ cuenta como NO
        assert ["salida_solicitada carrera=1", "salida_cancelada carrera=1"] == [
            e for e in eventos() if e.startswith("salida_")
        ]

    def test_el_no_de_finalizar_no_es_una_salida(self, eventos, app: App) -> None:
        pantalla = app.mostrar(PantallaTaximetro)
        pantalla.iniciar()
        pantalla.pedir_finalizar()
        pantalla.confirmacion.no.invoke()
        assert not [e for e in eventos() if e.startswith("salida_")]


class TestTarifas:
    def teclear(self, pantalla: CambiarTarifas, parado: str) -> None:
        pantalla.campos["parado"].delete(0, tk.END)
        pantalla.campos["parado"].insert(0, parado)
        pantalla.guardar()

    def test_no_numerica(self, eventos, app: App) -> None:
        self.teclear(app.mostrar(CambiarTarifas), "abc")
        assert eventos(logging.WARNING) == ["tarifa_rechazada tecleado='abc' motivo=no_numerica"]

    def test_no_valida(self, eventos, app: App) -> None:
        self.teclear(app.mostrar(CambiarTarifas), "0,06")
        assert eventos(logging.WARNING) == [
            "tarifa_rechazada parado=0.06 movimiento=0.05 "
            "motivo='La tarifa parado no puede ser mayor que la de en movimiento.'"
        ]


class TestHistorico:
    def test_consultado(self, eventos, raiz, tmp_path: Path, reloj, calendario) -> None:
        servicio = ServicioTaximetro(
            Taximetro(historial=Historial(tmp_path / "h.csv"), reloj=reloj, calendario=calendario)
        )
        App(servicio, raiz=raiz).mostrar(Historico)
        # Igual que en el CLI: con el día vacío, el total es el entero 0.
        assert "historico_consultado fecha=2025-06-01 carreras=0 total=0" in eventos()

    def test_ilegible_es_error_con_traza(self, eventos, caplog, raiz) -> None:
        class Ilegible:
            def ultimo_numero(self) -> int:
                return 0

            def resumen_del_dia(self, fecha):
                raise PermissionError("sin permiso")

        App(ServicioTaximetro(Taximetro(historial=Ilegible())), raiz=raiz).mostrar(Historico)
        assert eventos(logging.ERROR) == ["historico_ilegible"]
        assert any(r.exc_info for r in caplog.records if r.getMessage() == "historico_ilegible")


class TestErroresEnCallbacks:
    """tkinter se traga los errores de botones y temporizadores; aquí no se pierden."""

    def fallar(self) -> None:
        raise RuntimeError("fallo al pintar")

    def test_van_al_log_con_su_traza(self, eventos, caplog, app: App, procesar) -> None:
        app.raiz.after(0, self.fallar)  # pasa por el bucle de Tk, como un botón de verdad
        procesar(0.05)
        assert eventos(logging.ERROR) == ["error_inesperado"]
        registro = next(r for r in caplog.records if r.getMessage() == "error_inesperado")
        assert registro.exc_info[0] is RuntimeError

    def test_el_conductor_ve_un_aviso_y_el_programa_sigue(self, app: App, procesar) -> None:
        pantalla = app.mostrar(PantallaTaximetro)
        pantalla.iniciar()
        app.raiz.after(0, self.fallar)
        procesar(0.05)
        assert app.texto_aviso.cget("text") == ERROR_INESPERADO
        assert app._aviso.winfo_manager() == "place"
        app.cerrar_aviso.invoke()
        assert app._aviso.winfo_manager() == ""
        assert app.servicio.estado_actual() is not None  # la carrera sigue

    def test_con_la_ventana_ya_cerrada_basta_el_log(self, eventos, app: App) -> None:
        app.cerrar()
        app.error_en_callback(RuntimeError, RuntimeError("tarde"), None)
        assert "error_inesperado" in eventos(logging.ERROR)


def test_la_contrasena_tecleada_nunca_va_al_log(caplog, eventos, raiz) -> None:
    class AuthFalso:
        def comprobar(self, contrasena: str) -> bool:
            return contrasena == "clave-de-prueba"

    app = App(ServicioTaximetro(Taximetro(), AuthFalso()), raiz=raiz)
    pantalla = app.mostrar(Contrasena)
    for tecleada in ("una-errata", "clave-de-prueba"):
        pantalla.campo.insert(0, tecleada)
        pantalla.entrar()
    assert isinstance(app.pantalla, Administrador)
    assert "una-errata" not in caplog.text and "clave-de-prueba" not in caplog.text
