"""Fundos próprios por setor do mundo, com troca suave por posição."""

from __future__ import annotations

import math
import random

import pygame

from src.core.constants import ALTURA, LARGURA
from src.runtime.domain.world.scenarios import CENARIOS
from src.runtime.infrastructure.graphics.nebula_background import criar_fundo_nebuloso
from src.runtime.infrastructure.graphics.nebula_background import desenhar_planeta as _planeta
from src.runtime.infrastructure.graphics.smooth import luz_radial


def _misturar(a: tuple[int, int, int], b: tuple[int, int, int],
             proportion: float) -> tuple[int, int, int]:
    return tuple(round(a[index] * (1 - proportion) + b[index] * proportion)
                 for index in range(3))


def _estrela(surface: pygame.Surface, center: tuple[int, int], radius: int,
             color: tuple[int, int, int]) -> None:
    """Estrela distante com emissão radial suave e núcleo quente."""
    halo = luz_radial(color, radius * 2, 0.18)
    surface.blit(halo, halo.get_rect(center=center))
    for raio in range(radius, 0, -1):
        t = 1 - raio / radius
        cor = tuple(min(210, round(c * (0.35 + t * 0.5))) for c in color)
        pygame.draw.circle(surface, cor, center, raio)


def _cometa(surface: pygame.Surface, head: tuple[int, int],
            color: tuple[int, int, int], length: int) -> None:
    """Marca um cometa ou meteoroide com núcleo quente e cauda afilada."""
    x, y = head
    distant = (x - length, y + length // 3)
    near = (x - length // 3, y + length // 9)
    pygame.draw.line(surface, _misturar(color, (26, 34, 53), 0.72),
                     distant, head, 6)
    pygame.draw.line(surface, _misturar(color, (240, 220, 190), 0.35),
                     (x - length * 2 // 3, y + length * 2 // 9), head, 3)
    pygame.draw.line(surface, (252, 229, 190), near, head, 1)
    pygame.draw.circle(surface, _misturar(color, (246, 238, 217), 0.6), head, 4)
    pygame.draw.circle(surface, (255, 245, 220), head, 2)
    pygame.draw.circle(surface, color,
                       (x - length // 2, y + length // 6 + 4), 1)


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
        gas = _misturar(scene["cores_principais"][0], accent, 0.25)
        result = criar_fundo_nebuloso((LARGURA, ALTURA), top, bottom, gas,
                                      self.dimension * 1009 + sector * 97, comic)

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
            _estrela(surface, (1110 + jitter, 145), 32, (230, 181, 94))
            _planeta(surface, (125 + jitter, 535), 154,
                     _misturar(accent, (145, 111, 91), 0.5), craters=True)
            for _ in range(55):
                x = rng.randrange(105, 575)
                y = 500 + round(math.sin(x / 55) * 24) + rng.randrange(-16, 17)
                pygame.draw.circle(surface, accent, (x, y), rng.choice((1, 2)))
        elif sector == 1:
            _estrela(surface, (1190 + jitter, 85), 104, (183, 97, 103))
            _estrela(surface, (240 + jitter, 175), 13, (157, 207, 235))
            nodes = ((190, 335), (300, 230), (390, 315), (520, 205),
                     (650, 360), (780, 265), (940, 335))
            for point in nodes:
                pygame.draw.circle(surface, _misturar(accent, (181, 215, 235), 0.35),
                                   (point[0], point[1] // 2), 2)
            _cometa(surface, (710, 115), (159, 216, 230), 125)
        elif sector == 2:
            _estrela(surface, (1150, 135), 80, (217, 142, 93))
            _planeta(surface, (140 + jitter, 530), 175,
                     _misturar(accent, (165, 132, 96), 0.55), rings=True)
        elif sector == 3:
            center = (1020 + jitter, 175)
            _galaxia(surface, center, accent)
            _estrela(surface, center, 22, (212, 198, 181))
        elif sector == 4:
            # Faixa distante na periferia; nenhum falso perigo ocupa o centro.
            _galaxia(surface, (1080 + jitter, 170), _misturar(accent, (15, 20, 34), 0.6))
            _estrela(surface, (180, 560), 9, (157, 177, 205))
        else:
            _planeta(surface, (1140 + jitter, 535), 180,
                     _misturar(accent, (110, 172, 198), 0.6), craters=True)
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
