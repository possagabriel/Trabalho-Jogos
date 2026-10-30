"""Validacao opt-in do shader em um contexto OpenGL real (Mesa/driver)."""

from __future__ import annotations

import os

import pygame
import pytest

pytestmark = pytest.mark.gpu


def test_shader_compila_e_renderiza_cena_com_interface_preservada():
    if os.environ.get("RUN_GPU_TESTS") != "1":
        pytest.skip("validacao OpenGL real e executada separadamente no CI")

    try:
        from OpenGL.GL import (
            GL_NO_ERROR,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            glGetError,
            glReadPixels,
        )

        from src.runtime.infrastructure.graphics.gpu_renderer import ApresentadorGPU
    except ImportError as erro:
        pytest.skip(f"PyOpenGL indisponivel: {erro}")

    pygame.display.init()
    pygame.display.set_mode((320, 180), pygame.OPENGL | pygame.DOUBLEBUF)
    apresentador = None
    try:
        apresentador = ApresentadorGPU((128, 72))
        assert apresentador.shader_disponivel, apresentador.erros_shader
        assert apresentador.backend_shader == "GLSL 330", apresentador.erros_shader

        cena = pygame.Surface((128, 72))
        cena.fill((36, 52, 92))
        pygame.draw.rect(cena, (236, 94, 38), (35, 15, 58, 42))
        interface = pygame.Surface((128, 72), pygame.SRCALPHA)
        pygame.draw.rect(interface, (30, 240, 90, 255), (4, 4, 32, 12))
        apresentador.apresentar(
            cena, (0, 0, 320, 180), (320, 180), (0, 0, 0),
            interface=interface,
        )

        pixels = bytes(glReadPixels(0, 0, 320, 180, GL_RGB, GL_UNSIGNED_BYTE))
        cores = {pixels[i:i + 3] for i in range(0, len(pixels), 3)}
        assert len(cores) >= 4
        assert glGetError() == GL_NO_ERROR
    finally:
        if apresentador is not None:
            apresentador.liberar()
        pygame.display.quit()
