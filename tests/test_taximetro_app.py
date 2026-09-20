"""Tests del bucle CLI (US-04 / T4.1, T4.3 y EPIC D).

La sesión se guioniza: se le pasa una lista de comandos como `entrada` y se
recogen las líneas impresas en una lista como `salida`. Nada de parchear
`input`/`print` ni de leer stdout.
"""

from __future__ import annotations

from typing import Iterable

import pytest

from taximetro.taximetro import Taximetro
from taximetro.taximetro_app import (
    NO_RECONOCIDO,
    SALIR_CON_CARRERA,
    SIN_CARRERA_ACTIVA,
    YA_HAY_CARRERA,
    TaximetroApp,
)


class EntradaGuionizada:
    """Devuelve comandos de una lista; al agotarse, simula EOF (Ctrl+D)."""

    def __init__(self, comandos: Iterable[str]) -> None:
        self._comandos = iter(comandos)

    def __call__(self, prompt: str = "") -> str:
        try:
            return next(self._comandos)
        except StopIteration:
            raise EOFError from None


@pytest.fixture
def sesion(reloj, calendario):
    """Ejecuta una sesión con los comandos dados y devuelve las líneas impresas."""

    def _ejecutar(*comandos: str) -> list[str]:
        lineas: list[str] = []
        app = TaximetroApp(
            taximetro=Taximetro(reloj=reloj, calendario=calendario),
            entrada=EntradaGuionizada(comandos),
            salida=lineas.append,
        )
        app.ejecutar()
        return lineas

    return _ejecutar


def texto(lineas: list[str]) -> str:
    """Toda la salida de la sesión como un solo bloque."""
    return "\n".join(lineas)


class TestArranque:
    """US-01: el conductor no necesita documentación externa."""

    def test_muestra_las_instrucciones_al_arrancar(self, sesion) -> None:
        salida = texto(sesion("salir"))
        assert "TAXÍMETRO TTX-247" in salida
        assert "Tarifas vigentes" in salida

    def test_el_banner_incluye_las_tarifas_reales(self, sesion) -> None:
        salida = texto(sesion("salir"))
        assert "0,02 €/s" in salida
        assert "0,05 €/s" in salida

    def test_el_banner_explica_todos_los_comandos(self, sesion) -> None:
        salida = texto(sesion("salir"))
        for comando in ("iniciar", "parado", "movimiento", "importe", "finalizar", "ayuda", "salir"):
            assert comando in salida


class TestMenusContextuales:
    """TD.2: el conductor solo ve los comandos válidos ahora mismo."""

    def test_sin_carrera_no_ofrece_comandos_de_carrera(self, sesion) -> None:
        menu = [l for l in sesion("salir") if l.startswith("Sin carrera")][0]
        assert "iniciar" in menu and "salir" in menu
        assert "finalizar" not in menu and "importe" not in menu

    def test_con_carrera_no_ofrece_iniciar_ni_salir(self, sesion) -> None:
        menus = [l for l in sesion("iniciar") if l.startswith("Carrera nº 1 en curso")]
        assert menus, "debería mostrarse el menú de carrera activa"
        assert "finalizar" in menus[0] and "importe" in menus[0]
        assert "iniciar" not in menus[0]
        assert "salir" not in menus[0]

    def test_el_menu_activo_muestra_el_estado(self, sesion) -> None:
        menus = [l for l in sesion("iniciar", "movimiento") if "en curso" in l]
        assert "PARADO" in menus[0]
        assert "EN MOVIMIENTO" in menus[-1]


class TestIniciarCarrera:
    """US-01 / T1.3."""

    def test_iniciar_anuncia_la_carrera(self, sesion) -> None:
        salida = texto(sesion("iniciar"))
        assert "Carrera nº 1 iniciada · PARADO · 0,02 €/s" in salida

    def test_iniciar_con_carrera_activa_avisa(self, sesion) -> None:
        assert YA_HAY_CARRERA in sesion("iniciar", "iniciar")


class TestCambiarEstado:
    """US-02 / T2.4."""

    def test_movimiento_cambia_la_tarifa(self, sesion, reloj) -> None:
        salida = texto(sesion("iniciar", "movimiento"))
        assert "EN MOVIMIENTO" in salida

    def test_el_cambio_muestra_el_acumulado(self, reloj, calendario) -> None:
        lineas: list[str] = []
        comandos = iter(["iniciar", "movimiento"])

        def entrada(prompt: str = "") -> str:
            try:
                comando = next(comandos)
            except StopIteration:
                raise EOFError from None
            if comando == "movimiento":
                reloj.avanzar(100)  # 100 s parado -> 2,00 €
            return comando

        TaximetroApp(
            taximetro=Taximetro(reloj=reloj, calendario=calendario),
            entrada=entrada,
            salida=lineas.append,
        ).ejecutar()

        assert "EN MOVIMIENTO · 2,00 € acumulado" in lineas


class TestComandoImporte:
    """TD.3: total acumulado bajo demanda, de solo lectura."""

    def test_muestra_el_importe_sin_cambiar_de_estado(self, sesion) -> None:
        salida = texto(sesion("iniciar", "importe"))
        assert "Carrera nº 1 · PARADO · 0,00 € acumulado" in salida

    def test_consultar_el_importe_no_altera_el_total(self, reloj, calendario) -> None:
        # TD.5 desde el CLI: consultar el importe varias veces no puede cambiar
        # lo que se acaba cobrando.
        lineas: list[str] = []
        comandos = iter(["iniciar", "importe", "importe", "finalizar"])

        def entrada(prompt: str = "") -> str:
            try:
                comando = next(comandos)
            except StopIteration:
                raise EOFError from None
            reloj.avanzar(25)  # 25 s entre comando y comando
            return comando

        TaximetroApp(
            taximetro=Taximetro(reloj=reloj, calendario=calendario),
            entrada=entrada,
            salida=lineas.append,
        ).ejecutar()

        # 75 s parados desde `iniciar` hasta `finalizar`, a 0,02 €/s.
        assert "TOTAL A COBRAR: 1,50 €" in lineas


class TestFinalizar:
    """US-03 / T3.3."""

    def test_muestra_el_total_a_cobrar(self, sesion) -> None:
        assert "TOTAL A COBRAR: 0,00 €" in sesion("iniciar", "finalizar")

    def test_tras_finalizar_vuelve_el_menu_sin_carrera(self, sesion) -> None:
        lineas = sesion("iniciar", "finalizar")
        assert any(l.startswith("Sin carrera") for l in lineas[lineas.index(
            "TOTAL A COBRAR: 0,00 €"
        ):])


class TestEncadenarCarreras:
    """US-04 / T4.2, T4.3: el ciclo completo sin cerrar el programa."""

    def test_ciclo_iniciar_finalizar_iniciar(self, sesion) -> None:
        salida = texto(
            sesion("iniciar", "movimiento", "finalizar", "iniciar", "finalizar", "salir")
        )
        assert "Carrera nº 1 iniciada" in salida
        assert "Carrera nº 2 iniciada" in salida
        assert salida.count("TOTAL A COBRAR") == 2

    def test_las_carreras_se_numeran_en_orden(self, sesion) -> None:
        salida = texto(sesion("iniciar", "finalizar", "iniciar", "finalizar", "salir"))
        assert salida.index("Carrera nº 1 iniciada") < salida.index("Carrera nº 2 iniciada")


class TestComandoAyuda:
    """TD.6: el banner se puede recuperar cuando se va de pantalla."""

    def test_ayuda_reimprime_el_banner_sin_carrera(self, sesion) -> None:
        salida = texto(sesion("ayuda", "salir"))
        assert salida.count("TAXÍMETRO TTX-247") == 2  # arranque + ayuda

    def test_ayuda_funciona_tambien_durante_una_carrera(self, sesion) -> None:
        salida = texto(sesion("iniciar", "ayuda", "finalizar", "salir"))
        assert salida.count("TAXÍMETRO TTX-247") == 2

    def test_ayuda_no_interrumpe_la_carrera(self, sesion) -> None:
        lineas = sesion("iniciar", "ayuda")
        assert any("Carrera nº 1 en curso" in l for l in lineas[-2:])


class TestErroresDiferenciados:
    """TD.8: un comando en el modo equivocado no es lo mismo que una errata."""

    @pytest.mark.parametrize("comando", ["parado", "movimiento", "importe", "finalizar"])
    def test_comando_de_carrera_sin_carrera_activa(self, sesion, comando: str) -> None:
        assert SIN_CARRERA_ACTIVA in sesion(comando, "salir")

    @pytest.mark.parametrize("comando", ["finalizr", "xyz", ""])
    def test_comando_inexistente_sin_carrera(self, sesion, comando: str) -> None:
        assert NO_RECONOCIDO in sesion(comando, "salir")

    def test_comando_inexistente_durante_una_carrera(self, sesion) -> None:
        assert NO_RECONOCIDO in sesion("iniciar", "movimeinto")

    def test_salir_durante_una_carrera_no_cierra_el_programa(self, sesion) -> None:
        # `salir` no existe en el menú de carrera activa: cae en "no reconocido"
        # y la carrera sigue viva.
        lineas = sesion("iniciar", "salir", "importe")
        assert NO_RECONOCIDO in lineas
        assert any("Carrera nº 1 · PARADO" in l for l in lineas)

    def test_los_comandos_admiten_mayusculas_y_espacios(self, sesion) -> None:
        assert "Carrera nº 1 iniciada · PARADO · 0,02 €/s" in sesion("  INICIAR  ")


class TestSalir:
    """El programa solo se cierra desde el menú sin carrera."""

    def test_salir_termina_el_bucle(self, sesion) -> None:
        lineas = sesion("salir", "iniciar")
        # El `iniciar` posterior no llega a ejecutarse.
        assert not any("iniciada" in l for l in lineas)


class TestInterrupciones:
    """TD.7 y TP.4: Ctrl+C y EOF."""

    def _sesion_interrumpida(self, reloj, calendario, guion):
        """Ejecuta un guion donde un elemento puede ser una excepción."""
        lineas: list[str] = []
        pasos = iter(guion)

        def entrada(prompt: str = "") -> str:
            try:
                paso = next(pasos)
            except StopIteration:
                raise EOFError from None
            if isinstance(paso, type) and issubclass(paso, BaseException):
                raise paso
            return paso

        TaximetroApp(
            taximetro=Taximetro(reloj=reloj, calendario=calendario),
            entrada=entrada,
            salida=lineas.append,
        ).ejecutar()
        return lineas

    def test_ctrl_c_sin_carrera_sale_limpiamente(self, reloj, calendario) -> None:
        lineas = self._sesion_interrumpida(reloj, calendario, [KeyboardInterrupt])
        assert SALIR_CON_CARRERA not in lineas

    def test_ctrl_c_durante_una_carrera_no_la_pierde(self, reloj, calendario) -> None:
        lineas = self._sesion_interrumpida(
            reloj, calendario, ["iniciar", KeyboardInterrupt, "importe", "finalizar"]
        )
        assert SALIR_CON_CARRERA in lineas
        assert any("Carrera nº 1 · PARADO" in l for l in lineas)
        assert "TOTAL A COBRAR: 0,00 €" in lineas

    def test_eof_sin_carrera_sale_limpiamente(self, reloj, calendario) -> None:
        lineas = self._sesion_interrumpida(reloj, calendario, [])
        assert not any("TOTAL A COBRAR" in l for l in lineas)

    def test_eof_durante_una_carrera_cobra_antes_de_salir(
        self, reloj, calendario
    ) -> None:
        # Sin esto, cerrar el terminal a mitad de carrera perdería el importe
        # del pasajero (y soltaría un traceback).
        lineas = self._sesion_interrumpida(reloj, calendario, ["iniciar"])
        assert any(l.startswith("TOTAL A COBRAR") for l in lineas)
