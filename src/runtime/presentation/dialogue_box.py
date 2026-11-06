"""Caixa cartoon, retratos cacheados e efeitos visuais de cutscene."""

from __future__ import annotations

import math
import random
from functools import lru_cache
from typing import TYPE_CHECKING

import pygame

from src.core.constants import ALTURA, LARGURA, NOME_JOGO, VOID_BLACK
from src.infrastructure.graphics.comic_theme import CIANO, LARANJA, TINTA, opcoes_atuais
from src.runtime.infrastructure.assets import carregar_imagem
from src.runtime.infrastructure.graphics.fonts import fonte_texto, fonte_titulo
from src.runtime.infrastructure.graphics.menu_panels import (
    ACENTO_ORIGINAL,
    FUNDO_ORIGINAL,
    TEXTO_ATIVO_ORIGINAL,
    TEXTO_ORIGINAL,
    linhas_painel,
    painel_menu,
    texto_painel,
)
from src.runtime.infrastructure.graphics.smooth import desenhar_painel, desenhar_painel_cartoon

if TYPE_CHECKING:
    from src.runtime.controllers.cutscene import ControladorCutscene


def _painel(tela, cor, rect, **opcoes):
    """Usa o acabamento correspondente ao estilo visual selecionado."""
    desenhar = desenhar_painel_cartoon if opcoes_atuais().ativo else desenhar_painel
    if not opcoes_atuais().ativo:
        opcoes.pop("espessura_borda", None)
    desenhar(tela, cor, rect, **opcoes)


@lru_cache(maxsize=24)
def _arte_personagem(caminho: str) -> pygame.Surface | None:
    imagem = carregar_imagem(caminho)
    if imagem is None:
        return None
    return pygame.transform.smoothscale(imagem, (300, 300))


@lru_cache(maxsize=12)
def _onda_transmissao(quadro: int) -> pygame.Surface:
    arte = pygame.Surface((180, 26), pygame.SRCALPHA)
    for indice in range(24):
        altura = round(4 + 16 * abs(math.sin(indice * .7 + quadro * math.tau / 12)))
        pygame.draw.line(arte, CIANO, (indice * 7 + 5, 13 - altura // 2),
                         (indice * 7 + 5, 13 + altura // 2), 2)
    return arte


class DialogueBox:
    """Desenha a narrativa sobre a superfície lógica sem alocar retratos por quadro."""

    BOTAO_PULAR = pygame.Rect(1050, 20, 200, 46)
    BOTAO_CONFIRMAR = pygame.Rect(385, 350, 220, 55)
    BOTAO_CANCELAR = pygame.Rect(675, 350, 220, 55)
    BOTAO_HISTORICO = pygame.Rect(round(LARGURA * .655), round(ALTURA * .028),
                                round(LARGURA * .15), round(ALTURA * .064))
    AREA_FALA = pygame.Rect(round(LARGURA * .05), round(ALTURA * .60),
                           round(LARGURA * .90), round(ALTURA * .34))
    BOTAO_AVANCAR = pygame.Rect(round(LARGURA * .785), round(ALTURA * .888),
                               round(LARGURA * .15), round(ALTURA * .040))

    def __init__(self, personagens: dict[str, dict[str, str]]) -> None:
        self._fonte = fonte_texto(27)
        self._fonte_nome = fonte_titulo(30)
        self._fonte_titulo = fonte_titulo(56)
        self._fonte_auxiliar = fonte_texto(21)
        self._glifos: dict[tuple[str, tuple[int, int, int]], pygame.Surface] = {}
        self._icones = {chave: valor["retrato"] for chave, valor in personagens.items()}
        self._caminhos = {valor["retrato"]: valor["imagem"]
                          for valor in personagens.values() if "imagem" in valor}
        self._interlocutor = None
        self._cena_palco = None
        self._retratos = {
            icone: self._criar_retrato(icone) for icone in set(self._icones.values())
        }
        self._retratos_palco = {
            icone: pygame.transform.smoothscale(arte, (300, 300))
            for icone, arte in self._retratos.items()
        }
        self._retratos_apagados = {}
        for icone, arte in self._retratos_palco.items():
            copia = arte.copy()
            copia.set_alpha(100)
            self._retratos_apagados[icone] = copia
        for quadro in range(12):
            _onda_transmissao(quadro)
        self._titulos: dict[
            tuple[str, tuple[int, int, int], bool], pygame.Surface
        ] = {}
        self._texto_contornado: dict[
            tuple[int, str, tuple[int, int, int], int], pygame.Surface
        ] = {}
        self._glitches: dict[str, tuple[str, ...]] = {}
        self._estaticas = [self._criar_estatica(i) for i in range(4)]
        self._sombra = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        self._sombra.fill((*VOID_BLACK, 90))
        self._fade = pygame.Surface((LARGURA, ALTURA))

    def _criar_retrato(self, icone: str) -> pygame.Surface:
        if icone in self._caminhos:
            arte = _arte_personagem(self._caminhos[icone])
            if arte is not None:
                return arte
        superficie = pygame.Surface((132, 132), pygame.SRCALPHA)
        superficie.fill((32, 37, 47, 255))
        cor = CIANO if icone == "nave" else LARANJA
        pygame.draw.rect(superficie, TINTA, (3, 3, 126, 126), 5, border_radius=13)
        pygame.draw.rect(superficie, cor, (7, 7, 118, 118), 3, border_radius=10)
        if icone == "nave":
            pontos = [(66, 21), (100, 105), (66, 84), (32, 105)]
            pygame.draw.polygon(superficie, cor, pontos)
            pygame.draw.polygon(superficie, TINTA, pontos, 5)
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
            self._glifos[chave] = self._texto_outline(self._fonte, letra, cor, 3)
        return self._glifos[chave]

    def _texto_outline(self, fonte: pygame.font.Font, texto: str,
                       cor: tuple[int, int, int], espessura: int) -> pygame.Surface:
        chave = id(fonte), texto, cor, espessura
        if chave not in self._texto_contornado:
            base = fonte.render(texto, True, cor)
            contorno = fonte.render(texto, True, TINTA)
            resultado = pygame.Surface(
                (base.get_width() + espessura * 2, base.get_height() + espessura * 2),
                pygame.SRCALPHA,
            )
            for dx, dy in ((0, 0), (espessura * 2, 0), (0, espessura * 2),
                           (espessura * 2, espessura * 2), (espessura, 0),
                           (0, espessura), (espessura * 2, espessura),
                           (espessura, espessura * 2)):
                resultado.blit(contorno, (dx, dy))
            resultado.blit(base, (espessura, espessura))
            if len(self._texto_contornado) >= 512:
                self._texto_contornado.pop(next(iter(self._texto_contornado)))
            self._texto_contornado[chave] = resultado
        return self._texto_contornado[chave]

    @staticmethod
    def _cor_acento(cor: tuple[int, int, int]) -> tuple[int, int, int]:
        """Reserva o magenta para os quadros de glitch e alerta."""
        vermelho, verde, azul = cor
        if vermelho > verde * 1.45 and azul > verde * 1.45:
            return LARANJA if vermelho >= azul else CIANO
        return cor

    def _texto(self, tela: pygame.Surface, texto: str, x: int, y: int,
               largura: int, cor: tuple[int, int, int], completo: str | None = None) -> None:
        # O tamanho é escolhido pelo texto completo, evitando saltos durante a revelação.
        completo = completo if completo is not None else texto
        altura = max(1, round(ALTURA * .86) - y)
        for tamanho in range(27, 13, -1):
            fonte = fonte_texto(tamanho)
            linhas = linhas_painel(fonte, completo, largura - 8)
            passo = fonte.get_linesize() + 3
            if len(linhas) * passo <= altura:
                break
        cursor = 0
        for indice, linha in enumerate(linhas):
            inicio = completo.find(linha, cursor)
            cursor = inicio + len(linha)
            visiveis = max(0, len(texto) - inicio)
            trecho = linha[:visiveis]
            if trecho:
                arte = self._texto_outline(fonte, trecho, cor, 2)
                tela.blit(arte, (x, y + indice * passo))

    def _rotulo(self, tela: pygame.Surface, texto: str, rect: pygame.Rect,
                *, tamanho: int = 20, ativo: bool = False) -> None:
        arte = texto_painel(fonte_texto(tamanho), texto,
                            TEXTO_ATIVO_ORIGINAL if ativo else TEXTO_ORIGINAL,
                            max(1, rect.w - 12), max(1, rect.h - 4))
        tela.blit(arte, arte.get_rect(center=rect.center))

    def _palco(self, tela: pygame.Surface, controle: ControladorCutscene,
               personagem: str) -> None:
        catalogo = controle.catalogo.personagens
        if self._cena_palco is not controle.sequenciador.cena:
            self._cena_palco = controle.sequenciador.cena
            self._interlocutor = None
        if personagem != "jonathan":
            self._interlocutor = personagem
        for lado, chave in enumerate(("jonathan", self._interlocutor)):
            if chave not in catalogo:
                continue
            icone = self._icones[chave]
            if chave == personagem and controle.retrato_atual:
                icone = controle.retrato_atual
            if icone not in self._retratos_palco:
                self._retratos_palco[icone] = pygame.transform.smoothscale(
                    self.obter_retrato(icone), (300, 300))
                copia = self._retratos_palco[icone].copy()
                copia.set_alpha(100)
                self._retratos_apagados[icone] = copia
            ativo = chave == personagem
            tempo = controle.sequenciador.tempo
            entrada = 1 if controle.efeitos_reduzidos else min(1., tempo / .35)
            deslocamento = 0 if controle.efeitos_reduzidos else round(3 * math.sin(tempo * 1.3))
            x = round(LARGURA * (.12 if lado == 0 else .645))
            x += round((1 - entrada) * (-18 if lado == 0 else 18)) if ativo else 0
            y = round(ALTURA * .145) + (deslocamento if ativo else 0)
            moldura = pygame.Rect(x - 6, y - 6, 312, 312)
            tela.blit(painel_menu(moldura.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL,
                                  selecionado=ativo), moldura)
            arte = (self._retratos_palco if ativo else self._retratos_apagados)[icone]
            tela.blit(arte, (x, y))
        if not controle.sequenciador.leitura_concluida:
            quadro = 0 if controle.efeitos_reduzidos else int(controle.sequenciador.tempo * 6) % 12
            onda = _onda_transmissao(quadro)
            tela.blit(onda, onda.get_rect(center=(LARGURA // 2, round(ALTURA * .36))))

    def _historico(self, tela: pygame.Surface, controle: ControladorCutscene) -> None:
        tela.blit(self._sombra, (0, 0))
        painel = pygame.Rect(round(LARGURA * .07), round(ALTURA * .12),
                            round(LARGURA * .86), round(ALTURA * .76))
        tela.blit(painel_menu(painel.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL), painel)
        self._rotulo(tela, "HISTÓRICO DESTA CENA · APENAS O QUE VOCÊ JÁ LEU",
                      pygame.Rect(painel.x + 20, painel.y + 14, painel.w - 40, 32))
        linhas = controle.transcricao
        inicio = controle.historico_inicio
        for i, registro in enumerate(linhas[inicio:inicio + 4]):
            y = painel.y + 68 + i * 104
            nome = controle.catalogo.personagens[registro["personagem"]]["nome"]
            self._rotulo(tela, nome, pygame.Rect(painel.x + 24, y, painel.w - 48, 24), tamanho=17)
            fonte = fonte_texto(23)
            for tamanho in range(23, 15, -1):
                fonte = fonte_texto(tamanho)
                quebradas = linhas_painel(fonte, registro["texto"], painel.w - 64)
                if len(quebradas) <= 3:
                    break
            for j, texto in enumerate(quebradas):
                arte = texto_painel(fonte, texto, TEXTO_ORIGINAL, painel.w - 64, 24)
                tela.blit(arte, (painel.x + 32, y + 28 + j * 24))
        if not linhas:
            self._rotulo(tela, "As falas reveladas aparecerão aqui.",
                          pygame.Rect(painel.x + 24, painel.centery, painel.w - 48, 40))
        self._rotulo(tela, "↑↓ / RODA DO MOUSE  PERCORRER · H / ESC  VOLTAR À CENA",
                      pygame.Rect(painel.x + 24, painel.bottom - 36, painel.w - 48, 24), tamanho=16)

    def _cabecalho_cena(self, tela: pygame.Surface, controle: ControladorCutscene) -> None:
        cena = controle.sequenciador.cena
        if cena is not None:
            self._rotulo(tela, cena.nome or cena.id, pygame.Rect(24, 20, 780, 30), tamanho=22)
            total = sum(p["tipo"] == "fala" for p in cena.passos)
            if total:
                atual = min(total, len(controle.sequenciador.historico) + 1)
                self._rotulo(tela, f"{atual:02d} / {total:02d} · ESC PAUSAR",
                              pygame.Rect(24, 52, 500, 24), tamanho=16)
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
            indice = (0 if controle.efeitos_reduzidos else
                      int(controle.sequenciador.tempo * 2) % len(self._estaticas))
            tela.blit(self._estaticas[indice], (0, 0))
            texto = passo.get("texto", "")
            if texto:
                self._titulo(tela, self._texto_corrompido(texto, indice),
                             cor_dimensao, glitch=True)
        elif tipo == "titulo":
            self._titulo(tela, passo["texto"].replace("{titulo_jogo}", NOME_JOGO),
                         cor_dimensao)
        elif tipo == "fala":
            self._palco(tela, controle, passo["personagem"])
            painel = self.AREA_FALA
            tela.blit(painel_menu(painel.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL), painel)
            personagem = controle.catalogo.personagens[passo["personagem"]]
            self._rotulo(tela, personagem["nome"], pygame.Rect(
                painel.x + 24, painel.y + 12, round(painel.w * .5), 36), tamanho=30)
            self._rotulo(tela, personagem.get("cargo", "TRANSMISSÃO"), pygame.Rect(
                painel.centerx, painel.y + 16, round(painel.w * .45), 28), tamanho=16)
            self._texto(tela, controle.sequenciador.texto_visivel,
                        painel.x + 32, painel.y + 65, painel.w - 64,
                        TEXTO_ORIGINAL, passo.get("texto", ""))
            pronto = controle.sequenciador.leitura_concluida
            tela.blit(painel_menu(self.BOTAO_AVANCAR.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL,
                                  selecionado=pronto, botao=True,
                                  segmentado=False), self.BOTAO_AVANCAR)
            self._rotulo(tela, "CONTINUAR ›" if pronto else "REVELAR TEXTO", self.BOTAO_AVANCAR,
                          ativo=pronto, tamanho=18)
            self._rotulo(tela, "ENTER / CLIQUE  ·  A HISTÓRIA ESPERA POR VOCÊ",
                          pygame.Rect(painel.x + 24, self.BOTAO_AVANCAR.y,
                                      round(painel.w * .70), self.BOTAO_AVANCAR.h), tamanho=16)
        elif tipo == "fade":
            progresso = min(1.0, controle.sequenciador.tempo / max(0.001, passo["duracao"]))
            alfa = int(255 * (1 - progresso if passo.get("direcao") == "entrada"
                              else progresso))
            self._fade.fill(VOID_BLACK)
            self._fade.set_alpha(alfa)
            tela.blit(self._fade, (0, 0))
        self._cabecalho_cena(tela, controle)
        tela.blit(painel_menu(self.BOTAO_HISTORICO.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL,
                              botao=True, segmentado=False), self.BOTAO_HISTORICO)
        self._rotulo(tela, "H  HISTÓRICO", self.BOTAO_HISTORICO, tamanho=18)
        if controle.historico_aberto:
            self._historico(tela, controle)
            self._rotulo(tela, "H  VOLTAR À CENA", self.BOTAO_HISTORICO, tamanho=16)
            return
        cor_acento = self._cor_acento(cor_dimensao)
        _painel(tela, cor_acento, self.BOTAO_PULAR,
                                cor_fundo=(32, 37, 47), espessura_borda=4,
                                glow_raio=0)
        rotulo = self._texto_outline(self._fonte_auxiliar, "PULAR CENA",
                                     (244, 244, 247), 2)
        tela.blit(rotulo, rotulo.get_rect(center=self.BOTAO_PULAR.center))
        if controle.pausado:
            self._titulo(tela, "CENA PAUSADA", cor_dimensao)
        if controle.confirmacao_pulo:
            caixa = pygame.Rect(330, 255, 620, 180)
            _painel(tela, cor_acento, caixa,
                                    espessura_borda=4, glow_raio=0)
            texto = self._fonte_nome.render("Pular esta cena?", True, (244, 244, 247))
            tela.blit(texto, texto.get_rect(center=(640, 312)))
            for indice, (rect, rotulo) in enumerate(((self.BOTAO_CONFIRMAR, "PULAR"),
                                                     (self.BOTAO_CANCELAR, "CONTINUAR CENA"))):
                selecionado = indice == controle.selecao_pulo
                tela.blit(painel_menu(rect.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL,
                                      selecionado=selecionado, botao=True,
                                      segmentado=False), rect)
                texto_botao = texto_painel(self._fonte_auxiliar, rotulo,
                                           TEXTO_ATIVO_ORIGINAL if selecionado else TEXTO_ORIGINAL,
                                           rect.w - 16, rect.h - 10)
                tela.blit(texto_botao, texto_botao.get_rect(center=rect.center))

    def _titulo(self, tela: pygame.Surface, texto: str,
                cor: tuple[int, int, int], glitch: bool = False) -> None:
        chave = texto, cor, glitch
        if chave not in self._titulos:
            cor_titulo = (255, 76, 174) if glitch else self._cor_acento(cor)
            self._titulos[chave] = self._texto_outline(
                self._fonte_titulo, texto, cor_titulo, 4,
            )
        superficie = self._titulos[chave]
        if superficie.get_width() > LARGURA * .88:
            fator = LARGURA * .88 / superficie.get_width()
            superficie = pygame.transform.smoothscale(superficie, (
                round(superficie.get_width() * fator),
                max(1, round(superficie.get_height() * fator))))
            self._titulos[chave] = superficie
        tela.blit(superficie, superficie.get_rect(center=(LARGURA // 2, ALTURA // 2)))

    def desenhar_seletor(self, tela: pygame.Surface, controle: ControladorCutscene,
                        cor: tuple[int, int, int]) -> None:
        """Mostra IDs de cena para o atalho de depuração F8."""
        tela.blit(self._sombra, (0, 0))
        painel = pygame.Rect(230, 110, 820, 500)
        _painel(tela, cor, painel)
        titulo = self._fonte_nome.render("CENAS // DEBUG", True, cor)
        tela.blit(titulo, (265, 135))
        ids = list(controle.catalogo.cenas)
        inicio = max(0, min(controle.indice_debug, max(0, len(ids) - 11)))
        for linha_indice, indice in enumerate(range(inicio, min(len(ids), inicio + 11))):
            cor_linha = cor if indice == controle.indice_debug else (244, 244, 247)
            linha = self._fonte_auxiliar.render(ids[indice], True, cor_linha)
            tela.blit(linha, (285, 195 + linha_indice * 35))
