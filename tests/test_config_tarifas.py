"""Tests de `taximetro.config_tarifas.ConfigTarifas` (US-07 / T7.1, T7.2, T7.4).

Cada test trabaja en su propia carpeta temporal (`tmp_path`): ninguno toca el
`config/tarifas.json` del repo.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from taximetro.config_tarifas import RUTA_POR_DEFECTO, ConfigTarifas
from taximetro.tarifa import Tarifa


@pytest.fixture
def ruta(tmp_path: Path) -> Path:
    """Ruta del fichero de tarifas dentro de una carpeta que aún no existe."""
    return tmp_path / "config" / "tarifas.json"


def escribir(ruta: Path, contenido: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")


class TestFicheroValido:
    def test_lee_las_tarifas_del_fichero(self, ruta: Path) -> None:
        escribir(ruta, '{"parado": 0.03, "en_movimiento": 0.06}')
        tarifa = ConfigTarifas(ruta).cargar()
        assert (tarifa.parado, tarifa.en_movimiento) == (0.03, 0.06)

    def test_admite_enteros(self, ruta: Path) -> None:
        escribir(ruta, '{"parado": 1, "en_movimiento": 1}')
        assert ConfigTarifas(ruta).cargar().parado == 1

    def test_ignora_claves_de_mas(self, ruta: Path) -> None:
        escribir(ruta, '{"parado": 0.03, "en_movimiento": 0.06, "nota": "x"}')
        assert ConfigTarifas(ruta).cargar().en_movimiento == 0.06


class TestFicheroAusente:
    """US-07: si falta el fichero, valores por defecto sin que el programa falle."""

    def test_usa_las_tarifas_por_defecto(self, ruta: Path) -> None:
        tarifa = ConfigTarifas(ruta).cargar()
        assert (tarifa.parado, tarifa.en_movimiento) == (0.02, 0.05)

    def test_crea_el_fichero_para_el_tecnico(self, ruta: Path) -> None:
        ConfigTarifas(ruta).cargar()
        assert json.loads(ruta.read_text(encoding="utf-8")) == {
            "parado": 0.02,
            "en_movimiento": 0.05,
        }

    def test_sin_permiso_de_escritura_sigue_con_los_valores_por_defecto(
        self, tmp_path: Path
    ) -> None:
        # Un fichero ocupa el sitio de la carpeta: mkdir falla con OSError.
        (tmp_path / "config").write_text("", encoding="utf-8")
        tarifa = ConfigTarifas(tmp_path / "config" / "tarifas.json").cargar()
        assert tarifa.parado == 0.02


class TestFicheroInvalido:
    """US-07: fichero corrupto o con tarifas imposibles -> valores por defecto."""

    @pytest.mark.parametrize(
        "contenido",
        [
            "esto no es json",
            "",
            "[0.02, 0.05]",
            '"0.02"',
            '{"parado": 0.02}',
            '{"parado": "0,02", "en_movimiento": 0.05}',
            '{"parado": 0.06, "en_movimiento": 0.05}',
            '{"parado": 0, "en_movimiento": 0.05}',
        ],
    )
    def test_usa_las_tarifas_por_defecto(self, ruta: Path, contenido: str) -> None:
        escribir(ruta, contenido)
        tarifa = ConfigTarifas(ruta).cargar()
        assert (tarifa.parado, tarifa.en_movimiento) == (0.02, 0.05)

    def test_no_sobrescribe_el_fichero_del_tecnico(self, ruta: Path) -> None:
        # El técnico tiene que poder ver y corregir su error.
        escribir(ruta, '{"parado": 0.06, "en_movimiento": 0.05}')
        ConfigTarifas(ruta).cargar()
        assert ruta.read_text(encoding="utf-8") == '{"parado": 0.06, "en_movimiento": 0.05}'


class TestGuardar:
    def test_lo_guardado_se_vuelve_a_leer(self, ruta: Path) -> None:
        config = ConfigTarifas(ruta)
        config.guardar(Tarifa(parado=0.03, en_movimiento=0.07))
        tarifa = ConfigTarifas(ruta).cargar()
        assert (tarifa.parado, tarifa.en_movimiento) == (0.03, 0.07)

    def test_crea_la_carpeta_si_no_existe(self, ruta: Path) -> None:
        ConfigTarifas(ruta).guardar(Tarifa())
        assert ruta.exists()


class TestRuta:
    def test_por_defecto_es_config_tarifas_json(self) -> None:
        assert ConfigTarifas().ruta == RUTA_POR_DEFECTO == Path("config/tarifas.json")

    def test_el_ejemplo_versionado_es_un_fichero_valido(self) -> None:
        # config/tarifas.example.json documenta el formato. Se construye la
        # Tarifa directamente: `cargar()` caería en los valores por defecto,
        # que son los mismos, y el test pasaría con un ejemplo roto.
        ejemplo = Path(__file__).parent.parent / "config" / "tarifas.example.json"
        Tarifa(**json.loads(ejemplo.read_text(encoding="utf-8")))


class TestLogs:
    """US-06 / T6.2: el técnico ve en el log qué tarifas se cargaron y por qué."""

    def test_registra_las_tarifas_cargadas(self, eventos, ruta: Path) -> None:
        escribir(ruta, '{"parado": 0.03, "en_movimiento": 0.06}')
        ConfigTarifas(ruta).cargar()
        assert eventos() == [f"tarifas_cargadas ruta={ruta} parado=0.03 movimiento=0.06"]

    def test_registra_la_creacion_del_fichero(self, eventos, ruta: Path) -> None:
        ConfigTarifas(ruta).cargar()
        assert eventos() == [f"tarifas_creadas ruta={ruta}"]

    def test_un_fichero_invalido_es_warning_con_el_motivo(self, eventos, ruta: Path) -> None:
        escribir(ruta, '{"parado": 0.06, "en_movimiento": 0.05}')
        ConfigTarifas(ruta).cargar()
        (aviso,) = eventos(logging.WARNING)
        assert aviso.startswith(f"tarifas_invalidas ruta={ruta} error=TarifaInvalidaError")
        assert "parado no puede ser mayor" in aviso

    def test_no_poder_guardar_es_error(self, eventos, tmp_path: Path) -> None:
        (tmp_path / "config").write_text("", encoding="utf-8")  # bloquea mkdir
        ruta = tmp_path / "config" / "tarifas.json"
        with pytest.raises(OSError):
            ConfigTarifas(ruta).guardar(Tarifa())
        assert eventos(logging.ERROR) == [f"tarifas_no_guardadas ruta={ruta}"]
