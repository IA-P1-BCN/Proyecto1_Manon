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

from pathlib import Path
from typing import Iterable

import pytest

from taximetro.config_tarifas import ConfigTarifas
from taximetro.historial import Historial
from taximetro.taximetro import Taximetro
from taximetro.taximetro_app import (
    DESCRIPCIONES,
    HISTORICO_NO_GUARDADO,
    NADA_GUARDADO,
    OPCION_NO_VALIDA,
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


CONDUCTOR = "1"  # opción del menú de inicio
ADMIN_VOLVER = "3"  # Volver en el menú de Administrador
ADMINISTRADOR = "\nAdministrador"  # cómo empieza el menú de Administrador


@pytest.fixture
def sesion_libre(reloj, calendario):
    """Ejecuta una sesión desde el menú de inicio y devuelve las líneas impresas."""

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
            taximetro=Taximetro(reloj=reloj, calendario=calendario),
            entrada=entrada,
            salida=lineas.append,
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

    def test_el_taximetro_sigue_contando_durante_la_pregunta(
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
            taximetro=Taximetro(reloj=reloj, calendario=calendario),
            entrada=entrada,
            salida=lineas.append,
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

        TaximetroApp(taximetro=taximetro, entrada=entrada, salida=lineas.append).ejecutar()
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
            TaximetroApp(taximetro=taximetro, entrada=entrada, salida=lineas.append).ejecutar()
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
