"""Tests de estructura: el contrato de diseño acordado antes de implementar.

No comprueban comportamiento (eso es cosa de US-01 a US-04), sino que la API
pública es la que se decidió en `docs/decisions-fase1-scaffold.md`. Si alguien
renombra un método, le quita un parámetro inyectable o vuelve a poner el reloj
de pared, estos tests fallan y la decisión se revisa a conciencia en vez de
erosionarse sin querer.

Desde la Fase 3 también vigilan la frontera entre las interfaces y el dominio
(`docs/decisions-fase3.md`, *Structural refactor*).
"""

from __future__ import annotations

import ast
import inspect
import time
from datetime import datetime
from pathlib import Path

import pytest

from taximetro.auth import Auth
from taximetro.carrera import Carrera, CarreraFinalizadaError, Estado
from taximetro.servicio_taximetro import ServicioTaximetro
from taximetro.tarifa import Tarifa
from taximetro.taximetro import CarreraActivaError, Taximetro
from taximetro.taximetro_app import TaximetroApp
from taximetro.utils import formato_euros


def parametros(funcion) -> dict[str, inspect.Parameter]:
    """Devuelve los parámetros de `funcion` indexados por nombre."""
    return dict(inspect.signature(funcion).parameters)


class TestEstado:
    """El estado del vehículo es un Enum, no cadenas sueltas."""

    def test_tiene_los_dos_estados_del_briefing(self) -> None:
        assert Estado.PARADO.value == "parado"
        assert Estado.EN_MOVIMIENTO.value == "en_movimiento"


class TestCarrera:
    """Contrato de `Carrera` (US-01 a US-03, TD.4)."""

    def test_expone_la_api_acordada(self) -> None:
        assert callable(Carrera.cambiar_estado)
        assert callable(Carrera.finalizar)
        assert callable(Carrera.importe_actual), "TD.4: accesor de solo lectura"

    def test_recibe_la_tarifa_inyectada(self) -> None:
        assert "tarifa" in parametros(Carrera.__init__)

    def test_acumula_con_un_reloj_monotono(self) -> None:
        # Un reloj de pared puede retroceder (NTP, cambio manual) y restar
        # importe en silencio: el tramo se mide siempre con time.monotonic.
        reloj = parametros(Carrera.__init__)["reloj"]
        assert reloj.default is time.monotonic
        assert reloj.default is not time.time

    def test_sella_las_horas_con_un_calendario_aparte(self) -> None:
        calendario = parametros(Carrera.__init__)["calendario"]
        assert calendario.default == datetime.now


class TestTarifa:
    """Contrato de `Tarifa` (US-02)."""

    def test_calcula_por_estado_y_segundos(self) -> None:
        assert set(parametros(Tarifa.calcular_importe)) >= {"estado", "segundos"}


class TestTaximetro:
    """Contrato de `Taximetro` (US-01, US-04)."""

    def test_es_el_dueno_de_la_tarifa_y_los_relojes(self) -> None:
        esperados = {"tarifa", "reloj", "calendario"}
        assert esperados <= set(parametros(Taximetro.__init__))

    def test_inicia_carreras(self) -> None:
        assert callable(Taximetro.iniciar_carrera)

    def test_carga_y_cambia_tarifas_desde_la_configuracion(self) -> None:
        # US-07: la configuración entra por `Taximetro`, nunca por `Carrera`.
        assert "config" in parametros(Taximetro.__init__)
        assert "config" not in parametros(Carrera.__init__)
        assert callable(Taximetro.cambiar_tarifa)

    def test_cierra_carreras_y_resume_el_dia(self) -> None:
        # US-05: el histórico entra por `Taximetro`, que es quien cierra las
        # carreras; así ningún camino de cierre se queda sin guardar.
        assert "historial" in parametros(Taximetro.__init__)
        assert callable(Taximetro.finalizar_carrera)
        assert callable(Taximetro.resumen_del_dia)


class TestServicioTaximetro:
    """Contrato de la fachada que comparten las interfaces (Fase 3, T9.10).

    En la Fase 4 un cliente HTTP la sustituye con estos mismos métodos: si uno
    cambia de nombre, cambia el contrato de la futura API.
    """

    def test_envuelve_un_taximetro(self) -> None:
        assert "taximetro" in parametros(ServicioTaximetro.__init__)

    def test_recibe_el_auth_inyectado(self) -> None:
        # US-08: la contraseña entra por el servicio, que la comparten las dos
        # interfaces; sin `auth` el acceso se deniega.
        auth = parametros(ServicioTaximetro.__init__)["auth"]
        assert auth.default is None

    @pytest.mark.parametrize(
        "metodo",
        [
            "iniciar_carrera",
            "cambiar_estado",
            "estado_actual",
            "finalizar_carrera",
            "tarifas",
            "cambiar_tarifas",
            "resumen_del_dia",
            "comprobar_contrasena",
        ],
    )
    def test_expone_la_api_acordada(self, metodo: str) -> None:
        assert callable(getattr(ServicioTaximetro, metodo))


class TestAuth:
    """Contrato de `Auth` (US-08, T8.1)."""

    def test_comprueba_contra_un_fichero_inyectable(self) -> None:
        assert "ruta" in parametros(Auth.__init__)
        assert "contrasena" in parametros(Auth.comprobar)


class TestTaximetroApp:
    """Contrato de la capa CLI (US-04, EPIC D)."""

    def test_acepta_entrada_y_salida_inyectables(self) -> None:
        # Sin esta costura no se pueden testear los menús, los mensajes de
        # error ni Ctrl+C (TD.9).
        params = parametros(TaximetroApp.__init__)
        assert {"entrada", "salida"} <= set(params)
        assert params["entrada"].default is input
        assert params["salida"].default is print

    def test_tiene_bucle_principal(self) -> None:
        assert callable(TaximetroApp.ejecutar)


class TestExcepcionesDelDominio:
    """Las garantías del dominio son excepciones propias, no genéricas."""

    def test_son_excepciones_propias(self) -> None:
        assert issubclass(CarreraActivaError, Exception)
        assert issubclass(CarreraFinalizadaError, Exception)


class TestUtils:
    """Contrato del formateo de euros (T3.2)."""

    def test_existe_el_helper_de_formato(self) -> None:
        assert callable(formato_euros)
        assert "importe" in parametros(formato_euros)


# ----------------------------------------------------------------------
# Frontera interfaces / dominio (Fase 3, T9.12)
# ----------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parent.parent
PAQUETE = RAIZ / "taximetro"

# Lo único del paquete que una interfaz puede importar. `logs` y `utils` no son
# dominio: dan formato a los eventos y a los euros. Todo lo demás llega a través
# del servicio, que en la Fase 4 se sustituye por un cliente HTTP.
PERMITIDOS_A_LAS_INTERFACES = (
    "taximetro.servicio_taximetro",
    "taximetro.logs",
    "taximetro.utils",
)


def modulos_de_interfaz() -> list[Path]:
    """El CLI y todo lo que haya bajo `taximetro/gui/`, exista ya o no."""
    return [PAQUETE / "taximetro_app.py", *sorted((PAQUETE / "gui").rglob("*.py"))]


def nombre_de_modulo(ruta: Path) -> str:
    """`taximetro/gui/inicio.py` → `taximetro.gui.inicio`."""
    partes = ruta.relative_to(RAIZ).with_suffix("").parts
    return ".".join(partes[:-1] if partes[-1] == "__init__" else partes)


def importaciones_prohibidas(fuente: str, modulo: str, es_paquete: bool = False) -> list[str]:
    """Lo que `fuente` importa del paquete `taximetro` sin estar permitido.

    Usa `ast`, no expresiones regulares: ignora comentarios y cadenas, y ve
    también los imports dentro de funciones o bajo `TYPE_CHECKING`. Los
    relativos se resuelven, así que `from ..carrera import Carrera` no se cuela.
    Cada interfaz puede importar además de su propio paquete (p. ej. las
    pantallas de `taximetro.gui` entre sí).
    """
    paquete = modulo if es_paquete else modulo.rpartition(".")[0]
    propio = paquete if paquete != "taximetro" else modulo
    permitidos = (*PERMITIDOS_A_LAS_INTERFACES, propio)

    destinos: list[str] = []
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Import):
            destinos += [alias.name for alias in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            base = nodo.module or ""
            if nodo.level:
                partes = paquete.split(".")[: len(paquete.split(".")) - (nodo.level - 1)]
                base = ".".join([*partes, base] if base else partes)
            destinos += [f"{base}.{alias.name}" for alias in nodo.names]

    def permitido(destino: str) -> bool:
        return any(destino == p or destino.startswith(p + ".") for p in permitidos)

    return [
        destino
        for destino in destinos
        if (destino == "taximetro" or destino.startswith("taximetro."))
        and not permitido(destino)
    ]


class TestFronteraDeLasInterfaces:
    """Las interfaces solo conocen el servicio (US-09: «sin duplicarla»).

    Si una pantalla o el CLI importara `Carrera`, `Tarifa` o `Taximetro`,
    podría saltarse el servicio, y el día que este sea un cliente HTTP esa
    interfaz dejaría de funcionar.
    """

    @pytest.mark.parametrize(
        "ruta", modulos_de_interfaz(), ids=lambda ruta: nombre_de_modulo(ruta)
    )
    def test_solo_importa_el_servicio(self, ruta: Path) -> None:
        fuente = ruta.read_text(encoding="utf-8")
        modulo = nombre_de_modulo(ruta)
        prohibidas = importaciones_prohibidas(fuente, modulo, ruta.name == "__init__.py")
        assert prohibidas == [], (
            f"{modulo} importa del dominio {prohibidas}; "
            "debe pasar por taximetro.servicio_taximetro"
        )

    @pytest.mark.parametrize(
        "fuente",
        [
            "from taximetro.carrera import Carrera",
            "import taximetro.taximetro",
            "from taximetro import tarifa",
            "from ..historial import Historial",
            "def f():\n    from taximetro.tarifa import Tarifa",
            "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n"
            "    from taximetro.carrera import Carrera",
        ],
    )
    def test_el_comprobador_detecta_cada_forma_de_colarse(self, fuente: str) -> None:
        # Sin esto, un comprobador roto daría el test de arriba por bueno.
        assert importaciones_prohibidas(fuente, "taximetro.gui.pantalla") != []

    @pytest.mark.parametrize(
        "fuente",
        [
            "from taximetro.servicio_taximetro import Estado, ServicioTaximetro",
            "from taximetro.utils import formato_euros",
            "from taximetro.logs import campos",
            "from taximetro.gui.estilo import COLORES",
            "from .estilo import COLORES",
            "import tkinter as tk",
        ],
    )
    def test_el_comprobador_deja_pasar_lo_permitido(self, fuente: str) -> None:
        assert importaciones_prohibidas(fuente, "taximetro.gui.pantalla") == []

    def test_el_cli_no_puede_importar_de_otras_interfaces_como_propias(self) -> None:
        # El CLI vive en la raíz del paquete: «su propio paquete» es él mismo,
        # no todo `taximetro`, o cualquier import del dominio pasaría.
        assert importaciones_prohibidas(
            "from taximetro.carrera import Carrera", "taximetro.taximetro_app"
        ) == ["taximetro.carrera.Carrera"]
