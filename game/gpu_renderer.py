"""Fachada legada para o apresentador GPU canônico."""

from src.runtime.infrastructure.graphics.gpu_renderer import (
    FRAGMENT_SHADER,
    FRAGMENT_SHADER_330,
    GPU_DISPONIVEL,
    VERTEX_SHADER,
    VERTEX_SHADER_330,
    ApresentadorGPU,
    normalizar_intensidade,
    viewport_opengl,
)

__all__ = [
    "FRAGMENT_SHADER",
    "FRAGMENT_SHADER_330",
    "GPU_DISPONIVEL",
    "VERTEX_SHADER",
    "VERTEX_SHADER_330",
    "ApresentadorGPU",
    "normalizar_intensidade",
    "viewport_opengl",
]
