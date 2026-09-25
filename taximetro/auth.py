"""Auth: comprueba la contraseña del Administrador (US-08)."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
from pathlib import Path

from taximetro.logs import campos

logger = logging.getLogger(__name__)

# Relativa al directorio desde el que se lanza el programa, igual que
# `config/tarifas.json`. A diferencia de las tarifas, este fichero se versiona:
# solo contiene la sal y el hash, nunca la contraseña.
RUTA_POR_DEFECTO = Path("config") / "credenciales.json"

# Coste de scrypt: unos 16 MB de memoria y ~50 ms por comprobación. Se guarda
# junto al hash, así que subirlo más adelante no invalida la contraseña actual.
N, R, P = 2**14, 8, 1
BYTES_SAL = 16
BYTES_HASH = 32
MEMORIA_MAXIMA = 64 * 1024 * 1024  # holgada para N, R, P; frena un fichero absurdo


class CredencialesError(Exception):
    """El fichero de credenciales falta o no se puede leer: no se puede comprobar.

    Nunca significa «contraseña correcta»: quien la reciba deniega el acceso.
    """


class Auth:
    """La contraseña del Administrador, guardada como hash scrypt con sal.

    Poner o cambiar la contraseña es cosa del equipo técnico, fuera de la
    aplicación (`docs/decisions-fase3.md`, *US-08*). Aquí solo se comprueba.
    """

    def __init__(self, ruta: Path = RUTA_POR_DEFECTO) -> None:
        """Apunta al fichero de credenciales, sin leerlo todavía."""
        self._ruta = Path(ruta)

    @property
    def ruta(self) -> Path:
        """Dónde está el fichero."""
        return self._ruta

    def comprobar(self, contrasena: str) -> bool:
        """True si `contrasena` es la del Administrador.

        Relee el fichero en cada comprobación, así que un cambio del equipo
        técnico vale sin reiniciar. Lanza `CredencialesError` si el fichero
        falta o está roto. La contraseña tecleada no se registra nunca, ni
        siquiera si es incorrecta: suele ser una errata de la buena.
        """
        try:
            datos = json.loads(self._ruta.read_text(encoding="utf-8"))
            if datos["algoritmo"] != "scrypt":
                raise ValueError(f"algoritmo desconocido: {datos['algoritmo']!r}")
            esperado = bytes.fromhex(datos["hash"])
            if not esperado:
                raise ValueError("hash vacío")
            calculado = _scrypt(
                contrasena,
                sal=bytes.fromhex(datos["sal"]),
                n=datos["n"],
                r=datos["r"],
                p=datos["p"],
                largo=len(esperado),
            )
        except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
            # ValueError cubre el JSON mal formado, el hexadecimal roto y los
            # parámetros que scrypt rechaza (incluido pasarse de memoria);
            # TypeError, un JSON que no es un objeto o un parámetro no entero.
            logger.error(
                "credenciales_ilegibles %s",
                campos(ruta=self._ruta, error=type(error).__name__),
            )
            raise CredencialesError(
                f"No se pueden leer las credenciales de {self._ruta}."
            ) from error
        # Tarda lo mismo falle en el primer byte o en el último: el tiempo de
        # respuesta no da pistas sobre el hash.
        return hmac.compare_digest(calculado, esperado)

    @staticmethod
    def generar_credenciales(
        contrasena: str, n: int = N, r: int = R, p: int = P
    ) -> dict[str, object]:
        """El contenido del fichero de credenciales para `contrasena`.

        No lo usa ninguna pantalla: sirvió para generar una vez el fichero de la
        demo, y los tests lo usan para crear los suyos.
        """
        sal = secrets.token_bytes(BYTES_SAL)
        return {
            "algoritmo": "scrypt",
            "n": n,
            "r": r,
            "p": p,
            "sal": sal.hex(),
            "hash": _scrypt(contrasena, sal=sal, n=n, r=r, p=p, largo=BYTES_HASH).hex(),
        }


def _scrypt(contrasena: str, sal: bytes, n: int, r: int, p: int, largo: int) -> bytes:
    """El hash scrypt de la contraseña, con un tope de memoria."""
    if not all(type(valor) is int for valor in (n, r, p)):
        raise TypeError("n, r y p deben ser enteros")
    return hashlib.scrypt(
        contrasena.encode("utf-8"),
        salt=sal,
        n=n,
        r=r,
        p=p,
        dklen=largo,
        maxmem=MEMORIA_MAXIMA,
    )
