"""Menu scene — cinematic background, diegetic HUD, nave, destaque, transicao.

Migrated from game/menu_scene.py:
  FundoCinematico, HudMenu, NaveMenu, DestaqueMenu, TransicaoMissao,
  texto_espacado.

All visual elements receive a ``Layout`` for responsiveness — no hardcoded
pixel coordinates.
"""

from __future__ import annotations

import math
import random

import pygame

from src.core.constants import NEGRO


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def texto_espacado(
    fonte: pygame.font.Font, texto: str, espacamento: int,
    cor: tuple[int, int, int],
) -> pygame.Surface:
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


def _ease_out(t: float) -> float:
    return 1 - (1 - t) * (1 - t)


def _ease_in(t: float) -> float:
    return t * t


# ---------------------------------------------------------------------------
# Fundo cinematico
# ---------------------------------------------------------------------------

class FundoCinematico:
    """Fundo espacial com tres camadas de profundidade e elementos vivos."""

    def __init__(self, largura: int = 900, altura: int = 700) -> None:
        self._largura = largura
        self._altura = altura
        self.tempo: float = 0.0
        self._tile_largura = int(largura * 1.067)
        self._tile_altura = int(altura * 1.029)
        self.gradiente = self._criar_gradiente()
        self.nebulosa_fundo = self._criar_nebulosa(0.13, 7)
        self.nebulosa_frente = self._criar_nebulosa(0.19, 5)
        self.camadas = self._criar_estrelas()
        self.estrelas_heroicas = [
            [random.uniform(0, largura), random.uniform(0, altura),
             random.uniform(1.0, 2.4), random.uniform(0, math.tau)]
            for _ in range(34)
        ]
        self.planeta = self._criar_planeta(150, (26, 40, 86), (110, 190, 255),
                                           (150, 150, 210), True)
        self.lua = self._criar_planeta(52, (70, 60, 90), (150, 140, 190),
                                       (200, 190, 230), False)
        self.asteroides = self._criar_asteroides()
        self.particulas: list[dict] = []
        self.meteoros = [self._novo_meteoro() for _ in range(3)]

    # ----- construcao -----

    def _criar_gradiente(self) -> pygame.Surface:
        surf = pygame.Surface((1, self._altura))
        for y in range(self._altura):
            t = y / max(1, self._altura)
            r = int(10 + (3 - 10) * t)
            g = int(12 + (3 - 12) * t)
            b = int(38 + (15 - 38) * t)
            surf.set_at((0, y), (r, g, b))
        return pygame.transform.scale(surf, (self._largura, self._altura))

    def _criar_nebulosa(self, intensidade: float,
                        quantidade: int) -> pygame.Surface:
        surf = pygame.Surface((self._largura, self._altura), pygame.SRCALPHA)
        cores = [(70, 45, 140), (25, 85, 160), (130, 35, 120), (25, 120, 140)]
        for _ in range(quantidade):
            x = random.randint(-60, self._largura)
            y = random.randint(-60, self._altura)
            raio = random.randint(90, 240)
            blob = self._luz_radial(random.choice(cores), raio, intensidade)
            surf.blit(blob, blob.get_rect(center=(x, y)))
        return surf

    @staticmethod
    def _luz_radial(cor: tuple[int, int, int], raio: int,
                    intensidade: float) -> pygame.Surface:
        lado = raio * 2 + 20
        surf = pygame.Surface((lado, lado), pygame.SRCALPHA)
        cx = cy = lado // 2
        for r in range(raio, 0, -2):
            t = 1 - r / raio
            alpha = int(255 * intensidade * (1 - t))
            pygame.draw.circle(surf, cor + (alpha,), (cx, cy), r)
        return surf

    def _criar_estrelas(self) -> list[dict]:
        camadas = []
        for velocidade, qtd, brilho_min, brilho_max in (
            (0.22, 110, 60, 150),
            (0.55, 70, 100, 200),
            (1.15, 32, 150, 255),
        ):
            surf = pygame.Surface(
                (self._tile_largura, self._tile_altura), pygame.SRCALPHA,
            )
            for _ in range(qtd):
                x = random.randint(0, self._tile_largura - 1)
                y = random.randint(0, self._tile_altura - 1)
                brilho = random.randint(brilho_min, brilho_max)
                raio = random.choice((1, 1, 1, 2))
                pygame.draw.circle(
                    surf, (brilho, brilho, min(255, brilho + 18)),
                    (x, y), raio,
                )
            camadas.append({
                "surf": surf, "vel": velocidade,
                "x": random.uniform(0, self._tile_largura),
                "y": random.uniform(0, self._tile_altura),
            })
        return camadas

    def _criar_planeta(self, raio: int, cor_corpo: tuple,
                       cor_borda: tuple, cor_anel: tuple,
                       com_anel: bool) -> pygame.Surface:
        raio_esc = raio
        lado = raio_esc * 4
        surf = pygame.Surface((lado, lado), pygame.SRCALPHA)
        cx = cy = lado // 2
        atmosfera = self._luz_radial(cor_borda, raio_esc, 0.4)
        surf.blit(atmosfera, atmosfera.get_rect(center=(cx, cy)))
        for r in range(raio_esc, 0, -1):
            t = 1 - r / raio_esc
            brilho = 1.0 - 0.55 * t
            cor = tuple(int(min(255, c * brilho)) for c in cor_corpo)
            pygame.draw.circle(surf, cor + (255,), (cx, cy), r)
        if com_anel:
            anel = pygame.Surface((lado, lado), pygame.SRCALPHA)
            rect = pygame.Rect(cx - raio_esc * 2, cy - int(raio_esc * 0.6),
                               raio_esc * 4, int(raio_esc * 1.2))
            pygame.draw.ellipse(anel, cor_anel + (110,), rect,
                                max(3, int(raio_esc * 0.16)))
            surf.blit(anel, (0, 0))
        return surf

    def _criar_asteroides(self) -> list[dict]:
        asteroides = []
        for _ in range(5):
            raio = random.randint(9, 20)
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
                "x": random.uniform(0, self._largura),
                "y": random.uniform(0, self._altura),
                "vx": random.uniform(-0.35, 0.35),
                "vy": random.uniform(0.4, 1.1),
                "fase": random.uniform(0, math.tau),
            })
        return asteroides

    def _novo_meteoro(self) -> dict:
        return {
            "x": random.uniform(0, self._largura),
            "y": random.uniform(0, 130),
            "vx": random.uniform(-3.4, -1.5),
            "vy": random.uniform(2.2, 3.6),
            "vida": random.uniform(50, 95),
            "t": 0,
        }

    def _nova_particula(self) -> dict:
        return {
            "x": random.uniform(0, self._largura),
            "y": self._altura + 8,
            "vx": random.uniform(-0.5, 0.5),
            "vy": random.uniform(-0.7, -2.2),
            "r": random.uniform(0.6, 1.9),
            "cor": random.choice(((150, 170, 220), (200, 220, 255))),
            "t": 0,
            "max": random.randint(120, 220),
        }

    # ----- atualizacao -----

    def atualizar(self) -> None:
        self.tempo += 1 / 60.0
        for camada in self.camadas:
            camada["y"] += camada["vel"]
            if camada["y"] >= self._tile_altura:
                camada["y"] -= self._tile_altura
            camada["x"] += math.sin(self.tempo * 0.4) * 0.02
        for ast in self.asteroides:
            ast["x"] += ast["vx"]
            ast["y"] += ast["vy"]
            if ast["y"] > self._altura + 40:
                ast["y"] = -40
                ast["x"] = random.uniform(0, self._largura)
            if ast["x"] < -60:
                ast["x"] = self._largura + 60
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

    def desenhar(self, tela: pygame.Surface) -> None:
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

    def _desenhar_estrelas(self, tela: pygame.Surface) -> None:
        for camada in self.camadas:
            x = int(camada["x"])
            y = int(camada["y"])
            for off_x, off_y in (
                (0, 0), (self._tile_largura, 0),
                (0, self._tile_altura),
                (self._tile_largura, self._tile_altura),
            ):
                tela.blit(camada["surf"], (off_x - x, off_y - y))

    def _desenhar_planetas(self, tela: pygame.Surface) -> None:
        px = 60 + int(math.sin(self.tempo * 0.15) * 6)
        py = 702 - int(math.sin(self.tempo * 0.22) * 5)
        tela.blit(self.planeta, self.planeta.get_rect(center=(px, py)))
        lx = 900 + int(math.cos(self.tempo * 0.18) * 10)
        ly = 60 + int(math.sin(self.tempo * 0.12) * 8)
        tela.blit(self.lua, self.lua.get_rect(center=(lx, ly)))

    def _desenhar_heroicas(self, tela: pygame.Surface) -> None:
        for x, y, raio, fase in self.estrelas_heroicas:
            brilho = int(60 + 90 * (0.5 + 0.5 * math.sin(
                self.tempo * 3 + fase)))
            cor = (brilho, brilho, brilho + 25)
            pygame.draw.circle(tela, cor, (int(x), int(y)),
                               max(1, int(raio)))

    def _desenhar_particulas(self, tela: pygame.Surface) -> None:
        for p in self.particulas:
            fade = 1 - p["t"] / p["max"]
            cor = tuple(int(c * fade) for c in p["cor"])
            pygame.draw.circle(tela, cor, (int(p["x"]), int(p["y"])),
                               max(1, int(p["r"])))

    def _desenhar_meteoros(self, tela: pygame.Surface) -> None:
        for m in self.meteoros:
            fade = 1 - m["t"] / m["vida"]
            cor = tuple(int(230 * fade) for _ in range(3))
            pygame.draw.line(
                tela, cor, (int(m["x"]), int(m["y"])),
                (int(m["x"] - m["vx"] * 7), int(m["y"] - m["vy"] * 7)),
                2,
            )


# ---------------------------------------------------------------------------
# HUD diegetico
# ---------------------------------------------------------------------------

class HudMenu:
    """Elementos HUD de nave: molduras, radar, status e dados da missao."""

    def __init__(self, largura: int = 900, altura: int = 700) -> None:
        self._largura = largura
        self._altura = altura
        self.tempo: float = 0.0
        self._cache_texto: dict = {}
        self._coord: float = 430822.0
        self._coord_mult: float = 1.0
        self.radar_angulo: float = 0.0
        self.radar = self._criar_radar()
        self.banda = self._criar_banda()
        self.blips = [
            [random.uniform(0, math.tau), random.uniform(0.2, 0.8)]
            for _ in range(4)
        ]
        self._fuel: float = 0.72
        self._fuel_alvo: float = 0.72
        self._vel: float = 412.0
        self._vel_alvo: float = 412.0
        self._atualiza_contador: int = 0

    def _criar_radar(self) -> pygame.Surface:
        raio = 26
        lado = raio * 2 + 12
        surf = pygame.Surface((lado, lado), pygame.SRCALPHA)
        cx = cy = lado // 2
        pygame.draw.circle(surf, (90, 120, 170, 55), (cx, cy), raio, 1)
        pygame.draw.circle(surf, (90, 120, 170, 40), (cx, cy), raio - 9, 1)
        pygame.draw.circle(surf, (70, 95, 140, 30), (cx, cy), raio - 18, 1)
        pygame.draw.line(surf, (80, 110, 160, 45),
                         (cx - raio, cy), (cx + raio, cy), 1)
        pygame.draw.line(surf, (80, 110, 160, 45),
                         (cx, cy - raio), (cx, cy + raio), 1)
        for i in range(8):
            a = i * math.pi / 4
            pygame.draw.line(
                surf, (90, 130, 190, 35),
                (cx + math.cos(a) * (raio - 5), cy + math.sin(a) * (raio - 5)),
                (cx + math.cos(a) * raio, cy + math.sin(a) * raio), 1,
            )
        return surf

    def _criar_banda(self) -> pygame.Surface:
        surf = pygame.Surface((self._largura, 64), pygame.SRCALPHA)
        surf.fill((5, 7, 18, 165))
        pygame.draw.rect(surf, (30, 45, 90, 120), surf.get_rect(), 2)
        return surf

    def _texto(self, chave: str, fonte: pygame.font.Font, texto: str,
               cor: tuple, espacamento: int = 2) -> pygame.Surface:
        chave_cache = (id(fonte), chave, texto, tuple(cor), espacamento)
        if chave_cache not in self._cache_texto:
            self._cache_texto[chave_cache] = texto_espacado(
                fonte, texto, espacamento, cor,
            )
        return self._cache_texto[chave_cache]

    def _desenhar_texto(self, tela: pygame.Surface, chave: str,
                        fonte: pygame.font.Font, texto: str,
                        pos: tuple, cor: tuple, espacamento: int = 2,
                        alinhar: str = "esquerda") -> pygame.Rect:
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

    def atualizar(self) -> None:
        self.tempo += 1 / 60.0
        self.radar_angulo += 0.045
        self._atualiza_contador += 1
        if self._atualiza_contador % 5 == 0:
            self._coord += (random.uniform(1.2, 9.8) * self._coord_mult)
            if self._coord > 999999:
                self._coord_mult = -1.0
            elif self._coord < 100000:
                self._coord_mult = 1.0
        if random.random() < 0.03:
            self._fuel_alvo = max(0.4, min(0.85, self._fuel_alvo
                                           + random.uniform(-0.08, 0.08)))
        if random.random() < 0.05:
            self._vel_alvo = max(300, min(560, self._vel_alvo
                                          + random.uniform(-40, 40)))
        self._fuel += (self._fuel_alvo - self._fuel) * 0.02
        self._vel += (self._vel_alvo - self._vel) * 0.02

    # ----- desenho -----

    def desenhar(self, tela: pygame.Surface, tema: dict) -> None:
        l = self._largura
        h = self._altura
        primaria = tema["primaria"]
        secundaria = tema["secundaria"]
        borda = tema["borda_forte"]
        texto_cor = (205, 215, 240)
        dim = (140, 152, 190)
        fonte_p = pygame.font.SysFont("monospace", 12)
        fonte_m = pygame.font.SysFont("monospace", 15)
        fonte_t = pygame.font.SysFont("monospace", 16, bold=True)

        # canto superior esquerdo
        self._desenhar_texto(tela, "logo", fonte_t, "INCARNATE",
                             (32, 20), primaria, 4)
        self._desenhar_texto(tela, "sistema", fonte_p,
                             "// SISTEMA DIMENSIONAL", (34, 42), dim, 3)

        # canto superior direito
        pisca = 0.5 + 0.5 * math.sin(self.tempo * 3.2)
        cor_sys = (0, 255, 150) if pisca > 0.1 else (80, 255, 170)
        self._desenhar_texto(tela, "sys_rotulo", fonte_p, "SYS",
                             (l - 36, 20), dim, 2, "direita")
        self._desenhar_texto(tela, "sys_valor", fonte_p, "ONLINE",
                             (l - 34, 40), cor_sys, 2, "direita")
        coord_txt = "GRID %.0f.%.0f" % (self._coord % 1000,
                                        self._coord * 3 % 1000)
        self._desenhar_texto(tela, "coord", fonte_p, coord_txt,
                             (l - 34, 42), dim, 2, "direita")

        # radar
        cx, cy = 74, 588
        tela.blit(self.radar, self.radar.get_rect(center=(cx, cy)))
        a = self.radar_angulo
        r1 = 26
        pygame.draw.aaline(tela, primaria + (200,), (cx, cy),
                           (cx + math.cos(a) * r1, cy + math.sin(a) * r1), 2)
        for fase, _ in self.blips:
            bx = cx + math.cos(fase + self.tempo * 0.4) * r1 * 0.5
            by = cy + math.sin(fase + self.tempo * 0.4) * r1 * 0.5
            pygame.draw.circle(tela, secundaria, (int(bx), int(by)), 2)

        # banda inferior
        tela.blit(self.banda, (0, h - 64))
        pygame.draw.line(tela, primaria, (0, h - 64), (l, h - 64), 2)

        self._desenhar_texto(tela, "mis_rotulo", fonte_p, "MISSAO",
                             (40, h - 54), dim, 3)
        self._desenhar_texto(tela, "mis_valor", fonte_m,
                             "SALTO DIMENSIONAL", (40, h - 34), texto_cor, 3)
        self._desenhar_texto(tela, "mis_sub", fonte_p,
                             "TARGET // ENTER THE RIFT", (44, h - 20),
                             primaria, 2)

        self._desenhar_texto(tela, "fuel_rotulo", fonte_p, "COMBUSTIVEL",
                             (300, h - 56), dim, 3)
        x0, x1 = 300, 540
        y_barra = h - 40
        pygame.draw.rect(tela, (26, 30, 52), (x0, y_barra, x1 - x0, 9),
                         border_radius=4)
        larg = int((x1 - x0) * max(0.0, min(1.0, self._fuel)))
        if larg > 0:
            pygame.draw.rect(tela, primaria, (x0, y_barra, larg, 9),
                             border_radius=4)
        pct = int(self._fuel * 100)
        self._desenhar_texto(tela, "fuel_valor", fonte_p, f"{pct}%",
                             (556, y_barra + 4), texto_cor, 1, "direita")

        self._desenhar_texto(tela, "vel_rotulo", fonte_p, "VELOCIDADE",
                             (l - 40, h - 56), dim, 3, "direita")
        self._desenhar_texto(tela, "vel_valor", fonte_m,
                             "%.0f KC" % self._vel,
                             (l - 40, h - 36), (255, 200, 120), 3, "direita")
        self._desenhar_texto(tela, "vel_sub", fonte_p, "NAV MODE",
                             (l - 44, h - 22), borda, 2, "direita")


# ---------------------------------------------------------------------------
# Nave do jogador
# ---------------------------------------------------------------------------

class NaveMenu:
    """Nave do jogador em destaque no menu, com motores e balanco idle."""

    def __init__(self) -> None:
        self.tempo: float = 0.0

    def atualizar(self) -> None:
        self.tempo += 1 / 60.0

    def desenhar(self, tela: pygame.Surface, cor: tuple[int, int, int],
                 x: int, y: int, escala: float = 2.1) -> None:
        cx = int(x + math.sin(self.tempo * 1.7) * 5)
        cy = int(y + math.sin(self.tempo * 2.4) * 4)
        # Glow base
        pulso = 0.8 + 0.25 * math.sin(self.tempo * 7)
        for r in range(int(26 * escala * pulso), 0, -3):
            alpha = int(40 * (r / (26 * escala * pulso)))
            pygame.draw.circle(tela, cor + (alpha,), (cx, cy + int(16 * escala)),
                               r)
        # Traseira da nave (triangulo de fogo)
        base_y = cy + int(16 * escala)
        comprimento = int((14 + 7 * pulso) * escala)
        for larg, alfa in ((8, 90), (5, 170), (2, 255)):
            pygame.draw.polygon(
                tela,
                tuple(min(255, int(c * 0.5 + 90 * (larg == 2)))
                      for c in cor) + (alfa,),
                [(cx - larg // 2, base_y), (cx + larg // 2, base_y),
                 (cx, base_y + comprimento)],
            )
        # Corpo da nave (simplificado)
        pygame.draw.polygon(
            tela, cor,
            [(cx, cy - int(14 * escala)),
             (cx - int(10 * escala), cy + int(12 * escala)),
             (cx, cy + int(8 * escala)),
             (cx + int(10 * escala), cy + int(12 * escala))],
        )
        pygame.draw.polygon(
            tela, (255, 255, 255, 180),
            [(cx, cy - int(14 * escala)),
             (cx - int(10 * escala), cy + int(12 * escala)),
             (cx, cy + int(8 * escala)),
             (cx + int(10 * escala), cy + int(12 * escala))],
            1,
        )


# ---------------------------------------------------------------------------
# Destaque das opcoes
# ---------------------------------------------------------------------------

class DestaqueMenu:
    """Destaque deslizante das opcoes: paralelogramo inclinado + borda."""

    def __init__(self) -> None:
        self.y: float = 0.0
        self.alvo: float = 0.0
        self.tempo: float = 0.0
        self._pulso_escala: float = 0.0
        self._pulso_alvo: float = 0.0

    def atualizar(self) -> None:
        self.tempo += 1 / 60.0
        self.y += (self.alvo - self.y) * 0.16
        self._pulso_escala += (self._pulso_alvo - self._pulso_escala) * 0.1

    def pulsar(self) -> None:
        self._pulso_alvo = 1.0
        self._pulso_escala = 1.0

    def desenhar(self, tela: pygame.Surface, x: int, tema: dict) -> None:
        primaria = tema["primaria"]
        secundaria = tema["secundaria"]
        largura, altura, inclinacao = 360, 50, 16
        escala = 1.0 + 0.06 * self._pulso_escala + \
            0.02 * math.sin(self.tempo * 5)
        w = max(1, int(largura * escala))
        h = max(1, int(altura * escala))
        inc = max(1, int(inclinacao * escala))
        surf = pygame.Surface((w + inc, h), pygame.SRCALPHA)
        pts = [(0, inc), (w, 0), (w + inc, 0),
               (w + inc, h), (inc, h), (0, 0)]
        pygame.draw.polygon(surf, primaria + (66,), pts)
        pygame.draw.polygon(surf, primaria + (150,), pts, 2)
        pygame.draw.line(surf, secundaria + (200,), (0, 0), (w, 0), 3)
        rect = surf.get_rect(midleft=(x, int(self.y)))
        tela.blit(surf, rect)


# ---------------------------------------------------------------------------
# Transicao cinematografica
# ---------------------------------------------------------------------------

class TransicaoMissao:
    """Transicao ao iniciar a missao: zoom, tremida, riscas e flash."""

    def __init__(self, duracao: int = 950) -> None:
        self.duracao = duracao
        self.ativo: bool = False
        self.inicio: int = 0
        self.acao: callable | None = None
        self.tempo: float = 0.0

    def iniciar(self, acao: callable) -> None:
        self.ativo = True
        self.inicio = pygame.time.get_ticks()
        self.acao = acao
        self.tempo = 0.0

    def em_andamento(self) -> bool:
        return self.ativo

    def progresso(self) -> float:
        if not self.ativo:
            return 0.0
        return min(1.0, (pygame.time.get_ticks() - self.inicio) / self.duracao)

    def atualizar(self) -> bool:
        self.tempo += 1 / 60.0
        if self.ativo and self.progresso() >= 1.0:
            acao = self.acao
            self.ativo = False
            self.acao = None
            if acao:
                acao()
            return True
        return False

    def desenhar(self, tela: pygame.Surface, tema: dict) -> None:
        p = self.progresso()
        if p <= 0:
            return
        larg, alt = tela.get_size()
        # zoom
        zoom = 1.0 + 0.14 * _ease_in(p)
        if zoom > 1.001:
            nova = pygame.transform.smoothscale(
                tela, (int(larg * zoom), int(alt * zoom)),
            )
            tremida = int(math.sin(self.tempo * 55) * 5 * p)
            tela.fill(NEGRO)
            tela.blit(nova, nova.get_rect(center=(larg // 2 + tremida,
                                                   alt // 2)))
        # riscas
        vel = 8 + 40 * p
        for i in range(30):
            y = (i * 97 + int(self.tempo * 30)) % alt
            off = int((self.tempo * vel * (30 + i * 9))) % (larg + 500)
            x = off - 200
            cor = (200, 225, 255)
            pygame.draw.line(tela, cor, (x, y), (x + 180, y), 2)
        # pulso radial
        raio = int(30 + 300 * _ease_out(p))
        for r in range(raio, 0, -2):
            alpha = int(30 * (r / max(1, raio)) * p)
            pygame.draw.circle(tela, tema["primaria"] + (alpha,),
                               (larg // 2, alt // 2), r)
        # flash final
        if p > 0.8:
            alfa = int(255 * (p - 0.8) / 0.2)
            surf = pygame.Surface(tela.get_size())
            surf.fill((255, 255, 255))
            surf.set_alpha(alfa)
            tela.blit(surf, (0, 0))
