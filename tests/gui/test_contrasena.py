"""Tests de `taximetro.gui.contrasena.Contrasena`: la pantalla 2 (US-08, T9.7)."""

from __future__ import annotations

import pytest

from taximetro.gui import estilo
from taximetro.gui.administrador import Administrador
from taximetro.gui.app import App
from taximetro.gui.contrasena import INCORRECTA, NO_DISPONIBLE, VACIA, Contrasena
from taximetro.gui.inicio import Inicio
from taximetro.servicio_taximetro import ServicioTaximetro
from taximetro.taximetro import Taximetro

CONTRASENA = "clave-de-prueba"


class AuthFalso:
    """Acepta solo CONTRASENA; `Auth` y el servicio tienen sus propios tests."""

    def comprobar(self, contrasena: str) -> bool:
        return contrasena == CONTRASENA


@pytest.fixture
def pantalla(raiz) -> Contrasena:
    app = App(ServicioTaximetro(Taximetro(), AuthFalso()), raiz=raiz)
    return app.mostrar(Contrasena)


def pulsar_enter(campo) -> None:
    """Enter en `campo`: Tk solo entrega el teclado a una ventana visible y con el foco."""
    ventana = campo.winfo_toplevel()
    ventana.deiconify()
    campo.focus_force()
    ventana.update()
    campo.event_generate("<Return>")


def teclear(pantalla: Contrasena, texto: str) -> None:
    pantalla.campo.delete(0, "end")
    pantalla.campo.insert(0, texto)


def test_el_campo_no_ensena_lo_que_se_teclea(pantalla: Contrasena) -> None:
    assert pantalla.campo.cget("show") == "•"


def test_la_correcta_abre_el_administrador(pantalla: Contrasena) -> None:
    teclear(pantalla, CONTRASENA)
    pantalla.entrar_tecla.invoke()
    assert isinstance(pantalla.app.pantalla, Administrador)


def test_enter_tambien_entra(pantalla: Contrasena) -> None:
    app = pantalla.app
    teclear(pantalla, CONTRASENA)
    pulsar_enter(pantalla.campo)
    assert isinstance(app.pantalla, Administrador)


def test_incorrecta_avisa_vacia_el_campo_y_se_queda(pantalla: Contrasena) -> None:
    teclear(pantalla, "otra")
    pantalla.entrar_tecla.invoke()
    assert pantalla.app.pantalla is pantalla  # sin límite de intentos: se vuelve a probar
    assert pantalla.mensaje.cget("text") == INCORRECTA
    assert pantalla.campo.get() == ""
    assert pantalla._marco_campo.cget("highlightbackground") == estilo.CAMPO_BORDE_ERROR


def test_vacia_pide_escribirla(pantalla: Contrasena) -> None:
    pantalla.entrar_tecla.invoke()
    assert pantalla.mensaje.cget("text") == VACIA


def test_sin_credenciales_avisa_y_no_entra(raiz) -> None:
    # Servicio sin Auth: las credenciales no se pueden leer. Nunca se entra por defecto.
    app = App(ServicioTaximetro(Taximetro()), raiz=raiz)
    pantalla = app.mostrar(Contrasena)
    teclear(pantalla, CONTRASENA)
    pantalla.entrar_tecla.invoke()
    assert pantalla.mensaje.cget("text") == NO_DISPONIBLE
    assert app.pantalla is pantalla


def test_al_volver_a_escribir_se_quita_el_aviso(pantalla: Contrasena) -> None:
    pantalla.entrar_tecla.invoke()
    pantalla._al_teclear(type("Evento", (), {"keysym": "a"})())
    assert pantalla.mensaje.cget("text") == ""
    assert pantalla._marco_campo.cget("highlightbackground") == estilo.CAMPO_BORDE


def test_cancelar_vuelve_a_inicio(pantalla: Contrasena) -> None:
    pantalla.cancelar.invoke()
    assert isinstance(pantalla.app.pantalla, Inicio)
