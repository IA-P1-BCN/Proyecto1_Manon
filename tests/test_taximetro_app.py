"""Tests del bucle CLI (US-04 / T4.1, T4.3 y EPIC D).

La sesión se guioniza: se le pasa una lista de opciones tecleadas como
`entrada` y se recogen las líneas impresas en una lista como `salida`. Nada de
parchear `input`/`print` ni de leer stdout.

El menú es numerado y los números son locales a cada modo (ver
`docs/flujo-fase1.md` y `docs/decisions-fase2.md`):

    Menú de inicio  1 Conductor · 2 Administrador · 3 Salir
    Sin carrera     1 Iniciar carrera · 2 Ayuda · 3 Volver
    Carrera activa  1 Parar/Arrancar · 2 Ver importe · 3 Finalizar · 4 Ayuda
    Administrador   1 Cambiar tarifas · 2 Ver histórico · 3 Volver

La mayoría de los tests son del conductor: el fixture `sesion` teclea el `1`
(Conductor) del menú de inicio por ellos. `sesion_libre` empieza en el menú de
inicio.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import pytest

from taximetro.config_tarifas import ConfigTarifas
from taximetro.historial import Historial
from taximetro.servicio_taximetro import ServicioTaximetro
from taximetro.taximetro import Taximetro
from taximetro.auth import CredencialesError
from taximetro.taximetro_app import (
    CONTRASENA_INCORRECTA,
    CREDENCIALES_NO_DISPONIBLES,
    DESCRIPCIONES,
    HISTORICO_NO_GUARDADO,
    NADA_GUARDADO,
    OPCION_NO_VALIDA,
    TaximetroApp,
    leer_contrasena,
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


CONDUCTOR = "1"  # opción del menú de inicio
ADMIN_VOLVER = "3"  # Volver en el menú de Administrador
ADMINISTRADOR = "\nAdministrador"  # cómo empieza el menú de Administrador
CONTRASENA = "clave-de-prueba"  # la de AuthFalso; la real nunca va en los tests


class AuthFalso:
    """Acepta solo CONTRASENA, sin fichero ni scrypt: `Auth` tiene sus propios tests."""

    def comprobar(self, contrasena: str) -> bool:
        return contrasena == CONTRASENA


def servicio_de_prueba(taximetro: Taximetro) -> ServicioTaximetro:
    """El servicio de los tests: el taxímetro dado y la contraseña de AuthFalso."""
    return ServicioTaximetro(taximetro, AuthFalso())


def teclea_la_buena(prompt: str = "") -> str:
    """`entrada_oculta` por defecto en los tests: nunca el `getpass` real."""
    return CONTRASENA


@pytest.fixture
def sesion_libre(reloj, calendario):
    """Ejecuta una sesión desde el menú de inicio y devuelve las líneas impresas."""

    def _ejecutar(*opciones: str) -> list[str]:
        lineas: list[str] = []
        app = TaximetroApp(
            servicio=servicio_de_prueba(Taximetro(reloj=reloj, calendario=calendario)),
            entrada=EntradaGuionizada(opciones),
            salida=lineas.append,
            entrada_oculta=teclea_la_buena,
        )
        app.ejecutar()
        return lineas

    return _ejecutar


@pytest.fixture
def sesion(sesion_libre):
    """Como `sesion_libre`, pero ya dentro del perfil Conductor."""

    def _ejecutar(*opciones: str) -> list[str]:
        return sesion_libre(CONDUCTOR, *opciones)

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
        for perfil, grupo in DESCRIPCIONES.items():
            assert f"{perfil}:" in salida
            for etiqueta, descripcion in grupo:
                assert etiqueta in salida
                assert descripcion in salida


class TestMenuNumerado:
    """TD.2: el conductor solo ve, numeradas, las opciones válidas ahora mismo."""

    def test_sin_carrera_no_ofrece_opciones_de_carrera(self, sesion) -> None:
        menu = menus(sesion("3"), "Sin carrera")[0]
        assert "1) Iniciar carrera" in menu
        assert "2) Ayuda" in menu
        assert "3) Volver" in menu
        assert "Finalizar" not in menu and "Ver importe" not in menu

    def test_con_carrera_no_ofrece_iniciar_ni_salir(self, sesion) -> None:
        menu = menus(sesion("1"), "Carrera nº 1 en curso")[0]
        assert "2) Ver importe" in menu
        assert "3) Finalizar carrera" in menu
        assert "4) Ayuda" in menu
        assert "Iniciar carrera" not in menu
        assert "Salir" not in menu
        assert "Volver" not in menu  # con carrera no se llega al Administrador

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
        opciones = iter([CONDUCTOR, "1", "1"])
        llamadas = 0

        def entrada(prompt: str = "") -> str:
            nonlocal llamadas
            try:
                opcion = next(opciones)
            except StopIteration:
                raise EOFError from None
            llamadas += 1
            if llamadas == 3:
                reloj.avanzar(100)  # 100 s en movimiento -> 5,00 €
            return opcion

        TaximetroApp(
            servicio=servicio_de_prueba(Taximetro(reloj=reloj, calendario=calendario)),
            entrada=entrada,
            salida=lineas.append,
            entrada_oculta=teclea_la_buena,
        ).ejecutar()

        assert "PARADO · 5,00 € acumulado" in lineas


class TestOpcionImporte:
    """TD.3: total acumulado bajo demanda, de solo lectura."""

    def test_muestra_el_importe_sin_cambiar_de_estado(self, sesion) -> None:
        salida = texto(sesion("1", "2"))
        assert "Carrera nº 1 · EN MOVIMIENTO · 0,00 € acumulado" in salida

    def test_muestra_el_importe_de_cuando_se_pide(self, reloj, calendario) -> None:
        # T9.11: el menú se pinta con una foto de la carrera tomada antes de
        # esperar la opción. El importe tiene que ser el de cuando el
        # conductor lo pide, no el de esa foto.
        lineas: list[str] = []
        opciones = iter([CONDUCTOR, "1", "2"])

        def entrada(prompt: str = "") -> str:
            try:
                opcion = next(opciones)
            except StopIteration:
                raise EOFError from None
            if opcion == "2":
                reloj.avanzar(10)  # el conductor tarda 10 s en elegir
            return opcion

        TaximetroApp(
            servicio=servicio_de_prueba(Taximetro(reloj=reloj, calendario=calendario)),
            entrada=entrada,
            salida=lineas.append,
            entrada_oculta=teclea_la_buena,
        ).ejecutar()

        assert "Carrera nº 1 · EN MOVIMIENTO · 0,50 € acumulado" in texto(lineas)

    def test_consultar_el_importe_no_altera_el_total(self, reloj, calendario) -> None:
        # TD.5 desde el CLI: consultar el importe varias veces no puede cambiar
        # lo que se acaba cobrando.
        lineas: list[str] = []
        opciones = iter(["1", "2", "2", "3"])
        dentro = False

        def entrada(prompt: str = "") -> str:
            nonlocal dentro
            if not dentro:  # el menú de inicio no cuenta tiempo de carrera
                dentro = True
                return CONDUCTOR
            try:
                opcion = next(opciones)
            except StopIteration:
                raise EOFError from None
            reloj.avanzar(25)  # 25 s entre opción y opción
            return opcion

        TaximetroApp(
            servicio=servicio_de_prueba(Taximetro(reloj=reloj, calendario=calendario)),
            entrada=entrada,
            salida=lineas.append,
            entrada_oculta=teclea_la_buena,
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


class TestMenuDeInicio:
    """T7.5: se elige perfil al arrancar; Salir solo existe aquí."""

    def test_arranca_en_el_menu_de_inicio(self, sesion_libre) -> None:
        menu = menus(sesion_libre(), "Menú de inicio")[0]
        assert "1) Conductor" in menu
        assert "2) Administrador" in menu
        assert "3) Salir" in menu

    def test_el_banner_explica_como_elegir_perfil(self, sesion_libre) -> None:
        salida = texto(sesion_libre())
        assert "elige tu perfil" in salida
        assert "Salir, en el menú de inicio, cierra el programa." in salida

    def test_salir_termina_el_programa(self, sesion_libre) -> None:
        lineas = sesion_libre("3", "1")
        # El `1` posterior no llega a ejecutarse.
        assert not menus(lineas, "Sin carrera")

    def test_conductor_entra_en_el_bucle_de_carreras(self, sesion_libre) -> None:
        assert menus(sesion_libre("1"), "Sin carrera")

    def test_volver_del_conductor_regresa_al_menu_de_inicio(self, sesion_libre) -> None:
        lineas = sesion_libre("1", "3")
        assert len(menus(lineas, "Menú de inicio")) == 2
        assert lineas[-1].startswith("\nMenú de inicio")

    def test_administrador_tiene_su_propio_menu(self, sesion_libre) -> None:
        # La cabecera va en su propia línea: el menú de inicio también
        # contiene la palabra "Administrador".
        menu = menus(sesion_libre("2"), "\nAdministrador\n")[0]
        assert "Volver" in menu
        assert "Iniciar carrera" not in menu

    def test_volver_del_administrador_regresa_al_menu_de_inicio(
        self, sesion_libre
    ) -> None:
        lineas = sesion_libre("2", ADMIN_VOLVER)
        assert lineas[-1].startswith("\nMenú de inicio")

    def test_la_numeracion_sigue_al_volver_al_conductor(self, sesion_libre) -> None:
        # El taxímetro es el mismo en toda la sesión: salir al menú de inicio
        # no reinicia la cuenta de carreras.
        salida = texto(sesion_libre("1", "1", "3", "3", "2", ADMIN_VOLVER, "1", "1"))
        assert "Carrera nº 2 iniciada" in salida

    @pytest.mark.parametrize("tecleado", ["0", "4", "abc", ""])
    def test_opcion_no_valida_en_el_menu_de_inicio(
        self, sesion_libre, tecleado: str
    ) -> None:
        lineas = sesion_libre(tecleado)
        assert OPCION_NO_VALIDA in lineas
        assert len(menus(lineas, "Menú de inicio")) == 2

    def test_opcion_no_valida_en_el_administrador(self, sesion_libre) -> None:
        assert OPCION_NO_VALIDA in sesion_libre("2", "9")


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
            servicio=servicio_de_prueba(Taximetro(reloj=reloj, calendario=calendario)),
            entrada=entrada,
            salida=lineas.append,
            entrada_oculta=teclea_la_buena,
        ).ejecutar()
        return lineas

    def _sesion_conductor(self, reloj, calendario, guion):
        """Como `_sesion_interrumpida`, pero ya dentro del perfil Conductor."""
        return self._sesion_interrumpida(reloj, calendario, [CONDUCTOR, *guion])

    def test_ctrl_c_sin_carrera_sale_limpiamente(self, reloj, calendario) -> None:
        lineas = self._sesion_conductor(reloj, calendario, [KeyboardInterrupt, "1"])
        assert not menus(lineas, "Vas a salir")
        assert not any("iniciada" in linea for linea in lineas)

    @pytest.mark.parametrize("interrupcion", [KeyboardInterrupt, EOFError])
    def test_fuera_del_conductor_se_sale_limpiamente(
        self, reloj, calendario, interrupcion
    ) -> None:
        # En el menú de inicio y en el de Administrador no hay nada que perder.
        for guion in ([interrupcion, "1"], ["2", interrupcion, "1"]):
            lineas = self._sesion_interrumpida(reloj, calendario, guion)
            assert not menus(lineas, "Sin carrera")

    def test_ctrl_c_durante_una_carrera_pide_confirmacion(
        self, reloj, calendario
    ) -> None:
        lineas = self._sesion_conductor(reloj, calendario, ["1", KeyboardInterrupt])
        pregunta = menus(lineas, "Vas a salir")[0]
        assert "Vas a salir del programa con la carrera nº 1 en curso." in pregunta
        assert "1) Sí, finalizar la carrera y salir" in pregunta
        assert "2) No, seguir con la carrera" in pregunta

    def test_confirmar_finaliza_cobra_y_sale(self, reloj, calendario) -> None:
        # El "1" posterior no llega a ejecutarse: el programa ya se ha cerrado.
        lineas = self._sesion_conductor(
            reloj, calendario, ["1", KeyboardInterrupt, "1", "1"]
        )
        assert lineas[-1] == "TOTAL A COBRAR: 0,00 €"

    def test_no_vuelve_a_la_carrera_como_si_nada(self, reloj, calendario) -> None:
        lineas = self._sesion_conductor(
            reloj, calendario, ["1", KeyboardInterrupt, "2", "2", "3"]
        )
        assert any("Carrera nº 1 · EN MOVIMIENTO" in linea for linea in lineas)
        assert "TOTAL A COBRAR: 0,00 €" in lineas
        # Tras el total, la sesión sigue: vuelve el menú sin carrera.
        assert lineas[-1].startswith("\nSin carrera")

    @pytest.mark.parametrize("tecleado", ["3", "abc", ""])
    def test_una_respuesta_no_valida_repite_la_pregunta(
        self, reloj, calendario, tecleado: str
    ) -> None:
        lineas = self._sesion_conductor(
            reloj, calendario, ["1", KeyboardInterrupt, tecleado, "2"]
        )
        assert OPCION_NO_VALIDA in lineas
        assert len(menus(lineas, "Vas a salir")) == 2
        # «No» devuelve a la carrera; el EOF del final del guion la cierra.
        assert lineas[-2].startswith("\nCarrera nº 1 en curso")

    def test_un_segundo_ctrl_c_cuenta_como_no(self, reloj, calendario) -> None:
        lineas = self._sesion_conductor(
            reloj, calendario, ["1", KeyboardInterrupt, KeyboardInterrupt]
        )
        # Sigue la carrera; el EOF final es lo único que la cierra.
        ultimo_menu = [linea for linea in lineas if "  1) " in linea][-1]
        assert "Carrera nº 1 en curso" in ultimo_menu

    def test_eof_en_la_pregunta_cuenta_como_si(self, reloj, calendario) -> None:
        lineas = self._sesion_conductor(reloj, calendario, ["1", KeyboardInterrupt])
        assert lineas[-1] == "TOTAL A COBRAR: 0,00 €"

    def test_si_cobra_el_importe_del_ctrl_c(self, reloj, calendario) -> None:
        # Fase 3 (T9.8): el importe se congela al preguntar; el minuto que se
        # tarda en contestar «Sí» no se cobra.
        lineas: list[str] = []
        pasos = iter([CONDUCTOR, "1", KeyboardInterrupt, "1"])

        def entrada(prompt: str = "") -> str:
            paso = next(pasos)
            if paso == "1" and lineas and "Vas a salir" in lineas[-1]:
                reloj.avanzar(60)  # un minuto con la pregunta en pantalla
            if paso is KeyboardInterrupt:
                reloj.avanzar(10)  # 10 s de carrera antes del Ctrl+C
                raise paso
            return paso

        TaximetroApp(
            servicio=servicio_de_prueba(Taximetro(reloj=reloj, calendario=calendario)),
            entrada=entrada,
            salida=lineas.append,
            entrada_oculta=teclea_la_buena,
        ).ejecutar()
        assert "Importe a cobrar: 0,50 €" in menus(lineas, "Vas a salir")[0]
        assert "TOTAL A COBRAR: 0,50 €" in lineas

    def test_no_sigue_y_cobra_tambien_la_pregunta(
        self, reloj, calendario
    ) -> None:
        lineas: list[str] = []
        pasos = iter([CONDUCTOR, "1", KeyboardInterrupt, "2", "3"])

        def entrada(prompt: str = "") -> str:
            try:
                paso = next(pasos)
            except StopIteration:
                raise EOFError from None
            if paso == "2":
                reloj.avanzar(60)  # un minuto pensando con la pregunta en pantalla
            if paso is KeyboardInterrupt:
                raise paso
            return paso

        TaximetroApp(
            servicio=servicio_de_prueba(Taximetro(reloj=reloj, calendario=calendario)),
            entrada=entrada,
            salida=lineas.append,
            entrada_oculta=teclea_la_buena,
        ).ejecutar()
        # 60 s en movimiento a 0,05 €/s.
        assert "TOTAL A COBRAR: 3,00 €" in lineas

    def test_eof_sin_carrera_sale_limpiamente(self, reloj, calendario) -> None:
        lineas = self._sesion_conductor(reloj, calendario, [])
        assert not any("TOTAL A COBRAR" in linea for linea in lineas)

    def test_eof_durante_una_carrera_cobra_antes_de_salir(
        self, reloj, calendario
    ) -> None:
        # Sin esto, cerrar el terminal a mitad de carrera perdería el importe
        # del pasajero (y soltaría un traceback).
        lineas = self._sesion_conductor(reloj, calendario, ["1"])
        assert any(linea.startswith("TOTAL A COBRAR") for linea in lineas)


class AuthIlegible:
    """Unas credenciales que no se pueden leer (fichero ausente o roto)."""

    def comprobar(self, contrasena: str) -> bool:
        raise CredencialesError("sin fichero")


class TestContrasenaDelAdministrador:
    """US-08 en el CLI (T8.5): mismas reglas que la pantalla de contraseña."""

    @pytest.fixture
    def ejecutar(self):
        """Corre una sesión; `claves` es lo que se teclea en la contraseña, en orden.

        Un elemento que sea una excepción (KeyboardInterrupt, EOFError) se lanza
        en vez de teclearse. Devuelve las líneas impresas.
        """

        def _ejecutar(opciones, claves, auth=None) -> list[str]:
            pendientes = iter(claves)

            def entrada_oculta(prompt: str = "") -> str:
                clave = next(pendientes)
                if isinstance(clave, type) and issubclass(clave, BaseException):
                    raise clave
                return clave

            lineas: list[str] = []
            TaximetroApp(
                servicio=ServicioTaximetro(Taximetro(), auth or AuthFalso()),
                entrada=EntradaGuionizada(opciones),
                salida=lineas.append,
                entrada_oculta=entrada_oculta,
            ).ejecutar()
            return lineas

        return _ejecutar

    def test_la_correcta_abre_el_administrador(self, ejecutar) -> None:
        lineas = ejecutar(["2", ADMIN_VOLVER, "3"], [CONTRASENA])
        assert menus(lineas, ADMINISTRADOR + "\n")

    def test_tras_un_fallo_se_vuelve_a_pedir(self, ejecutar) -> None:
        lineas = ejecutar(["2", ADMIN_VOLVER, "3"], ["otra", CONTRASENA])
        assert lineas.count(CONTRASENA_INCORRECTA) == 1
        assert menus(lineas, ADMINISTRADOR + "\n")

    def test_vacia_vuelve_al_menu_de_inicio(self, ejecutar) -> None:
        lineas = ejecutar(["2", "3"], [""])
        assert not menus(lineas, ADMINISTRADOR + "\n")
        assert CONTRASENA_INCORRECTA not in lineas

    def test_ctrl_c_vuelve_al_menu_de_inicio(self, ejecutar) -> None:
        # Como en Cambiar tarifas: Ctrl+C cancela, no cierra el programa.
        lineas = ejecutar(["2", "3"], [KeyboardInterrupt])
        assert not menus(lineas, ADMINISTRADOR + "\n")
        assert len(menus(lineas, "\nMenú de inicio")) == 2

    def test_eof_cierra_el_programa(self, eventos, ejecutar) -> None:
        ejecutar(["2"], [EOFError])
        assert "aplicacion_cerrada motivo=eof" in eventos()

    def test_sin_credenciales_avisa_y_no_insiste(self, ejecutar) -> None:
        # Reintentar no arregla un fichero que falta: se avisa y se vuelve.
        lineas = ejecutar(["2", "3"], [CONTRASENA], auth=AuthIlegible())
        assert CREDENCIALES_NO_DISPONIBLES in lineas
        assert not menus(lineas, ADMINISTRADOR + "\n")

    def test_cada_entrada_la_vuelve_a_pedir(self, ejecutar) -> None:
        # Volver y entrar otra vez pide otra vez la contraseña.
        lineas = ejecutar(["2", ADMIN_VOLVER, "2", ADMIN_VOLVER, "3"], [CONTRASENA, CONTRASENA])
        assert len(menus(lineas, ADMINISTRADOR + "\n")) == 2

    def test_la_contrasena_no_se_imprime(self, ejecutar) -> None:
        lineas = ejecutar(["2", ADMIN_VOLVER, "3"], ["una-errata", CONTRASENA])
        assert "una-errata" not in texto(lineas)
        assert CONTRASENA not in texto(lineas)


class TestLeerContrasena:
    """La entrada oculta por defecto del CLI."""

    def test_en_una_terminal_usa_getpass(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class Terminal:
            def isatty(self) -> bool:
                return True

        monkeypatch.setattr("sys.stdin", Terminal())
        monkeypatch.setattr("getpass.getpass", lambda pregunta: "oculta")
        assert leer_contrasena("Contraseña: ") == "oculta"

    def test_con_la_entrada_redirigida_lee_una_linea(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # En Windows `getpass` ignoraría la entrada redirigida y se quedaría
        # esperando al teclado.
        class Tuberia:
            def isatty(self) -> bool:
                return False

        monkeypatch.setattr("sys.stdin", Tuberia())
        monkeypatch.setattr("builtins.input", lambda pregunta: "de-la-tuberia")
        assert leer_contrasena("Contraseña: ") == "de-la-tuberia"

    def test_es_la_entrada_oculta_por_defecto(self) -> None:
        app = TaximetroApp(servicio_de_prueba(Taximetro()))
        assert app._entrada_oculta is leer_contrasena


class TestCambiarTarifas:
    """T7.6: el Administrador cambia las tarifas y se aplican a la próxima carrera.

    Menú de Administrador: 1 Cambiar tarifas · 2 Ver histórico · 3 Volver.
    """

    ADMIN_TARIFAS = ("2", "1")  # Administrador -> Cambiar tarifas

    def test_muestra_las_tarifas_vigentes_antes_de_pedir(self, sesion_libre) -> None:
        lineas = sesion_libre(*self.ADMIN_TARIFAS)
        assert "Tarifas vigentes: parado 0,02 €/s · en movimiento 0,05 €/s" in lineas

    def test_guarda_y_confirma_las_tarifas_nuevas(self, sesion_libre) -> None:
        lineas = sesion_libre(*self.ADMIN_TARIFAS, "0,03", "0,06")
        assert (
            "Tarifas guardadas: parado 0,03 €/s · en movimiento 0,06 €/s. "
            "Se aplican desde la próxima carrera."
        ) in lineas

    def test_acepta_punto_decimal(self, sesion_libre) -> None:
        lineas = sesion_libre(*self.ADMIN_TARIFAS, "0.03", " 0.06 ")
        assert any(linea.startswith("Tarifas guardadas") for linea in lineas)

    def test_la_proxima_carrera_cobra_la_tarifa_nueva(self, sesion_libre) -> None:
        # Administrador -> cambiar -> Volver -> Conductor -> Iniciar carrera
        lineas = sesion_libre(*self.ADMIN_TARIFAS, "0,03", "0,06", ADMIN_VOLVER, "1", "1")
        assert "Carrera nº 1 iniciada · EN MOVIMIENTO · 0,06 €/s" in lineas

    def test_la_ayuda_muestra_las_tarifas_nuevas(self, sesion_libre) -> None:
        salida = texto(sesion_libre(*self.ADMIN_TARIFAS, "0,03", "0,06", ADMIN_VOLVER, "1", "2"))
        assert "En movimiento ........ 0,06 €/s" in salida

    def test_tras_cambiar_vuelve_al_menu_de_administrador(self, sesion_libre) -> None:
        lineas = sesion_libre(*self.ADMIN_TARIFAS, "0,03", "0,06")
        assert lineas[-1].startswith(ADMINISTRADOR)

    @pytest.mark.parametrize(
        ("parado", "en_movimiento", "mensaje"),
        [
            ("0,06", "0,05", "no puede ser mayor"),
            ("0", "0,05", "mayor que 0"),
            ("0,025", "0,05", "2 decimales"),
            ("0,02", "2", "como máximo 1,00"),
        ],
    )
    def test_rechaza_tarifas_invalidas_sin_cambiar_nada(
        self, sesion_libre, parado: str, en_movimiento: str, mensaje: str
    ) -> None:
        lineas = sesion_libre(*self.ADMIN_TARIFAS, parado, en_movimiento, "1")
        rechazo = next(linea for linea in lineas if mensaje in linea)
        assert rechazo.endswith(NADA_GUARDADO)
        assert "Tarifas vigentes: parado 0,02 €/s · en movimiento 0,05 €/s" in lineas[-3:]

    def test_rechaza_lo_que_no_es_un_numero(self, sesion_libre) -> None:
        lineas = sesion_libre(*self.ADMIN_TARIFAS, "abc")
        assert (
            f"«abc» no es un número. Escribe, por ejemplo, 0,03. {NADA_GUARDADO}"
        ) in lineas
        # No llega a pedir la segunda tarifa: vuelve al menú de Administrador.
        assert lineas[-1].startswith(ADMINISTRADOR)

    def test_el_segundo_valor_tampoco_puede_ser_texto(self, sesion_libre) -> None:
        lineas = sesion_libre(*self.ADMIN_TARIFAS, "0,03", "")
        assert any("no es un número" in linea for linea in lineas)
        assert not any(linea.startswith("Tarifas guardadas") for linea in lineas)


class TestCambiarTarifasEnFichero:
    """T7.6 con fichero real: lo que guarda el Administrador sobrevive al cierre."""

    def _ejecutar(self, taximetro: Taximetro, *guion) -> list[str]:
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
            servicio=servicio_de_prueba(taximetro),
            entrada=entrada,
            salida=lineas.append,
            entrada_oculta=teclea_la_buena,
        ).ejecutar()
        return lineas

    def test_la_siguiente_sesion_arranca_con_las_tarifas_guardadas(
        self, tmp_path: Path
    ) -> None:
        ruta = tmp_path / "tarifas.json"
        self._ejecutar(Taximetro(config=ConfigTarifas(ruta)), "2", "1", "0,03", "0,06")
        salida = texto(self._ejecutar(Taximetro(config=ConfigTarifas(ruta))))
        assert "En movimiento ........ 0,06 €/s" in salida

    def test_si_no_se_puede_escribir_avisa_y_no_cambia_nada(self, tmp_path: Path) -> None:
        (tmp_path / "config").write_text("", encoding="utf-8")  # bloquea mkdir
        config = ConfigTarifas(tmp_path / "config" / "tarifas.json")
        lineas = self._ejecutar(Taximetro(config=config), "2", "1", "0,03", "0,06", "1")
        assert f"No se pudo escribir el fichero de tarifas. {NADA_GUARDADO}" in lineas
        assert "Tarifas vigentes: parado 0,02 €/s · en movimiento 0,05 €/s" in lineas[-3:]

    @pytest.mark.parametrize("guion", [[KeyboardInterrupt], ["0,03", KeyboardInterrupt]])
    def test_ctrl_c_mientras_se_teclea_cancela(self, tmp_path: Path, guion) -> None:
        ruta = tmp_path / "tarifas.json"
        taximetro = Taximetro(config=ConfigTarifas(ruta))
        lineas = self._ejecutar(taximetro, "2", "1", *guion)
        assert f"Cambio cancelado. {NADA_GUARDADO}" in lineas
        assert lineas[-1].startswith(ADMINISTRADOR)
        assert taximetro.tarifa.parado == 0.02
        assert ConfigTarifas(ruta).cargar().parado == 0.02


class Avanzar:
    """Paso de guion: deja pasar `segundos` en los dos relojes, sin teclear nada."""

    def __init__(self, segundos: float) -> None:
        self.segundos = segundos


class TestVerHistorico:
    """US-05 / T5.3: el Administrador ve las carreras de hoy y el total de caja.

    Menú de Administrador: 1 Cambiar tarifas · 2 Ver histórico · 3 Volver.
    """

    ADMIN_HISTORICO = ("2", "2")  # Administrador -> Ver histórico
    # Conductor -> Iniciar -> 60 s en movimiento (3,00 €) -> Finalizar -> Volver
    CARRERA_DE_3_EUROS = ("1", "1", Avanzar(60), "3", "3")

    @pytest.fixture
    def historial(self, tmp_path: Path) -> Historial:
        return Historial(tmp_path / "data" / "historial.csv")

    @pytest.fixture
    def ejecutar(self, historial, reloj, calendario):
        """Ejecuta un guion con histórico real; `Avanzar` y excepciones valen como pasos."""

        def _ejecutar(*guion, historial=historial) -> list[str]:
            lineas: list[str] = []
            pasos = iter(guion)

            def entrada(prompt: str = "") -> str:
                while True:
                    try:
                        paso = next(pasos)
                    except StopIteration:
                        raise EOFError from None
                    if isinstance(paso, Avanzar):
                        reloj.avanzar(paso.segundos)
                        calendario.avanzar(paso.segundos)
                        continue
                    if isinstance(paso, type) and issubclass(paso, BaseException):
                        raise paso
                    return paso

            taximetro = Taximetro(historial=historial, reloj=reloj, calendario=calendario)
            TaximetroApp(
                servicio=servicio_de_prueba(taximetro),
                entrada=entrada,
                salida=lineas.append,
                entrada_oculta=teclea_la_buena,
            ).ejecutar()
            return lineas

        return _ejecutar

    def test_el_menu_de_administrador_ofrece_el_historico(self, ejecutar) -> None:
        menu = menus(ejecutar("2"), ADMINISTRADOR + "\n")[0]
        assert "2) Ver histórico" in menu
        assert "3) Volver" in menu

    def test_sin_carreras(self, ejecutar) -> None:
        lineas = ejecutar(*self.ADMIN_HISTORICO)
        assert "Histórico de hoy · 01/06/2025\nNo hay carreras terminadas hoy." in lineas

    def test_lista_las_carreras_y_el_total(self, ejecutar) -> None:
        # Una de 3,00 € y otra de 20 s (1,00 €).
        lineas = ejecutar(
            *self.CARRERA_DE_3_EUROS,
            "1", "1", Avanzar(20), "3", "3",
            *self.ADMIN_HISTORICO,
        )
        tabla = next(linea for linea in lineas if linea.startswith("Histórico de hoy"))
        assert tabla.splitlines() == [
            "Histórico de hoy · 01/06/2025",
            "    Nº  Inicio    Fin          Importe",
            "     1  08:00:00  08:01:00      3,00 €",
            "     2  08:01:00  08:01:20      1,00 €",
            "  2 carreras · Total del día: 4,00 €",
        ]

    def test_una_sola_carrera_en_singular(self, ejecutar) -> None:
        salida = texto(ejecutar(*self.CARRERA_DE_3_EUROS, *self.ADMIN_HISTORICO))
        assert "1 carrera · Total del día: 3,00 €" in salida

    def test_tras_el_historico_vuelve_al_menu_de_administrador(self, ejecutar) -> None:
        lineas = ejecutar(*self.ADMIN_HISTORICO)
        assert lineas[-1].startswith(ADMINISTRADOR)

    def test_las_carreras_de_ayer_no_cuentan(self, ejecutar) -> None:
        lineas = ejecutar(*self.CARRERA_DE_3_EUROS, Avanzar(24 * 3600), *self.ADMIN_HISTORICO)
        assert any("No hay carreras terminadas hoy." in linea for linea in lineas)

    def test_el_historico_sobrevive_al_cierre(self, ejecutar) -> None:
        ejecutar(*self.CARRERA_DE_3_EUROS)
        salida = texto(ejecutar(*self.ADMIN_HISTORICO))
        assert "Total del día: 3,00 €" in salida

    def test_la_numeracion_sigue_en_la_siguiente_sesion(self, ejecutar) -> None:
        ejecutar(*self.CARRERA_DE_3_EUROS, *self.CARRERA_DE_3_EUROS)
        assert "Carrera nº 3 iniciada · EN MOVIMIENTO · 0,05 €/s" in ejecutar("1", "1")

    @pytest.mark.parametrize(
        "cierre",
        [
            pytest.param(("3",), id="finalizar"),
            pytest.param((KeyboardInterrupt, "1"), id="ctrl_c_si"),
            pytest.param((), id="eof"),
        ],
    )
    def test_todo_cierre_de_carrera_se_guarda(self, ejecutar, historial, cierre) -> None:
        ejecutar("1", "1", Avanzar(60), *cierre)
        assert [r.importe for r in historial.registros()] == [3.00]

    def test_si_no_se_puede_guardar_muestra_el_total_y_avisa(
        self, ejecutar, tmp_path: Path
    ) -> None:
        (tmp_path / "bloqueo").write_text("", encoding="utf-8")  # bloquea mkdir
        historial = Historial(tmp_path / "bloqueo" / "historial.csv")
        lineas = ejecutar("1", "1", Avanzar(60), "3", historial=historial)
        assert "TOTAL A COBRAR: 3,00 €" in lineas
        assert lineas[lineas.index("TOTAL A COBRAR: 3,00 €") + 1] == HISTORICO_NO_GUARDADO
        # La carrera está cerrada: el menú vuelve a ser el de sin carrera.
        assert lineas[-1].startswith("\nSin carrera")

    def test_si_no_se_puede_leer_lo_dice(self, ejecutar, historial) -> None:
        class HistorialIlegible(Historial):
            def resumen_del_dia(self, fecha):
                raise PermissionError

        lineas = ejecutar(*self.ADMIN_HISTORICO, historial=HistorialIlegible(historial.ruta))
        assert "No se pudo leer el histórico." in lineas
        assert lineas[-1].startswith(ADMINISTRADOR)


class TestLogs:
    """US-06 / T6.2: la capa CLI registra arranque, cierre y decisiones del usuario."""

    @pytest.fixture
    def guion(self, reloj, calendario):
        """Ejecuta un guion donde un paso puede ser una excepción a lanzar."""

        def _ejecutar(*pasos, taximetro=None) -> list[str]:
            lineas: list[str] = []
            restantes = iter(pasos)

            def entrada(prompt: str = "") -> str:
                try:
                    paso = next(restantes)
                except StopIteration:
                    raise EOFError from None
                if isinstance(paso, BaseException) or (
                    isinstance(paso, type) and issubclass(paso, BaseException)
                ):
                    raise paso
                return paso

            TaximetroApp(
                servicio=servicio_de_prueba(
                    taximetro or Taximetro(reloj=reloj, calendario=calendario)
                ),
                entrada=entrada,
                salida=lineas.append,
                entrada_oculta=teclea_la_buena,
            ).ejecutar()
            return lineas

        return _ejecutar

    def test_registra_el_arranque_con_las_tarifas(self, eventos, guion) -> None:
        guion("3")
        assert eventos()[0] == "aplicacion_iniciada parado=0.02 movimiento=0.05"

    @pytest.mark.parametrize(
        ("pasos", "motivo"),
        [
            pytest.param(("3",), "salir", id="salir"),
            pytest.param((KeyboardInterrupt,), "ctrl_c", id="ctrl_c"),
            pytest.param((), "eof", id="eof"),
            pytest.param(("1", "1", KeyboardInterrupt, "1"), "ctrl_c_con_carrera", id="ctrl_c_si"),
            pytest.param(("1", "1"), "eof_con_carrera", id="eof_carrera"),
        ],
    )
    def test_registra_el_cierre_y_su_motivo(self, eventos, guion, pasos, motivo) -> None:
        guion(*pasos)
        assert eventos()[-1] == f"aplicacion_cerrada motivo={motivo}"

    def test_registra_el_perfil_elegido(self, eventos, guion) -> None:
        guion("1", "3", "2", ADMIN_VOLVER, "3")
        assert "perfil_elegido perfil=conductor" in eventos()
        assert "perfil_elegido perfil=administrador" in eventos()

    @pytest.mark.parametrize(
        ("respuesta", "evento"),
        [("1", "salida_confirmada"), ("2", "salida_cancelada"), (KeyboardInterrupt, "salida_cancelada")],
    )
    def test_registra_la_respuesta_a_ctrl_c(self, eventos, guion, respuesta, evento) -> None:
        guion("1", "1", KeyboardInterrupt, respuesta)
        registrados = eventos()
        assert "salida_solicitada carrera=1" in registrados
        assert f"{evento} carrera=1" in registrados

    def test_una_tarifa_rechazada_es_warning(self, eventos, guion) -> None:
        guion("2", "1", "0,06", "0,05", "2", "1", "abc")
        assert eventos(logging.WARNING) == [
            "tarifa_rechazada parado=0.06 movimiento=0.05 "
            "motivo='La tarifa parado no puede ser mayor que la de en movimiento.'",
            "tarifa_rechazada tecleado='abc' motivo=no_numerica",
        ]

    def test_registra_el_cambio_cancelado(self, eventos, guion) -> None:
        guion("2", "1", KeyboardInterrupt)
        assert "cambio_tarifas_cancelado" in eventos()

    def test_registra_la_consulta_del_historico(
        self, eventos, guion, tmp_path: Path, reloj, calendario
    ) -> None:
        historial = Historial(tmp_path / "historial.csv")
        taximetro = Taximetro(historial=historial, reloj=reloj, calendario=calendario)
        guion("1", "1", "3", "3", "2", "2", taximetro=taximetro)
        assert "historico_consultado fecha=2025-06-01 carreras=1 total=0.00" in eventos()

    def test_un_historico_ilegible_es_error(self, eventos, guion, tmp_path: Path) -> None:
        class HistorialIlegible(Historial):
            def resumen_del_dia(self, fecha):
                raise PermissionError

        taximetro = Taximetro(historial=HistorialIlegible(tmp_path / "h.csv"))
        guion("2", "2", taximetro=taximetro)
        assert eventos(logging.ERROR) == ["historico_ilegible"]

    def test_un_error_inesperado_queda_registrado_con_su_traza(
        self, eventos, guion, caplog
    ) -> None:
        with pytest.raises(RuntimeError):
            guion(RuntimeError("fallo"))
        (registro,) = [r for r in caplog.records if r.getMessage() == "error_inesperado"]
        assert registro.levelno == logging.ERROR
        assert registro.exc_info is not None
        assert not any(e.startswith("aplicacion_cerrada") for e in eventos())
