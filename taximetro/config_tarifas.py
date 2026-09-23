"""ConfigTarifas: lee y guarda las tarifas en un fichero JSON (US-07)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from taximetro.logs import campos
from taximetro.tarifa import Tarifa, TarifaInvalidaError

logger = logging.getLogger(__name__)

# Relativa al directorio desde el que se lanza el programa, que es la raíz del
# repo (`python -m taximetro.taximetro_app`). Si en la Fase 4 se empaqueta, se
# revisa.
RUTA_POR_DEFECTO = Path("config") / "tarifas.json"


class ConfigTarifas:
    """El fichero de tarifas: `{"parado": 0.02, "en_movimiento": 0.05}` en €/s.

    Solo sabe de ficheros; las reglas de qué es una tarifa válida viven en
    `Tarifa`. Un técnico puede editar el fichero a mano (US-07) y el
    Administrador lo reescribe desde el menú (T7.6).
    """

    def __init__(self, ruta: Path = RUTA_POR_DEFECTO) -> None:
        """Apunta al fichero de tarifas, sin leerlo todavía."""
        self._ruta = Path(ruta)

    @property
    def ruta(self) -> Path:
        """Dónde está el fichero, para poder decírselo al técnico."""
        return self._ruta

    def cargar(self) -> Tarifa:
        """Devuelve las tarifas del fichero; nunca falla.

        Si el fichero no existe, lo crea con las tarifas por defecto. Si existe
        pero no es válido, usa las tarifas por defecto y **no** lo toca: es la
        edición a mano de un técnico, y sobrescribirla le borraría el error que
        tiene que corregir.
        """
        if not self._ruta.exists():
            tarifa = Tarifa()
            try:
                self.guardar(tarifa)
            except OSError:
                pass  # ya registrado por `guardar`; se sigue con las de por defecto
            else:
                logger.info("tarifas_creadas %s", campos(ruta=self._ruta))
            return tarifa

        try:
            datos = json.loads(self._ruta.read_text(encoding="utf-8"))
            tarifa = Tarifa(parado=datos["parado"], en_movimiento=datos["en_movimiento"])
        except (OSError, ValueError, KeyError, TypeError, TarifaInvalidaError) as error:
            # ValueError cubre el JSON mal formado (JSONDecodeError) y
            # TarifaInvalidaError; TypeError, un JSON que no es un objeto.
            logger.warning(
                "tarifas_invalidas %s",
                campos(ruta=self._ruta, error=type(error).__name__, detalle=repr(str(error))),
            )
            return Tarifa()
        logger.info(
            "tarifas_cargadas %s",
            campos(ruta=self._ruta, parado=tarifa.parado, movimiento=tarifa.en_movimiento),
        )
        return tarifa

    def guardar(self, tarifa: Tarifa) -> None:
        """Escribe las tarifas en el fichero, creando la carpeta si hace falta."""
        datos = {"parado": tarifa.parado, "en_movimiento": tarifa.en_movimiento}
        try:
            self._ruta.parent.mkdir(parents=True, exist_ok=True)
            self._ruta.write_text(json.dumps(datos, indent=2) + "\n", encoding="utf-8")
        except OSError:
            logger.error("tarifas_no_guardadas %s", campos(ruta=self._ruta), exc_info=True)
            raise
