"""Tests de `taximetro.gui.pantalla.Pantalla`: la base de las pantallas (T9.3).

Lo importante son los temporizadores: el refresco del importe cada 200 ms
(T9.13) no puede seguir llamando a una pantalla que ya no está.
"""

from __future__ import annotations

from taximetro.gui.app import App
from taximetro.gui.pantalla import Pantalla


class Vacia(Pantalla):
    """Una pantalla sin nada, para probar la base."""


class TestProgramar:
    def test_llama_a_la_funcion_pasado_el_tiempo(self, app: App, procesar) -> None:
        llamadas: list[str] = []
        app.mostrar(Vacia).programar(10, lambda: llamadas.append("tic"))
        procesar(0.2)
        assert llamadas == ["tic"]

    def test_salir_de_la_pantalla_cancela_lo_pendiente(self, app: App, procesar) -> None:
        llamadas: list[str] = []
        app.mostrar(Vacia).programar(50, lambda: llamadas.append("tic"))
        app.mostrar(Vacia)  # se cambia de pantalla antes de que llegue
        procesar(0.2)
        assert llamadas == []

    def test_un_temporizador_ya_disparado_no_molesta_al_salir(
        self, app: App, procesar
    ) -> None:
        # Cancelar un `after` que ya se ejecutó daría error en tkinter.
        pantalla = app.mostrar(Vacia)
        pantalla.programar(1, lambda: None)
        procesar(0.1)
        app.mostrar(Vacia)
        assert not pantalla.winfo_exists()

    def test_devuelve_el_identificador_de_after(self, app: App) -> None:
        identificador = app.mostrar(Vacia).programar(1000, lambda: None)
        assert isinstance(identificador, str) and identificador.startswith("after")
