"""Tests de `python -m taximetro` (`taximetro/__main__.py`): el arranque de la interfaz."""

from __future__ import annotations

import taximetro.__main__ as principal


def test_configura_los_logs_y_abre_la_app_sobre_el_servicio_real(monkeypatch) -> None:
    pasos: list[object] = []
    servicio = object()

    class AppFalsa:
        def __init__(self, recibido) -> None:
            pasos.append(("app", recibido))

        def ejecutar(self) -> None:
            pasos.append("ejecutar")

    monkeypatch.setattr(principal, "configurar_logs", lambda: pasos.append("logs"))
    monkeypatch.setattr(principal.ServicioTaximetro, "por_defecto", classmethod(lambda cls: servicio))
    monkeypatch.setattr(principal, "App", AppFalsa)

    principal.main()

    # Los logs primero, para que quede registrada también la carga de tarifas.
    assert pasos == ["logs", ("app", servicio), "ejecutar"]
