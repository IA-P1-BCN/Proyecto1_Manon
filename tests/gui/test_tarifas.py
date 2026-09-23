"""Tests de `taximetro.gui.tarifas.CambiarTarifas`: la pantalla 7 (T9.7).

Los mensajes son los del CLI (`flujo-fase2.md`); las reglas, las de `Tarifa`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from taximetro.config_tarifas import ConfigTarifas
from taximetro.gui import estilo
from taximetro.gui.administrador import Administrador
from taximetro.gui.app import App
from taximetro.gui.tarifas import NO_ESCRITO, CambiarTarifas
from taximetro.servicio_taximetro import ServicioTaximetro, TarifasVigentes
from taximetro.taximetro import Taximetro


@pytest.fixture
def pantalla(app: App) -> CambiarTarifas:
    return app.mostrar(CambiarTarifas)


def teclear(pantalla: CambiarTarifas, parado: str | None = None, en_movimiento: str | None = None) -> None:
    for nombre, texto in (("parado", parado), ("en_movimiento", en_movimiento)):
        if texto is not None:
            pantalla.campos[nombre].delete(0, "end")
            pantalla.campos[nombre].insert(0, texto)


def pulsar_enter(campo) -> None:
    """Enter en `campo`: Tk solo entrega el teclado a una ventana visible y con el foco."""
    ventana = campo.winfo_toplevel()
    ventana.deiconify()
    campo.focus_force()
    ventana.update()
    campo.event_generate("<Return>")


def en_rojo(pantalla: CambiarTarifas) -> set[str]:
    return {
        nombre
        for nombre, marco in pantalla._marcos.items()
        if marco.cget("highlightbackground") == estilo.CAMPO_BORDE_ERROR
    }


class TestAlEntrar:
    def test_campos_rellenos_con_las_vigentes(self, pantalla: CambiarTarifas) -> None:
        # Así se puede cambiar solo una: la única diferencia con el CLI.
        assert pantalla.campos["parado"].get() == "0,02"
        assert pantalla.campos["en_movimiento"].get() == "0,05"
        assert pantalla.vigentes.cget("text") == (
            "Tarifas vigentes: parado 0,02 €/s · en movimiento 0,05 €/s"
        )

    def test_cada_campo_con_el_color_de_su_estado(self, pantalla: CambiarTarifas) -> None:
        assert pantalla.campos["parado"].cget("fg") == estilo.LED_AMBAR
        assert pantalla.campos["en_movimiento"].cget("fg") == estilo.LED_VERDE


class TestGuardar:
    def test_guarda_y_lo_dice_en_verde(self, pantalla: CambiarTarifas) -> None:
        teclear(pantalla, en_movimiento="0.06")  # coma o punto
        pantalla.guardar_tecla.invoke()
        assert pantalla.servicio.tarifas() == TarifasVigentes(0.02, 0.06)
        assert pantalla.mensaje.cget("text") == (
            "Tarifas guardadas: parado 0,02 €/s · en movimiento 0,06 €/s. "
            "Se aplican desde la próxima carrera."
        )
        assert pantalla.mensaje.cget("fg") == estilo.MENSAJE_OK
        assert "0,06" in pantalla.vigentes.cget("text")

    def test_enter_tambien_guarda(self, pantalla: CambiarTarifas) -> None:
        teclear(pantalla, parado="0,03")
        pulsar_enter(pantalla.campos["parado"])
        assert pantalla.servicio.tarifas().parado == 0.03


class TestErrores:
    """Nada se guarda y el campo culpable se pone en rojo."""

    @pytest.mark.parametrize(
        "parado, en_movimiento, mensaje, culpables",
        [
            ("abc", None, "«abc» no es un número. Escribe, por ejemplo, 0,03. No se ha guardado nada.", {"parado"}),
            (None, "", "«» no es un número. Escribe, por ejemplo, 0,03. No se ha guardado nada.", {"en_movimiento"}),
            (None, "2", "Cada tarifa debe ser mayor que 0 y como máximo 1,00 €/s. No se ha guardado nada.", {"en_movimiento"}),
            ("0,021", None, "Cada tarifa admite como máximo 2 decimales. No se ha guardado nada.", {"parado"}),
            ("0,06", None, "La tarifa parado no puede ser mayor que la de en movimiento. No se ha guardado nada.", {"parado", "en_movimiento"}),
        ],
    )
    def test_mensaje_del_cli_y_campo_en_rojo(
        self, pantalla: CambiarTarifas, parado, en_movimiento, mensaje, culpables
    ) -> None:
        teclear(pantalla, parado, en_movimiento)
        pantalla.guardar_tecla.invoke()
        assert pantalla.mensaje.cget("text") == mensaje
        assert pantalla.mensaje.cget("fg") == estilo.MENSAJE_ERROR
        assert en_rojo(pantalla) == culpables
        assert pantalla.servicio.tarifas() == TarifasVigentes(0.02, 0.05)

    def test_si_no_se_puede_escribir_el_fichero(self, raiz, tmp_path: Path) -> None:
        (tmp_path / "bloqueo").write_text("", encoding="utf-8")
        taximetro = Taximetro(config=ConfigTarifas(tmp_path / "bloqueo" / "tarifas.json"))
        pantalla = App(ServicioTaximetro(taximetro), raiz=raiz).mostrar(CambiarTarifas)
        teclear(pantalla, parado="0,03")
        pantalla.guardar_tecla.invoke()
        assert pantalla.mensaje.cget("text") == NO_ESCRITO
        assert pantalla.servicio.tarifas().parado == 0.02

    def test_al_volver_a_escribir_se_quita_el_aviso(self, pantalla: CambiarTarifas) -> None:
        teclear(pantalla, parado="abc")
        pantalla.guardar_tecla.invoke()
        pantalla._al_teclear(type("Evento", (), {"keysym": "a"})())
        assert pantalla.mensaje.cget("text") == ""
        assert en_rojo(pantalla) == set()


def test_volver_sin_guardar(pantalla: CambiarTarifas) -> None:
    teclear(pantalla, parado="0,03")
    pantalla.volver.invoke()
    assert isinstance(pantalla.app.pantalla, Administrador)
    assert pantalla.servicio.tarifas().parado == 0.02
