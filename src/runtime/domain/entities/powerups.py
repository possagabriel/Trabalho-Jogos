"""Power-ups que caem durante o jogo."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Callable, Literal, TypeAlias

import pygame

from src.runtime.infrastructure.graphics.cel_shading import circulo_com_contorno, desenhar_highlight
from src.core.constants import AZUL, BRANCO, CIANO, DOURADO, LARANJA, VERDE, \
    VERDE_CLARO
from src.runtime.infrastructure.graphics.smooth import desenhar_circulo, desenhar_glow
from src.runtime.domain.entities.weapons import ARMARIA

if TYPE_CHECKING:
    from src.runtime.domain.entities.player import Jogador

TipoPowerUp: TypeAlias = Literal[
    "escudo", "vida", "arma", "velocidade", "moedas", "skin",
    "especial_cura", "especial_imortal",
]


class PowerUp:
    CORES = {"escudo": AZUL, "vida": VERDE, "arma": CIANO, "velocidade": LARANJA,
             "moedas": DOURADO, "skin": VERDE_CLARO,
             "especial_cura": VERDE, "especial_imortal": (220, 220, 255)}
    SIMBOLOS = {"escudo": "E", "vida": "+", "arma": "A", "velocidade": "V",
                "moedas": "C", "skin": "S", "especial_cura": "+3",
                "especial_imortal": "I"}

    def __init__(self, tipo: TipoPowerUp, x: float, y: float) -> None:
        self.tipo = tipo
        self.x = x
        self.y = y
        self.raio = 14
        self.tempo = random.randint(0, 60)
        self.vel_y = 2

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.raio), int(self.y - self.raio),
                           self.raio * 2, self.raio * 2)

    def atualizar(self) -> None:
        self.y += self.vel_y
        self.tempo += 1
        self.x += math.sin(self.tempo * 0.05) * 0.5

    def aplicar(self, jogador: Jogador,
                desbloquear_skin: Callable[[str], bool] | None = None) -> str:
        """Aplica o efeito. Retorna a mensagem para exibir."""
        if self.tipo == "vida":
            if jogador.vida >= jogador.max_vida:
                return "Vida no maximo!"
            jogador.vida += 1
            return "Vida +1"
        if self.tipo == "escudo":
            jogador.escudo = True
            return "Escudo ativado!"
        if self.tipo == "velocidade":
            jogador.velocidade = min(9, jogador.velocidade + 1)
            return "Velocidade +1"
        if self.tipo == "moedas":
            jogador.moedas_jogo += 100
            return "Moedas +100"
        if self.tipo == "skin":
            if desbloquear_skin and desbloquear_skin("cristal"):
                return "VISUAL CRISTAL DESBLOQUEADO!"
            jogador.moedas_jogo += 500
            return "Visual repetido! +500 moedas"
        if self.tipo == "arma":
            if jogador.arma_atual >= len(ARMARIA) - 1:
                jogador.moedas_jogo += 200
                return "Arma maxima! +200 moedas"
            bloqueadas = [i for i in range(len(ARMARIA))
                          if i not in jogador.armas_desbloqueadas]
            if not bloqueadas:
                jogador.moedas_jogo += 200
                return "Arma maxima! +200 moedas"
            nova = bloqueadas[0]
            jogador.armas_desbloqueadas.append(nova)
            return f"Arma nova: {ARMARIA[nova]['nome']}! Selecione com TAB"
        return ""

    def desenhar(self, tela: pygame.Surface) -> None:
        pulso = 1 + 0.2 * math.sin(self.tempo * 0.2)
        raio = self.raio * pulso
        x, y = self.x, self.y
        cor = self.CORES[self.tipo]
        desenhar_glow(tela, cor, (x, y), raio * 2.2, 0.7)
        circulo_com_contorno(tela, cor, (x, y), int(raio),
                            espessura_contorno=3)
        desenhar_highlight(tela, (x, y), raio, intensidade=0.6)
        fonte = pygame.font.Font(None, 22)
        texto = fonte.render(self.SIMBOLOS[self.tipo], True, BRANCO)
        tela.blit(texto, texto.get_rect(center=(int(x), int(y))))


def sortear_tipo() -> TipoPowerUp:
    return random.choices(["escudo", "vida", "arma", "velocidade", "moedas"],
                          [12, 28, 22, 14, 24])[0]
