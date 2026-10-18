"""Testes do apresentador OpenGL."""

import ctypes

import pygame

from game.config import ALTURA, LARGURA
from game.gpu_renderer import (
    FRAGMENT_SHADER,
    FRAGMENT_SHADER_330,
    VERTEX_SHADER_330,
    ApresentadorGPU,
    normalizar_intensidade,
    viewport_opengl,
)


def test_viewport_opengl_inverte_apenas_o_eixo_vertical():
    assert viewport_opengl((100, 50, 900, 700), 1080) == (100, 330, 900, 700)


def test_viewport_opengl_impede_dimensoes_nulas():
    assert viewport_opengl((0, 0, 0, 0), 720) == (0, 720, 1, 1)


def test_upload_reutiliza_buffer_da_surface_nativa_sem_copia():
    apresentador = object.__new__(ApresentadorGPU)
    apresentador.largura = LARGURA
    apresentador.altura = ALTURA
    apresentador._tipo_buffer = ctypes.c_ubyte * (LARGURA * ALTURA * 4)
    superficie = pygame.Surface((LARGURA, ALTURA))
    pixels, _ = apresentador._pixels(superficie)
    assert isinstance(pixels, ctypes.Array)
    pixels[0] = 255
    assert superficie.get_at((0, 0)).b == 255


def test_upload_converte_surface_com_formato_diferente():
    apresentador = object.__new__(ApresentadorGPU)
    apresentador.largura = 10
    apresentador.altura = 10
    apresentador._tipo_buffer = ctypes.c_ubyte * (10 * 10 * 4)
    superficie = pygame.Surface((10, 10), depth=24)
    pixels, _ = apresentador._pixels(superficie)
    assert isinstance(pixels, bytes)


def test_intensidade_do_shader_e_normalizada():
    assert normalizar_intensidade(-1) == 0.0
    assert normalizar_intensidade(2) == 1.0
    assert normalizar_intensidade("0.35") == 0.35
    assert normalizar_intensidade("invalida") == 0.7


def test_shader_contem_os_efeitos_comic_esperados():
    assert "posterizada" in FRAGMENT_SHADER
    assert "sobel_x" in FRAGMENT_SHADER
    assert "hachura" in FRAGMENT_SHADER
    assert "grao" in FRAGMENT_SHADER
    assert "luz_posterizada" in FRAGMENT_SHADER
    assert "posicao_logica" in FRAGMENT_SHADER
    assert "gl_FragCoord" not in FRAGMENT_SHADER


def test_shader_moderno_usa_vbo_e_saida_explicita():
    assert "#version 330 core" in VERTEX_SHADER_330
    assert "layout(location = 0)" in VERTEX_SHADER_330
    assert "out vec4 cor_saida" in FRAGMENT_SHADER_330


def test_configuracao_do_shader_mapeia_qualidade_e_estado():
    apresentador = object.__new__(ApresentadorGPU)

    apresentador.configurar_shader(
        True, 2.0, "ALTA", contorno=0.4, tons=6, hachuras=False,
        grao=0.2, saturacao=1.4, preservar_interface=False)
    assert apresentador.shader_ativo is True
    assert apresentador.intensidade_shader == 1.0
    assert apresentador.qualidade_shader == 1.0
    assert apresentador.contorno_shader == 0.4
    assert apresentador.tons_shader == 6
    assert apresentador.hachuras_shader is False
    assert apresentador.grao_shader == 0.2
    assert apresentador.saturacao_shader == 1.4
    assert apresentador.preservar_interface is False

    apresentador.configurar_shader(False, -1.0, "desconhecida")
    assert apresentador.shader_ativo is False
    assert apresentador.intensidade_shader == 0.0
    assert apresentador.qualidade_shader == 0.5


def test_falha_de_shader_fica_registrada(caplog):
    apresentador = object.__new__(ApresentadorGPU)
    apresentador.erros_shader = []

    apresentador._registrar_erro("GLSL teste", RuntimeError("codigo invalido"))

    assert apresentador.erros_shader == ["GLSL teste: codigo invalido"]
    assert "codigo invalido" in caplog.text
