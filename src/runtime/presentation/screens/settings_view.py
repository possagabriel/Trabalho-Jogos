"""Geometria e apresentação compartilhadas das configurações dos dois estilos."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

import pygame

from src.core.constants import NEGRO
from src.core.settings import ACOES_CONTROLE, RESOLUCOES
from src.infrastructure.graphics.comic_theme import OpcoesVisuais, opcoes_atuais
from src.runtime.infrastructure.graphics.menu_panels import (
    ACENTO_ORIGINAL,
    BORDA_ORIGINAL,
    FUNDO_ORIGINAL,
    TEXTO_ATIVO_ORIGINAL,
    TEXTO_ORIGINAL,
    cor_menu,
    icone_menu_original,
    painel_menu,
    texto_painel,
)
from src.runtime.infrastructure.graphics.smooth import linha_suave, retangulo_suave

if TYPE_CHECKING:
    from src.infrastructure.ui.layout import Layout
    from src.runtime.presentation.screens.settings_screen import TelaConfiguracoesJogo


CATEGORIAS_CONFIG = (
    ("ÁUDIO", (0, 1)),
    ("TELA", (2, 3, 7, 8, 9, 10)),
    ("CONTROLES", (4, 5, 27, 28)),
    ("VISUAL", (6, 11, 20, 21, 22, 23, 24)),
    ("SHADER", (12, 13, 14, 15, 16, 17, 18, 19)),
    ("CONFORTO", (25, 26)),
)

DESCRICOES_CONFIG = (
    "Volume da trilha sonora durante os menus e as partidas.",
    "Volume de disparos, impactos e sons da interface.",
    "Escolha o tamanho da janela. A mudança pede confirmação antes de ser salva.",
    "Alterna entre janela e tela cheia, mantendo a resolução escolhida.",
    "Ajusta a resposta dos controles. O valor padrão é 100%.",
    "Personalize as teclas de movimento, disparo, esquiva e pausa.",
    "Escolha a paleta de cores do jogo. O console ORIGINAL mantém sua identidade orbital.",
    "Escolha áreas seguras ou fundo nas bordas. A área de jogo mantém a proporção.",
    "Ajuste zoom e posição da imagem. Você pode cancelar para recuperar o ajuste anterior.",
    "Equilibre o detalhe dos efeitos e a fluidez. Não altera as regras do jogo.",
    "Mostra informações de desempenho na tela durante a partida.",
    "Escolha a apresentação ORIGINAL ou o acabamento de quadrinhos do COMIC.",
    "Acabamento de quadrinhos pela placa gráfica. Atua no estilo COMIC quando compatível.",
    "Força do acabamento de quadrinhos. Atua quando o shader COMIC está ativo.",
    "Força dos contornos do shader. Atua quando o shader COMIC está ativo.",
    "Quantidade de faixas de cor do shader. Menos tons deixam a imagem mais marcada.",
    "Ativa as hachuras do acabamento GPU no estilo COMIC.",
    "Textura de grão do shader. Atua quando o shader COMIC está ativo.",
    "Saturação das cores do shader. O valor padrão é 100%.",
    "Mantém textos e interface fora do acabamento do shader para preservar a leitura.",
    "Nível de detalhe do estilo COMIC. As opções abaixo indicam quando estão inativas.",
    "Textura de papel do estilo COMIC. Não aparece com detalhe BAIXA.",
    "Pontos de impressão do estilo COMIC. Não aparecem com detalhe BAIXA.",
    "Traços de sombra do estilo COMIC. Não aparecem com detalhe BAIXA.",
    "Movimento dos traços no COMIC. Só aparece com detalhe ALTA e efeitos normais.",
    "Reduza ou desligue os flashes. No ORIGINAL, isso também mantém as animações "
    "decorativas estáticas.",
    "Reduza ou desligue o tremor da câmera sem mudar as regras da partida.",
    "Exibe a área de colisão para facilitar a leitura. Não altera seu tamanho.",
    "Exibe a mira personalizada durante a partida.",
)


def categoria_config(indice: int) -> int:
    """Encontra a categoria de um índice do catálogo existente."""
    return next(i for i, (_nome, grupo) in enumerate(CATEGORIAS_CONFIG) if indice in grupo)


@dataclass(frozen=True)
class GeometriaConfiguracoes:
    """Áreas compartilhadas pelo desenho e pelos cliques do painel orbital."""

    painel: pygame.Rect
    abas: tuple[pygame.Rect, ...]
    lista: pygame.Rect
    contexto: pygame.Rect


def geometria_config_original(layout: Layout) -> GeometriaConfiguracoes:
    """Reserva abas, lista de opções e ajuda dentro da área segura."""
    margem, gap = layout.px(16), layout.px(6)
    largura = min(layout.largura - layout.px(80), layout.px(1090))
    altura = min(layout.altura - layout.px(210), layout.px(500))
    painel = pygame.Rect(layout.x(.5) - largura // 2, layout.px(108), largura, altura)
    quantidade = len(CATEGORIAS_CONFIG)
    largura_aba = (largura - margem * 2 - gap * (quantidade - 1)) // quantidade
    abas = tuple(pygame.Rect(painel.x + margem + i * (largura_aba + gap),
                             painel.y + margem, largura_aba, layout.px(36))
                  for i in range(len(CATEGORIAS_CONFIG)))
    lista = pygame.Rect(painel.x + margem, painel.y + layout.px(76),
                         round(largura * .64), altura - layout.px(92))
    contexto = pygame.Rect(lista.right + margem, lista.y,
                            painel.right - lista.right - margem * 2, lista.h)
    return GeometriaConfiguracoes(painel, abas, lista, contexto)


def _paragrafo(fonte: pygame.font.Font, texto: str, cor: tuple,
               tamanho: tuple[int, int]) -> pygame.Surface:
    """Cacheia texto com quebra de palavras e ajuste à altura disponível."""
    return _paragrafo_cache(fonte, texto, cor, tamanho, opcoes_atuais())


@lru_cache(maxsize=256)
def _paragrafo_cache(fonte: pygame.font.Font, texto: str, cor: tuple,
                     tamanho: tuple[int, int], visual: OpcoesVisuais) -> pygame.Surface:
    largura, altura = tamanho
    linhas, atual = [], ""
    for palavra in texto.split():
        candidata = f"{atual} {palavra}".strip()
        if atual and fonte.size(candidata)[0] > largura:
            linhas.append(atual)
            atual = palavra
        else:
            atual = candidata
    linhas.append(atual)
    passo = fonte.get_linesize()
    arte = pygame.Surface((largura, max(1, passo * len(linhas))), pygame.SRCALPHA)
    for i, linha in enumerate(linhas):
        arte.blit(texto_painel(fonte, linha, cor, largura, passo), (0, i * passo))
    if arte.get_height() > altura:
        arte = pygame.transform.smoothscale(arte, (largura, altura))
    return arte


class PainelConfiguracoesOriginal:
    """Desenha a configuração existente com acabamento ORIGINAL ou COMIC."""

    def __init__(self, tela: TelaConfiguracoesJogo) -> None:
        self.tela = tela
        self.menu = tela.menu
        self._overlay: pygame.Surface | None = None

    def geometria(self) -> GeometriaConfiguracoes:
        """Retorna a geometria proporcional ao layout ativo."""
        return geometria_config_original(self.menu.layout)

    def linhas(self) -> list[tuple[int, pygame.Rect]]:
        """Associa cada opção visível à sua área de interação."""
        lista, layout = self.geometria().lista, self.menu.layout
        return [(indice, pygame.Rect(lista.x, lista.y + i * layout.px(56),
                                      lista.w, layout.px(50)))
                 for i, indice in enumerate(self.tela.indices_visiveis_original())]

    def trilha_slider(self) -> tuple[int, int]:
        """Retorna os limites do slider usados no desenho, clique e arraste."""
        lista = self.geometria().lista
        return lista.x + round(lista.w * .46), lista.right - self.menu.layout.px(74)

    def linhas_submodo(self, modo: str) -> list[tuple[int, pygame.Rect]]:
        """Compartilha a grade dos controles e da seleção de resolução."""
        layout, lista = self.menu.layout, self.geometria().lista
        if modo == "resolucao":
            inicio, fim = self.menu._resolucoes_visiveis()
            indices, passo, altura = range(inicio, fim), 40, 36
        else:
            indices, passo, altura = range(len(ACOES_CONTROLE)), 48, 42
        return [(indice, pygame.Rect(lista.x, lista.y + i * layout.px(passo),
                                      lista.w, layout.px(altura)))
                 for i, indice in enumerate(indices)]

    def _texto(self, destino: pygame.Surface, texto: str, rect: pygame.Rect,
                tamanho: int = 18, cor: tuple = TEXTO_ORIGINAL) -> None:
        arte = texto_painel(self.menu.layout.fonte_texto(tamanho), texto, cor, rect.w, rect.h)
        destino.blit(arte, arte.get_rect(center=rect.center))

    def _painel(self, destino: pygame.Surface, rect: pygame.Rect, ativo: bool = False) -> None:
        destino.blit(painel_menu(rect.size, FUNDO_ORIGINAL, BORDA_ORIGINAL,
                                       selecionado=ativo), rect)

    def _botao(self, destino: pygame.Surface, rect: pygame.Rect, rotulo: str,
                icone: str, ativo: bool = False) -> None:
        layout = self.menu.layout
        destino.blit(painel_menu(rect.size, FUNDO_ORIGINAL, BORDA_ORIGINAL,
                                       selecionado=ativo, botao=True), rect)
        arte = icone_menu_original(icone, ativo, layout.px(22))
        destino.blit(arte, arte.get_rect(center=(rect.x + layout.px(20), rect.centery)))
        texto = pygame.Rect(rect.x + layout.px(44), rect.y + layout.px(6),
                             rect.w - layout.px(66), rect.h - layout.px(12))
        self._texto(destino, rotulo, texto, 20,
                     TEXTO_ATIVO_ORIGINAL if ativo else TEXTO_ORIGINAL)

    def _contexto(self, destino: pygame.Surface, titulo: str, valor: str,
                   descricao: str, dica: str) -> None:
        rect, layout = self.geometria().contexto, self.menu.layout
        self._painel(destino, rect, True)
        for texto, y, h, tamanho, cor in (
                ("AJUSTE SELECIONADO", 10, 24, 15, ACENTO_ORIGINAL),
                (titulo.upper(), 42, 44, 23, TEXTO_ORIGINAL),
                (valor, 98, 32, 21, ACENTO_ORIGINAL)):
            self._texto(destino, texto, pygame.Rect(rect.x + layout.px(12),
                         rect.y + layout.px(y), rect.w - layout.px(24), layout.px(h)), tamanho, cor)
        for texto, y, altura in ((descricao, 150, 130), (dica, 292, 78)):
            area = pygame.Rect(rect.x + layout.px(16), rect.y + layout.px(y),
                                rect.w - layout.px(32), layout.px(altura))
            arte = _paragrafo(layout.fonte_texto(18), texto, TEXTO_ORIGINAL, area.size)
            destino.blit(arte, area)

    def desenhar(self, destino: pygame.Surface) -> None:
        """Renderiza a aba ativa ou uma subtela sem modificar valores."""
        menu, layout = self.menu, self.menu.layout
        if menu.config_submodo == "ajuste":
            self._desenhar_ajuste(destino)
            return
        titulo = {"controles": "CONFIGURAÇÕES // CONTROLES",
                  "resolucao": "CONFIGURAÇÕES // RESOLUÇÃO"}.get(
                      menu.config_submodo, "CONFIGURAÇÕES // SISTEMAS")
        menu._cabecalho_sub_animado(destino, titulo, ACENTO_ORIGINAL)
        self._painel(destino, self.geometria().painel)
        if menu.config_submodo in ("controles", "resolucao"):
            self._desenhar_submodo(destino)
        else:
            self._desenhar_geral(destino)
        botoes = menu._botoes_rodape(["VOLTAR"] if menu.config_submodo else ["SALVAR", "VOLTAR"])
        for botao in botoes:
            self._botao(destino, botao.rect, botao.texto,
                         "voltar" if botao.texto == "VOLTAR" else "equipar",
                         botao.rect.collidepoint(menu.mouse))
        dica = ("SETAS: SELECIONAR  ·  ENTER: ABRIR  ·  ESC: VOLTAR" if menu.config_submodo else
                "TAB: ABAS  ·  SETAS: SELECIONAR / AJUSTAR  ·  ENTER: ABRIR  ·  ESC: VOLTAR")
        self._texto(destino, dica, pygame.Rect(0, layout.altura - layout.px(96),
                                              layout.largura, layout.px(22)), 16)
        if menu.remapando:
            self._desenhar_remapeamento(destino)

    def _desenhar_geral(self, destino: pygame.Surface) -> None:
        menu, layout = self.menu, self.menu.layout
        categoria = categoria_config(menu.config_selecao)
        abas = zip(CATEGORIAS_CONFIG, self.geometria().abas)
        for indice, ((nome, _grupo), aba) in enumerate(abas):
            ativo = indice == categoria
            destino.blit(painel_menu(aba.size, FUNDO_ORIGINAL, BORDA_ORIGINAL,
                                           selecionado=ativo, botao=True, segmentado=False), aba)
            self._texto(destino, nome, aba.inflate(-layout.px(10), -layout.px(6)), 18,
                         TEXTO_ATIVO_ORIGINAL if ativo else TEXTO_ORIGINAL)
        for indice, rect in self.linhas():
            self._painel(destino, rect, indice == menu.config_selecao)
            rotulo = menu._linhas_config()[indice][0]
            self._texto(destino, rotulo, pygame.Rect(rect.x + layout.px(12), rect.y,
                         round(rect.w * .4), rect.h), 19)
            self._desenhar_controle(destino, indice, rect)
        indice = menu.config_selecao
        rotulo, tipo = menu._linhas_config()[indice]
        dica = ("Arraste a barra ou use ← / → para ajustar." if menu._eh_slider_config(tipo) else
                "Use ← / → para mudar ou ENTER para abrir.")
        self._contexto(destino, rotulo, self.tela.valor_opcao(indice),
                         DESCRICOES_CONFIG[indice], dica)
        grupo = CATEGORIAS_CONFIG[categoria][1]
        lista = self.geometria().lista
        self._texto(destino, f"{grupo.index(indice) + 1} / {len(grupo)} AJUSTES  ·  CTRL+S: SALVAR",
                     pygame.Rect(lista.x, lista.bottom - layout.px(28), lista.w, layout.px(22)),
                     16, ACENTO_ORIGINAL)

    def _desenhar_controle(self, destino: pygame.Surface, indice: int, rect: pygame.Rect) -> None:
        menu, layout = self.menu, self.menu.layout
        tipo = menu._linhas_config()[indice][1]
        x0, x1 = self.trilha_slider()
        if menu._eh_slider_config(tipo):
            fracao = self.tela.fracao_slider(indice)
            trilha = pygame.Rect(x0, rect.centery - layout.px(3), x1 - x0, layout.px(6))
            retangulo_suave(destino, cor_menu(BORDA_ORIGINAL), trilha, layout.px(3))
            preenchido = trilha.copy()
            preenchido.w = max(1, round(trilha.w * fracao))
            retangulo_suave(destino, cor_menu(ACENTO_ORIGINAL), preenchido, layout.px(3))
            marcador = pygame.Rect(x0 + preenchido.w - layout.px(4),
                                   rect.centery - layout.px(9), layout.px(8), layout.px(18))
            retangulo_suave(destino, cor_menu(TEXTO_ORIGINAL), marcador, layout.px(2))
            self._texto(destino, self.tela.valor_opcao(indice),
                         pygame.Rect(x1 + layout.px(8), rect.y,
                                     rect.right - x1 - layout.px(14), rect.h), 18)
        else:
            area = pygame.Rect(x0, rect.y + layout.px(6), rect.right - x0 - layout.px(10),
                                rect.h - layout.px(12))
            self._texto(destino, self.tela.valor_opcao(indice), area.inflate(-layout.px(32), 0),
                         17, ACENTO_ORIGINAL)
            for x, sinal in ((area.left, "‹"), (area.right - layout.px(16), "›")):
                self._texto(destino, sinal, pygame.Rect(x, area.y, layout.px(16), area.h), 24)

    def _desenhar_submodo(self, destino: pygame.Surface) -> None:
        menu, layout, modo = self.menu, self.menu.layout, self.menu.config_submodo
        titulo = "TECLAS DE COMANDO" if modo == "controles" else "MODOS DE VÍDEO"
        if modo == "resolucao":
            inicio, fim = menu._resolucoes_visiveis()
            titulo += f"  ·  {inicio + 1}–{fim} DE {len(RESOLUCOES)}"
        self._texto(destino, titulo, pygame.Rect(self.geometria().painel.x,
                     self.geometria().painel.y + layout.px(16), self.geometria().painel.w,
                     layout.px(32)), 22, ACENTO_ORIGINAL)
        for indice, rect in self.linhas_submodo(modo):
            selecionado = indice == (menu.controle_selecao if modo == "controles" else
                                       menu.resolucao_selecao)
            self._painel(destino, rect, selecionado)
            if modo == "controles":
                nome = ACOES_CONTROLE[indice].upper()
                valor = pygame.key.name(menu.jogo.config.controles[ACOES_CONTROLE[indice]]).upper()
            else:
                nome, valor = RESOLUCOES[indice], "ATUAL" if (
                    RESOLUCOES[indice] == menu.jogo.config["resolucao"]) else "TESTAR"
            self._texto(destino, nome, pygame.Rect(rect.x + layout.px(12), rect.y,
                                                   rect.w // 2, rect.h), 20)
            self._texto(destino, valor, pygame.Rect(rect.centerx, rect.y,
                                                    rect.w // 2 - layout.px(12), rect.h),
                         18, ACENTO_ORIGINAL)
        if modo == "controles":
            acao = ACOES_CONTROLE[menu.controle_selecao]
            self._contexto(destino, acao, pygame.key.name(menu.jogo.config.controles[acao]).upper(),
                             "Selecione a ação e pressione ENTER ou clique para trocar a tecla.",
                             "ESC cancela a troca. Teclas já usadas são sinalizadas.")
        else:
            self._contexto(destino, "Resolução", RESOLUCOES[menu.resolucao_selecao],
                             "A nova resolução entra em teste. Confirme para mantê-la; "
                             "sem confirmação, a anterior volta.",
                             "ENTER testa a seleção. ESC retorna às configurações.")

    def _escurecer(self, destino: pygame.Surface) -> None:
        if self._overlay is None or self._overlay.get_size() != destino.get_size():
            self._overlay = pygame.Surface(destino.get_size(), pygame.SRCALPHA)
            self._overlay.fill((*NEGRO, 220))
        destino.blit(self._overlay, (0, 0))

    def _desenhar_remapeamento(self, destino: pygame.Surface) -> None:
        layout, menu = self.menu.layout, self.menu
        self._escurecer(destino)
        rect = layout.rect("centro", .7, .38)
        self._painel(destino, rect, True)
        for texto, y, tamanho, cor in (
                ("NOVO COMANDO", 24, 22, ACENTO_ORIGINAL),
                (menu.remapando.upper(), 74, 30, TEXTO_ORIGINAL),
                ("PRESSIONE A NOVA TECLA", 130, 22, TEXTO_ORIGINAL),
                ("ESC: CANCELAR", 194, 18, ACENTO_ORIGINAL)):
            area = pygame.Rect(rect.x + layout.px(16), rect.y + layout.px(y),
                                rect.w - layout.px(32), layout.px(32))
            self._texto(destino, texto, area, tamanho, cor)

    def _desenhar_ajuste(self, destino: pygame.Surface) -> None:
        layout, menu = self.menu.layout, self.menu
        menu._cabecalho_sub_animado(destino, "CONFIGURAÇÕES // AJUSTAR TELA", ACENTO_ORIGINAL)
        frame = menu._frame_janela()
        retangulo_suave(destino, cor_menu(ACENTO_ORIGINAL), frame, 1, 2)
        for dx, dy in ((layout.px(60), 0), (0, layout.px(60))):
            linha_suave(destino, cor_menu(BORDA_ORIGINAL),
                         (frame.centerx - dx, frame.centery - dy),
                         (frame.centerx + dx, frame.centery + dy), 1)
        cfg = menu.jogo.config
        painel = pygame.Rect(layout.px(40), layout.altura - layout.px(164),
                              layout.largura - layout.px(80), layout.px(130))
        self._painel(destino, painel)
        valor = (f"ESCALA {cfg['ajuste_escala'] * 100:.0f}%  ·  "
                 f"X {cfg['ajuste_off_x']:+.0f}  ·  Y {cfg['ajuste_off_y']:+.0f}")
        self._texto(destino, valor, pygame.Rect(painel.x, painel.y + layout.px(12),
                                               painel.w, layout.px(30)), 22, ACENTO_ORIGINAL)
        for i, dica in enumerate(("SETAS: POSIÇÃO  ·  W/S: ZOOM  ·  R: RESTAURAR",
                                  "ENTER: SALVAR  ·  ESC: CANCELAR")):
            self._texto(destino, dica, pygame.Rect(painel.x, painel.y + layout.px(52 + i * 32),
                                                  painel.w, layout.px(24)), 18)

    def desenhar_confirmacao(self, destino: pygame.Surface) -> None:
        """Mantém a confirmação temporizada no mesmo acabamento das opções."""
        menu, layout = self.menu, self.menu.layout
        self._escurecer(destino)
        rect = layout.rect("centro", 580 / 900, 340 / 700)
        self._painel(destino, rect, True)
        modo = "TELA CHEIA" if menu.jogo.config["tela_cheia"] else "JANELA"
        for texto, y, tamanho, cor in (
                ("MANTER ESTA RESOLUÇÃO?", 26, 26, TEXTO_ORIGINAL),
                (f"{menu.jogo.config['resolucao']}  ·  {modo}", 86, 22, ACENTO_ORIGINAL),
                (f"RETORNO AUTOMÁTICO EM {menu._segundos_confirmacao_resolucao()}s", 142,
                 20, TEXTO_ORIGINAL),
                ("ENTER: MANTER  ·  ESC: REVERTER", 208, 18, TEXTO_ORIGINAL)):
            area = pygame.Rect(rect.x + layout.px(16), rect.y + layout.px(y),
                                rect.w - layout.px(32), layout.px(34))
            self._texto(destino, texto, area, tamanho, cor)
        for botao, rotulo, icone in zip(menu._botoes_confirmacao_resolucao(),
                                        ("MANTER", "REVERTER"), ("equipar", "voltar")):
            self._botao(destino, botao, rotulo, icone, botao.collidepoint(menu.mouse))
