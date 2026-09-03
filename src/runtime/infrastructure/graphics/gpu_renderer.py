"""Apresentacao acelerada por GPU da superficie logica do jogo."""

import ctypes

import pygame

try:
    from OpenGL.GL import GL_BGRA, GL_BLEND, GL_CLAMP_TO_EDGE, \
        GL_COLOR_BUFFER_BIT, GL_DEPTH_TEST, GL_LINEAR, GL_MODELVIEW, \
        GL_PROJECTION, GL_RGBA, GL_TEXTURE_2D, \
        GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_WRAP_S, \
        GL_TEXTURE_WRAP_T, GL_TRIANGLE_STRIP, GL_UNPACK_ALIGNMENT, \
        GL_UNSIGNED_BYTE, glBegin, glBindTexture, glClear, glClearColor, \
        glColor4f, glDeleteTextures, glDisable, glEnable, glEnd, \
        glGenTextures, glLoadIdentity, glMatrixMode, glPixelStorei, \
        glTexCoord2f, glTexImage2D, glTexParameteri, glTexSubImage2D, \
        glVertex2f, glViewport
except (ImportError, AttributeError):  # pragma: no cover - depende do sistema
    glGenTextures = None
    # Os testes do conversor de pixels nao exigem um contexto OpenGL. Mantenha
    # os enums disponiveis quando PyOpenGL for opcionalmente indisponivel.
    GL_RGBA = 0x1908
    GL_BGRA = 0x80E1


GPU_DISPONIVEL = glGenTextures is not None


def viewport_opengl(destino, altura_janela):
    """Converte um rect com origem superior para o viewport do OpenGL."""
    x, y, largura, altura = destino
    return (int(x), int(altura_janela - y - altura),
            max(1, int(largura)), max(1, int(altura)))


class ApresentadorGPU:
    """Envia o frame do Pygame para uma textura e o apresenta via OpenGL.

    A rasterizacao do jogo continua numa ``Surface`` pequena e previsivel.
    A GPU cuida da composicao e da escala para a resolucao da janela, que era
    o trecho mais caro em resolucoes altas.
    """

    def __init__(self, tamanho_logico):
        if glGenTextures is None:
            raise RuntimeError("PyOpenGL nao esta instalado")

        self.largura, self.altura = tamanho_logico
        self._tipo_buffer = ctypes.c_ubyte * (self.largura * self.altura * 4)
        self.textura = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.textura)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.largura, self.altura,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)

    def _pixels(self, superficie):
        """Retorna o buffer sem copia quando a Surface usa o formato nativo."""
        if (superficie.get_bytesize() == 4 and
                superficie.get_pitch() == self.largura * 4 and
                superficie.get_shifts()[:3] == (16, 8, 0)):
            return self._tipo_buffer.from_buffer(superficie.get_view("1")), \
                GL_BGRA
        return pygame.image.tobytes(superficie, "RGBA"), GL_RGBA

    def apresentar(self, superficie, destino, tamanho_janela, cor_fundo):
        """Apresenta uma ``Surface`` no rect físico informado."""
        largura, altura = tamanho_janela
        glViewport(0, 0, largura, altura)
        glClearColor(*(canal / 255 for canal in cor_fundo), 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        glBindTexture(GL_TEXTURE_2D, self.textura)
        pixels, formato = self._pixels(superficie)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.largura, self.altura,
                        formato, GL_UNSIGNED_BYTE, pixels)

        glViewport(*viewport_opengl(destino, altura))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_TRIANGLE_STRIP)
        # A memoria do Pygame comeca no topo; a textura OpenGL, na base.
        glTexCoord2f(0.0, 1.0)
        glVertex2f(-1.0, -1.0)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(1.0, -1.0)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(-1.0, 1.0)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(1.0, 1.0)
        glEnd()

    def liberar(self):
        """Libera objetos enquanto o contexto OpenGL ainda esta ativo."""
        try:
            glDeleteTextures([self.textura])
        except Exception:  # pragma: no cover - contexto ja encerrado
            pass
