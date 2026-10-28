"""Fundos próprios por setor do mundo, com troca suave por posição."""

from __future__ import annotations

import math
import random

import pygame

from src.core.constants import ALTURA, LARGURA
from src.runtime.domain.world.scenarios import CENARIOS


def _misturar(a: tuple[int, int, int], b: tuple[int, int, int],
             proportion: float) -> tuple[int, int, int]:
    return tuple(round(a[index] * (1 - proportion) + b[index] * proportion)
                 for index in range(3))


def _estrela(surface: pygame.Surface, center: tuple[int, int], radius: int,
             color: tuple[int, int, int]) -> None:
    """Desenha estrelas de tamanhos distintos, da anã à supergigante."""
    x, y = center
    halo = _misturar(color, (25, 31, 48), 0.55)
    pygame.draw.circle(surface, halo, center, radius + max(5, radius // 3), 2)
    pygame.draw.circle(surface, color, center, radius)
    pygame.draw.circle(surface, _misturar(color, (255, 255, 240), 0.55),
                       (x - radius // 4, y - radius // 4), max(2, radius // 3))
    reach = radius + max(10, radius // 2)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        pygame.draw.line(surface, halo, (x + dx * radius, y + dy * radius),
                         (x + dx * reach, y + dy * reach), 2)


def _planeta(surface: pygame.Surface, center: tuple[int, int], radius: int,
             color: tuple[int, int, int], *, rings: bool = False,
             craters: bool = False) -> None:
    """Compõe um corpo rochoso, gasoso ou gelado com sombra e relevo."""
    x, y = center
    shade = _misturar(color, (9, 15, 31), 0.65)
    light = _misturar(color, (210, 228, 240), 0.35)
    if rings:
        pygame.draw.ellipse(surface, light,
                            (x - radius * 2, y - radius // 3,
                             radius * 4, radius * 2 // 3), 4)
    pygame.draw.circle(surface, shade, center, radius)
    pygame.draw.circle(surface, color,
                       (x - radius // 7, y - radius // 9), radius * 6 // 7)
    pygame.draw.circle(surface, light,
                       (x - radius // 3, y - radius // 3), max(4, radius // 7), 2)
    if craters:
        for dx, dy, size in ((-0.33, 0.12, 0.13), (0.12, -0.27, 0.08),
                             (0.29, 0.32, 0.11)):
            pygame.draw.circle(surface, shade,
                               (x + round(radius * dx), y + round(radius * dy)),
                               max(2, round(radius * size)), 2)
    else:
        for offset in (-0.32, -0.04, 0.25):
            yy = y + round(radius * offset)
            span = round(radius * math.sqrt(max(0.0, 1 - offset * offset)))
            pygame.draw.arc(surface, light,
                            (x - span, yy - 11, span * 2, 22), 0.2, 2.9, 2)
    if rings:
        pygame.draw.arc(surface, light,
                        (x - radius * 2, y - radius // 3,
                         radius * 4, radius * 2 // 3), math.pi, math.tau, 4)


def _nebulosa(surface: pygame.Surface, center: tuple[int, int],
              color: tuple[int, int, int], rng: random.Random) -> None:
    """Acumula camadas translúcidas de gás e poeira com estrelas jovens."""
    veil = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    for index in range(9):
        radius_x = 65 + index * 20
        radius_y = 35 + index * 12
        x = center[0] + rng.randrange(-110, 111)
        y = center[1] + rng.randrange(-85, 86)
        pygame.draw.ellipse(veil, (*color, 12 + index),
                            (x - radius_x, y - radius_y,
                             radius_x * 2, radius_y * 2))
    surface.blit(veil, (0, 0))
    for _ in range(18):
        x = center[0] + rng.randrange(-180, 181)
        y = center[1] + rng.randrange(-120, 121)
        pygame.draw.circle(surface, _misturar(color, (236, 240, 250), 0.5),
                           (x, y), rng.choice((1, 1, 2)))


def _cometa(surface: pygame.Surface, head: tuple[int, int],
            color: tuple[int, int, int], length: int) -> None:
    """Marca um cometa ou meteoroide com cauda direcional."""
    x, y = head
    pygame.draw.line(surface, _misturar(color, (26, 34, 53), 0.55),
                     (x - length, y + length // 3), (x, y), 5)
    pygame.draw.line(surface, color,
                     (x - length // 2, y + length // 6), (x, y), 2)
    pygame.draw.circle(surface, color, head, 4)


def _galaxia(surface: pygame.Surface, center: tuple[int, int],
             accent: tuple[int, int, int]) -> None:
    """Espalha braços espirais densos em uma galáxia inclinada."""
    for arm in range(4):
        for index in range(125):
            radius = 12 + index * 2.0
            angle = index * 0.075 + arm * math.tau / 4
            x = round(center[0] + math.cos(angle) * radius)
            y = round(center[1] + math.sin(angle) * radius * 0.52)
            if 0 <= x < LARGURA and 0 <= y < ALTURA:
                color = _misturar(accent, (211, 203, 224), index / 170)
                pygame.draw.circle(surface, color, (x, y), 1 if index > 20 else 2)


class SectorBackground:
    """Cacheia seis composições e acompanha o setor próximo da nave."""

    TRANSITION_SECONDS = 1.0
    motifs = (
        "sistema_rochoso", "constelacoes", "gigante_gasoso",
        "galaxia_espiral", "horizonte_negro", "exoplaneta_gelado",
    )

    def __init__(self, dimension: int,
                 sectors: tuple[tuple[str, tuple[float, float],
                                      tuple[int, int, int]], ...],
                 position: tuple[float, float]) -> None:
        self.dimension = dimension
        self.sectors = sectors
        self.current_sector = self._nearest(*position)
        self.target_sector = self.current_sector
        self.transition = 1.0
        self._transitioning = False
        self._interrupted = False
        self._sources: dict[bool, pygame.Surface] = {}
        self._surfaces: dict[tuple[int, bool], pygame.Surface] = {}
        self._blend = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

    def _nearest(self, x: float, y: float) -> int:
        return min(range(len(self.sectors)), key=lambda index:
                   math.hypot(x - self.sectors[index][1][0],
                              y - self.sectors[index][1][1]))

    def update(self, x: float, y: float, dt: float) -> None:
        """Segue o setor próximo com transição contínua e ritmo suavizado."""
        self.transition_to(x, y)
        if not self._transitioning:
            return
        self.transition = min(1.0, self.transition + max(0.0, dt) / self.TRANSITION_SECONDS)
        if self.transition >= 1.0:
            self.current_sector = self.target_sector
            self._transitioning = False
            self._interrupted = False

    def transition_to(self, x: float, y: float) -> None:
        """Aponta para o novo setor sem perder o quadro misturado atual."""
        nearest = self._nearest(x, y)
        if nearest == self.target_sector:
            return
        if self._transitioning:
            self._capture_source()
        else:
            self._interrupted = False
        self.target_sector = nearest
        self.transition = 0.0
        self._transitioning = True

    @staticmethod
    def _eased(progress: float) -> float:
        progress = max(0.0, min(1.0, progress))
        return progress * progress * (3.0 - 2.0 * progress)

    def _capture_source(self) -> None:
        """Congela a mistura atual apenas quando o alvo muda no meio da troca."""
        amount = round(255 * self._eased(self.transition))
        for comic in (False, True):
            source = self._sources.get(comic)
            if source is None:
                source = pygame.Surface((LARGURA, ALTURA))
                self._sources[comic] = source
            if not self._interrupted:
                source.blit(self.surface_for_sector(self.current_sector, comic), (0, 0))
            self._blend.blit(self.surface_for_sector(self.target_sector, comic), (0, 0))
            self._blend.set_alpha(amount)
            source.blit(self._blend, (0, 0))
        self._interrupted = True

    def surface_for_sector(self, sector: int, comic: bool) -> pygame.Surface:
        """Obtém a composição cacheada de um setor e estilo de apresentação."""
        key = (sector, comic)
        if key in self._surfaces:
            return self._surfaces[key]
        rng = random.Random(self.dimension * 1009 + sector * 97 + int(comic))
        scene = CENARIOS[self.dimension - 1]
        accent = self.sectors[sector][2]
        top = _misturar(scene["topo"], accent, 0.22)
        bottom = _misturar(scene["base"], accent, 0.18)
        if comic:
            top = _misturar((37, 37, 43), accent, 0.22)
            bottom = _misturar((52, 46, 43), accent, 0.16)
        result = pygame.Surface((LARGURA, ALTURA))
        for y in range(ALTURA):
            color = _misturar(top, bottom, y / max(1, ALTURA - 1))
            pygame.draw.line(result, color, (0, y), (LARGURA, y))

        for _ in range(95):
            x, y = rng.randrange(LARGURA), rng.randrange(ALTURA)
            color = _misturar(accent, (185, 198, 220), rng.uniform(0.2, 0.65))
            pygame.draw.circle(result, color, (x, y), rng.choice((1, 1, 2)))
        self._draw_motif(result, sector, accent, rng)
        if comic:
            ink = _misturar(top, (7, 10, 18), 0.4)
            for y in range(8, ALTURA, 24):
                for x in range(8 + (y // 24 % 2) * 12, LARGURA, 24):
                    pygame.draw.circle(result, ink, (x, y), 1)
        self._surfaces[key] = result
        return result

    def _draw_motif(self, surface: pygame.Surface, sector: int,
                    accent: tuple[int, int, int], rng: random.Random) -> None:
        """Atribui uma silhueta própria a cada uma das seis áreas."""
        jitter = rng.randrange(-55, 56)
        if sector == 0:
            _estrela(surface, (970 + jitter, 430), 43, (230, 181, 94))
            _planeta(surface, (320 + jitter, 395), 126,
                     _misturar(accent, (145, 111, 91), 0.5), craters=True)
            _planeta(surface, (495 + jitter, 245), 29, (129, 143, 158), craters=True)
            for _ in range(55):
                x = rng.randrange(105, 575)
                y = 500 + round(math.sin(x / 55) * 24) + rng.randrange(-16, 17)
                pygame.draw.circle(surface, accent, (x, y), rng.choice((1, 2)))
        elif sector == 1:
            _estrela(surface, (1030 + jitter, 400), 94, (183, 97, 103))
            _estrela(surface, (240 + jitter, 175), 13, (157, 207, 235))
            nodes = ((190, 335), (300, 230), (390, 315), (520, 205),
                     (650, 360), (780, 265), (940, 335))
            for start, end in zip(nodes, nodes[1:]):
                pygame.draw.line(surface, _misturar(accent, (178, 204, 224), 0.45),
                                 start, end, 2)
            for point in nodes:
                pygame.draw.circle(surface, (181, 215, 235), point, 5)
            _cometa(surface, (710, 115), (159, 216, 230), 125)
        elif sector == 2:
            _estrela(surface, (1100, 195), 115, (217, 142, 93))
            _planeta(surface, (420 + jitter, 410), 162,
                     _misturar(accent, (165, 132, 96), 0.55), rings=True)
            for point, radius in (((700, 280), 24), ((785, 485), 17),
                                  ((270, 170), 13)):
                _planeta(surface, point, radius, (135, 146, 159), craters=True)
        elif sector == 3:
            _nebulosa(surface, (830, 350), _misturar(accent, (100, 133, 180), 0.4), rng)
            center = (780 + jitter, 360)
            _galaxia(surface, center, accent)
            _estrela(surface, center, 22, (212, 198, 181))
        elif sector == 4:
            _nebulosa(surface, (625, 355), _misturar(accent, (105, 69, 135), 0.45), rng)
            center = (635 + jitter, 360)
            pygame.draw.ellipse(surface, (191, 115, 176),
                                (center[0] - 240, center[1] - 70, 480, 140), 7)
            pygame.draw.circle(surface, (170, 160, 213), center, 118, 3)
            pygame.draw.circle(surface, (5, 8, 19), center, 108)
            for _ in range(9):
                _cometa(surface,
                        (rng.randrange(110, 1170), rng.randrange(110, 620)),
                        (157, 177, 205), rng.randrange(35, 95))
        else:
            _nebulosa(surface, (380, 270), _misturar(accent, (98, 144, 177), 0.55), rng)
            _planeta(surface, (920 + jitter, 415), 142,
                     _misturar(accent, (110, 172, 198), 0.6), craters=True)
            _planeta(surface, (1080 + jitter, 215), 35,
                     (173, 199, 213), craters=True)
            _estrela(surface, (265, 470), 16, (153, 218, 234))
            _cometa(surface, (655, 130), (151, 216, 231), 135)

    def render(self, surface: pygame.Surface, comic: bool) -> None:
        """Desenha o setor atual e mistura gradualmente o próximo."""
        source = (self._sources[comic] if self._interrupted else
                  self.surface_for_sector(self.current_sector, comic))
        surface.blit(source, (0, 0))
        if self._transitioning:
            self._blend.blit(self.surface_for_sector(self.target_sector, comic), (0, 0))
            self._blend.set_alpha(round(255 * self._eased(self.transition)))
            surface.blit(self._blend, (0, 0))
