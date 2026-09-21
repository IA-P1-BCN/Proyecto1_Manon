"""Tests del bucle CLI (US-04 / T4.1, T4.3 y EPIC D).

La sesión se guioniza: se le pasa una lista de opciones tecleadas como
`entrada` y se recogen las líneas impresas en una lista como `salida`. Nada de
parchear `input`/`print` ni de leer stdout.

El menú es numerado y los números son locales a cada modo (ver
`docs/flujo-fase1.md`):

    Sin carrera     1 Iniciar carrera · 2 Ayuda · 3 Salir
    Carrera activa  1 Parar/Arrancar · 2 Ver importe · 3 Finalizar · 4 Ayuda
"""

from __future__ import annotations

from typing import Iterable

import pytest

from taximetro.taximetro import Taximetro
from taximetro.taximetro_app import (
    DESCRIPCIONES,
    OPCION_NO_VALIDA,
    SALIR_CON_CARRERA,
    TaximetroApp,
)


class EntradaGuionizada:
    """Devuelve opciones de una lista; al agotarse, simula EOF (Ctrl+D)."""

    def __init__(self, opciones: Iterable[str]) -> None:
        self._opciones = iter(opciones)

    def __call__(self, prompt: str = "") -> str:
        try:
            return next(self._opciones)
        except StopIteration:
            raise EOFError from None


@pytest.fixture
def sesion(reloj, calendario):
    """Ejecuta una sesión con las opciones dadas y devuelve las líneas impresas."""

    def _ejecutar(*opciones: str) -> list[str]:
        lineas: list[str] = []
        app = TaximetroApp(
            taximetro=Taximetro(reloj=reloj, calendario=calendario),
            entrada=EntradaGuionizada(opciones),
            salida=lineas.append,
        )
        app.ejecutar()
        return lineas

    return _ejecutar


def texto(lineas: list[str]) -> str:
    """Toda la salida de la sesión como un solo bloque."""
    return "\n".join(lineas)


def menus(lineas: list[str], cabecera: str) -> list[str]:
    """Los bloques de menú cuya cabecera coincide. Cada menú es una sola línea
    impresa con saltos dentro, así que se filtran por la cabecera y por llevar
    opciones numeradas."""
    return [linea for linea in lineas if cabecera in linea and "  1) " in linea]


class TestArranque:
    """US-01: el conductor no necesita documentación externa."""

    def test_muestra_las_instrucciones_al_arrancar(self, sesion) -> None:
        salida = texto(sesion("3"))
        assert "TAXÍMETRO TTX-247" in salida
        assert "Tarifas vigentes" in salida

    def test_el_banner_incluye_las_tarifas_reales(self, sesion) -> None:
        salida = texto(sesion("3"))
        assert "0,02 €/s" in salida
        assert "0,05 €/s" in salida

    def test_el_banner_explica_que_se_teclean_numeros(self, sesion) -> None:
        # US-01 con el menú numerado: si el banner no dice que se teclea un
        # número, el conductor puede intentar escribir la palabra.
        assert "número" in texto(sesion("3"))

    def test_el_banner_explica_todas_las_opciones(self, sesion) -> None:
        salida = texto(sesion("3"))
        for etiqueta, descripcion in DESCRIPCIONES:
            assert etiqueta in salida
            assert descripcion in salida


class TestMenuNumerado:
    """TD.2: el conductor solo ve, numeradas, las opciones válidas ahora mismo."""

    def test_sin_carrera_no_ofrece_opciones_de_carrera(self, sesion) -> None:
        menu = menus(sesion("3"), "Sin carrera")[0]
        assert "1) Iniciar carrera" in menu
        assert "2) Ayuda" in menu
        assert "3) Salir" in menu
        assert "Finalizar" not in menu and "Ver importe" not in menu

    def test_con_carrera_no_ofrece_iniciar_ni_salir(self, sesion) -> None:
        menu = menus(sesion("1"), "Carrera nº 1 en curso")[0]
        assert "2) Ver importe" in menu
        assert "3) Finalizar carrera" in menu
        assert "4) Ayuda" in menu
        assert "Iniciar carrera" not in menu
        assert "Salir" not in menu

    def test_cada_modo_numera_sus_propias_opciones(self, sesion) -> None:
        # El 1 no significa lo mismo en los dos menús, y es correcto: solo hay
        # un menú en pantalla a la vez.
        lineas = sesion("1")
        assert "1) Iniciar carrera" in menus(lineas, "Sin carrera")[0]
        assert "1) Parar" in menus(lineas, "Carrera nº 1 en curso")[0]

    def test_el_menu_activo_muestra_el_estado(self, sesion) -> None:
        bloques = menus(sesion("1", "1"), "en curso")
        assert "EN MOVIMIENTO" in bloques[0]
        assert "PARADO" in bloques[-1]

    def test_el_menu_ofrece_siempre_la_accion_contraria(self, sesion) -> None:
        # La opción de cambio nunca ofrece el estado en el que ya se está: en
        # movimiento se ofrece Parar, y parado se ofrece Arrancar.
        bloques = menus(sesion("1", "1"), "en curso")
        assert "1) Parar" in bloques[0]
        assert "1) Arrancar" in bloques[-1]

    def test_el_menu_se_separa_del_texto_anterior(self, sesion) -> None:
        # Una línea en blanco por delante: el menú se busca de un vistazo.
        for bloque in menus(sesion("1", "3", "3"), ""):
            assert bloque.startswith("\n")


class TestIniciarCarrera:
    """US-01 / T1.3."""

    def test_iniciar_anuncia_la_carrera(self, sesion) -> None:
        # La carrera nace EN MOVIMIENTO: se inicia cuando el taxi arranca.
        salida = texto(sesion("1"))
        assert "Carrera nº 1 iniciada · EN MOVIMIENTO · 0,05 €/s" in salida

    def test_durante_una_carrera_ningun_numero_inicia_otra(self, sesion) -> None:
        # Sustituye al antiguo aviso 'Ya hay una carrera activa': con el menú
        # numerado no existe ninguna tecla que abra una segunda carrera.
        salida = texto(sesion("1", "1", "2", "4"))
        assert "Carrera nº 2" not in salida


class TestCambiarEstado:
    """US-02 / T2.4: una sola opción que alterna entre los dos estados."""

    def test_la_opcion_de_cambio_alterna(self, sesion) -> None:
        bloques = menus(sesion("1", "1", "1"), "en curso")
        assert "EN MOVIMIENTO" in bloques[0]
        assert "PARADO" in bloques[1]
        assert "EN MOVIMIENTO" in bloques[2]

    def test_el_cambio_muestra_el_acumulado(self, reloj, calendario) -> None:
        lineas: list[str] = []
        opciones = iter(["1", "1"])
        primera = True

        def entrada(prompt: str = "") -> str:
            nonlocal primera
            try:
                opcion = next(opciones)
            except StopIteration:
                raise EOFError from None
            if not primera:
                reloj.avanzar(100)  # 100 s en movimiento -> 5,00 €
            primera = False
            return opcion

        TaximetroApp(
            taximetro=Taximetro(reloj=reloj, calendario=calendario),
            entrada=entrada,
            salida=lineas.append,
        ).ejecutar()

        assert "PARADO · 5,00 € acumulado" in lineas


class TestOpcionImporte:
    """TD.3: total acumulado bajo demanda, de solo lectura."""

    def test_muestra_el_importe_sin_cambiar_de_estado(self, sesion) -> None:
        salida = texto(sesion("1", "2"))
        assert "Carrera nº 1 · EN MOVIMIENTO · 0,00 € acumulado" in salida

    def test_consultar_el_importe_no_altera_el_total(self, reloj, calendario) -> None:
        # TD.5 desde el CLI: consultar el importe varias veces no puede cambiar
        # lo que se acaba cobrando.
        lineas: list[str] = []
        opciones = iter(["1", "2", "2", "3"])

        def entrada(prompt: str = "") -> str:
            try:
                opcion = next(opciones)
            except StopIteration:
                raise EOFError from None
            reloj.avanzar(25)  # 25 s entre opción y opción
            return opcion

        TaximetroApp(
            taximetro=Taximetro(reloj=reloj, calendario=calendario),
            entrada=entrada,
            salida=lineas.append,
        ).ejecutar()

        # 75 s en movimiento desde iniciar hasta finalizar, a 0,05 €/s.
        assert "TOTAL A COBRAR: 3,75 €" in lineas


class TestFinalizar:
    """US-03 / T3.3."""

    def test_muestra_el_total_a_cobrar(self, sesion) -> None:
        assert "TOTAL A COBRAR: 0,00 €" in sesion("1", "3")

    def test_tras_finalizar_vuelve_el_menu_sin_carrera(self, sesion) -> None:
        lineas = sesion("1", "3")
        posteriores = lineas[lineas.index("TOTAL A COBRAR: 0,00 €") :]
        assert menus(posteriores, "Sin carrera")


class TestEncadenarCarreras:
    """US-04 / T4.2, T4.3: el ciclo completo sin cerrar el programa."""

    def test_ciclo_iniciar_finalizar_iniciar(self, sesion) -> None:
        salida = texto(sesion("1", "1", "3", "1", "3", "3"))
        assert "Carrera nº 1 iniciada" in salida
        assert "Carrera nº 2 iniciada" in salida
        assert salida.count("TOTAL A COBRAR") == 2

    def test_las_carreras_se_numeran_en_orden(self, sesion) -> None:
        salida = texto(sesion("1", "3", "1", "3", "3"))
        assert salida.index("Carrera nº 1 iniciada") < salida.index(
            "Carrera nº 2 iniciada"
        )


class TestOpcionAyuda:
    """TD.6: el banner se puede recuperar cuando se va de pantalla."""

    def test_ayuda_reimprime_el_banner_sin_carrera(self, sesion) -> None:
        salida = texto(sesion("2", "3"))
        assert salida.count("TAXÍMETRO TTX-247") == 2  # arranque + ayuda

    def test_ayuda_funciona_tambien_durante_una_carrera(self, sesion) -> None:
        salida = texto(sesion("1", "4", "3", "3"))
        assert salida.count("TAXÍMETRO TTX-247") == 2

    def test_ayuda_no_interrumpe_la_carrera(self, sesion) -> None:
        lineas = sesion("1", "4")
        assert any("Carrera nº 1 en curso" in linea for linea in lineas[-2:])


class TestEntradaNoValida:
    """TD.8: con el menú numerado solo queda un error posible."""

    @pytest.mark.parametrize(
        "tecleado", ["0", "4", "9", "-1", "abc", "", "finalizar", "²"]
    )
    def test_lo_que_no_es_un_numero_del_menu(self, sesion, tecleado: str) -> None:
        # Incluye las palabras del CLI anterior: ya no se aceptan.
        assert OPCION_NO_VALIDA in sesion(tecleado, "3")

    def test_un_numero_fuera_del_menu_activo(self, sesion) -> None:
        # El menú con carrera llega hasta el 4.
        assert OPCION_NO_VALIDA in sesion("1", "5")

    def test_la_carrera_sobrevive_a_una_entrada_no_valida(self, sesion) -> None:
        lineas = sesion("1", "9", "2")
        assert OPCION_NO_VALIDA in lineas
        assert any("Carrera nº 1 · EN MOVIMIENTO" in linea for linea in lineas)

    def test_admite_espacios_alrededor_del_numero(self, sesion) -> None:
        assert "Carrera nº 1 iniciada · EN MOVIMIENTO · 0,05 €/s" in sesion("  1  ")


class TestSalir:
    """El programa solo se cierra desde el menú sin carrera."""

    def test_salir_termina_el_bucle(self, sesion) -> None:
        lineas = sesion("3", "1")
        # El `1` posterior no llega a ejecutarse.
        assert not any("iniciada" in linea for linea in lineas)


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
            reloj, calendario, ["1", KeyboardInterrupt, "2", "3"]
        )
        assert SALIR_CON_CARRERA in lineas
        assert any("Carrera nº 1 · EN MOVIMIENTO" in linea for linea in lineas)
        assert "TOTAL A COBRAR: 0,00 €" in lineas

    def test_eof_sin_carrera_sale_limpiamente(self, reloj, calendario) -> None:
        lineas = self._sesion_interrumpida(reloj, calendario, [])
        assert not any("TOTAL A COBRAR" in linea for linea in lineas)

    def test_eof_durante_una_carrera_cobra_antes_de_salir(
        self, reloj, calendario
    ) -> None:
        # Sin esto, cerrar el terminal a mitad de carrera perdería el importe
        # del pasajero (y soltaría un traceback).
        lineas = self._sesion_interrumpida(reloj, calendario, ["1"])
        assert any(linea.startswith("TOTAL A COBRAR") for linea in lineas)
