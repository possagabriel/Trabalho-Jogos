"""Camadas 2D pré-renderizadas para a rolagem dos cenários."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from src.core.constants import ALTURA, LARGURA
from src.infrastructure.graphics.comic_render import fundo_comic
from src.infrastructure.graphics.comic_theme import opcoes_atuais
from src.runtime.domain.world.landmarks import (
    EstadoMundoVisual,
    TransicaoDestino,
    curva_evolucao,
)
from src.runtime.domain.world.scroll import (
    EstadoAvanco,
    deslocamento_camada,
    faixas_repetidas,
)
from src.runtime.infrastructure.graphics.landmarks import CamadaMarcos

QUALIDADE_CAMADAS = {"BAIXA": (3, 28), "MEDIA": (4, 52), "ALTA": (5, 84)}
LIMITE_LINHAS_DIMENSAO = {1: 52, 2: 60, 3: 44, 4: 48, 5: 70, 6: 56}
FATORES = (0.08, 0.18, 0.36, 0.68, 1.0)
ESTILOS = {
    1: ("estrela", "nebulosa", "estrela", "detrito"),
    2: ("nebulosa", "brasa", "estrela", "detrito"),
    3: ("nebulosa", "bolha", "estrela", "bolha"),
    4: ("nebulosa", "cristal", "estrela", "cristal"),
    5: ("estrela", "fenda", "estrela", "detrito"),
    6: ("nebulosa", "grade", "estrela", "cristal"),
}


def _ler(config: object, chave: str, padrao: object) -> object:
    try:
        return config[chave]  # type: ignore[index]
    except (KeyError, TypeError):
        return padrao


def _espelhar(base: pygame.Surface) -> pygame.Surface:
    """Cria uma repetição contínua em ambos os eixos a partir da arte existente."""
    largura, altura = base.get_size()
    tile = pygame.Surface((largura * 2, altura * 2))
    tile.blit(base, (0, 0))
    tile.blit(pygame.transform.flip(base, True, False), (largura, 0))
    tile.blit(pygame.transform.flip(base, False, True), (0, altura))
    tile.blit(pygame.transform.flip(base, True, True), (largura, altura))
    return tile


def _forma(tela: pygame.Surface, estilo: str, cor: tuple[int, int, int],
           x: int, y: int, raio: int) -> None:
    """Desenha um detalhe pequeno somente durante a preparação da camada."""
    if estilo in ("estrela", "bolha", "brasa"):
        pygame.draw.circle(tela, cor, (x, y), raio, 1 if estilo == "bolha" else 0)
    elif estilo == "cristal":
        pygame.draw.polygon(tela, cor, ((x, y - raio * 2), (x + raio, y),
                                        (x, y + raio * 2), (x - raio, y)))
    elif estilo == "grade":
        pygame.draw.line(tela, cor, (x - raio * 3, y), (x + raio * 3, y), 1)
    elif estilo == "fenda":
        pygame.draw.line(tela, cor, (x - raio, y - raio), (x + raio, y + raio), 2)
    elif estilo == "nebulosa":
        pygame.draw.circle(tela, cor, (x, y), raio * 4, 1)
    else:
        pygame.draw.polygon(tela, cor, ((x, y - raio), (x + raio, y),
                                        (x, y + raio), (x - raio, y)))


def _preparar_detalhes(cenario_id: int, indice: int, estilo: str,
                       cor: tuple[int, int, int], quantidade: int) -> pygame.Surface:
    """Preenche um tile com detalhes de brilho e tamanho proporcionais à camada."""
    tile = pygame.Surface((LARGURA, ALTURA))
    tile.fill((0, 0, 0))
    tile.set_colorkey((0, 0, 0))
    aleatorio = random.Random(2_021 + cenario_id * 100 + indice)
    brilho = (0.35, 0.52, 0.7, 0.85)[min(indice, 3)]
    cor_cam = tuple(max(1, min(255, int(c * brilho))) for c in cor)
    raio = max(1, indice + (1 if estilo in ("detrito", "cristal") else 0))
    margem = raio * (4 if estilo in ("nebulosa", "grade") else 2)
    for _ in range(quantidade):
        x = aleatorio.randrange(LARGURA)
        y = aleatorio.randrange(ALTURA)
        for sx in (-LARGURA, 0, LARGURA):
            for sy in (-ALTURA, 0, ALTURA):
                if -margem <= x + sx < LARGURA + margem and \
                        -margem <= y + sy < ALTURA + margem:
                    _forma(tile, estilo, cor_cam, x + sx, y + sy, raio)
    return tile


class ScrollingLayer:
    """Conserva um tile e o desloca por recortes sem redesenhar seus detalhes."""

    def __init__(self, tile: pygame.Surface, fator: float) -> None:
        self.tile = tile
        self.fator = fator
        self.x = 0.0
        self.y = 0.0

    def atualizar(self, velocidade: float, dt: float,
                  direcao: tuple[float, float]) -> None:
        """Acumula o deslocamento periódico da camada."""
        dx, dy = deslocamento_camada(direcao, velocidade, self.fator, dt)
        largura, altura = self.tile.get_size()
        self.x = (self.x + dx) % largura
        self.y = (self.y + dy) % altura

    def desenhar(self, tela: pygame.Surface) -> None:
        """Cobre a tela com recortes periódicos do mesmo tile."""
        largura, altura = self.tile.get_size()
        for origem_x, destino_x, faixa_x in faixas_repetidas(largura, self.x):
            dx = min(faixa_x, tela.get_width() - destino_x)
            if dx <= 0:
                continue
            for origem_y, destino_y, faixa_y in faixas_repetidas(altura, self.y):
                dy = min(faixa_y, tela.get_height() - destino_y)
                if dy > 0:
                    tela.blit(self.tile, (destino_x, destino_y),
                              pygame.Rect(origem_x, origem_y, dx, dy))


@dataclass(slots=True)
class _Linha:
    x: float
    y: float
    classe: int


class SpeedLines:
    """Pool fixo de rastros com sprites pequenos pré-renderizados."""

    def __init__(self, quantidade: int, cor: tuple[int, int, int],
                 direcao: tuple[float, float], semente: int,
                 paletas: tuple[tuple[int, int, int], ...] | None = None) -> None:
        aleatorio = random.Random(semente)
        self.linhas = [_Linha(aleatorio.randrange(LARGURA),
                              aleatorio.randrange(ALTURA), i % 3)
                       for i in range(quantidade)]
        self.ativas = 0
        self._nivel = 0
        self._paleta_nivel = 0
        modulo = math.hypot(*direcao) or 1.0
        dx, dy = direcao[0] / modulo, direcao[1] / modulo
        cores = paletas or (cor,) * 5
        self._sprites: dict[tuple[int, int, int], pygame.Surface] = {}
        for classe in range(3):
            for nivel in range(1, 5):
                comprimento = (3 + classe * 3) * nivel
                largura = max(5, math.ceil(abs(dx * comprimento)) + 5)
                altura = max(5, math.ceil(abs(dy * comprimento)) + 5)
                sprite = pygame.Surface((largura, altura))
                sprite.fill((0, 0, 0))
                sprite.set_colorkey((0, 0, 0))
                brilho_linha = 0.25 + nivel * 0.15 + classe * 0.08
                inicio = (round(2 + max(0, dx * comprimento)),
                          round(2 + max(0, dy * comprimento)))
                fim = (round(inicio[0] - dx * comprimento),
                       round(inicio[1] - dy * comprimento))
                for indice_paleta, cor_paleta in enumerate(cores):
                    variante = sprite.copy()
                    tom = tuple(max(1, min(255, int(c * brilho_linha)))
                                for c in cor_paleta)
                    pygame.draw.line(variante, tom, inicio, fim, 1 + classe // 2)
                    self._sprites[classe, nivel, indice_paleta] = variante

    def atualizar(self, velocidade: float, velocidade_base: float, dt: float,
                  direcao: tuple[float, float], intensidade: float,
                  evolucao: float = 0.0) -> None:
        """Move apenas as linhas ativas e reutiliza os objetos ao atravessar bordas."""
        razao = velocidade / velocidade_base if velocidade_base > 0 else 0.0
        fracao = max(0.0, min(1.0, razao * intensidade))
        self.ativas = min(len(self.linhas), int(len(self.linhas) * fracao))
        self._nivel = min(4, max(1, math.ceil(razao * 3))) if self.ativas else 0
        self._paleta_nivel = min(4, max(0, round(evolucao * 4)))
        dx, dy = deslocamento_camada(direcao, velocidade, 1.0, dt)
        for indice in range(self.ativas):
            linha = self.linhas[indice]
            linha.x = (linha.x + dx) % LARGURA
            linha.y = (linha.y + dy) % ALTURA

    def desenhar(self, tela: pygame.Surface) -> None:
        """Compõe somente as linhas ativas sobre o fundo."""
        for indice in range(self.ativas):
            linha = self.linhas[indice]
            sprite = self._sprites[linha.classe, self._nivel, self._paleta_nivel]
            tela.blit(sprite, (round(linha.x), round(linha.y)))


class ParallaxBackground:
    """Composição de 3 a 5 camadas por dimensão, incluindo a arte de base."""

    def __init__(self, cenario: object, qualidade: str,
                 direcao: tuple[float, float], linhas_ativas: bool = True,
                 camadas_ativas: bool = True) -> None:
        self.cenario = cenario
        self.qualidade = qualidade if qualidade in QUALIDADE_CAMADAS else "MEDIA"
        self.direcao = direcao
        self.linhas_ativas = linhas_ativas
        self.camadas_ativas = camadas_ativas
        numero, limite = QUALIDADE_CAMADAS[self.qualidade]
        self._numero = numero if camadas_ativas else 1
        self._limite = min(limite, LIMITE_LINHAS_DIMENSAO[cenario.id])
        self._bases: dict[tuple[object, ...], ScrollingLayer] = {}
        self._detalhes: list[ScrollingLayer] = []
        self._linhas: SpeedLines | None = None
        self._pronto = False
        self._config: object = {}
        self._semente = 0
        self._marcos: CamadaMarcos | None = None
        self._destino: TransicaoDestino | None = None
        self._progresso = 0.0

    def configurar_percurso(self, config: object, semente: int) -> None:
        """Prepara as regras do percurso com opções antigas ou atuais."""
        self._config = config
        self._semente = int(semente)
        self._marcos = CamadaMarcos(self.cenario, self.qualidade, config, self._semente)

    @property
    def marco_atual(self) -> str:
        """Identificadores dos marcos que atravessam a tela."""
        return self._marcos.marco_atual if self._marcos else "--"

    @property
    def proximos_marcos(self) -> str:
        """Próximos marcos sorteados e suas contagens regressivas."""
        return self._marcos.proximos_marcos if self._marcos else "--"

    @property
    def fator_evolucao(self) -> float:
        """Fator suavizado da curva de progresso do cenário."""
        return self._marcos.fator_evolucao if self._marcos else 0.0

    @property
    def semente(self) -> int:
        """Semente desta partida, usada no sorteio visual reproduzível."""
        return self._semente

    @property
    def memoria_marcos(self) -> int:
        """Memória dos sprites de marcos que já foram pré-renderizados."""
        return self._marcos.memoria_cache if self._marcos else 0

    def iniciar_saida_dimensao(self) -> None:
        """Inicia o fade dos marcos antes de revelar a dimensão seguinte."""
        if self._marcos:
            self._marcos.iniciar_saida_dimensao()

    def iniciar_entrada_dimensao(self) -> None:
        """Inicia o fade dos marcos ao revelar esta dimensão."""
        if self._marcos:
            self._marcos.iniciar_entrada_dimensao()

    def destino_boss_iniciado(self, destino: TransicaoDestino) -> None:
        """Anexa o portal de chegada do boss ao cenário atual."""
        self._destino = destino
        if self._marcos:
            self._marcos.iniciar_destino(destino)

    @property
    def numero_camadas(self) -> int:
        """Quantidade de camadas efetivamente preparadas."""
        return self._numero

    @property
    def particulas_ativas(self) -> int:
        """Quantidade de linhas móveis atualmente visíveis."""
        return self._linhas.ativas if self._linhas is not None else 0

    def _preparar(self) -> None:
        if self._pronto:
            return
        self._pronto = True
        cenario = self.cenario
        estilos = ESTILOS[cenario.id]
        for indice in range(self._numero - 1):
            estilo = estilos[indice]
            cor = (cenario.cores_principais[indice % len(cenario.cores_principais)]
                   if estilo in ("detrito", "grade", "fenda") else cenario.cor_estrela)
            tile = _preparar_detalhes(cenario.id, indice, estilo, cor,
                                     40 + indice * 22)
            self._detalhes.append(ScrollingLayer(tile, FATORES[indice + 1]))
        brilho_inicio, brilho_fim = cenario.evolucao_brilho
        paletas = tuple(
            tuple(
                round((base * (1 - progresso) + alvo * progresso)
                      * (brilho_inicio + (brilho_fim - brilho_inicio) * progresso))
                for base, alvo in zip(cenario.cor_estrela, cenario.cor_evolucao)
            )
            for progresso in (0.0, 0.25, 0.5, 0.75, 1.0)
        )
        self._linhas = SpeedLines(
            self._limite, cenario.cor_estrela, self.direcao,
            8_100 + cenario.id, paletas,
        )

    def _base(self, cor_fundo_cutscene: tuple[int, int, int] | None = None) -> ScrollingLayer:
        opcoes = opcoes_atuais()
        chave = (opcoes.ativo, opcoes.qualidade, opcoes.papel, opcoes.halftone,
                 cor_fundo_cutscene)
        if chave not in self._bases:
            if opcoes.ativo:
                fonte = fundo_comic((LARGURA, ALTURA), self.cenario.id,
                                    opcoes.qualidade, opcoes.papel, opcoes.halftone)
            else:
                fonte = self.cenario.fundo_estatico
                if cor_fundo_cutscene is not None:
                    from src.runtime.presentation.cutscene_raster import (
                        filtrar_fundo_cutscene,
                    )

                    fonte = filtrar_fundo_cutscene(fonte, cor_fundo_cutscene)
            camada = ScrollingLayer(_espelhar(fonte), FATORES[0])
            if self._bases:
                anterior = next(iter(self._bases.values()))
                camada.x, camada.y = anterior.x, anterior.y
            self._bases[chave] = camada
            if len(self._bases) > 2:
                self._bases.pop(next(iter(self._bases)))
        return self._bases[chave]

    def atualizar(self, velocidade: float, velocidade_base: float, dt: float,
                  estado: EstadoAvanco, desvio_parado: float,
                  intensidade: float, progresso: float = 0.0,
                  estado_jogo: str = "JOGANDO") -> None:
        """Avança as camadas com velocidade residual apenas nas distantes."""
        self._preparar()
        self._progresso = min(1.0, max(0.0, progresso))
        if estado is None:
            estado = EstadoAvanco.AVANCANDO
        fase = EstadoMundoVisual(estado.value)
        evolucao_ativa = bool(_ler(self._config, "avanco_evolucao_paleta", True))
        ritmo_ativo = bool(_ler(self._config, "avanco_ritmo_variavel", True))
        if self._marcos:
            self._marcos.atualizar(
                velocidade_base, dt, fase, self._progresso, estado_jogo,
            )
        factor = (self._marcos.ritmo_factor if self._marcos and ritmo_ativo else 1.0)
        evolucao = curva_evolucao(self._progresso, self.cenario.curva_evolucao)
        densidade = (self.cenario.evolucao_densidade[0]
                     + (self.cenario.evolucao_densidade[1]
                        - self.cenario.evolucao_densidade[0]) * evolucao
                     if evolucao_ativa else 1.0)
        passagem = self._marcos.em_passagem if self._marcos and ritmo_ativo else False
        velocidade_visual = velocidade * factor
        residual = (velocidade_base * max(0.0, desvio_parado)
                    if estado is EstadoAvanco.PARADO else 0.0)
        distante = max(velocidade_visual, residual)
        for base in self._bases.values():
            base.atualizar(distante, dt, self.direcao)
        for indice, camada in enumerate(self._detalhes):
            vel = distante if indice == 0 else velocidade_visual
            camada.atualizar(vel, dt, self.direcao)
        if self._linhas is not None:
            self._linhas.atualizar(
                velocidade_visual if self.linhas_ativas else 0.0,
                velocidade_base, dt, self.direcao,
                intensidade * densidade * (1.22 if passagem else 1.0),
                evolucao if evolucao_ativa else 0.0,
            )

    def desenhar(self, tela: pygame.Surface,
                 cor_fundo_cutscene: tuple[int, int, int] | None = None) -> None:
        """Desenha a arte, os planos distantes e os rastros em ordem."""
        self._preparar()
        self._base(cor_fundo_cutscene).desenhar(tela)
        for camada in self._detalhes:
            camada.desenhar(tela)
        if self._marcos:
            self._marcos.desenhar(tela)
        if self.linhas_ativas and self._linhas is not None:
            self._linhas.desenhar(tela)
