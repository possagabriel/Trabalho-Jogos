"""Caixa cartoon, retratos cacheados e efeitos visuais de cutscene."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

from src.core.constants import ALTURA, LARGURA, NOME_JOGO, VOID_BLACK
from src.runtime.infrastructure.graphics.fonts import fonte_texto, fonte_titulo
from src.runtime.infrastructure.graphics.smooth import desenhar_painel_cartoon

if TYPE_CHECKING:
    from src.runtime.controllers.cutscene import ControladorCutscene


class DialogueBox:
    """Desenha a narrativa sobre a superfície lógica sem alocar retratos por quadro."""

    BOTAO_PULAR = pygame.Rect(1050, 20, 200, 46)
    BOTAO_CONFIRMAR = pygame.Rect(385, 350, 220, 55)
    BOTAO_CANCELAR = pygame.Rect(675, 350, 220, 55)

    def __init__(self, personagens: dict[str, dict[str, str]]) -> None:
        self._fonte = fonte_texto(27)
        self._fonte_nome = fonte_titulo(30)
        self._fonte_titulo = fonte_titulo(56)
        self._fonte_auxiliar = fonte_texto(21)
        self._glifos: dict[tuple[str, tuple[int, int, int]], pygame.Surface] = {}
        self._icones = {chave: valor["retrato"] for chave, valor in personagens.items()}
        self._retratos = {
            icone: self._criar_retrato(icone) for icone in set(self._icones.values())
        }
        self._titulos: dict[tuple[str, tuple[int, int, int]], pygame.Surface] = {}
        self._glitches: dict[str, tuple[str, ...]] = {}
        self._estaticas = [self._criar_estatica(i) for i in range(4)]
        self._sombra = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        self._sombra.fill((*VOID_BLACK, 90))
        self._fade = pygame.Surface((LARGURA, ALTURA))

    def _criar_retrato(self, icone: str) -> pygame.Surface:
        superficie = pygame.Surface((132, 132), pygame.SRCALPHA)
        superficie.fill((20, 24, 42, 245))
        cor = (25, 217, 255) if icone == "nave" else (255, 200, 87)
        pygame.draw.rect(superficie, cor, (4, 4, 124, 124), 5, border_radius=13)
        if icone == "nave":
            pontos = [(66, 21), (100, 105), (66, 84), (32, 105)]
            pygame.draw.polygon(superficie, cor, pontos)
            pygame.draw.polygon(superficie, VOID_BLACK, pontos, 5)
        elif icone == "hexagono":
            pontos = [(66 + 43 * math.cos(i * math.tau / 6),
                       66 + 43 * math.sin(i * math.tau / 6)) for i in range(6)]
            pygame.draw.polygon(superficie, cor, pontos, 7)
        elif icone == "glitch":
            for y in range(25, 113, 17):
                pygame.draw.line(superficie, cor, (24 + y % 13, y), (105, y), 4)
        else:
            pygame.draw.polygon(superficie, cor, [(66, 19), (112, 66),
                                                  (66, 113), (20, 66)], 7)
        return superficie

    def obter_retrato(self, icone: str) -> pygame.Surface:
        """Cria cada variante de retrato uma vez ao trocar de personagem."""
        if icone not in self._retratos:
            self._retratos[icone] = self._criar_retrato(icone)
        return self._retratos[icone]

    def _criar_estatica(self, indice: int) -> pygame.Surface:
        superficie = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        sorteio = random.Random(600 + indice)
        for _ in range(45):
            y = sorteio.randrange(ALTURA)
            x = sorteio.randrange(LARGURA)
            pygame.draw.line(superficie, (180, 220, 255, 32),
                             (x, y), (min(LARGURA, x + sorteio.randrange(30, 320)), y))
        return superficie

    def _texto_corrompido(self, texto: str, indice: int) -> str:
        if texto not in self._glitches:
            variantes = []
            for quadro in range(4):
                sorteio = random.Random(f"{texto}:{quadro}")
                variantes.append("".join(
                    sorteio.choice("#%/01") if letra.isalpha() and sorteio.random() < 0.14
                    else letra for letra in texto
                ))
            self._glitches[texto] = tuple(variantes)
        return self._glitches[texto][indice]

    def _glifo(self, letra: str, cor: tuple[int, int, int]) -> pygame.Surface:
        chave = letra, cor
        if chave not in self._glifos:
            self._glifos[chave] = self._fonte.render(letra, True, cor)
        return self._glifos[chave]

    def _texto(self, tela: pygame.Surface, texto: str, x: int, y: int,
               largura: int, cor: tuple[int, int, int]) -> None:
        inicio = x
        for letra in texto:
            if letra == "\n":
                x, y = inicio, y + 34
                continue
            glifo = self._glifo(letra, cor)
            if x + glifo.get_width() > inicio + largura and letra == " ":
                x, y = inicio, y + 34
                continue
            if x + glifo.get_width() > inicio + largura:
                x, y = inicio, y + 34
            tela.blit(glifo, (x, y))
            x += glifo.get_width()

    def desenhar(self, tela: pygame.Surface, controle: ControladorCutscene,
                cor_dimensao: tuple[int, int, int]) -> None:
        """Desenha o passo corrente, controles e confirmação de pulo."""
        if controle.seletor_debug:
            self.desenhar_seletor(tela, controle, cor_dimensao)
            return
        passo = controle.sequenciador.passo
        if passo is None:
            return
        tela.blit(self._sombra, (0, 0))
        tipo = passo["tipo"]
        if tipo == "glitch":
            indice = int(controle.sequenciador.tempo * 12) % len(self._estaticas)
            tela.blit(self._estaticas[indice], (0, 0))
            texto = passo.get("texto", "")
            if texto:
                self._titulo(tela, self._texto_corrompido(texto, indice), cor_dimensao)
        elif tipo == "titulo":
            self._titulo(tela, passo["texto"].replace("{titulo_jogo}", NOME_JOGO),
                         cor_dimensao)
        elif tipo == "fala":
            painel = pygame.Rect(110, 500, 1060, 184)
            desenhar_painel_cartoon(tela, cor_dimensao, painel)
            personagem = controle.catalogo.personagens[passo["personagem"]]
            icone = controle.retrato_atual or self._icones[passo["personagem"]]
            tela.blit(self.obter_retrato(icone), (132, 525))
            nome = self._fonte_nome.render(personagem["nome"], True, cor_dimensao)
            tela.blit(nome, (288, 519))
            self._texto(tela, controle.sequenciador.texto_visivel,
                        288, 566, 850, (244, 244, 247))
        elif tipo == "fade":
            progresso = min(1.0, controle.sequenciador.tempo / max(0.001, passo["duracao"]))
            alfa = int(255 * (1 - progresso if passo.get("direcao") == "entrada"
                              else progresso))
            self._fade.fill(VOID_BLACK)
            self._fade.set_alpha(alfa)
            tela.blit(self._fade, (0, 0))
        desenhar_painel_cartoon(tela, cor_dimensao, self.BOTAO_PULAR,
                                cor_fundo=(18, 18, 35), glow_raio=4)
        rotulo = self._fonte_auxiliar.render("PULAR CENA", True, (244, 244, 247))
        tela.blit(rotulo, rotulo.get_rect(center=self.BOTAO_PULAR.center))
        if controle.pausado:
            self._titulo(tela, "CENA PAUSADA", cor_dimensao)
        if controle.confirmacao_pulo:
            caixa = pygame.Rect(330, 255, 620, 180)
            desenhar_painel_cartoon(tela, cor_dimensao, caixa)
            texto = self._fonte_nome.render("Pular esta cena?", True, (244, 244, 247))
            tela.blit(texto, texto.get_rect(center=(640, 312)))
            for rect, rotulo in ((self.BOTAO_CONFIRMAR, "PULAR"),
                                 (self.BOTAO_CANCELAR, "CANCELAR")):
                desenhar_painel_cartoon(tela, cor_dimensao, rect, glow_raio=2)
                texto_botao = self._fonte_auxiliar.render(rotulo, True, (244, 244, 247))
                tela.blit(texto_botao, texto_botao.get_rect(center=rect.center))

    def _titulo(self, tela: pygame.Surface, texto: str,
                cor: tuple[int, int, int]) -> None:
        chave = texto, cor
        if chave not in self._titulos:
            self._titulos[chave] = self._fonte_titulo.render(texto, True, cor)
        superficie = self._titulos[chave]
        tela.blit(superficie, superficie.get_rect(center=(LARGURA // 2, ALTURA // 2)))

    def desenhar_seletor(self, tela: pygame.Surface, controle: ControladorCutscene,
                        cor: tuple[int, int, int]) -> None:
        """Mostra IDs de cena para o atalho de depuração F8."""
        tela.blit(self._sombra, (0, 0))
        painel = pygame.Rect(230, 110, 820, 500)
        desenhar_painel_cartoon(tela, cor, painel)
        titulo = self._fonte_nome.render("CENAS // DEBUG", True, cor)
        tela.blit(titulo, (265, 135))
        ids = list(controle.catalogo.cenas)
        inicio = max(0, min(controle.indice_debug, max(0, len(ids) - 11)))
        for linha_indice, indice in enumerate(range(inicio, min(len(ids), inicio + 11))):
            cor_linha = cor if indice == controle.indice_debug else (244, 244, 247)
            linha = self._fonte_auxiliar.render(ids[indice], True, cor_linha)
            tela.blit(linha, (285, 195 + linha_indice * 35))
