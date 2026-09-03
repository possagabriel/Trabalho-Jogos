"""Testes do apresentador OpenGL."""

import ctypes

import pygame

from game.config import ALTURA, LARGURA
from game.gpu_renderer import ApresentadorGPU, viewport_opengl


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
