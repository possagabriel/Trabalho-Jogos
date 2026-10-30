"""Cena visual do menu principal: fundo cinematico, HUD diegetico, nave e
transicoes.

Reune todos os elementos puramente visuais do menu em componentes
reutilizaveis (com caching de superficies para manter 60 FPS):
- ``FundoCinematico``: tres camadas de profundidade (nebulosas, planeta,
  asteroides, estrelas com parallax e particulas em primeiro plano).
- ``HudMenu``: elementos HUD diegeticos de uma nave (molduras, radar,
  status do sistema, dados da missao).
- ``NaveMenu``: nave do jogador em destaque com motores e balanco idle.
- ``DestaqueMenu``: destaque deslizante das opcoes (paralelogramo inclinado).
- ``TransicaoMissao``: transicao cinematografica ao iniciar a partida.

Todos os componentes recebem um ``Layout`` (responsivo) e derivam posicoes,
tamanhos e fontes dele — nenhuma coordenada rigida e usada.
"""

import math
import random

import pygame

from src.core.constants import ALTURA, LARGURA, NEGRO
from src.infrastructure.graphics.comic_render import desenhar_fundo
from src.infrastructure.graphics.comic_theme import opcoes_atuais
from src.infrastructure.ui.layout import Layout
from src.runtime.domain.entities.player import Jogador
from src.runtime.domain.world.scenarios import Cenario
from src.runtime.infrastructure.assets import carregar_imagem
from src.runtime.infrastructure.graphics.meteor_shower import (
    desenhar_meteoro,
    gerar_chuva,
    janela_chuva,
)
from src.runtime.infrastructure.graphics.smooth import (
    desenhar_cantos,
    desenhar_circulo,
    desenhar_glow,
    gradiente_vertical,
    luz_radial,
)


def texto_espacado(fonte, texto, espacamento, cor):
    """Surface de texto com espacamento entre caracteres (estilo HUD)."""
    larguras = [fonte.size(ch)[0] for ch in texto]
    total = sum(larguras) + espacamento * max(0, len(texto) - 1)
    surf = pygame.Surface((max(1, total), fonte.get_height()), pygame.SRCALPHA)
    x = 0
    for ch, larg in zip(texto, larguras):
        glyph = fonte.render(ch, True, cor)
        surf.blit(glyph, (x, 0))
        x += larg + espacamento
    return surf


def _ease_out(t):
    return 1 - (1 - t) * (1 - t)


def _ease_in(t):
    return t * t


# ---------------------------------------------------------------------------
# Fundo cinematico
# ---------------------------------------------------------------------------

class FundoCinematico:
    """Fundo espacial com tres camadas de profundidade e elementos vivos."""

    def __init__(self, layout=None):
        self._layout = layout or Layout()
        self.tempo = 0.0
        self._tile_largura = self._layout.px(960)
        self._tile_altura = self._layout.px(720)
        self.fundo_imagem = self._carregar_imagem_fundo()
        self.gradiente = gradiente_vertical((10, 12, 38), (3, 3, 15))
        self.nebulosa_fundo = self._criar_nebulosa(0.13, 7)
        self.nebulosa_frente = self._criar_nebulosa(0.19, 5)
        self.camadas = self._criar_estrelas()
        self.estrelas_heroicas = [
            [random.uniform(0, self._layout.largura),
             random.uniform(0, self._layout.altura),
             random.uniform(1.0, 2.4), random.uniform(0, math.tau)]
            for _ in range(34)]
        self.planeta = self._criar_planeta(150, (26, 40, 86), (110, 190, 255),
                                           (150, 150, 210), True)
        self.asteroides = self._criar_asteroides()
        self.particulas = []
        self.meteoros = ()
        self._ciclo_meteoros = -1

    # ----- construcao -----

    def _carregar_imagem_fundo(self):
        """Carrega 'fundo-menuprincipal.png' (pasta images/) em cover.

        Se o arquivo nao existir, retorna ``None`` e o menu usa o fundo
        cinematico procedural normalmente.
        """
        img = carregar_imagem("fundo-menuprincipal.png")
        if img is None:
            return None
        larg = self._layout.largura
        alt = self._layout.altura
        iw, ih = img.get_size()
        escala = max(larg / iw, alt / ih)
        novow = max(larg, int(iw * escala))
        novoh = max(alt, int(ih * escala))
        if (novow, novoh) != (iw, ih):
            img = pygame.transform.smoothscale(img, (novow, novoh))
        ox = (novow - larg) // 2
        oy = (novoh - alt) // 2
        if (ox, oy) != (0, 0):
            img = img.subsurface((ox, oy, larg, alt)).copy()
        return img

    def _criar_nebulosa(self, intensidade, quantidade):
        layout = self._layout
        surf = pygame.Surface((layout.largura, layout.altura), pygame.SRCALPHA)
        cores = [(70, 45, 140), (25, 85, 160), (130, 35, 120), (25, 120, 140)]
        for _ in range(quantidade):
            x = random.randint(-layout.px(100), layout.largura)
            y = random.randint(-layout.px(100), layout.altura)
            raio = random.randint(layout.px(90), layout.px(240))
            blob = luz_radial(random.choice(cores), raio, intensidade)
            surf.blit(blob, blob.get_rect(center=(x, y)))
        return surf

    def _criar_estrelas(self):
        camadas = []
        for velocidade, qtd, brilho_min, brilho_max in (
                (0.22, 110, 60, 150), (0.55, 70, 100, 200), (1.15, 32, 150, 255)):
            surf = pygame.Surface((self._tile_largura, self._tile_altura),
                                  pygame.SRCALPHA)
            for _ in range(qtd):
                x = random.randint(0, self._tile_largura - 1)
                y = random.randint(0, self._tile_altura - 1)
                brilho = random.randint(brilho_min, brilho_max)
                raio = random.choice((1, 1, 1, 2))
                pygame.draw.circle(surf, (brilho, brilho,
                                          min(255, brilho + 18)), (x, y), raio)
            camadas.append({"surf": surf, "vel": velocidade,
                            "x": random.uniform(0, self._tile_largura),
                            "y": random.uniform(0, self._tile_altura)})
        return camadas

    def _criar_planeta(self, raio, cor_corpo, cor_borda, cor_anel, com_anel):
        layout = self._layout
        raio = layout.px(raio)
        lado = raio * 4
        surf = pygame.Surface((lado, lado), pygame.SRCALPHA)
        cx = cy = lado // 2
        atmosfera = luz_radial(cor_borda, raio, 0.4)
        surf.blit(atmosfera, atmosfera.get_rect(center=(cx, cy)))
        for r in range(raio, 0, -1):
            t = 1 - r / raio
            brilho = 1.0 - 0.55 * t
            cor = tuple(int(min(255, c * brilho)) for c in cor_corpo)
            pygame.draw.circle(surf, cor + (255,), (cx, cy), r)
        for i in range(7):
            y = cy - layout.px(12) + i * layout.px(4)
            cor = tuple(int(min(255, c * (0.85 + 0.12 * i))) for c in cor_borda)
            pygame.draw.line(surf, cor + (80,), (cx - raio, y), (cx + raio, y), 2)
        if com_anel:
            anel = pygame.Surface((lado, lado), pygame.SRCALPHA)
            rect = pygame.Rect(cx - raio * 2, cy - int(raio * 0.6),
                               raio * 4, int(raio * 1.2))
            pygame.draw.ellipse(anel, cor_anel + (110,), rect,
                                max(3, int(raio * 0.16)))
            surf.blit(anel, (0, 0))
        return surf

    def _criar_asteroides(self):
        layout = self._layout
        asteroides = []
        for _ in range(5):
            raio = random.randint(layout.px(9), layout.px(20))
            lados = random.randint(6, 9)
            pts = []
            for i in range(lados):
                a = i * math.tau / lados + random.uniform(-0.25, 0.25)
                r = raio * random.uniform(0.7, 1.15)
                pts.append((math.cos(a) * r, math.sin(a) * r))
            min_x = min(p[0] for p in pts)
            max_x = max(p[0] for p in pts)
            min_y = min(p[1] for p in pts)
            max_y = max(p[1] for p in pts)
            larg = int(max_x - min_x) + 8
            alt = int(max_y - min_y) + 8
            sup = pygame.Surface((larg, alt), pygame.SRCALPHA)
            pts2 = [(p[0] - min_x + 4, p[1] - min_y + 4) for p in pts]
            cor = random.choice(((60, 66, 92), (74, 80, 108), (52, 58, 84)))
            pygame.draw.polygon(sup, cor + (255,), pts2)
            pygame.draw.polygon(sup, (150, 160, 200, 170), pts2, 2)
            asteroides.append({
                "surf": sup, "ox": int(min_x) - 4, "oy": int(min_y) - 4,
                "x": random.uniform(0, layout.largura), "y": random.uniform(0, layout.altura),
                "vx": random.uniform(-0.35, 0.35), "vy": random.uniform(0.4, 1.1),
                "fase": random.uniform(0, math.tau)})
        return asteroides

    def _nova_particula(self):
        layout = self._layout
        return {"x": random.uniform(0, layout.largura), "y": layout.altura + layout.px(8),
                "vx": random.uniform(-0.5, 0.5),
                "vy": random.uniform(-0.7, -2.2),
                "r": random.uniform(0.6, 1.9),
                "cor": random.choice(((150, 170, 220), (200, 220, 255))),
                "t": 0, "max": random.randint(120, 220)}

    # ----- atualizacao -----

    def atualizar(self):
        layout = self._layout
        self.tempo += 1 / 60.0
        for camada in self.camadas:
            camada["y"] += camada["vel"]
            if camada["y"] >= self._tile_altura:
                camada["y"] -= self._tile_altura
            camada["x"] += math.sin(self.tempo * 0.4) * 0.02
        for ast in self.asteroides:
            ast["x"] += ast["vx"]
            ast["y"] += ast["vy"]
            if ast["y"] > layout.altura + layout.px(40):
                ast["y"] = -layout.px(40)
                ast["x"] = random.uniform(0, layout.largura)
            if ast["x"] < -layout.px(60):
                ast["x"] = layout.largura + layout.px(60)
        if len(self.particulas) < 42 and random.random() < 0.4:
            self.particulas.append(self._nova_particula())
        for p in self.particulas[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["t"] += 1
            if p["t"] >= p["max"]:
                self.particulas.remove(p)

    # ----- desenho -----

    def desenhar(
        self,
        tela: pygame.Surface,
        cor_fundo_cutscene: tuple[int, int, int] | None = None,
    ) -> None:
        if opcoes_atuais().ativo:
            desenhar_fundo(tela)
            return
        if self.fundo_imagem is not None:
            fundo = self.fundo_imagem
            if cor_fundo_cutscene is not None:
                from src.runtime.presentation.cutscene_raster import filtrar_fundo_cutscene

                fundo = filtrar_fundo_cutscene(fundo, cor_fundo_cutscene)
            tela.blit(fundo, (0, 0))
        else:
            tela.blit(self.gradiente, (0, 0))
        dx = int(math.sin(self.tempo * 0.12) * 18)
        dy = int(math.cos(self.tempo * 0.1) * 10)
        tela.blit(self.nebulosa_fundo, (dx, dy))
        self._desenhar_estrelas(tela)
        self._desenhar_planetas(tela)
        tela.blit(self.nebulosa_frente, (-dx // 2, -dy // 2))
        self._desenhar_heroicas(tela)
        for ast in self.asteroides:
            tela.blit(ast["surf"], (int(ast["x"] + ast["ox"]),
                                    int(ast["y"] + ast["oy"])))
        self._desenhar_particulas(tela)
        self._desenhar_meteoros(tela)

    def _desenhar_estrelas(self, tela):
        for camada in self.camadas:
            x = int(camada["x"])
            y = int(camada["y"])
            for off_x, off_y in ((0, 0), (self._tile_largura, 0),
                                 (0, self._tile_altura),
                                 (self._tile_largura, self._tile_altura)):
                tela.blit(camada["surf"], (off_x - x, off_y - y))

    def _desenhar_planetas(self, tela):
        layout = self._layout
        px = layout.px(60) + int(math.sin(self.tempo * 0.15) * layout.px(6))
        py = layout.px(702) - int(math.sin(self.tempo * 0.22) * layout.px(5))
        tela.blit(self.planeta, self.planeta.get_rect(center=(px, py)))

    def _desenhar_heroicas(self, tela):
        for x, y, raio, fase in self.estrelas_heroicas:
            brilho = int(60 + 90 * (0.5 + 0.5 * math.sin(self.tempo * 3 + fase)))
            cor = (brilho, brilho, brilho + 25)
            pygame.draw.circle(tela, cor, (int(x), int(y)), max(1, int(raio)))

    def _desenhar_particulas(self, tela):
        for p in self.particulas:
            fade = 1 - p["t"] / p["max"]
            cor = tuple(int(c * fade) for c in p["cor"])
            pygame.draw.circle(tela, cor, (int(p["x"]), int(p["y"])),
                               max(1, int(p["r"])))

    def _desenhar_meteoros(self, tela):
        janela = janela_chuva(self.tempo)
        if janela is None:
            return
        ciclo, fase = janela
        if ciclo != self._ciclo_meteoros:
            self.meteoros = gerar_chuva(
                7601 + ciclo, self._layout.largura, self._layout.altura, 4)
            self._ciclo_meteoros = ciclo
        for meteoro in self.meteoros:
            desenhar_meteoro(tela, meteoro, fase - meteoro.atraso)


class FundoMenuParallax:
    """Fundo do menu composto uma vez com ``ParallaxBackground`` em BAIXA.

    O gameplay anima as camadas a cada quadro; o menu reutiliza a mesma
    composição do cenário 1 como superfície estática em cache. A troca de
    resolução apenas reescala o cache, e os filtros de cutscene são guardados
    por cor para não repetir a posterização por quadro.
    """

    QUALIDADE = "BAIXA"
    CENARIO_ID = 1

    def __init__(self, layout=None):
        self._layout = layout or Layout()
        self._nativa: pygame.Surface | None = None
        self._nativa_estilo: tuple | None = None
        self._cache: pygame.Surface | None = None
        self._cache_tamanho = (0, 0)
        self._cache_estilo: tuple | None = None
        self._tingidos: dict[tuple[int, int, int], pygame.Surface] = {}

    def set_layout(self, layout: Layout) -> None:
        """Atualiza o canvas lógico sem recompilar a composição nativa."""
        if layout is self._layout and self._cache is not None:
            return
        self._layout = layout
        self._descartar_cache()

    def _descartar_cache(self) -> None:
        self._cache = None
        self._cache_tamanho = (0, 0)
        self._cache_estilo = None
        self._tingidos.clear()

    @staticmethod
    def _chave_estilo() -> tuple:
        opcoes = opcoes_atuais()
        return (opcoes.ativo, opcoes.qualidade, opcoes.papel,
                opcoes.halftone, opcoes.hachuras, opcoes.line_boil)

    def _compor_nativa(self, estilo: tuple) -> pygame.Surface:
        if self._nativa is None or self._nativa_estilo != estilo:
            cenario = Cenario(self.CENARIO_ID)
            cenario.configurar_avanco(
                self.QUALIDADE, (0.0, 1.0), False, True,
                {"avanco_marcos": False, "avanco_ritmo_variavel": False})
            nativa = pygame.Surface((LARGURA, ALTURA))
            nativa.fill(NEGRO)
            cenario.parallax.desenhar(nativa)
            self._nativa = nativa
            self._nativa_estilo = estilo
        return self._nativa

    def _recortar_cover(self, base: pygame.Surface) -> pygame.Surface:
        largura, altura = self._layout.largura, self._layout.altura
        if (largura, altura) == base.get_size():
            return base
        largura_base, altura_base = base.get_size()
        escala = max(largura / largura_base, altura / altura_base)
        redimensionada = pygame.transform.smoothscale(
            base, (max(largura, int(largura_base * escala)),
                   max(altura, int(altura_base * escala))))
        x = (redimensionada.get_width() - largura) // 2
        y = (redimensionada.get_height() - altura) // 2
        return redimensionada.subsurface((x, y, largura, altura)).copy()

    def _cache_estatico(self) -> pygame.Surface:
        tamanho = (self._layout.largura, self._layout.altura)
        estilo = self._chave_estilo()
        if (self._cache is None or self._cache_tamanho != tamanho
                or self._cache_estilo != estilo):
            self._cache = self._recortar_cover(self._compor_nativa(estilo))
            self._cache_tamanho = tamanho
            self._cache_estilo = estilo
            self._tingidos.clear()
        return self._cache

    @property
    def cache_estatico(self) -> bool:
        """Indica se a composição já foi preparada neste layout."""
        return self._cache is not None

    @property
    def qualidade(self) -> str:
        """Qualidade fixa usada na composição do fundo do menu."""
        return self.QUALIDADE

    def atualizar(self) -> None:
        """O fundo do menu é estático; não há camadas para animar."""

    def desenhar(
        self,
        tela: pygame.Surface,
        cor_fundo_cutscene: tuple[int, int, int] | None = None,
    ) -> None:
        """Desenha a composição cacheada, tingindo por cutscene se pedido."""
        fundo = self._cache_estatico()
        if cor_fundo_cutscene is not None:
            chave = tuple(cor_fundo_cutscene)
            tingido = self._tingidos.get(chave)
            if tingido is None:
                from src.runtime.presentation.cutscene_raster import (
                    filtrar_fundo_cutscene,
                )

                tingido = filtrar_fundo_cutscene(self._cache_estatico(), chave)
                self._tingidos[chave] = tingido
            fundo = tingido
        tela.blit(fundo, (0, 0))


# ---------------------------------------------------------------------------
# HUD diegetico
# ---------------------------------------------------------------------------

class HudMenu:
    """Molduras neon do menu sem telemetria decorativa sem fonte de dados."""

    def __init__(self, layout=None):
        self._layout = layout or Layout()
        self.tempo = 0.0
        self._cache_texto = {}
        self._coord = 430822.0
        self._coord_multiplicador = 1.0
        self.radar_angulo = 0.0
        self.radar = self._criar_radar()
        self.banda = self._criar_banda()
        self.blips = [[random.uniform(0, math.tau), random.uniform(0.2, 0.8)]
                      for _ in range(4)]
        self._fuel = 0.72
        self._fuel_alvo = 0.72
        self._vel = 412.0
        self._vel_alvo = 412.0
        self._atualiza_contador = 0

    def _criar_radar(self):
        layout = self._layout
        raio = layout.px(26)
        lado = raio * 2 + layout.px(12)
        surf = pygame.Surface((lado, lado), pygame.SRCALPHA)
        cx = cy = lado // 2
        pygame.draw.circle(surf, (90, 120, 170, 55), (cx, cy), raio, 1)
        pygame.draw.circle(surf, (90, 120, 170, 40), (cx, cy), raio - layout.px(9), 1)
        pygame.draw.circle(surf, (70, 95, 140, 30), (cx, cy), raio - layout.px(18), 1)
        pygame.draw.line(surf, (80, 110, 160, 45), (cx - raio, cy), (cx + raio, cy), 1)
        pygame.draw.line(surf, (80, 110, 160, 45), (cx, cy - raio), (cx, cy + raio), 1)
        for i in range(8):
            a = i * math.pi / 4
            pygame.draw.line(surf, (90, 130, 190, 35),
                             (cx + math.cos(a) * (raio - layout.px(5)),
                              cy + math.sin(a) * (raio - layout.px(5))),
                             (cx + math.cos(a) * raio, cy + math.sin(a) * raio), 1)
        return surf

    def _criar_banda(self):
        surf = pygame.Surface((self._layout.largura, self._layout.px(64)),
                              pygame.SRCALPHA)
        surf.fill((5, 7, 18, 165))
        rect = surf.get_rect()
        pygame.draw.rect(surf, (30, 45, 90, 120), rect, 2)
        return surf

    def _texto(self, chave, fonte, texto, cor, espacamento=2):
        chave_cache = (id(fonte), chave, texto, tuple(cor), espacamento)
        if chave_cache not in self._cache_texto:
            self._cache_texto[chave_cache] = texto_espacado(
                fonte, texto, espacamento, cor)
        return self._cache_texto[chave_cache]

    def _desenhar_texto(self, tela, chave, fonte, texto, pos, cor,
                        espacamento=2, alinhar="esquerda"):
        surf = self._texto(chave, fonte, texto, cor, espacamento)
        if alinhar == "direita":
            rect = surf.get_rect(topright=pos)
        elif alinhar == "centro":
            rect = surf.get_rect(center=pos)
        else:
            rect = surf.get_rect(topleft=pos)
        tela.blit(surf, rect)
        return rect

    # ----- atualizacao -----

    def atualizar(self):
        self.tempo += 1 / 60.0
        self.radar_angulo += 0.045
        self._atualiza_contador += 1
        if self._atualiza_contador % 5 == 0:
            self._coord += random.uniform(1.2, 9.8) * self._coord_multiplicador
            if self._coord > 999999:
                self._coord_multiplicador = -1.0
            elif self._coord < 100000:
                self._coord_multiplicador = 1.0
        if random.random() < 0.03:
            self._fuel_alvo = max(0.4, min(0.85, self._fuel_alvo +
                                           random.uniform(-0.08, 0.08)))
        if random.random() < 0.05:
            self._vel_alvo = max(300, min(560, self._vel_alvo +
                                          random.uniform(-40, 40)))
        self._fuel += (self._fuel_alvo - self._fuel) * 0.02
        self._vel += (self._vel_alvo - self._vel) * 0.02

    # ----- desenho -----

    def desenhar(self, tela, tema, estilo="COMIC"):
        layout = self._layout
        primaria = tema["primaria"]
        borda = tema["borda_forte"]

        desenhar_cantos(tela, borda,
                        pygame.Rect(layout.px(12), layout.px(12),
                                    layout.largura - layout.px(24), layout.altura - layout.px(24)),
                        tamanho=layout.px(16), espessura=layout.px(3))
        desenhar_cantos(tela, primaria,
                        pygame.Rect(layout.px(20), layout.px(20),
                                    layout.largura - layout.px(40), layout.altura - layout.px(40)),
                        tamanho=layout.px(8), espessura=layout.px(2))



# ---------------------------------------------------------------------------
# Nave do jogador
# ---------------------------------------------------------------------------

class NaveMenu:
    """Nave do jogador em destaque no menu, com motores e balanco idle."""

    def __init__(self):
        self._jogador = None
        self._skin_id = None
        self._sprites = {}
        self.tempo = 0.0

    def atualizar(self):
        self.tempo += 1 / 60.0

    def desenhar(self, tela, skin, x, y, escala=2.1, tema=None):
        if skin.id != self._skin_id:
            self._jogador = Jogador(skin=skin)
            self._skin_id = skin.id
        jog = self._jogador
        jog.x, jog.y = 48, 52
        jog.tilt = 0.35
        jog.invencivel = 0

        chave = (skin.id, round(escala, 2), opcoes_atuais())
        surf = self._sprites.get(chave)
        if surf is None:
            base = pygame.Surface((96, 96), pygame.SRCALPHA)
            jog.skin.desenhar(base, jog)
            if abs(escala - 1.0) > 0.01:
                base = pygame.transform.smoothscale(
                    base, (int(96 * escala), int(96 * escala)))
            self._sprites[chave] = base
            surf = base

        bob = math.sin(self.tempo * 2.4) * 4
        cx = int(x + math.sin(self.tempo * 1.7) * 5)
        cy = int(y + bob)
        rect = surf.get_rect(center=(cx, cy))
        tela.blit(surf, rect)

        cor = skin.cor
        if tema:
            cor = tema["primaria"]
        base_y = cy + int(16 * escala)
        pulso = 0.8 + 0.25 * math.sin(self.tempo * 7)
        desenhar_glow(tela, cor, (cx, base_y), int(26 * escala * pulso), 0.8)
        desenhar_glow(tela, cor, (cx, base_y), int(12 * escala), 1.2)
        comprimento = int((14 + 7 * pulso) * escala)
        for larg, alfa in ((8, 90), (5, 170), (2, 255)):
            pygame.draw.polygon(
                tela, tuple(min(255, int(c * 0.5 + 90 * (larg == 2)))
                            for c in cor) + (alfa,),
                [(cx - larg // 2, base_y), (cx + larg // 2, base_y),
                 (cx, base_y + comprimento)])
        if tema:
            desenhar_circulo(tela, tema["borda_forte"], (cx, cy),
                             int(58 * escala), 1, brilho=0.7)


# ---------------------------------------------------------------------------
# Destaque das opcoes
# ---------------------------------------------------------------------------

class DestaqueMenu:
    """Destaque deslizante das opcoes: paralelogramo inclinado + borda.

    O destaque se move suavemente entre as opcoes (um unico bloco), dando o
    ritmo visual de menus de RPG japoneses, sem depender so de cor.
    """

    def __init__(self, layout=None):
        self._layout = layout or Layout()
        self.y = 0.0
        self.alvo = 0.0
        self.tempo = 0.0
        self._formas = {}
        self._pulso_escala = 0.0
        self._pulso_alvo = 0.0

    def _forma(self, tema):
        chave = tuple(sorted(tema.items()))
        if chave in self._formas:
            return self._formas[chave]
        layout = self._layout
        primaria = tema["primaria"]
        secundaria = tema["secundaria"]
        largura, altura, inclinacao = layout.px(360), layout.px(50), layout.px(16)
        surf = pygame.Surface((largura + inclinacao, altura), pygame.SRCALPHA)
        pts = [(0, inclinacao), (largura, 0), (largura + inclinacao, 0),
               (largura + inclinacao, altura), (inclinacao, altura), (0, 0)]
        pygame.draw.polygon(surf, primaria + (66,), pts)
        pygame.draw.polygon(surf, primaria + (150,), pts, 2)
        pygame.draw.line(surf, secundaria + (200,), (0, 0), (largura, 0), 3)
        # detalhe interno
        pygame.draw.polygon(surf, (255, 255, 255, 26),
                            [(layout.px(6), inclinacao - layout.px(4)),
                             (largura - layout.px(4), layout.px(3)),
                             (largura - layout.px(4), layout.px(10)),
                             (layout.px(6), inclinacao + layout.px(3))])
        self._formas[chave] = surf
        return surf

    def atualizar(self):
        self.tempo += 1 / 60.0
        self.y += (self.alvo - self.y) * 0.16
        self._pulso_escala += (self._pulso_alvo - self._pulso_escala) * 0.1

    def pulsar(self):
        self._pulso_alvo = 1.0
        self._pulso_escala = 1.0

    def desenhar(self, tela, x, tema):
        forma = self._forma(tema)
        rect = forma.get_rect(midleft=(x, int(self.y)))
        tela.blit(forma, rect)


# ---------------------------------------------------------------------------
# Transicao cinematografica
# ---------------------------------------------------------------------------

class TransicaoMissao:
    """Transicao ao iniciar a missao: zoom, tremida, riscas e flash."""

    def __init__(self, duracao=950, layout=None):
        self._layout = layout or Layout()
        self.duracao = duracao
        self.ativo = False
        self.inicio = 0
        self.acao = None
        self.tempo = 0.0
        self._flash = None

    def iniciar(self, acao):
        self.ativo = True
        self.inicio = pygame.time.get_ticks()
        self.acao = acao
        self.tempo = 0.0

    def em_andamento(self):
        return self.ativo

    def progresso(self):
        if not self.ativo:
            return 0.0
        return min(1.0, (pygame.time.get_ticks() - self.inicio) / self.duracao)

    def atualizar(self):
        self.tempo += 1 / 60.0
        if self.ativo and self.progresso() >= 1.0:
            acao = self.acao
            self.ativo = False
            self.acao = None
            if acao:
                acao()
            return True
        return False

    def desenhar(self, tela, tema, intensidade_flash=1.0, intensidade_tremor=1.0):
        layout = self._layout
        p = self.progresso()
        if p <= 0:
            return
        zoom = 1.0 + 0.14 * _ease_in(p)
        if zoom > 1.001:
            larg, alt = tela.get_size()
            nova = pygame.transform.smoothscale(
                tela, (int(larg * zoom), int(alt * zoom)))
            tremida = int(math.sin(self.tempo * 55) * 5 * p * intensidade_tremor)
            tela.fill(NEGRO)
            tela.blit(nova, nova.get_rect(center=(larg // 2 + tremida,
                                                  alt // 2)))

        # riscas de velocidade
        vel = 8 + 40 * p
        for i in range(30):
            y = (i * 97 + int(self.tempo * 30)) % layout.altura
            off = int((self.tempo * vel * (30 + i * 9))) % (layout.largura + 500)
            x = off - 200
            alfa = 60 + int(180 * (i / 30) * p)
            cor = (200, 225, 255)
            pygame.draw.line(tela, cor, (x, y), (x + 180, y), 2)
            if i % 3 == 0:
                pygame.draw.line(tela, cor, (x + 60, y - 3), (x + 110, y - 3), 1)

        # pulso radial central
        raio = int(30 + 300 * _ease_out(p))
        desenhar_glow(tela, tema["primaria"], (layout.x(0.5), layout.y(0.5)),
                      max(8, raio // 6), 0.4 + 0.5 * p)

        # flash final
        if p > 0.8 and intensidade_flash:
            alfa = int(255 * (p - 0.8) / 0.2 * intensidade_flash)
            if self._flash is None or self._flash.get_size() != tela.get_size():
                self._flash = pygame.Surface(tela.get_size())
                self._flash.fill((255, 255, 255))
            self._flash.set_alpha(alfa)
            tela.blit(self._flash, (0, 0))
