"""Configuración de los logs de operación (US-06).

Cada módulo escribe en su propio logger (`logging.getLogger(__name__)`), todos
colgando de `taximetro`. Este módulo solo decide *adónde* van: un fichero con
rotación. Lo llama únicamente el programa real (`__main__`), así que los tests
y cualquier otro uso del paquete nunca escriben en disco; los tests leen los
eventos con `caplog`.

Formato: una línea por evento, `evento clave=valor ...`, para poder buscar con
grep sin parsear frases.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

RUTA_POR_DEFECTO = Path("logs") / "taximetro.log"
TAMANO_MAXIMO = 1_000_000  # bytes por fichero antes de rotar
COPIAS = 5  # taximetro.log.1 … taximetro.log.5; la más antigua se descarta

FORMATO = "%(asctime)s %(levelname)s %(name)s %(message)s"
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"

LOGGER_RAIZ = "taximetro"


def configurar_logs(ruta: Path = RUTA_POR_DEFECTO) -> logging.Handler:
    """Envía los eventos del paquete a `ruta`, con rotación; devuelve el handler.

    Nunca impide arrancar: si el fichero no se puede abrir, el taxímetro sigue
    funcionando sin logs. Llamarla dos veces sustituye el handler anterior en
    vez de duplicar cada línea.
    """
    raiz = logging.getLogger(LOGGER_RAIZ)
    raiz.setLevel(logging.INFO)
    for anterior in [h for h in raiz.handlers if getattr(h, "_taximetro", False)]:
        raiz.removeHandler(anterior)
        anterior.close()

    try:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler = RotatingFileHandler(
            ruta, maxBytes=TAMANO_MAXIMO, backupCount=COPIAS, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter(FORMATO, FORMATO_FECHA))
    except OSError:
        # Sin un handler, `logging` imprimiría los WARNING en la consola del
        # conductor; un NullHandler los descarta en silencio.
        handler = logging.NullHandler()

    handler._taximetro = True  # type: ignore[attr-defined]
    raiz.addHandler(handler)
    return handler


def campos(**valores: object) -> str:
    """`clave=valor` separados por espacios, en el orden dado.

    Los importes (float) salen con dos decimales, como en el ticket.
    """
    return " ".join(
        f"{clave}={valor:.2f}" if isinstance(valor, float) else f"{clave}={valor}"
        for clave, valor in valores.items()
    )
