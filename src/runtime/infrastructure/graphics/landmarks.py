"""Marcos procedurais de percurso, pré-renderizados e limitados por qualidade."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

import pygame

from src.core.constants import ALTURA, LARGURA
from src.runtime.domain.world.landmarks import (
    EstadoMundoVisual,
    FadeDimensao,
    RitmoVariavel,
    SorteadorMarcos,
    curva_evolucao,
)

QUALIDADE_MARCOS = {
    "BAIXA": {"ativos": 1, "tamanho": 240, "escala": 0.76},
    "MEDIA": {"ativos": 2, "tamanho": 360, "escala": 0.9},
    "ALTA": {"ativos": 3, "tamanho": 480, "escala": 1.0},
}
ALFA_MARCO = 154
ESPESSURA_CONTORNO = 8


def _misturar(
    cor: tuple[int, int, int], cinza: int = 92, mistura: float = 0.38
) -> tuple[int, int, int]:
    """Reduz saturação para preservar o contraste das entidades jogáveis."""
    return tuple(round(canal * (1 - mistura) + cinza * mistura) for canal in cor)


def _contorno(cor: tuple[int, int, int]) -> tuple[int, int, int]:
    """Gera uma tinta escura consistente com o estilo cartoon do jogo."""
    return tuple(max(10, round(canal * 0.32)) for canal in cor)


def _poligono_regular(
    centro: tuple[int, int], raio_x: int, raio_y: int, lados: int, fase: float = -math.pi / 2
) -> list[tuple[int, int]]:
    """Calcula vértices de uma forma para usar durante o pré-render."""
    return [
        (
            round(centro[0] + math.cos(fase + math.tau * i / lados) * raio_x),
            round(centro[1] + math.sin(fase + math.tau * i / lados) * raio_y),
        )
        for i in range(lados)
    ]


def _desenhar_planeta(surface: pygame.Surface, cor: tuple[int, int, int]) -> None:
    largura, altura = surface.get_size()
    centro = (largura // 2, altura // 2)
    raio = min(largura, altura) * 0.31
    caixa = pygame.Rect(0, 0, round(raio * 2), round(raio * 2))
    caixa.center = centro
    pygame.draw.circle(surface, _contorno(cor), centro, round(raio + 5))
    pygame.draw.circle(surface, (*cor, ALFA_MARCO), centro, round(raio))
    pygame.draw.arc(
        surface,
        (220, 225, 240, 170),
        caixa.inflate(-raio, -raio),
        math.pi * 0.12,
        math.pi * 0.78,
        4,
    )


def _desenhar_anel(surface: pygame.Surface, cor: tuple[int, int, int]) -> None:
    largura, altura = surface.get_size()
    centro = (largura // 2, altura // 2)
    caixa = pygame.Rect(0, 0, round(largura * 0.9), round(altura * 0.34))
    caixa.center = centro
    pygame.draw.ellipse(surface, _contorno(cor), caixa.inflate(0, 12), 12)
    pygame.draw.ellipse(surface, (*cor, ALFA_MARCO), caixa, 7)
    pygame.draw.ellipse(surface, (220, 225, 240, 150), caixa.inflate(-22, -10), 2)


def _desenhar_estacao(surface: pygame.Surface, cor: tuple[int, int, int]) -> None:
    largura, altura = surface.get_size()
    centro = (largura // 2, altura // 2)
    raio = min(largura, altura) * 0.19
    corpo = _poligono_regular(centro, round(raio), round(raio), 8)
    pygame.draw.polygon(surface, _contorno(cor), corpo, 0)
    interior = _poligono_regular(centro, round(raio * 0.82), round(raio * 0.82), 8)
    pygame.draw.polygon(surface, (*cor, ALFA_MARCO), interior, 0)
    for direcao in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        ponta = (
            round(centro[0] + direcao[0] * raio * 1.8),
            round(centro[1] + direcao[1] * raio * 1.8),
        )
        pygame.draw.line(surface, _contorno(cor), centro, ponta, 14)
        pygame.draw.circle(surface, (*cor, ALFA_MARCO), ponta, 15)
        pygame.draw.circle(surface, _contorno(cor), ponta, 15, 4)
    pygame.draw.circle(surface, (225, 235, 245, 180), centro, 10)


def _desenhar_destrocos(surface: pygame.Surface, cor: tuple[int, int, int], semente: int) -> None:
    aleatorio = random.Random(semente)
    largura, altura = surface.get_size()
    for _ in range(7):
        centro = (
            aleatorio.randint(largura // 5, largura * 4 // 5),
            aleatorio.randint(altura // 5, altura * 4 // 5),
        )
        raio = aleatorio.randint(max(12, largura // 28), max(18, largura // 12))
        vertices = _poligono_regular(
            centro, raio, round(raio * 0.8), aleatorio.randint(5, 8), aleatorio.random()
        )
        pygame.draw.polygon(surface, _contorno(cor), vertices)
        menores = [
            (round(centro[0] + (x - centro[0]) * 0.8), round(centro[1] + (y - centro[1]) * 0.8))
            for x, y in vertices
        ]
        pygame.draw.polygon(surface, (*cor, ALFA_MARCO), menores)


def _desenhar_cristal(surface: pygame.Surface, cor: tuple[int, int, int]) -> None:
    largura, altura = surface.get_size()
    centro = (largura // 2, altura // 2)
    vertices = _poligono_regular(centro, round(largura * 0.28), round(altura * 0.43), 6)
    pygame.draw.polygon(surface, _contorno(cor), vertices)
    internos = [
        (round(centro[0] + (x - centro[0]) * 0.82), round(centro[1] + (y - centro[1]) * 0.82))
        for x, y in vertices
    ]
    pygame.draw.polygon(surface, (*cor, ALFA_MARCO), internos)
    pygame.draw.line(surface, (235, 245, 245, 180), vertices[0], centro, 4)


def _desenhar_nebulosa(surface: pygame.Surface, cor: tuple[int, int, int]) -> None:
    largura, altura = surface.get_size()
    centro = (largura // 2, altura // 2)
    for indice, escala in enumerate((0.32, 0.25, 0.18)):
        ponto = (
            centro[0] + (indice - 1) * round(largura * 0.19),
            centro[1] + round((indice % 2) * altura * 0.08),
        )
        raio = round(largura * escala)
        pygame.draw.circle(surface, _contorno(cor), ponto, raio + 5)
        pygame.draw.circle(surface, (*cor, 92), ponto, raio)


def _desenhar_portal(surface: pygame.Surface, cor: tuple[int, int, int]) -> None:
    largura, altura = surface.get_size()
    centro = (largura // 2, altura // 2)
    caixa = pygame.Rect(0, 0, round(largura * 0.38), round(altura * 0.72))
    caixa.center = centro
    pygame.draw.ellipse(surface, _contorno(cor), caixa.inflate(24, 24), 0)
    pygame.draw.ellipse(surface, (*cor, ALFA_MARCO), caixa, 11)
    pygame.draw.ellipse(surface, (235, 240, 255, 175), caixa.inflate(-24, -24), 4)


_DESENHADORES = {
    "planeta": _desenhar_planeta,
    "anel": _desenhar_anel,
    "estacao": _desenhar_estacao,
    "destrocos": _desenhar_destrocos,
    "cristal": _desenhar_cristal,
    "nebulosa": _desenhar_nebulosa,
    "portal": _desenhar_portal,
}


@dataclass(slots=True)
class _MarcoAtivo:
    """Sprite e posição reaproveitados pelo pool do cenário."""

    identificador: str
    surface: pygame.Surface
    x: float = 0.0
    y: float = 0.0
    velocidade: float = 0.0
    opacidade: float = 1.0

    def bounds(self) -> pygame.Rect:
        return self.surface.get_rect(center=(round(self.x), round(self.y)))


class CamadaMarcos:
    """Agenda, move e desenha marcos com surfaces pré-renderizadas."""

    def __init__(self, cenario: Any, qualidade: str, config: Any, semente: int) -> None:
        self.cenario = cenario
        self.qualidade = qualidade if qualidade in QUALIDADE_MARCOS else "MEDIA"
        self.config = config
        self.semente = int(semente)
        self._aleatorio = random.Random(self.semente ^ (cenario.id * 9_973))
        self._limite_tamanho = max(
            64,
            min(
                int(_ler(config, "avanco_marco_tamanho_max", 420)),
                QUALIDADE_MARCOS[self.qualidade]["tamanho"],
            ),
        )
        self._max_ativos = QUALIDADE_MARCOS[self.qualidade]["ativos"]
        self._cache: dict[str, pygame.Surface] = {}
        self._ativos: list[_MarcoAtivo] = []
        self._pool: list[_MarcoAtivo] = []
        self._specs = {spec["id"]: spec for spec in cenario.marcos}
        self._habilitado = bool(_ler(config, "avanco_marcos", True))
        self._ritmo_habilitado = bool(_ler(config, "avanco_ritmo_variavel", True))
        if self._habilitado:
            for identificador in self._specs:
                self._sprite(identificador)
        self._sorteador = SorteadorMarcos(
            tuple(self._specs),
            self.semente ^ cenario.id,
            cenario.intervalo_marcos[0],
            cenario.intervalo_marcos[1],
        )
        self._proximo = self._sorteador.proximo()
        self._relogio = self._proximo.intervalo
        self._fade = FadeDimensao()
        self._fade_direcao = 0
        self._ritmo = RitmoVariavel(
            self.semente ^ 0x5A17,
            _ler(config, "avanco_ritmo_intervalo", 8.0),
            _ler(config, "avanco_ritmo_variacao", 0.08),
            _ler(config, "avanco_ritmo_passagem", 2.5),
        )
        self._factor_evolucao = 0.0
        self._destino: Any = None

    @property
    def marco_atual(self) -> str:
        """Lista os identificadores dos marcos atualmente visíveis."""
        return ", ".join(marco.identificador for marco in self._ativos) or "--"

    @property
    def proximos_marcos(self) -> str:
        """Retorna o próximo sorteio e o tempo restante para o F3."""
        return f"{self._proximo.marco} em {max(0.0, self._relogio):.1f}s"

    @property
    def memoria_cache(self) -> int:
        """Bytes ocupados pelos sprites já pré-renderizados."""
        return sum(surface.get_pitch() * surface.get_height() for surface in self._cache.values())

    @property
    def fator_evolucao(self) -> float:
        """Fator suavizado de evolução da dimensão."""
        return self._factor_evolucao

    @property
    def ritmo_factor(self) -> float:
        """Multiplicador visual de velocidade atual."""
        return self._ritmo.fator

    @property
    def em_passagem(self) -> bool:
        """Indica se o trecho visual acelerado está ativo."""
        return self._ritmo.em_passagem

    @property
    def opacidade_dimensao(self) -> float:
        """Fator de fade dos marcos no cenário atual."""
        if self._fade.ativo:
            return self._fade.antiga if self._fade_direcao < 0 else self._fade.nova
        return 0.0 if self._fade_direcao < 0 else 1.0

    def iniciar_saida_dimensao(self) -> None:
        """Faz os marcos da dimensão antiga desaparecerem gradualmente."""
        self._fade.iniciar()
        self._fade_direcao = -1

    def iniciar_entrada_dimensao(self) -> None:
        """Faz os marcos da dimensão nova surgirem gradualmente."""
        self._fade.iniciar()
        self._fade_direcao = 1

    def iniciar_destino(self, destino: Any) -> None:
        """Associa o destino da sequência de boss a esta dimensão."""
        self._destino = destino

    def _sprite(self, identificador: str) -> pygame.Surface:
        if identificador in self._cache:
            return self._cache[identificador]
        spec = self._specs[identificador]
        escala = QUALIDADE_MARCOS[self.qualidade]["escala"]
        diametro = max(64, min(round(int(spec["tamanho"]) * escala), self._limite_tamanho))
        surface = pygame.Surface((diametro, diametro), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        cor = _misturar(tuple(spec["cor"]))
        desenhador = _DESENHADORES[spec["forma"]]
        if spec["forma"] == "destrocos":
            hash_fixo = sum((indice + 1) * ord(char) for indice, char in enumerate(identificador))
            desenhador(surface, cor, self.semente ^ hash_fixo)
        else:
            desenhador(surface, cor)
        surface.set_alpha(ALFA_MARCO)
        self._cache[identificador] = surface
        return surface

    def _spawn(self, velocidade_base: float) -> None:
        if len(self._ativos) >= self._max_ativos:
            return
        identificador = self._proximo.marco
        spec = self._specs[identificador]
        sprite_base = self._sprite(identificador)
        sprite = sprite_base.copy()
        dx, dy = self.cenario.direcao_avanco
        modulo = math.hypot(dx, dy) or 1.0
        dx, dy = dx / modulo, dy / modulo
        px, py = -dy, dx
        meio = (LARGURA / 2, ALTURA / 2)
        raio = max(sprite.get_size()) / 2
        ext_perp = abs(px) * LARGURA / 2 + abs(py) * ALTURA / 2
        ext_dir = abs(dx) * LARGURA / 2 + abs(dy) * ALTURA / 2 + raio
        escolhido: tuple[float, float] | None = None
        for _ in range(12):
            offset = self._aleatorio.uniform(-ext_perp, ext_perp)
            x, y = meio[0] + px * offset - dx * ext_dir, meio[1] + py * offset - dy * ext_dir
            sprite_rect = sprite.get_rect(center=(round(x), round(y)))
            if all(not sprite_rect.colliderect(marco.bounds()) for marco in self._ativos):
                escolhido = x, y
                break
        self._proximo = self._sorteador.proximo()
        self._relogio = self._proximo.intervalo
        if escolhido is None:
            if len(self._pool) < self._max_ativos:
                self._pool.append(_MarcoAtivo(identificador, sprite))
            return
        if self._pool:
            marco = self._pool.pop()
            marco.identificador, marco.surface = identificador, sprite
            marco.x, marco.y = escolhido
        else:
            marco = _MarcoAtivo(identificador, sprite, *escolhido)
        marco.velocidade = velocidade_base * float(spec["velocidade"])
        marco.opacidade = 1.0
        marco.surface.set_alpha(ALFA_MARCO)
        self._ativos.append(marco)

    def atualizar(
        self,
        velocidade: float,
        dt: float,
        estado_avanco: EstadoMundoVisual,
        progresso: float,
        estado_jogo: str,
    ) -> None:
        """Avança sprites e curvas visuais somente durante a simulação ativa."""
        if estado_jogo.upper() in ("PAUSA", "CUTSCENE", "MELHORIA", "GAME_OVER"):
            return
        dt = max(0.0, float(dt))
        curva = curva_evolucao(progresso, self.cenario.curva_evolucao)
        self._factor_evolucao = curva
        if self._fade.ativo:
            self._fade.atualizar(dt, estado_avanco, estado_jogo)
        fade = self.opacidade_dimensao
        self._ritmo.atualizar(dt)
        if self._habilitado:
            self._relogio -= dt
            if self._relogio <= 0:
                self._spawn(velocidade)
        dx, dy = self.cenario.direcao_avanco
        modulo = math.hypot(dx, dy) or 1.0
        fator_ritmo = self._ritmo.fator if self._ritmo_habilitado else 1.0
        for marco in self._ativos[:]:
            distancia = marco.velocidade * fator_ritmo * dt
            marco.x += dx / modulo * distancia
            marco.y += dy / modulo * distancia
            marco.opacidade = fade
            marco.surface.set_alpha(round(ALFA_MARCO * fade))
            if not marco.bounds().colliderect(
                pygame.Rect(
                    -self._limite_tamanho,
                    -self._limite_tamanho,
                    LARGURA + self._limite_tamanho * 2,
                    ALTURA + self._limite_tamanho * 2,
                )
            ):
                self._ativos.remove(marco)
                if len(self._pool) < self._max_ativos:
                    self._pool.append(marco)
        if self._destino is not None:
            self._destino.atualizar(dt, estado_avanco, estado_jogo)

    def desenhar(self, tela: pygame.Surface) -> None:
        """Desenha os marcos ao fundo, com cor e opacidade contidas."""
        if not bool(_ler(self.config, "avanco_marcos", True)):
            return
        for marco in self._ativos:
            tela.blit(marco.surface, marco.bounds())
        if self._destino is not None:
            self._desenhar_destino(
                tela, self._destino, self.cenario.cor_evolucao,
                self.opacidade_dimensao,
            )

    @staticmethod
    def _desenhar_destino(
        tela: pygame.Surface, destino: Any, cor: tuple[int, int, int], fade: float,
    ) -> None:
        """Desenha o portal do boss com primitivas sem alocar surfaces por frame."""
        visibilidade = destino.opacidade * fade
        if destino.estado.value == "INATIVO" or visibilidade <= 0:
            return
        escala = destino.escala
        centro_x = LARGURA // 2
        centro_y = round(ALTURA * (0.28 + (1 - destino.opacidade) * 0.48))
        raio_x = round(110 * escala)
        raio_y = round(180 * escala)
        intensidade = 0.3 + visibilidade * 0.3
        tinta = tuple(round(canal * intensidade) for canal in _misturar(cor, 75, 0.5))
        caixa = pygame.Rect(centro_x - raio_x, centro_y - raio_y, raio_x * 2, raio_y * 2)
        pygame.draw.ellipse(tela, _contorno(tinta), caixa.inflate(12, 12), 8)
        pygame.draw.ellipse(tela, tinta, caixa, 5)
        brilho = tuple(round(canal * intensidade) for canal in (205, 215, 235))
        pygame.draw.ellipse(tela, brilho, caixa.inflate(-18, -24), 2)


def _ler(config: Any, chave: str, padrao: Any) -> Any:
    """Lê valores de configurações antigas sem depender de um tipo concreto."""
    try:
        return config[chave]
    except (KeyError, TypeError):
        return padrao
