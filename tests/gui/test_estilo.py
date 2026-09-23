"""Tests de `taximetro.gui.estilo`: el tema de la interfaz (T9.5).

Fijan las reglas táctiles del diseño y los colores aprobados, para que un
cambio de tema no las rompa sin que nadie se entere.
"""

from __future__ import annotations

import re

import pytest

from taximetro.gui import estilo
from taximetro.servicio_taximetro import Estado

HEX = re.compile(r"^#[0-9a-f]{6}$")


def fuentes_del_tema() -> dict[str, estilo.Fuente]:
    return {nombre: valor for nombre, valor in vars(estilo).items() if nombre.startswith("FUENTE_")}


class TestFuentes:
    """Texto mínimo de 24 px en toda la interfaz."""

    def test_rechaza_un_texto_por_debajo_del_minimo(self) -> None:
        with pytest.raises(ValueError, match="24 px"):
            estilo.fuente(23)

    def test_el_minimo_es_24_px(self) -> None:
        assert estilo.TEXTO_MIN == 24
        assert estilo.fuente(24)[1] == -24

    def test_el_tamano_va_en_pixeles(self) -> None:
        # Negativo = píxeles en tkinter: coincide con la maqueta en cualquier pantalla.
        assert estilo.fuente(56, negrita=True) == (estilo.FAMILIA, -56, "bold")

    @pytest.mark.parametrize("nombre", sorted(fuentes_del_tema()))
    def test_ninguna_fuente_del_tema_baja_del_minimo(self, nombre: str) -> None:
        familia, tamano, peso = fuentes_del_tema()[nombre]
        assert tamano <= -estilo.TEXTO_MIN, f"{nombre}: {-tamano} px"
        assert peso in ("normal", "bold")

    def test_la_familia_es_la_del_sistema(self) -> None:
        assert estilo.FAMILIA in ("Segoe UI", "DejaVu Sans")


class TestMedidasTactiles:
    """`docs/diseno-interfaz-fase3.md`, *Reglas de diseño táctil*."""

    def test_valores_aprobados(self) -> None:
        assert (estilo.ANCHO, estilo.ALTO) == (1280, 800)
        assert estilo.ZONA_TACTIL_MIN == 88
        assert estilo.TECLA_PRINCIPAL_MIN == 120
        assert estilo.SEPARACION >= 24
        assert estilo.LATERAL == 240

    @pytest.mark.parametrize(
        "alto",
        ["TECLA_PRINCIPAL_MIN", "TECLA_LATERAL", "TECLA_CONFIRMAR", "TECLA_ENTRAR",
         "TECLA_GUARDAR", "CAMPO"],
    )
    def test_nada_pulsable_por_debajo_de_la_zona_tactil(self, alto: str) -> None:
        assert getattr(estilo, alto) >= estilo.ZONA_TACTIL_MIN


class TestColores:
    def test_colores_aprobados(self) -> None:
        # La tabla *Colores y estados* del diseño.
        assert (estilo.FONDO, estilo.VISOR_FONDO) == ("#1c1c1c", "#070707")
        assert (estilo.LED_ROJO, estilo.LED_ROJO_APAGADO) == ("#ff2a1a", "#260806")
        assert estilo.OCUPADO_ENCENDIDA.fondo == "#c62828"
        assert estilo.LIBRE_ENCENDIDA.fondo == "#1e7a3c"
        assert estilo.ROJA.fondo == "#8e1b17"
        assert estilo.VERDE.fondo == "#1e6b37"

    def test_todos_son_hex_de_seis_cifras(self) -> None:
        valores = [v for n, v in vars(estilo).items() if n.isupper() and isinstance(v, str)]
        colores = [v for v in valores if v.startswith("#")]
        for objeto in vars(estilo).values():
            if isinstance(objeto, (estilo.Lampara, estilo.Variante, estilo.AspectoEstado)):
                colores += [v for v in vars(objeto).values() if v.startswith("#")]
        assert colores and all(HEX.match(color) for color in colores), colores


class TestEstados:
    """El estado se ve de un vistazo, y nunca solo por el color."""

    def test_cada_estado_tiene_color_y_texto(self) -> None:
        assert set(estilo.ESTADOS) == set(Estado)
        for aspecto in estilo.ESTADOS.values():
            assert aspecto.texto
            assert HEX.match(aspecto.color)

    def test_en_movimiento_verde_parado_ambar(self) -> None:
        assert estilo.ESTADOS[Estado.EN_MOVIMIENTO] == estilo.AspectoEstado("#3ddc6e", "EN MOVIMIENTO")
        assert estilo.ESTADOS[Estado.PARADO] == estilo.AspectoEstado("#ffb020", "PARADO")


class TestAclarar:
    def test_mezcla_con_blanco(self) -> None:
        assert estilo.aclarar("#000000", 0.5) == "#808080"
        assert estilo.aclarar("#ffffff") == "#ffffff"

    def test_una_tecla_pulsada_se_ve_mas_clara(self) -> None:
        pulsada = estilo.ROJA.pulsada
        assert HEX.match(pulsada)
        assert int(pulsada[1:3], 16) > int(estilo.ROJA.fondo[1:3], 16)
