"""Tela de recordes e resumo persistido do jogador."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.core.constants import BRANCO, CIANO, DOURADO, VOID_BLACK
from src.runtime.infrastructure.graphics.smooth import desenhar_cantos, desenhar_glow, \
    linha_suave, retangulo_suave
from src.infrastructure.ui.layout import CENTRO, LARGURA_BASE, ALTURA_BASE
from src.infrastructure.graphics.theme import tema_atual
from src.runtime.presentation.ui import BotaoNeon

if TYPE_CHECKING:
    from src.runtime.presentation.menu import MenuPrincipal


class TelaRecordesJogo:
    """Implementa a apresentacao dos recordes e estatisticas."""

    def __init__(self, menu: MenuPrincipal) -> None:
        self.menu = menu

    def botao_voltar(self) -> BotaoNeon:
        """Cria o botao de retorno ao menu principal."""
        layout = self.menu.layout
        return BotaoNeon("VOLTAR", (layout.x(0.5) - layout.px(90),
                                    layout.altura - layout.px(64), layout.px(180), layout.px(46)))

    def desenhar(self, tela: pygame.Surface) -> None:
        """Renderiza um painel de recordes em formato de arquivo de voo."""
        menu = self.menu
        layout = menu.layout
        tema = tema_atual(menu.jogo.config["tema"])
        lista = menu.jogo.recordes
        painel = layout.rect(CENTRO, 790 / LARGURA_BASE, 510 / ALTURA_BASE, dy=-12)
        menu._painel_sub(tela, painel, tema)
        menu._detalhe_painel(tela, painel, tema, DOURADO)
        desenhar_cantos(tela, tema["secundaria"], painel, tamanho=layout.px(20))

        # Cabeçalho de arquivo com uma barra de energia que organiza o painel.
        cabecalho = pygame.Rect(painel.x + layout.px(20), painel.y + layout.px(18),
                                painel.w - layout.px(40), layout.px(66))
        retangulo_suave(tela, (13, 22, 45), cabecalho, layout.px(12))
        retangulo_suave(tela, tema["primaria"], cabecalho, layout.px(12), 2,
                         glow_cor=tema["primaria"], glow_raio=layout.px(13))
        desenhar_glow(tela, tema["secundaria"],
                      (cabecalho.x + layout.px(34), cabecalho.centery),
                      layout.px(22), 0.8)
        pygame.draw.circle(tela, tema["secundaria"],
                           (cabecalho.x + layout.px(34), cabecalho.centery),
                           layout.px(7))
        menu._blit_alfa(tela, menu.fonte_cabecalho.render("RECORDES", True, BRANCO),
                        (cabecalho.x + layout.px(58), cabecalho.y + layout.px(11)), 255)
        rotulo = menu.fonte_pequena.render("// GALERIA DA FENDA", True,
                                           tema["secundaria"])
        menu._blit_alfa(tela, rotulo,
                        (cabecalho.right - rotulo.get_width() - layout.px(18),
                         cabecalho.y + layout.px(25)), 255)

        # A classificação ocupa a esquerda; a telemetria do piloto, a direita.
        ranking = pygame.Rect(painel.x + layout.px(20), painel.y + layout.px(101),
                              layout.px(500), painel.h - layout.px(178))
        telemetria = pygame.Rect(ranking.right + layout.px(16), ranking.y,
                                 painel.right - ranking.right - layout.px(20), ranking.h)
        retangulo_suave(tela, (9, 16, 34), ranking, layout.px(12))
        retangulo_suave(tela, tema["secundaria"], ranking, layout.px(12), 1)
        retangulo_suave(tela, (9, 16, 34), telemetria, layout.px(12))
        retangulo_suave(tela, tema["primaria"], telemetria, layout.px(12), 1)

        ranking_titulo = menu.fonte_pequena.render("CLASSIFICAÇÃO GLOBAL", True,
                                                    tema["secundaria"])
        tela.blit(ranking_titulo, (ranking.x + layout.px(18), ranking.y + layout.px(14)))
        linha_suave(tela, tema["secundaria"],
                    (ranking.x + layout.px(18), ranking.y + layout.px(42)),
                    (ranking.right - layout.px(18), ranking.y + layout.px(42)), 1)
        if not lista:
            mensagem = menu.fonte_media.render("AGUARDANDO PRIMEIRO VOO", True,
                                                (185, 195, 225))
            tela.blit(mensagem, mensagem.get_rect(center=(ranking.centerx,
                                                           ranking.centery - layout.px(10))))
            dica = menu.fonte_pequena.render("Complete uma missão para registrar seu nome.",
                                              True, (125, 140, 180))
            tela.blit(dica, dica.get_rect(center=(ranking.centerx,
                                                   ranking.centery + layout.px(24))))
        else:
            y = ranking.y + layout.px(55)
            for indice, registro in enumerate(lista[:5]):
                linha = pygame.Rect(ranking.x + layout.px(12), y,
                                    ranking.w - layout.px(24), layout.px(42))
                cor = (DOURADO if indice == 0 else tema["secundaria"]
                       if indice < 3 else (122, 142, 184))
                fundo = (43, 33, 18) if indice == 0 else (16, 27, 51)
                retangulo_suave(tela, fundo, linha, layout.px(8))
                retangulo_suave(tela, cor, linha, layout.px(8), 1,
                                 glow_cor=cor if indice == 0 else None,
                                 glow_raio=layout.px(8))
                medalha = (linha.x + layout.px(24), linha.centery)
                pygame.draw.circle(tela, cor, medalha, layout.px(12))
                posicao = menu.fonte_pequena.render(str(indice + 1), True, VOID_BLACK)
                tela.blit(posicao, posicao.get_rect(center=medalha))
                nome = menu.fonte_media.render(registro["nome"].upper(), True, BRANCO)
                tela.blit(nome, (linha.x + layout.px(46), linha.y + layout.px(7)))
                nivel = menu.fonte_pequena.render(f"NV {registro['nivel']:02d}", True,
                                                   (160, 175, 210))
                tela.blit(nivel, (linha.x + layout.px(205), linha.y + layout.px(13)))
                pontos = f"{registro['pontos']:,}".replace(",", ".")
                score = menu.fonte_media.render(pontos, True, cor)
                tela.blit(score, score.get_rect(midright=(linha.right - layout.px(18),
                                                          linha.centery)))
                y += layout.px(47)
        jogador = menu.jogo.progresso.jogador
        estatisticas = menu.jogo.progresso.dados["estatisticas"]
        melhor = f"{lista[0]['pontos']:,}".replace(",", ".") if lista else "0"
        titulo_telemetria = menu.fonte_pequena.render("TELEMETRIA", True, tema["primaria"])
        tela.blit(titulo_telemetria, (telemetria.x + layout.px(15),
                                      telemetria.y + layout.px(14)))
        dados = [("MELHOR", melhor), ("VISUAIS", f"{len(menu.jogo.loja.lista_desbloqueadas())}/10"),
                 ("ABATES", str(estatisticas["inimigos_derrotados"])),
                 ("FENDAS", str(jogador["bosses_derrotados"]))]
        for indice, (rotulo, valor) in enumerate(dados):
            y = telemetria.y + layout.px(52 + indice * 52)
            caixa = pygame.Rect(telemetria.x + layout.px(12), y,
                                telemetria.w - layout.px(24), layout.px(42))
            retangulo_suave(tela, (15, 25, 48), caixa, layout.px(7))
            rot = menu.fonte_pequena.render(rotulo, True, (142, 160, 204))
            tela.blit(rot, (caixa.x + layout.px(10), caixa.y + layout.px(5)))
            val = menu.fonte_media.render(valor, True,
                                          DOURADO if indice == 0 else BRANCO)
            tela.blit(val, val.get_rect(midright=(caixa.right - layout.px(10),
                                                  caixa.centery + layout.px(6))))
        piloto = menu.fonte_pequena.render(f"PILOTO // {jogador['nome'].upper()}", True,
                                           tema["secundaria"])
        tela.blit(piloto, piloto.get_rect(center=(telemetria.centerx,
                                                  telemetria.bottom - layout.px(24))))
        botao = self.botao_voltar()
        botao.atualizar(menu.mouse)
        menu._desenhar_botao_entrada(tela, botao, menu.fonte_media, menu._frac_sub(0.6, 0.25))
