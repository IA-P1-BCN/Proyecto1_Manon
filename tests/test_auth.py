"""Tests de `taximetro.auth.Auth` (US-08: T8.1, T8.2, T8.4).

Los ficheros de prueba usan un scrypt barato (`n` pequeño) para no gastar
50 ms en cada test; el coste va guardado en el fichero, igual que en el real.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from taximetro.auth import Auth, CredencialesError, RUTA_POR_DEFECTO

CONTRASENA = "clave-de-prueba"
BARATO = {"n": 2**4, "r": 8, "p": 1}


def escribir(ruta: Path, datos: object) -> Path:
    """Guarda `datos` como JSON en `ruta` y la devuelve."""
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    return ruta


@pytest.fixture
def auth(tmp_path: Path) -> Auth:
    """Un Auth cuyo fichero guarda el hash de CONTRASENA."""
    datos = Auth.generar_credenciales(CONTRASENA, **BARATO)
    return Auth(escribir(tmp_path / "credenciales.json", datos))


class TestComprobar:
    """US-08: correcta e incorrecta (T8.4)."""

    def test_la_contrasena_correcta_entra(self, auth: Auth) -> None:
        assert auth.comprobar(CONTRASENA) is True

    @pytest.mark.parametrize(
        "tecleada",
        ["otra", "", "Clave-de-prueba", "clave-de-prueba ", CONTRASENA[:-1]],
    )
    def test_cualquier_otra_no_entra(self, auth: Auth, tecleada: str) -> None:
        assert auth.comprobar(tecleada) is False

    def test_admite_caracteres_no_ascii(self, tmp_path: Path) -> None:
        datos = Auth.generar_credenciales("contraseña·€", **BARATO)
        auth = Auth(escribir(tmp_path / "c.json", datos))
        assert auth.comprobar("contraseña·€") is True
        assert auth.comprobar("contrasena·€") is False

    def test_relee_el_fichero_en_cada_comprobacion(self, auth: Auth) -> None:
        # El equipo técnico cambia la contraseña y vale sin reiniciar.
        escribir(auth.ruta, Auth.generar_credenciales("nueva", **BARATO))
        assert auth.comprobar("nueva") is True
        assert auth.comprobar(CONTRASENA) is False

    def test_usa_los_parametros_guardados_en_el_fichero(self, tmp_path: Path) -> None:
        # Si se sube el coste más adelante, las contraseñas ya guardadas siguen valiendo.
        datos = Auth.generar_credenciales(CONTRASENA, n=2**5, r=4, p=2)
        assert Auth(escribir(tmp_path / "c.json", datos)).comprobar(CONTRASENA) is True


class TestGenerarCredenciales:
    """T8.2: hash scrypt con sal, nunca la contraseña en claro."""

    def test_guarda_algoritmo_parametros_sal_y_hash(self) -> None:
        datos = Auth.generar_credenciales(CONTRASENA)
        assert datos["algoritmo"] == "scrypt"
        assert (datos["n"], datos["r"], datos["p"]) == (2**14, 8, 1)
        assert len(bytes.fromhex(datos["sal"])) == 16
        assert len(bytes.fromhex(datos["hash"])) == 32

    def test_no_contiene_la_contrasena(self) -> None:
        assert CONTRASENA not in json.dumps(Auth.generar_credenciales(CONTRASENA, **BARATO))

    def test_cada_vez_una_sal_distinta(self) -> None:
        # Con sal, la misma contraseña da hashes distintos: una tabla
        # precalculada no sirve.
        uno = Auth.generar_credenciales(CONTRASENA, **BARATO)
        otro = Auth.generar_credenciales(CONTRASENA, **BARATO)
        assert uno["sal"] != otro["sal"]
        assert uno["hash"] != otro["hash"]


class TestFicheroNoDisponible:
    """Sin fichero válido no se entra nunca, y se sabe por qué."""

    @pytest.mark.parametrize(
        "contenido",
        [
            "{no es json",
            "[1, 2, 3]",
            json.dumps({"algoritmo": "md5", "n": 16, "r": 8, "p": 1, "sal": "00", "hash": "00"}),
            json.dumps({"algoritmo": "scrypt", "n": 16, "r": 8, "p": 1, "sal": "00"}),
            json.dumps({"algoritmo": "scrypt", "n": 16, "r": 8, "p": 1, "sal": "zz", "hash": "00"}),
            json.dumps({"algoritmo": "scrypt", "n": 16, "r": 8, "p": 1, "sal": "00", "hash": ""}),
            json.dumps({"algoritmo": "scrypt", "n": 15, "r": 8, "p": 1, "sal": "00", "hash": "00"}),
            json.dumps({"algoritmo": "scrypt", "n": "16", "r": 8, "p": 1, "sal": "00", "hash": "00"}),
            json.dumps({"algoritmo": "scrypt", "n": True, "r": 8, "p": 1, "sal": "00", "hash": "00"}),
            json.dumps({"algoritmo": "scrypt", "n": 2**30, "r": 8, "p": 1, "sal": "00", "hash": "00"}),
        ],
        ids=[
            "json-roto",
            "no-es-objeto",
            "otro-algoritmo",
            "sin-hash",
            "hex-roto",
            "hash-vacio",
            "n-no-potencia-de-2",
            "n-texto",
            "n-booleano",
            "demasiada-memoria",
        ],
    )
    def test_un_fichero_roto_no_deja_entrar(self, tmp_path: Path, contenido: str) -> None:
        ruta = tmp_path / "c.json"
        ruta.write_text(contenido, encoding="utf-8")
        with pytest.raises(CredencialesError):
            Auth(ruta).comprobar(CONTRASENA)

    def test_sin_fichero_no_deja_entrar(self, tmp_path: Path) -> None:
        with pytest.raises(CredencialesError):
            Auth(tmp_path / "no-existe.json").comprobar(CONTRASENA)


class TestLogs:
    """US-06 en US-08: se registra el problema, nunca la contraseña."""

    def test_un_fichero_ilegible_es_error(self, eventos, tmp_path: Path) -> None:
        auth = Auth(tmp_path / "no-existe.json")
        with pytest.raises(CredencialesError):
            auth.comprobar(CONTRASENA)
        assert eventos(logging.ERROR) == [
            f"credenciales_ilegibles ruta={auth.ruta} error=FileNotFoundError"
        ]

    def test_comprobar_no_registra_la_contrasena(
        self, eventos, caplog, auth: Auth, tmp_path: Path
    ) -> None:
        auth.comprobar("una-errata-de-la-buena")
        with pytest.raises(CredencialesError):
            Auth(tmp_path / "no-existe.json").comprobar("una-errata-de-la-buena")
        assert "una-errata-de-la-buena" not in caplog.text


class TestFicheroVersionado:
    """T8.2: el `config/credenciales.json` que va en el repositorio."""

    RUTA = Path(__file__).resolve().parent.parent / RUTA_POR_DEFECTO

    def test_por_defecto_es_config_credenciales_json(self) -> None:
        assert RUTA_POR_DEFECTO == Path("config") / "credenciales.json"
        assert Auth().ruta == RUTA_POR_DEFECTO

    def test_es_legible_y_rechaza_una_contrasena_cualquiera(self) -> None:
        # La contraseña de la demo no se escribe en los tests
        # (`docs/decisions-fase3.md`): basta con que el fichero se pueda
        # comprobar sin CredencialesError, y que no deje entrar a cualquiera.
        assert Auth(self.RUTA).comprobar("no-es-la-contrasena") is False

    def test_usa_el_coste_real(self) -> None:
        datos = json.loads(self.RUTA.read_text(encoding="utf-8"))
        assert (datos["algoritmo"], datos["n"], datos["r"], datos["p"]) == ("scrypt", 2**14, 8, 1)
