"""Apresentacao e pos-processamento da superficie logica pela GPU."""

from __future__ import annotations

import ctypes
import logging

import pygame

from src.core.settings import OpcoesShaderComic, limitar_float
from src.runtime.infrastructure.graphics.shader_sources import (
    FRAGMENT_SHADER,
    FRAGMENT_SHADER_330,
    VERTEX_SHADER,
    VERTEX_SHADER_330,
)

LOGGER = logging.getLogger(__name__)

try:
    from OpenGL.GL import (
        GL_ARRAY_BUFFER,
        GL_BGRA,
        GL_BLEND,
        GL_CLAMP_TO_EDGE,
        GL_COLOR_BUFFER_BIT,
        GL_COMPILE_STATUS,
        GL_DEPTH_TEST,
        GL_FLOAT,
        GL_FRAGMENT_SHADER,
        GL_LINEAR,
        GL_LINK_STATUS,
        GL_MODELVIEW,
        GL_ONE_MINUS_SRC_ALPHA,
        GL_PROJECTION,
        GL_QUADS,
        GL_RGBA,
        GL_SRC_ALPHA,
        GL_STATIC_DRAW,
        GL_TEXTURE0,
        GL_TEXTURE_2D,
        GL_TEXTURE_MAG_FILTER,
        GL_TEXTURE_MIN_FILTER,
        GL_TEXTURE_WRAP_S,
        GL_TEXTURE_WRAP_T,
        GL_TRIANGLE_STRIP,
        GL_UNPACK_ALIGNMENT,
        GL_UNSIGNED_BYTE,
        GL_VERTEX_SHADER,
        glActiveTexture,
        glAttachShader,
        glBegin,
        glBindBuffer,
        glBindTexture,
        glBindVertexArray,
        glBlendFunc,
        glBufferData,
        glClear,
        glClearColor,
        glColor4f,
        glCompileShader,
        glCreateProgram,
        glCreateShader,
        glDeleteBuffers,
        glDeleteProgram,
        glDeleteShader,
        glDeleteTextures,
        glDeleteVertexArrays,
        glDisable,
        glDrawArrays,
        glEnable,
        glEnableVertexAttribArray,
        glEnd,
        glGenBuffers,
        glGenTextures,
        glGenVertexArrays,
        glGetProgramInfoLog,
        glGetProgramiv,
        glGetShaderInfoLog,
        glGetShaderiv,
        glGetUniformLocation,
        glLinkProgram,
        glLoadIdentity,
        glMatrixMode,
        glPixelStorei,
        glShaderSource,
        glTexCoord2f,
        glTexImage2D,
        glTexParameteri,
        glTexSubImage2D,
        glUniform1f,
        glUniform1i,
        glUniform2f,
        glUseProgram,
        glVertex2f,
        glVertexAttribPointer,
        glViewport,
    )
except (ImportError, AttributeError):  # pragma: no cover - depende do sistema
    glGenTextures = None
    glCreateShader = None
    GL_RGBA = 0x1908
    GL_BGRA = 0x80E1


GPU_DISPONIVEL = glGenTextures is not None


def normalizar_intensidade(valor: object, padrao: float = 0.7) -> float:
    """Converte uma intensidade persistida para o intervalo aceito."""
    return limitar_float(valor, padrao)


def viewport_opengl(destino, altura_janela):
    """Converte um rect com origem superior para o viewport do OpenGL."""
    x, y, largura, altura = destino
    return (int(x), int(altura_janela - y - altura),
            max(1, int(largura)), max(1, int(altura)))


class ApresentadorGPU:
    """Escala a cena e aplica o acabamento comic com fallback legado."""

    _NOMES_UNIFORMES = (
        "quadro", "resolucao", "intensidade", "qualidade",
        "forca_contorno", "tons", "usar_hachuras", "forca_grao",
        "saturacao",
    )

    def __init__(self, tamanho_logico):
        if glGenTextures is None:
            raise RuntimeError("PyOpenGL nao esta instalado")

        self.largura, self.altura = tamanho_logico
        self._tipo_buffer = ctypes.c_ubyte * (self.largura * self.altura * 4)
        self.textura = self._criar_textura()
        self.textura_interface = self._criar_textura()
        self.textura_hud = self._criar_textura_tamanho((1, 1))
        self._tamanho_textura_hud = (1, 1)
        self.vao = self.vbo = 0
        self.erros_shader: list[str] = []
        self.backend_shader = "FIXO"
        self.programa = self._criar_programa_moderno()
        if not self.programa:
            self.programa = self._criar_programa(
                VERTEX_SHADER, FRAGMENT_SHADER, "GLSL 120")
            if self.programa:
                self.backend_shader = "GLSL 120"
        self.shader_disponivel = bool(self.programa)
        self.opcoes_shader = OpcoesShaderComic()
        self._uniformes = {}
        if self.shader_disponivel:
            self._uniformes = {
                nome: glGetUniformLocation(self.programa, nome)
                for nome in self._NOMES_UNIFORMES
            }
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        if not self.vao:
            glEnable(GL_TEXTURE_2D)

    def _criar_textura(self):
        textura = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, textura)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.largura, self.altura,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        return textura

    @staticmethod
    def _criar_textura_tamanho(tamanho):
        """Cria textura auxiliar com dimensões independentes da cena lógica."""
        largura, altura = tamanho
        textura = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, textura)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, largura, altura,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        return textura

    @staticmethod
    def _compilar_shader(codigo, tipo):
        shader = glCreateShader(tipo)
        glShaderSource(shader, codigo)
        glCompileShader(shader)
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            log = glGetShaderInfoLog(shader)
            glDeleteShader(shader)
            raise RuntimeError(f"Falha ao compilar shader: {log!r}")
        return shader

    def _registrar_erro(self, backend: str, erro: Exception) -> None:
        mensagem = f"{backend}: {erro}"
        self.erros_shader.append(mensagem)
        LOGGER.warning("Shader comic indisponivel em %s", mensagem)

    def _criar_programa(self, codigo_vertice, codigo_fragmento, backend):
        if glCreateShader is None:
            return 0
        vertice = fragmento = programa = 0
        try:
            vertice = self._compilar_shader(codigo_vertice, GL_VERTEX_SHADER)
            fragmento = self._compilar_shader(codigo_fragmento, GL_FRAGMENT_SHADER)
            programa = glCreateProgram()
            glAttachShader(programa, vertice)
            glAttachShader(programa, fragmento)
            glLinkProgram(programa)
            if not glGetProgramiv(programa, GL_LINK_STATUS):
                raise RuntimeError(
                    f"Falha ao vincular shader: {glGetProgramInfoLog(programa)!r}")
            return programa
        except Exception as erro:  # pragma: no cover - varia conforme driver
            self._registrar_erro(backend, erro)
            if programa:
                glDeleteProgram(programa)
            return 0
        finally:
            if vertice:
                glDeleteShader(vertice)
            if fragmento:
                glDeleteShader(fragmento)

    def _criar_programa_moderno(self):
        programa = self._criar_programa(
            VERTEX_SHADER_330, FRAGMENT_SHADER_330, "GLSL 330")
        if not programa:
            return 0
        try:
            vertices = (ctypes.c_float * 16)(
                -1, -1, 0, 1, 1, -1, 1, 1,
                -1, 1, 0, 0, 1, 1, 1, 0,
            )
            self.vao = glGenVertexArrays(1)
            self.vbo = glGenBuffers(1)
            glBindVertexArray(self.vao)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(vertices), vertices,
                         GL_STATIC_DRAW)
            passo = 4 * ctypes.sizeof(ctypes.c_float)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, False, passo,
                                  ctypes.c_void_p(0))
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 2, GL_FLOAT, False, passo,
                                  ctypes.c_void_p(2 * ctypes.sizeof(ctypes.c_float)))
            glBindVertexArray(0)
            self.backend_shader = "GLSL 330"
            return programa
        except Exception as erro:  # pragma: no cover - varia conforme driver
            self._registrar_erro("VBO/VAO", erro)
            glDeleteProgram(programa)
            if self.vbo:
                glDeleteBuffers(1, [self.vbo])
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
            self.vao = self.vbo = 0
            return 0

    def configurar_shader(
        self,
        ativo: bool,
        intensidade: float = 0.7,
        qualidade: str = "MEDIA",
        *,
        contorno: float = 0.75,
        tons: int = 3,
        hachuras: bool = True,
        grao: float = 0.35,
        saturacao: float = 1.1,
        preservar_interface: bool = True,
    ) -> None:
        """Mantem compatibilidade com a API anterior baseada em argumentos."""
        estilo = "COMIC" if ativo else "ORIGINAL"
        self.aplicar_opcoes_shader(OpcoesShaderComic.de_config({
            "estilo_visual": estilo,
            "shader_comic": ativo,
            "intensidade_shader": intensidade,
            "qualidade_comic": qualidade,
            "contorno_shader": contorno,
            "tons_shader": tons,
            "hachuras_shader": hachuras,
            "grao_shader": grao,
            "saturacao_shader": saturacao,
            "preservar_interface": preservar_interface,
        }))

    def aplicar_opcoes_shader(self, opcoes: OpcoesShaderComic) -> None:
        """Troca todas as opções do filtro como uma unidade imutável."""
        self.opcoes_shader = opcoes

    @property
    def shader_ativo(self) -> bool:
        return self.opcoes_shader.ativo

    @property
    def intensidade_shader(self) -> float:
        return self.opcoes_shader.intensidade

    @property
    def qualidade_shader(self) -> float:
        return {"BAIXA": 0.0, "MEDIA": 0.5, "ALTA": 1.0}[
            self.opcoes_shader.qualidade]

    @property
    def contorno_shader(self) -> float:
        return self.opcoes_shader.contorno

    @property
    def tons_shader(self) -> int:
        return self.opcoes_shader.tons

    @property
    def hachuras_shader(self) -> bool:
        return self.opcoes_shader.hachuras

    @property
    def grao_shader(self) -> float:
        return self.opcoes_shader.grao

    @property
    def saturacao_shader(self) -> float:
        return self.opcoes_shader.saturacao

    @property
    def preservar_interface(self) -> bool:
        return self.opcoes_shader.preservar_interface

    def _uniforme_1f(self, nome, valor):
        local = self._uniformes.get(nome, -1)
        if local >= 0:
            glUniform1f(local, valor)

    def _uniforme_1i(self, nome, valor):
        local = self._uniformes.get(nome, -1)
        if local >= 0:
            glUniform1i(local, valor)

    def _ativar_shader(self, intensidade=None):
        if not self.shader_disponivel:
            return
        glUseProgram(self.programa)
        if intensidade is None:
            intensidade = self.intensidade_shader if self.shader_ativo else 0.0
        self._uniforme_1i("quadro", 0)
        local_resolucao = self._uniformes.get("resolucao", -1)
        if local_resolucao >= 0:
            glUniform2f(local_resolucao, self.largura, self.altura)
        self._uniforme_1f("intensidade", intensidade)
        self._uniforme_1f("qualidade", self.qualidade_shader)
        self._uniforme_1f("forca_contorno", self.contorno_shader)
        self._uniforme_1f("tons", float(self.tons_shader))
        self._uniforme_1i("usar_hachuras", int(self.hachuras_shader))
        self._uniforme_1f("forca_grao", self.grao_shader)
        self._uniforme_1f("saturacao", self.saturacao_shader)

    def _pixels(self, superficie):
        """Retorna o buffer sem copia quando a Surface usa o formato nativo."""
        largura, altura = superficie.get_size()
        if (superficie.get_bytesize() == 4 and
                superficie.get_pitch() == largura * 4 and
                superficie.get_shifts()[:3] == (16, 8, 0)):
            tipo_buffer = ctypes.c_ubyte * (largura * altura * 4)
            return tipo_buffer.from_buffer(superficie.get_view("1")), GL_BGRA
        return pygame.image.tobytes(superficie, "RGBA"), GL_RGBA

    def _enviar_textura(self, textura, superficie):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, textura)
        largura, altura = superficie.get_size()
        if (textura == self.textura_hud and
                self._tamanho_textura_hud != (largura, altura)):
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, largura, altura,
                         0, GL_RGBA, GL_UNSIGNED_BYTE, None)
            self._tamanho_textura_hud = (largura, altura)
        pixels, formato = self._pixels(superficie)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, largura, altura,
                        formato, GL_UNSIGNED_BYTE, pixels)

    def _desenhar_quad(self):
        if self.vao:
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            glBindVertexArray(0)
            return
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_TRIANGLE_STRIP)
        for u, v, x, y in (
            (0, 1, -1, -1), (1, 1, 1, -1),
            (0, 0, -1, 1), (1, 0, 1, 1),
        ):
            glTexCoord2f(u, v)
            glVertex2f(x, y)
        glEnd()

    def _desenhar_textura(self, textura, intensidade=None, mistura=False):
        glBindTexture(GL_TEXTURE_2D, textura)
        if mistura:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self._ativar_shader(intensidade)
        self._desenhar_quad()
        if self.shader_disponivel:
            glUseProgram(0)
        if mistura:
            glDisable(GL_BLEND)

    def _desenhar_efeito_borda(self, destino, tamanho_janela, efeito):
        """Desenha um efeito translucido nas faixas externas da cena."""
        if efeito is None:
            return
        largura, altura = tamanho_janela
        x, y, w, h = destino
        esquerda, topo = max(0, x), max(0, y)
        direita, base = min(largura, x + w), min(altura, y + h)
        retangulos = []
        if topo > 0:
            retangulos.append((0, 0, largura, topo))
        if base < altura:
            retangulos.append((0, base, largura, altura - base))
        if esquerda > 0 and base > topo:
            retangulos.append((0, topo, esquerda, base - topo))
        if direita < largura and base > topo:
            retangulos.append((direita, topo, largura - direita, base - topo))
        if not retangulos:
            retangulos.append((0, 0, largura, altura))

        cor, alfa = efeito
        glViewport(0, 0, largura, altura)
        glUseProgram(0)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(*(canal / 255 for canal in cor), alfa / 255)
        glBegin(GL_QUADS)
        for rx, ry, rw, rh in retangulos:
            esquerda_ndc = 2 * rx / largura - 1
            direita_ndc = 2 * (rx + rw) / largura - 1
            topo_ndc = 1 - 2 * ry / altura
            base_ndc = 1 - 2 * (ry + rh) / altura
            glVertex2f(esquerda_ndc, base_ndc)
            glVertex2f(direita_ndc, base_ndc)
            glVertex2f(direita_ndc, topo_ndc)
            glVertex2f(esquerda_ndc, topo_ndc)
        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glColor4f(1.0, 1.0, 1.0, 1.0)

    def apresentar(
        self, superficie, destino, tamanho_janela, cor_fundo,
        interface=None, fundo=None, efeito_borda=None, hud=None,
    ):
        """Apresenta fundo decorativo, cena 16:9 e interface opcional."""
        largura, altura = tamanho_janela
        glViewport(0, 0, largura, altura)
        glClearColor(*(canal / 255 for canal in cor_fundo), 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        if fundo is not None:
            self._enviar_textura(self.textura, fundo)
            glViewport(0, 0, largura, altura)
            self._desenhar_textura(self.textura, intensidade=0.0)
        self._enviar_textura(self.textura, superficie)
        if interface is not None:
            self._enviar_textura(self.textura_interface, interface)
        glViewport(*viewport_opengl(destino, altura))
        self._desenhar_textura(self.textura)
        if interface is not None and self.preservar_interface:
            self._desenhar_textura(
                self.textura_interface, intensidade=0.0, mistura=True)
        if hud is not None:
            self._enviar_textura(self.textura_hud, hud)
            glViewport(*viewport_opengl(destino, altura))
            self._desenhar_textura(
                self.textura_hud, intensidade=0.0, mistura=True)
        self._desenhar_efeito_borda(destino, tamanho_janela, efeito_borda)

    def liberar(self):
        """Libera objetos enquanto o contexto OpenGL ainda esta ativo."""
        try:
            if self.programa:
                glDeleteProgram(self.programa)
                self.programa = 0
            if self.vbo:
                glDeleteBuffers(1, [self.vbo])
                self.vbo = 0
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
                self.vao = 0
            glDeleteTextures([self.textura, self.textura_interface,
                              self.textura_hud])
        except Exception:  # pragma: no cover - contexto ja encerrado
            pass
