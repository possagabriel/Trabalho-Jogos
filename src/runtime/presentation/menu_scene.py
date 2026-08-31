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

from src.runtime.infrastructure.assets import carregar_imagem
from src.core.constants import NEGRO
from src.infrastructure.ui.layout import Layout
from src.runtime.domain.entities.player import Jogador
from src.runtime.infrastructure.graphics.smooth import desenhar_cantos, desenhar_circulo, desenhar_glow, \
    gradiente_vertical, luz_radial, retangulo_suave


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
        self.lua = self._criar_planeta(52, (70, 60, 90), (150, 140, 190),
                                       (200, 190, 230), False)
        self.asteroides = self._criar_asteroides()
        self.particulas = []
        self.meteoros = [self._novo_meteoro() for _ in range(3)]

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
        l = self._layout
        surf = pygame.Surface((l.largura, l.altura), pygame.SRCALPHA)
        cores = [(70, 45, 140), (25, 85, 160), (130, 35, 120), (25, 120, 140)]
        for _ in range(quantidade):
            x = random.randint(-l.px(100), l.largura)
            y = random.randint(-l.px(100), l.altura)
            raio = random.randint(l.px(90), l.px(240))
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
        l = self._layout
        raio = l.px(raio)
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
            y = cy - l.px(12) + i * l.px(4)
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
        l = self._layout
        asteroides = []
        for _ in range(5):
            raio = random.randint(l.px(9), l.px(20))
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
                "x": random.uniform(0, l.largura), "y": random.uniform(0, l.altura),
                "vx": random.uniform(-0.35, 0.35), "vy": random.uniform(0.4, 1.1),
                "fase": random.uniform(0, math.tau)})
        return asteroides

    def _novo_meteoro(self):
        l = self._layout
        return {"x": random.uniform(0, l.largura), "y": random.uniform(0, l.px(130)),
                "vx": random.uniform(-3.4, -1.5), "vy": random.uniform(2.2, 3.6),
                "vida": random.uniform(50, 95), "t": 0}

    def _nova_particula(self):
        l = self._layout
        return {"x": random.uniform(0, l.largura), "y": l.altura + l.px(8),
                "vx": random.uniform(-0.5, 0.5),
                "vy": random.uniform(-0.7, -2.2),
                "r": random.uniform(0.6, 1.9),
                "cor": random.choice(((150, 170, 220), (200, 220, 255))),
                "t": 0, "max": random.randint(120, 220)}

    # ----- atualizacao -----

    def atualizar(self):
        l = self._layout
        self.tempo += 1 / 60.0
        for camada in self.camadas:
            camada["y"] += camada["vel"]
            if camada["y"] >= self._tile_altura:
                camada["y"] -= self._tile_altura
            camada["x"] += math.sin(self.tempo * 0.4) * 0.02
        for ast in self.asteroides:
            ast["x"] += ast["vx"]
            ast["y"] += ast["vy"]
            if ast["y"] > l.altura + l.px(40):
                ast["y"] = -l.px(40)
                ast["x"] = random.uniform(0, l.largura)
            if ast["x"] < -l.px(60):
                ast["x"] = l.largura + l.px(60)
        for m in self.meteoros[:]:
            m["x"] += m["vx"]
            m["y"] += m["vy"]
            m["t"] += 1
            if m["t"] >= m["vida"]:
                self.meteoros.remove(m)
                self.meteoros.append(self._novo_meteoro())
        if len(self.particulas) < 42 and random.random() < 0.4:
            self.particulas.append(self._nova_particula())
        for p in self.particulas[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["t"] += 1
            if p["t"] >= p["max"]:
                self.particulas.remove(p)

    # ----- desenho -----

    def desenhar(self, tela):
        if self.fundo_imagem is not None:
            tela.blit(self.fundo_imagem, (0, 0))
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
        l = self._layout
        px = l.px(60) + int(math.sin(self.tempo * 0.15) * l.px(6))
        py = l.px(702) - int(math.sin(self.tempo * 0.22) * l.px(5))
        tela.blit(self.planeta, self.planeta.get_rect(center=(px, py)))
        lx = l.px(900) + int(math.cos(self.tempo * 0.18) * l.px(10))
        ly = l.px(60) + int(math.sin(self.tempo * 0.12) * l.px(8))
        tela.blit(self.lua, self.lua.get_rect(center=(lx, ly)))

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
        for m in self.meteoros:
            fade = 1 - m["t"] / m["vida"]
            cor = tuple(int(230 * fade) for _ in range(3))
            pygame.draw.line(tela, cor, (int(m["x"]), int(m["y"])),
                             (int(m["x"] - m["vx"] * 7),
                              int(m["y"] - m["vy"] * 7)), 2)


# ---------------------------------------------------------------------------
# HUD diegetico
# ---------------------------------------------------------------------------

class HudMenu:
    """Elementos HUD de nave: molduras, radar, status e dados da missao."""

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
        l = self._layout
        raio = l.px(26)
        lado = raio * 2 + l.px(12)
        surf = pygame.Surface((lado, lado), pygame.SRCALPHA)
        cx = cy = lado // 2
        pygame.draw.circle(surf, (90, 120, 170, 55), (cx, cy), raio, 1)
        pygame.draw.circle(surf, (90, 120, 170, 40), (cx, cy), raio - l.px(9), 1)
        pygame.draw.circle(surf, (70, 95, 140, 30), (cx, cy), raio - l.px(18), 1)
        pygame.draw.line(surf, (80, 110, 160, 45), (cx - raio, cy), (cx + raio, cy), 1)
        pygame.draw.line(surf, (80, 110, 160, 45), (cx, cy - raio), (cx, cy + raio), 1)
        for i in range(8):
            a = i * math.pi / 4
            pygame.draw.line(surf, (90, 130, 190, 35),
                             (cx + math.cos(a) * (raio - l.px(5)),
                              cy + math.sin(a) * (raio - l.px(5))),
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

    def desenhar(self, tela, tema):
        l = self._layout
        primaria = tema["primaria"]
        secundaria = tema["secundaria"]
        borda = tema["borda_forte"]
        texto_cor = (205, 215, 240)
        dim = (140, 152, 190)

        desenhar_cantos(tela, borda,
                        pygame.Rect(l.px(12), l.px(12),
                                    l.largura - l.px(24), l.altura - l.px(24)),
                        tamanho=l.px(16), espessura=l.px(3))
        desenhar_cantos(tela, primaria,
                        pygame.Rect(l.px(20), l.px(20),
                                    l.largura - l.px(40), l.altura - l.px(40)),
                        tamanho=l.px(8), espessura=l.px(2))

        # canto superior esquerdo: logo + missao
        self._desenhar_texto(tela, "logo", l.fonte_titulo(16), "VOID//SHIFT",
                             (l.px(32), l.px(20)), primaria, 4)
        self._desenhar_texto(tela, "sistema", l.fonte_texto(12),
                             "// SISTEMA DIMENSIONAL", (l.px(34), l.px(42)),
                             dim, 3)

        # canto superior direito: status + coordenadas
        pisca = 0.5 + 0.5 * math.sin(self.tempo * 3.2)
        cor_sys = (0, 255, 150) if pisca > 0.1 else (80, 255, 170)
        self._desenhar_texto(tela, "sys_rotulo", l.fonte_texto(12), "SYS",
                             (l.largura - l.px(36), l.px(20)), dim, 2, "direita")
        self._desenhar_texto(tela, "sys_valor", l.fonte_texto(12), "ONLINE",
                             (l.largura - l.px(34), l.px(40)), cor_sys, 2,
                             "direita")
        coord_txt = "GRID %.0f.%.0f" % (self._coord % 1000,
                                        self._coord * 3 % 1000)
        self._desenhar_texto(tela, "coord", l.fonte_texto(11), coord_txt,
                             (l.largura - l.px(34), l.px(42)), dim, 2, "direita")

        # radar inferior esquerdo
        cx, cy = l.px(74), l.px(588)
        tela.blit(self.radar, self.radar.get_rect(center=(cx, cy)))
        a = self.radar_angulo
        r1 = l.px(26)
        pygame.draw.aaline(tela, primaria + (200,), (cx, cy),
                           (cx + math.cos(a) * r1, cy + math.sin(a) * r1), 2)
        pygame.draw.aaline(tela, (200, 220, 255, 140), (cx, cy),
                           (cx + math.cos(a + 2.2) * r1 * 0.7,
                            cy + math.sin(a + 2.2) * r1 * 0.7), 1)
        for fase, raio in self.blips:
            bx = cx + math.cos(fase + self.tempo * 0.4) * r1 * 0.5
            by = cy + math.sin(fase + self.tempo * 0.4) * r1 * 0.5
            desenhar_circulo(tela, secundaria, (bx, by), l.px(2), brilho=1.2)



        # missao
        self._desenhar_texto(tela, "mis_rotulo", l.fonte_texto(12), "MISSAO",
                             (l.px(40), l.altura - l.px(54)), dim, 3)
        self._desenhar_texto(tela, "mis_valor", l.fonte_texto(15),
                             "SALTO DIMENSIONAL", (l.px(40), l.altura - l.px(34)),
                             texto_cor, 3)
        self._desenhar_texto(tela, "mis_sub", l.fonte_texto(11),
                             "TARGET // ENTER THE RIFT", (l.px(44),
                                                          l.altura - l.px(20)),
                             primaria, 2)

        # velocidade + coordenadas
        self._desenhar_texto(tela, "vel_rotulo", l.fonte_texto(12),
                             "VELOCIDADE", (l.largura - l.px(40),
                                            l.altura - l.px(56)),
                             dim, 3, "direita")
        self._desenhar_texto(tela, "vel_valor", l.fonte_texto(15),
                             "%.0f KC" % self._vel, (l.largura - l.px(40),
                                                     l.altura - l.px(36)),
                             (255, 200, 120), 3, "direita")
        self._desenhar_texto(tela, "vel_sub", l.fonte_texto(11),
                             "NAV MODE", (l.largura - l.px(44),
                                          l.altura - l.px(22)),
                             borda, 2, "direita")


# ---------------------------------------------------------------------------
# Nave do jogador
# ---------------------------------------------------------------------------

class NaveMenu:
    """Nave do jogador em destaque no menu, com motores e balanco idle."""

    def __init__(self):
        self._jogador = None
        self._skin_id = None
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

        surf = pygame.Surface((96, 96), pygame.SRCALPHA)
        jog.skin.desenhar(surf, jog)
        if abs(escala - 1.0) > 0.01:
            surf = pygame.transform.smoothscale(
                surf, (int(96 * escala), int(96 * escala)))

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
        l = self._layout
        primaria = tema["primaria"]
        secundaria = tema["secundaria"]
        largura, altura, inclinacao = l.px(360), l.px(50), l.px(16)
        surf = pygame.Surface((largura + inclinacao, altura), pygame.SRCALPHA)
        pts = [(0, inclinacao), (largura, 0), (largura + inclinacao, 0),
               (largura + inclinacao, altura), (inclinacao, altura), (0, 0)]
        pygame.draw.polygon(surf, primaria + (66,), pts)
        pygame.draw.polygon(surf, primaria + (150,), pts, 2)
        pygame.draw.line(surf, secundaria + (200,), (0, 0), (largura, 0), 3)
        # detalhe interno
        pygame.draw.polygon(surf, (255, 255, 255, 26),
                            [(l.px(6), inclinacao - l.px(4)),
                             (largura - l.px(4), l.px(3)),
                             (largura - l.px(4), l.px(10)),
                             (l.px(6), inclinacao + l.px(3))])
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
        h = forma.get_height()
        escala = 1.0 + 0.06 * self._pulso_escala + \
            0.02 * math.sin(self.tempo * 5)
        if abs(escala - 1.0) > 0.01:
            forma = pygame.transform.smoothscale(
                forma, (max(1, int(forma.get_width() * escala)),
                        max(1, int(h * escala))))
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

    def desenhar(self, tela, tema):
        l = self._layout
        p = self.progresso()
        if p <= 0:
            return
        zoom = 1.0 + 0.14 * _ease_in(p)
        if zoom > 1.001:
            larg, alt = tela.get_size()
            nova = pygame.transform.smoothscale(
                tela, (int(larg * zoom), int(alt * zoom)))
            tremida = int(math.sin(self.tempo * 55) * 5 * p)
            tela.fill(NEGRO)
            tela.blit(nova, nova.get_rect(center=(larg // 2 + tremida,
                                                  alt // 2)))

        # riscas de velocidade
        vel = 8 + 40 * p
        for i in range(30):
            y = (i * 97 + int(self.tempo * 30)) % l.altura
            off = int((self.tempo * vel * (30 + i * 9))) % (l.largura + 500)
            x = off - 200
            alfa = 60 + int(180 * (i / 30) * p)
            cor = (200, 225, 255)
            pygame.draw.line(tela, cor, (x, y), (x + 180, y), 2)
            if i % 3 == 0:
                pygame.draw.line(tela, cor, (x + 60, y - 3), (x + 110, y - 3), 1)

        # pulso radial central
        raio = int(30 + 300 * _ease_out(p))
        desenhar_glow(tela, tema["primaria"], (l.x(0.5), l.y(0.5)),
                      max(8, raio // 6), 0.4 + 0.5 * p)

        # flash final
        if p > 0.8:
            alfa = int(255 * (p - 0.8) / 0.2)
            surf = pygame.Surface(tela.get_size())
            surf.fill((255, 255, 255))
            surf.set_alpha(alfa)
            tela.blit(surf, (0, 0))
