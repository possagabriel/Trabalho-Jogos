"""Tela de recordes e resumo persistido do jogador."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.infrastructure.graphics.comic_theme import opcoes_atuais
from src.runtime.infrastructure.graphics.menu_panels import (
    ACENTO_ORIGINAL,
    TEXTO_ATIVO_ORIGINAL,
    TEXTO_ORIGINAL,
    painel_menu,
    texto_painel,
)
from src.runtime.presentation.components import (
    Botao,
    CabecalhoTela,
    EstadoVazio,
    ItemLista,
    Lista,
    Painel,
    RodapeAcoes,
    tokens_atuais,
)
from src.runtime.presentation.components.primitives import desenhar_texto, fonte

if TYPE_CHECKING:
    from src.runtime.presentation.menu import MenuPrincipal


def _pontos(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


class TelaRecordesJogo:
    """Implementa a apresentacao dos recordes e estatisticas."""

    def __init__(self, menu: MenuPrincipal) -> None:
        self.menu = menu
        self._cabecalho = CabecalhoTela("RECORDES")

    def botao_voltar(self) -> Botao:
        """Cria o botao de retorno alinhado ao rodape padrao."""
        rect = self.menu._botoes_rodape(["VOLTAR"])[0].rect
        return Botao("VOLTAR", rect)

    def desenhar(self, tela: pygame.Surface) -> None:
        """Renderiza um painel de recordes em formato de arquivo de voo."""
        if opcoes_atuais().ativo:
            self._desenhar_comic(tela)
            return
        menu = self.menu
        layout = menu.layout
        tk = tokens_atuais(menu.jogo.config["tema"])
        lista = menu.jogo.recordes
        self._cabecalho.cor = tk.superficie.destaque
        self._cabecalho.desenhar(
            tela,
            layout,
            tokens=tk,
            progresso=menu._frac_sub(0.0, 0.35),
        )
        painel = Painel(
            menu._painel_recordes(),
            titulo="ARQUIVO DE VOO",
            subtitulo="// GALERIA DA FENDA",
            cor_borda=tk.superficie.borda_forte,
            cor_fundo=tk.superficie.fundo,
            mostrar_cantos=True,
        )
        painel.desenhar(
            tela,
            layout,
            tokens=tk,
            progresso=menu._frac_sub(0.04, 0.45),
        )
        area = painel.area_conteudo(layout)
        ranking = pygame.Rect(
            area.x + layout.px(2),
            area.y,
            min(layout.px(500), int(area.w * 0.49)),
            max(layout.px(180), area.h - layout.px(60)),
        )
        telemetria = pygame.Rect(
            ranking.right + layout.px(16),
            ranking.y,
            area.right - ranking.right - layout.px(16),
            ranking.h,
        )
        self._desenhar_ranking(tela, ranking, lista, layout, tk)
        self._desenhar_telemetria(tela, telemetria, lista, layout, tk)
        rodape = RodapeAcoes([self.botao_voltar()], dicas=["ESC  VOLTAR"])
        rodape.atualizar(menu.mouse)
        rodape.desenhar(
            tela,
            layout,
            fonte_usada=menu.fonte_media,
            tokens=tk,
            progresso=menu._frac_sub(0.6, 0.25),
        )

    def _desenhar_comic(self, tela: pygame.Surface) -> None:
        """Organiza o placar em cinco quadros com colunas de largura estável."""
        menu, layout = self.menu, self.menu.layout
        painel = menu._painel_recordes()
        tela.blit(painel_menu(painel.size, (0, 0, 0), ACENTO_ORIGINAL), painel)

        def texto(rotulo: str, rect: pygame.Rect, selecionado: bool = False) -> None:
            cor = TEXTO_ATIVO_ORIGINAL if selecionado else TEXTO_ORIGINAL
            arte = texto_painel(menu.fonte_media, rotulo, cor,
                                max(1, rect.w - layout.px(16)), rect.h - layout.px(6))
            tela.blit(arte, arte.get_rect(center=rect.center))

        margem = layout.px(24)
        texto("RECORDES // GALERIA DE PILOTOS", pygame.Rect(
            painel.x + margem, painel.y + layout.px(16),
            painel.w - margem * 2, layout.px(38)))
        lista = menu.jogo.recordes
        topo = painel.y + layout.px(72)
        altura = max(1, (painel.h - layout.px(150)) // 5)
        for i, registro in enumerate(lista[:5]):
            rect = pygame.Rect(painel.x + margem, topo + i * altura,
                               painel.w - margem * 2, altura - layout.px(8))
            primeiro = i == 0
            tela.blit(painel_menu(rect.size, (0, 0, 0), ACENTO_ORIGINAL,
                                  selecionado=primeiro, botao=True, segmentado=False), rect)
            for x, w, rotulo in ((0, .12, f"{i + 1:02d}"),
                                 (.12, .44, str(registro['nome']).upper()),
                                 (.56, .16, f"NV {registro['nivel']:02d}"),
                                 (.72, .28, f"{_pontos(registro['pontos'])} PTS")):
                texto(rotulo, pygame.Rect(rect.x + round(rect.w * x), rect.y,
                                          round(rect.w * w), rect.h), primeiro)
        if not lista:
            texto("SEU PRIMEIRO VOO COMEÇA UMA HISTÓRIA.", pygame.Rect(
                painel.x + margem, topo, painel.w - margem * 2, altura * 2))
        jogador = menu.jogo.progresso.jogador
        estatisticas = menu.jogo.progresso.dados["estatisticas"]
        liberadas = len(menu.jogo.loja.lista_desbloqueadas())
        total = len(menu.jogo.loja.skins)
        texto(f"PILOTO: {jogador['nome'].upper()} · VISUAIS {liberadas}/{total}", pygame.Rect(
            painel.x + margem, painel.bottom - layout.px(66),
            painel.w - margem * 2, layout.px(26)))
        texto(f"{estatisticas['inimigos_derrotados']} ABATES · "
              f"{jogador['bosses_derrotados']} CHEFES DERROTADOS", pygame.Rect(
                  painel.x + margem, painel.bottom - layout.px(36),
                  painel.w - margem * 2, layout.px(26)))
        botao = self.botao_voltar()
        tela.blit(painel_menu(botao.rect.size, (0, 0, 0), ACENTO_ORIGINAL,
                              botao=True), botao.rect)
        texto("ESC  VOLTAR", botao.rect)

    def _desenhar_ranking(
        self,
        tela: pygame.Surface,
        rect: pygame.Rect,
        lista: list[dict],
        layout,
        tk,
    ) -> None:
        Painel(
            rect,
            cor_borda=tk.superficie.destaque,
            cor_fundo=tk.superficie.fundo,
            mostrar_cantos=False,
            raio=tk.superficie.raio_pequeno,
            glow=8,
        ).desenhar(tela, layout, tokens=tk)
        titulo = fonte(layout, tk.tipografia.subtitulo, tokens=tk)
        desenhar_texto(
            tela,
            "CLASSIFICACAO GLOBAL",
            (rect.x + layout.px(18), rect.y + layout.px(14)),
            titulo,
            tk.superficie.destaque,
            alinhamento="topleft",
            tokens=tk,
        )
        pygame.draw.line(
            tela,
            tk.superficie.destaque,
            (rect.x + layout.px(18), rect.y + layout.px(42)),
            (rect.right - layout.px(18), rect.y + layout.px(42)),
            max(1, layout.px(1)),
        )
        itens = [
            ItemLista(
                titulo=registro["nome"].upper(),
                subtitulo=f"NV {registro['nivel']:02d}",
                valor=_pontos(registro["pontos"]),
                destaque=indice == 0,
            )
            for indice, registro in enumerate(lista[:5])
        ]
        area_lista = pygame.Rect(
            rect.x + layout.px(12),
            rect.y + layout.px(55),
            rect.w - layout.px(24),
            max(1, rect.bottom - rect.y - layout.px(67)),
        )
        Lista(
            area_lista,
            itens,
            altura_linha=tk.altura_lista,
            espaco=tk.espaco_lista,
            mostrar_indice=True,
            estado_vazio=EstadoVazio(
                "AGUARDANDO PRIMEIRO VOO",
                "Complete uma missao para registrar seu nome.",
            ),
        ).desenhar(tela, layout, tokens=tk)

    def _desenhar_telemetria(
        self,
        tela: pygame.Surface,
        rect: pygame.Rect,
        lista: list[dict],
        layout,
        tk,
    ) -> None:
        Painel(
            rect,
            cor_borda=tk.superficie.borda_forte,
            cor_fundo=tk.superficie.fundo,
            mostrar_cantos=False,
            raio=tk.superficie.raio_pequeno,
            glow=8,
        ).desenhar(tela, layout, tokens=tk)
        titulo = fonte(layout, tk.tipografia.subtitulo, tokens=tk)
        desenhar_texto(
            tela,
            "TELEMETRIA",
            (rect.x + layout.px(15), rect.y + layout.px(14)),
            titulo,
            tk.superficie.borda_forte,
            alinhamento="topleft",
            tokens=tk,
        )
        jogador = self.menu.jogo.progresso.jogador
        estatisticas = self.menu.jogo.progresso.dados["estatisticas"]
        melhor = _pontos(lista[0]["pontos"]) if lista else "0"
        dados = [
            ("MELHOR", melhor, True),
            ("VISUAIS", f"{len(self.menu.jogo.loja.lista_desbloqueadas())}/"
             f"{len(self.menu.jogo.loja.skins)}", False),
            ("ABATES", str(estatisticas["inimigos_derrotados"]), False),
            ("FENDAS", str(jogador["bosses_derrotados"]), False),
        ]
        itens = [
            ItemLista(titulo=rotulo, valor=valor, destaque=destaque)
            for rotulo, valor, destaque in dados
        ]
        area_lista = pygame.Rect(
            rect.x + layout.px(12),
            rect.y + layout.px(52),
            rect.w - layout.px(24),
            max(1, rect.h - layout.px(104)),
        )
        Lista(
            area_lista,
            itens,
            altura_linha=tk.altura_lista,
            espaco=tk.espaco_lista * 2,
            mostrar_indice=False,
            mostrar_fundo=True,
        ).desenhar(tela, layout, tokens=tk)
        piloto = fonte(layout, tk.tipografia.legenda, tokens=tk)
        desenhar_texto(
            tela,
            f"PILOTO // {jogador['nome'].upper()}",
            (rect.centerx, rect.bottom - layout.px(24)),
            piloto,
            tk.superficie.destaque,
            alinhamento="centro",
            tokens=tk,
        )
