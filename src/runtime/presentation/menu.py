"""Menu profissional: telas, animacoes, notificacoes e dialogos.

Implementa o menu principal com identidade visual cinematografica: fundo
espacial em camadas (parallax), HUD diegetico de nave, titulo com composicao
assimetrica e tipografia forte, opcoes com destaque deslizante (paralelogramo
inclinado), animacoes de entrada escalonadas e transicao cinematografica ao
iniciar a missao. Preserva todas as telas (continuar, loja, recordes,
configuracoes) e a logica de persistencia existente.

Responsividade: nenhuma posicao/tamanho e fixo em pixels. Tudo passa pelo
``Layout`` (game.layout): ancoras na grade 3x3, proporcoes da superficie,
escala da base de design (900x700) e safe areas. Assim o menu se recompoe
em qualquer resolucao sem coordenadas rigidas.
"""

import math
import logging
import os

import pygame

from src.runtime.presentation.screens.continue_screen import TelaContinuarJogo
from src.core.constants import BRANCO, CIANO, DOURADO, QUANTUM_CYAN, VERDE
from src.infrastructure.ui.layout import ALTURA_BASE, CENTRO, LARGURA_BASE, TOPO_DIREITA, \
    TOPO_ESQUERDA, Layout
from src.runtime.presentation.screens.main_menu_screen import TelaPrincipalJogo
from src.runtime.presentation.screens.menu_screens import (TelaConfiguracoes, TelaContinuar, TelaLoja,
                           TelaPrincipal, TelaRecordes)
from src.runtime.presentation.screens.records_screen import TelaRecordesJogo
from src.runtime.presentation.screens.store_screen import TelaLojaJogo
from src.runtime.presentation.screens.settings_screen import TelaConfiguracoesJogo
from game.phase_select import PhaseSelectScreen
from src.runtime.presentation.menu_scene import DestaqueMenu, FundoCinematico, HudMenu, NaveMenu, \
    TransicaoMissao, texto_espacado
from src.runtime.domain.entities.player import Jogador
from src.runtime.infrastructure.persistence.save_system import ARQUIVO_RECORDES, SistemaProgressao
from src.core.settings import ACOES_CONTROLE, RESOLUCOES, TEMAS
from src.runtime.infrastructure.persistence.shop import LojaSkins
from src.runtime.infrastructure.graphics.smooth import desenhar_cantos, desenhar_circulo as \
    desenhar_circulo_suave, desenhar_glow, ease_out, ease_out_back, \
    desenhar_poligono, linha_suave, painel_glass, retangulo_suave, texto_suave, \
    desenhar_painel_cartoon, desenhar_botao_cartoon, desenhar_estrela
from src.infrastructure.graphics.theme import tema_atual
from src.runtime.presentation.ui import BotaoNeon

NEGRO = (0, 0, 0)
LOGGER = logging.getLogger(__name__)


def formatar_pontos(n):
    """Formata numeros com separador de milhar no padrao brasileiro."""
    return f"{n:,}".replace(",", ".")


class OpcaoMenu:
    """Opcao do menu principal com identidade visual forte na selecao.

    O item selecionado recebe fonte maior, glow, eco de glitch e uma linha
    de acento; os demais permanecem discretos. A entrada e animada com um
    deslocamento horizontal que se dissipa (efeito "saindo da tela").
    """

    def __init__(self, texto, y, funcao):
        self.texto = texto
        self.y = y
        self.funcao = funcao
        self.hover = False

    def get_rect(self, x, fonte, layout):
        larg = fonte.size(self.texto)[0]
        alt = fonte.get_height()
        pad_x = layout.px(46)
        pad_y = layout.px(16)
        return pygame.Rect(x - pad_x, self.y - alt // 2 - pad_y,
                           larg + pad_x * 2, alt + pad_y * 2)

    def atualizar(self, mouse_pos, x, fonte, layout):
        self.hover = self.get_rect(x, fonte, layout).collidepoint(mouse_pos)

    @staticmethod
    def _blit(tela, surf, x, y, alfa, centrado=False):
        if alfa <= 0:
            return
        rect = (surf.get_rect(center=(x, y)) if centrado
                else surf.get_rect(midleft=(x, y)))
        if alfa >= 255:
            tela.blit(surf, rect)
        else:
            s = surf.copy()
            s.set_alpha(int(alfa))
            tela.blit(s, rect)

    def desenhar(self, tela, fonte, fonte_sel, tema, x, selecionado,
                 deslocamento, alfa, layout):
        primaria = tema["primaria"]
        secundaria = tema["secundaria"]
        fonte_ativa = fonte_sel if selecionado else fonte
        cor = BRANCO if selecionado else (172, 182, 222)
        xf = x + deslocamento
        y = self.y
        if selecionado:
            surf = texto_suave(fonte_ativa, self.texto, secundaria, primaria,
                               6, True)
            self._blit(tela, surf, xf + layout.px(4), y + layout.px(2), alfa)
        surf = texto_suave(fonte_ativa, self.texto, cor,
                           primaria if selecionado else None,
                           5 if selecionado else 0, True)
        self._blit(tela, surf, xf, y, alfa)
        if selecionado and alfa >= 255:
            larg = fonte_ativa.size(self.texto)[0]
            linha_suave(tela, primaria,
                         (xf, y + fonte_ativa.get_height() // 2 + layout.px(4)),
                         (xf + larg,
                          y + fonte_ativa.get_height() // 2 + layout.px(4)), 3)


class SistemaNotificacao:
    """Notificacoes temporarias (toasts) no canto superior direito."""

    CORES = {"sucesso": (0, 130, 60), "erro": (150, 20, 20),
             "conquista": (150, 100, 0), "info": (30, 60, 130)}

    def __init__(self, layout=None):
        self._layout = layout or Layout()
        self.notificacoes = []

    def adicionar(self, mensagem, tipo="info", duracao=3000):
        self.notificacoes.append({
            "mensagem": mensagem, "tipo": tipo, "duracao": duracao,
            "inicio": pygame.time.get_ticks(), "alpha": 255,
        })

    def atualizar(self):
        for notif in self.notificacoes[:]:
            decorrido = pygame.time.get_ticks() - notif["inicio"]
            if decorrido > notif["duracao"]:
                notif["alpha"] -= 6
                if notif["alpha"] <= 0:
                    self.notificacoes.remove(notif)

    def desenhar(self, tela, fonte):
        l = self._layout
        y = l.px(24)
        altura_toast = l.px(44)
        for notif in self.notificacoes[:]:
            texto = fonte.render(notif["mensagem"], True, BRANCO)
            largura = texto.get_width() + l.px(48)
            fundo = pygame.Surface((largura, altura_toast), pygame.SRCALPHA)
            cor = self.CORES[notif["tipo"]]
            rect = pygame.Rect(0, 0, largura, altura_toast)
            retangulo_suave(fundo, cor + (int(notif["alpha"] * 0.85),), rect, 8)
            retangulo_suave(fundo, BRANCO + (int(notif["alpha"]),), rect, 8, 1)
            x = l.largura - largura - l.px(20)
            tela.blit(fundo, (x, y))
            texto.set_alpha(notif["alpha"])
            tela.blit(texto, (x + l.px(24), y + l.px(11)))
            y += l.px(54)


class Dialogo:
    """Dialogo modal de confirmacao com visual cartoon.

    Painel com borda preta grossa, cantos arredondados, icone de alerta
    animado, titulo com sombra cartoon, botoes 'bolha' com hover brilhante
    e dicas de teclado. Animacao de entrada com bounce (ease_out_back).
    """

    def __init__(self, titulo, mensagem, funcao_confirmar, funcao_cancelar,
                 layout=None):
        self._layout = layout or Layout()
        self.titulo = titulo
        self.mensagem = mensagem
        self.funcao_confirmar = funcao_confirmar
        self.funcao_cancelar = funcao_cancelar
        self.ativo = True
        self._t0 = pygame.time.get_ticks()
        self._largura, self._altura = self._layout.px(540), self._layout.px(320)
        self._x = self._layout.x(0.5) - self._largura // 2
        self._y = self._layout.y(0.5) - self._altura // 2
        self._rect = pygame.Rect(self._x, self._y, self._largura, self._altura)

    def _retangulos(self):
        l = self._layout
        rect = self._rect
        btn_w, btn_h = l.px(170), l.px(50)
        confirmar = pygame.Rect(rect.centerx - btn_w - l.px(12),
                                rect.bottom - l.px(82),
                                btn_w, btn_h)
        cancelar = pygame.Rect(rect.centerx + l.px(12),
                               rect.bottom - l.px(82),
                               btn_w, btn_h)
        return confirmar, cancelar

    def tratar_evento(self, evento, mouse_pos=None):
        if not self.ativo:
            return
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._confirmar()
            elif evento.key == pygame.K_ESCAPE:
                self._cancelar()
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            confirmar, cancelar = self._retangulos()
            if confirmar.collidepoint(mouse_pos or evento.pos):
                self._confirmar()
            elif cancelar.collidepoint(mouse_pos or evento.pos):
                self._cancelar()

    def _confirmar(self):
        if self.ativo:
            self.ativo = False
            self.funcao_confirmar()

    def _cancelar(self):
        if self.ativo:
            self.ativo = False
            self.funcao_cancelar()

    def _animacao(self):
        """Progresso da entrada (0..1) e fator de escala do painel."""
        t = (pygame.time.get_ticks() - self._t0) / 250.0
        p = max(0.0, min(1.0, t))
        return p, ease_out_back(p)

    def desenhar(self, tela, fonte_titulo, fonte_texto, mouse_pos=(0, 0),
                 tema=None):
        l = self._layout
        tema = tema or {
            "primaria": (120, 90, 220), "secundaria": (0, 200, 120),
            "terciaria": (255, 70, 90), "fundo_painel": (12, 14, 32),
            "borda_forte": (200, 200, 230),
        }
        p, escala = self._animacao()
        t = pygame.time.get_ticks() * 0.001

        # overlay de foco
        overlay = pygame.Surface((l.largura, l.altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(190 * p)))
        tela.blit(overlay, (0, 0))

        # painel com entrada em escala (bounce cartoon)
        largura = int(self._largura * (0.92 + 0.08 * escala))
        altura = int(self._altura * (0.92 + 0.08 * escala))
        x = self._x - (largura - self._largura) // 2
        y = self._y - (altura - self._altura) // 2
        rect = pygame.Rect(x, y, largura, altura)
        self._rect = rect

        # painel cartoon (borda grossa preta + fundo arredondado)
        desenhar_painel_cartoon(tela, tema["primaria"], rect,
                                cor_fundo=(14, 14, 30), raio_canto=24,
                                espessura_borda=6, alpha=245, glow_raio=22)

        alfa = int(255 * p)
        pulso = 0.6 + 0.4 * math.sin(t * 3.0)

        # estrelas decorativas animadas
        for i, (sx, sy, sr) in enumerate([
            (rect.x + l.px(28), rect.y + l.px(28), l.px(10)),
            (rect.right - l.px(28), rect.y + l.px(28), l.px(8)),
            (rect.x + l.px(22), rect.bottom - l.px(28), l.px(7)),
            (rect.right - l.px(22), rect.bottom - l.px(28), l.px(9)),
        ]):
            rot = t * 60 + i * 72
            cor_estrela = tema["secundaria"] if i % 2 == 0 else tema["terciaria"]
            desenhar_estrela(tela, (sx, sy), sr, cor_estrela, pontas=4,
                             rotacao=rot)

        # icone de alerta cartoon (circulo com ! pulsante)
        icone_cor = tema["terciaria"]
        ix, iy = rect.centerx, rect.y + l.px(50)
        raio_icone = l.px(24) + int(2 * pulso)
        # sombra do circulo (em surface SRCALPHA para alpha funcionar)
        sombra_size = raio_icone * 2 + 10
        sombra_icone = pygame.Surface((sombra_size, sombra_size), pygame.SRCALPHA)
        desenhar_circulo_suave(sombra_icone, (0, 0, 0, 100),
                               (sombra_size // 2 + 3, sombra_size // 2 + 4),
                               raio_icone)
        tela.blit(sombra_icone, (ix - sombra_size // 2,
                                 iy - sombra_size // 2))
        # circulo de fundo
        desenhar_circulo_suave(tela, icone_cor, (ix, iy), raio_icone)
        # contorno preto
        desenhar_circulo_suave(tela, (0, 0, 0), (ix, iy), raio_icone, 3)
        # brilho interno (em surface SRCALPHA)
        hl_size = raio_icone * 2 + 10
        hl_icone = pygame.Surface((hl_size, hl_size), pygame.SRCALPHA)
        desenhar_circulo_suave(hl_icone, (255, 255, 255, 80),
                               (hl_size // 2 - raio_icone // 4,
                                hl_size // 2 - raio_icone // 4),
                               raio_icone // 3)
        tela.blit(hl_icone, (ix - hl_size // 2, iy - hl_size // 2))
        # exclamacao
        retangulo_suave(tela, BRANCO,
                         pygame.Rect(ix - 2, iy - l.px(10), 5, l.px(12)), 2)
        desenhar_circulo_suave(tela, BRANCO, (ix, iy + l.px(7)), 3)

        # titulo com sombra cartoon
        titulo_fonte = fonte_titulo
        # sombra
        sombra_surf = titulo_fonte.render(self.titulo, True, (0, 0, 0))
        sombra_surf.set_alpha(int(160 * p))
        tela.blit(sombra_surf, sombra_surf.get_rect(
            center=(rect.centerx + 3, rect.y + l.px(100) + 3)))
        # titulo
        titulo_surf = titulo_fonte.render(self.titulo, True,
                                          tema["primaria"])
        titulo_surf.set_alpha(alfa)
        tela.blit(titulo_surf, titulo_surf.get_rect(
            center=(rect.centerx, rect.y + l.px(100))))

        # mensagem (quebrada em linhas)
        palavras = self.mensagem.split()
        linhas, atual = [], []
        for palavra in palavras:
            teste = " ".join(atual + [palavra])
            if fonte_texto.size(teste)[0] > self._largura - l.px(70):
                linhas.append(" ".join(atual))
                atual = [palavra]
            else:
                atual.append(palavra)
        if atual:
            linhas.append(" ".join(atual))
        y_texto = rect.y + l.px(136)
        for linha in linhas:
            # sombra
            sombra = fonte_texto.render(linha, True, (0, 0, 0))
            sombra.set_alpha(int(120 * p))
            tela.blit(sombra, sombra.get_rect(
                center=(rect.centerx + 2, y_texto + 2)))
            # texto
            surface = fonte_texto.render(linha, True, (220, 225, 250))
            surface.set_alpha(alfa)
            tela.blit(surface, surface.get_rect(center=(rect.centerx,
                                                        y_texto)))
            y_texto += l.px(32)

        # botoes cartoon (bolha)
        confirmar, cancelar = self._retangulos()
        hover_conf = confirmar.collidepoint(mouse_pos)
        hover_canc = cancelar.collidepoint(mouse_pos)
        self._desenhar_botao_cartoon(tela, confirmar, "SIM, TENHO!",
                                     fonte_texto, (30, 160, 80), (20, 120, 60),
                                     hover_conf, alfa, l, p)
        self._desenhar_botao_cartoon(tela, cancelar, "CANCELAR",
                                     fonte_texto, (180, 40, 50), (130, 25, 30),
                                     hover_canc, alfa, l, p)

        # dica de teclado com visual cartoon
        dica = texto_suave(fonte_texto,
                           "ENTER confirmar   |   ESC cancelar",
                           (170, 175, 210), glow_cor=(40, 40, 80),
                           glow_raio=2)
        dica.set_alpha(int(210 * p))
        tela.blit(dica, dica.get_rect(center=(rect.centerx,
                                              rect.bottom - l.px(22))))

    def _desenhar_botao_cartoon(self, tela, rect, texto, fonte, cor_fundo,
                                cor_borda, hover, alfa, l, p=1.0):
        """Botoes 'bolha' cartoon com sombra, borda grossa e brilho no hover."""
        # sombra deslocada
        sombra_rect = pygame.Rect(rect.x + 3, rect.y + 4, rect.w, rect.h)
        sombra = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        retangulo_suave(sombra, (0, 0, 0, 100),
                         pygame.Rect(0, 0, rect.w, rect.h), rect.h // 2)
        tela.blit(sombra, sombra_rect.topleft)

        # glow no hover
        if hover:
            desenhar_glow(tela, cor_fundo, rect.center,
                          max(rect.w, rect.h) // 2, 0.5)

        # fundo do botao
        cor = tuple(min(255, c + 25) for c in cor_fundo) if hover else cor_fundo
        fundo = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        retangulo_suave(fundo, tuple(cor[:3]) + (int(240 * p),),
                         pygame.Rect(0, 0, rect.w, rect.h), rect.h // 2)
        tela.blit(fundo, rect.topleft)

        # borda preta grossa
        retangulo_suave(tela, (0, 0, 0), rect, rect.h // 2, 4)
        # borda colorida
        retangulo_suave(tela, cor_borda, rect, rect.h // 2, 2)

        # highlight interno
        hl = pygame.Surface((rect.w - 12, rect.h // 3), pygame.SRCALPHA)
        for i in range(rect.h // 5):
            t_hl = i / (rect.h // 5)
            a = int(40 * (1 - t_hl))
            retangulo_suave(hl, (255, 255, 255, a),
                             pygame.Rect(0, i, rect.w - 12, 1), 1)
        tela.blit(hl, (rect.x + 6, rect.y + 4))

        # texto com sombra
        txt = fonte.render(texto, True, (255, 255, 255))
        txt.set_alpha(int(255 * alfa))
        sombra_txt = fonte.render(texto, True, (0, 0, 0))
        sombra_txt.set_alpha(int(140 * alfa))
        tx = rect.centerx - txt.get_width() // 2
        ty = rect.centery - txt.get_height() // 2
        tela.blit(sombra_txt, (tx + 2, ty + 2))
        tela.blit(txt, (tx, ty))


class TransicaoTela:
    """Fade suave de entrada/saida entre telas."""

    def __init__(self, duracao=450, layout=None):
        self._layout = layout or Layout()
        self.duracao = duracao
        self.ativo = False
        self.inicio = 0
        self.alpha = 0

    def iniciar(self):
        self.ativo = True
        self.inicio = pygame.time.get_ticks()

    def atualizar(self):
        if self.ativo:
            progresso = (pygame.time.get_ticks() - self.inicio) / self.duracao
            if progresso >= 1:
                self.ativo = False
                self.alpha = 0
            else:
                self.alpha = int(255 * abs(math.sin(progresso * math.pi)))

    def desenhar(self, tela):
        if self.ativo and self.alpha > 0:
            overlay = pygame.Surface((self._layout.largura,
                                      self._layout.altura))
            overlay.fill(NEGRO)
            overlay.set_alpha(self.alpha)
            tela.blit(overlay, (0, 0))


class MenuPrincipal:
    """Controla todas as telas do menu (menu, continuar, loja, recordes,
    config) com identidade visual cinematografica e HUD diegetico."""

    def __init__(self, jogo, layout=None):
        self.jogo = jogo
        self.layout = layout or Layout()
        self.subestado = "MENU"
        self.fundo = FundoCinematico(self.layout)
        self.hud = HudMenu(self.layout)
        self.nave = NaveMenu()
        self.destaque = DestaqueMenu(self.layout)
        self.notificacoes = SistemaNotificacao(self.layout)
        self.dialogo = None
        self.transicao = TransicaoTela(layout=self.layout)
        self.transicao_missao = TransicaoMissao(layout=self.layout)
        self.alpha_entrada = 0
        self.mouse = (0, 0)

        self.fonte_logo = self.layout.fonte_titulo(64)
        self.fonte_sub = self.layout.fonte_texto(44)
        self.fonte_legenda = self.layout.fonte_texto(20)
        self.fonte_opcao = self.layout.fonte_titulo(27)
        self.fonte_opcao_sel = self.layout.fonte_titulo(32)
        self.fonte_media = self.layout.fonte_texto(26)
        self.fonte_pequena = self.layout.fonte_texto(20)
        self.fonte_cabecalho = self.layout.fonte_titulo(38)

        # layout ancorado: coluna de opcoes e cabecalhos derivados da
        # proporcao da tela interna (container), nao de pixels fixos
        self.x_opcoes = self.layout.x(0.61)
        self.opcao_selecionada = 0
        self.opcoes = []
        self._construir_opcoes_menu()

        self.entrada_t = 0.0
        self.entrada_total = 1.3
        self._titulo_cache = {}
        self._bloco_logo_cache = {}
        self._cabecalho_cache = {}
        self._cache_espacado = {}

        self.continuar_selecao = 0
        self.loja_selecao = 0
        self.preview_skin = None
        self.config_selecao = 0
        self.config_submodo = None
        self.controle_selecao = 0
        self.remapando = None
        self.resolucao_selecao = 0
        self.resolucao_scroll = 0
        self.config_scroll = 0
        self.ajuste_snapshot = (1.0, 0, 0)
        self.sub_anim = 0.0
        self.sub_anim_total = 0.9
        self.preview_anim = 0.0
        self.tela_principal = TelaPrincipalJogo(self)
        self.tela_continuar = TelaContinuarJogo(self)
        self.tela_recordes = TelaRecordesJogo(self)
        self.tela_loja = TelaLojaJogo(self)
        self.tela_configuracoes = TelaConfiguracoesJogo(self)
        self.telas = {
            "MENU": TelaPrincipal(self),
            "CONTINUAR": TelaContinuar(self),
            "LOJA": TelaLoja(self),
            "RECORDES": TelaRecordes(self),
            "CONFIG": TelaConfiguracoes(self),
        }
        self.phase_screen = PhaseSelectScreen(jogo, layout=self.layout)

    # ------------------------------------------------------------------ fontes

    def _recriar_fontes(self):
        """Recria todas as fontes com base no layout atual."""
        self.fonte_logo = self.layout.fonte_titulo(64)
        self.fonte_sub = self.layout.fonte_texto(44)
        self.fonte_legenda = self.layout.fonte_texto(20)
        self.fonte_opcao = self.layout.fonte_titulo(27)
        self.fonte_opcao_sel = self.layout.fonte_titulo(32)
        self.fonte_media = self.layout.fonte_texto(26)
        self.fonte_pequena = self.layout.fonte_texto(20)
        self.fonte_cabecalho = self.layout.fonte_titulo(38)
        self.x_opcoes = self.layout.x(0.61)
        self._titulo_cache.clear()
        self._bloco_logo_cache.clear()
        self._cabecalho_cache.clear()
        self._cache_espacado.clear()
        self.phase_screen.set_layout(self.layout)

    # ------------------------------------------------------------------ sons

    def _som(self, nome):
        self.jogo.sons.tocar(nome)

    # --------------------------------------------------------------- opcoes

    def _construir_opcoes_menu(self):
        itens = [
            ("01 // CONTINUAR", self._abrir_continuar),
            ("02 // LOBBY", self._abrir_lobby),
            ("03 // HANGAR", self._abrir_loja),
            ("04 // RECORDES", self._abrir_recordes),
            ("05 // CONFIGURAÇÕES", self._abrir_config),
            ("06 // SAIR", self._sair),
        ]
        # ancora a coluna alinhada a esquerda: nunca deixa o texto mais longo
        # estourar a borda direita da tela (usa a fonte da opcao selecionada)
        largura_max = max(self.fonte_opcao_sel.size(texto)[0]
                          for texto, _ in itens)
        x_max = self.layout.largura - largura_max - self.layout.px(24)
        self.x_opcoes = min(self.layout.x(0.61), x_max)
        y = self.layout.px(180)
        self.opcoes = []
        for texto, funcao in itens:
            self.opcoes.append(OpcaoMenu(texto, y, funcao))
            y += self.layout.px(58)
        self.opcao_selecionada = 0
        self.destaque.y = self.opcoes[0].y
        self.destaque.alvo = self.opcoes[0].y

    def _selecionar(self, indice):
        """Muda a selecao atual com som e pulsar no destaque."""
        if indice == self.opcao_selecionada:
            return
        self.opcao_selecionada = indice
        self.destaque.alvo = self.opcoes[indice].y
        self.destaque.pulsar()
        self._som("navegar")

    def _iniciar_missao(self, acao):
        """Inicia uma missao passando pela transicao cinematografica."""
        self._som("navegar")
        self.transicao_missao.iniciar(acao)

    def _abrir_continuar(self):
        self._som("navegar")
        self.continuar_selecao = 0
        self.sub_anim = 0.0
        self.subestado = "CONTINUAR"
        self.transicao.iniciar()

    def _abrir_lobby(self):
        """Abre o Lobby na fase salva, sem reiniciar a campanha."""
        self._abrir_fases()

    def _abrir_fases(self, nova_campanha=False):
        """Abre o lobby de fases sem alterar o save antes da confirmacao."""
        self._som("navegar")
        if nova_campanha:
            self.phase_screen.iniciar_nova_campanha()
        else:
            self.phase_screen.refresh()
        self.subestado = "FASES"
        self.sub_anim = 0.0
        self.transicao.iniciar()

    def _abrir_loja(self):
        self._som("navegar")
        self.loja_selecao = self._indice_skin_atual()
        self.preview_skin = None
        self.preview_anim = 0.0
        self.sub_anim = 0.0
        self.subestado = "LOJA"
        self.transicao.iniciar()

    def _abrir_recordes(self):
        self._som("navegar")
        self.jogo.recordes = SistemaProgressao.carregar_recordes()
        self.sub_anim = 0.0
        self.subestado = "RECORDES"
        self.transicao.iniciar()

    def _abrir_config(self):
        self._som("navegar")
        self.config_selecao = 0
        self.config_submodo = None
        self.remapando = None
        self.resolucao_selecao = 0
        self.resolucao_scroll = 0
        self.config_scroll = 0
        self.sub_anim = 0.0
        self.subestado = "CONFIG"
        self.transicao.iniciar()

    def _sair(self):
        self._som("navegar")
        self._mostrar_dialogo(
            "Sair do Jogo", "Tem certeza que deseja sair?",
            self._confirmar_sair, lambda: None)

    def _confirmar_sair(self):
        self.jogo._salvar_tudo()
        self.jogo.rodando = False

    def _voltar_menu(self):
        self.phase_screen.cancelar_nova_campanha()
        self._som("navegar")
        self.preview_skin = None
        self.preview_anim = 0.0
        self.config_submodo = None
        self.remapando = None
        self.resolucao_selecao = 0
        self.resolucao_scroll = 0
        self.config_scroll = 0
        self.sub_anim = 0.0
        self.subestado = "MENU"
        self.transicao.iniciar()
        self.entrada_t = 0.0

    def _mostrar_dialogo(self, titulo, mensagem, confirmar, cancelar):
        self.dialogo = Dialogo(titulo, mensagem, confirmar, cancelar,
                               self.layout)

    # ----------------------------------------------------------- continuar

    def _tem_save(self):
        return self.jogo.progresso.existe_save()

    def _acao_continuar(self, indice):
        if indice == 0:
            if self._tem_save():
                self._iniciar_missao(self.jogo._preparar_jogo)
            else:
                self._som("erro")
                self.notificacoes.adicionar("Nenhum save encontrado!", "erro")
        elif indice == 1:
            self._mostrar_dialogo(
                "Novo Jogo",
                "Isso apagara seu progresso (moedas, skins e recordes). "
                "Continuar?",
                self._resetar_e_jogar, lambda: None)
        else:
            self._voltar_menu()

    def _resetar_e_jogar(self):
        self.jogo.progresso.resetar_progresso()
        try:
            if os.path.exists(ARQUIVO_RECORDES):
                os.remove(ARQUIVO_RECORDES)
        except OSError as erro:
            LOGGER.warning("Nao foi possivel apagar os recordes: %s", erro)
        self.jogo.loja = LojaSkins()
        self.jogo.progresso.sincronizar_loja(self.jogo.loja)
        self.jogo.progresso.salvar_arquivo()
        self.jogo.recordes = []
        self.jogo.nome_jogador = "Jogador"
        self.notificacoes.adicionar("Progresso reiniciado!", "sucesso")
        self._som("comprar")
        self._iniciar_missao(self.jogo._preparar_jogo)

    def _botoes_continuar(self):
        l = self.layout
        largura = l.px(205)
        cx = l.x(0.5)
        x1 = cx - largura - l.px(15)
        x2 = cx + l.px(15)
        b0 = BotaoNeon("CONTINUAR",
                       (x1, l.altura - l.px(118), largura, l.px(48)))
        b1 = BotaoNeon("NOVO JOGO",
                       (x2, l.altura - l.px(118), largura, l.px(48)))
        b2 = BotaoNeon("VOLTAR",
                       (cx - l.px(90), l.altura - l.px(60), l.px(180),
                        l.px(42)))
        return [b0, b1, b2]

    def _painel_central(self, largura_design, altura_design, dy_design=0):
        """Container central (ancora CENTRO) a partir de px de design."""
        return self.layout.rect(CENTRO, largura_design / LARGURA_BASE,
                                altura_design / ALTURA_BASE, dy=dy_design)

    def _desenhar_continuar(self, tela):
        l = self.layout
        tema = tema_atual(self.jogo.config["tema"])
        self._cabecalho_sub_animado(tela, "CARREGANDO JOGO",
                                    tema["secundaria"])
        tem = self._tem_save()
        painel = self._painel_central(520, 330, -35)
        self._painel_sub(tela, painel, tema)
        self._detalhe_painel(tela, painel, tema, tema["secundaria"])
        jog = self.jogo.progresso.jogador
        titulo = ("PROGRESSO ENCONTRADO" if tem else "SEM PROGRESSO")
        cor = (150, 230, 120) if tem else (230, 120, 120)
        dx, dy, alfa = self._entrada_anim(self._frac_sub(0.14, 0.3),
                                          dy_design=-14)
        surface = self.fonte_media.render(titulo, True, cor)
        self._blit_alfa(tela, surface, surface.get_rect(
            center=(painel.centerx + dx, painel.y + l.px(28) + dy)),
            int(255 * alfa))
        if tem:
            skin = self.jogo.loja.pegar_skin(jog["skin_atual"])
            linhas = [
                ("Jogador", jog["nome"]),
                ("Nivel", str(jog["nivel_maximo"])),
                ("Pontos totais", formatar_pontos(jog["total_pontos"])),
                ("Bosses", str(jog["bosses_derrotados"])),
                ("Moedas", formatar_pontos(jog["moedas"])),
                ("Skin", skin.nome),
                ("Cenarios", f"{len(jog['cenarios_desbloqueados'])}/6"),
            ]
            y = painel.y + l.px(62)
            for i, (rotulo, valor) in enumerate(linhas):
                dx, dy, alfa = self._entrada_anim(
                    self._frac_sub(0.20 + i * 0.05, 0.35), dx_design=-30)
                surf_r = self.fonte_media.render(f"{rotulo}:", True,
                                                 (170, 175, 225))
                self._blit_alfa(tela, surf_r,
                                (painel.x + l.px(70) + dx, y + dy),
                                int(255 * alfa))
                surf_v = self.fonte_media.render(valor, True, BRANCO)
                self._blit_alfa(tela, surf_v, surf_v.get_rect(
                    midleft=(painel.x + l.px(250) + dx, y + l.px(9) + dy)),
                    int(255 * alfa))
                y += l.px(36)
        else:
            dx, dy, alfa = self._entrada_anim(self._frac_sub(0.2, 0.35),
                                              dx_design=-20)
            surface = self.fonte_media.render(
                "Nenhum progresso salvo ainda.", True, (200, 200, 240))
            self._blit_alfa(tela, surface, surface.get_rect(
                center=(painel.centerx + dx, painel.centery + dy)),
                int(255 * alfa))
        botoes = self._botoes_continuar()
        for i, botao in enumerate(botoes):
            botao.atualizar(self.mouse)
            self._desenhar_botao_entrada(
                tela, botao, self.fonte_media,
                self._frac_sub(0.55 + i * 0.06, 0.3))
        if self.continuar_selecao < 2:
            retangulo_suave(tela, (255, 200, 100),
                             botoes[self.continuar_selecao].rect, 10, 3)

    # --------------------------------------------------------------- loja

    def _indice_skin_atual(self):
        for i, skin in enumerate(self.jogo.loja.skins):
            if skin.id == self.jogo.loja.skin_atual:
                return i
        return 0

    def _rects_loja(self):
        l = self.layout
        colunas, celula = 4, l.px(205)
        x_inicio = (l.largura - colunas * celula) // 2
        y_inicio = l.px(122)
        return [pygame.Rect(x_inicio + (i % colunas) * celula,
                            y_inicio + (i // colunas) * l.px(150),
                            celula - l.px(10), l.px(138))
                for i in range(len(self.jogo.loja.skins))]

    def _botoes_loja(self):
        l = self.layout
        nomes = ["COMPRAR", "EQUIPAR", "PRÉVIA", "VOLTAR"]
        largura, espaco = l.px(140), l.px(18)
        total = largura * 4 + espaco * 3
        x = (l.largura - total) // 2
        y = l.altura - l.px(94)
        return {nome.lower(): BotaoNeon(nome, (x + i * (largura + espaco),
                                               y, largura, l.px(46)))
                for i, nome in enumerate(nomes)}

    def _desenhar_preview_skin(self, tela, skin, x, y):
        prev = Jogador(skin=skin)
        prev.x, prev.y = x, y
        prev.tilt = 0
        prev.invencivel = 0
        prev.desenhar(tela, None)

    def _desenhar_loja(self, tela):
        l = self.layout
        tema = tema_atual(self.jogo.config["tema"])
        self._cabecalho_sub_animado(tela, "LOJA DE VISUAIS", tema["primaria"])
        dx, dy, alfa = self._entrada_anim(self._frac_sub(0.06, 0.3),
                                          dx_design=-16)
        surface = self.fonte_media.render(
            f"Moedas: {formatar_pontos(self.jogo.loja.moedas)}", True,
            DOURADO)
        self._blit_alfa(tela, surface, (l.px(20) + dx, l.px(30) + dy),
                        int(255 * alfa))
        skin_atual = self.jogo.loja.pegar_skin(self.jogo.loja.skin_atual)
        surface = self.fonte_media.render(
            f"Skin atual: {skin_atual.nome}", True, tema["secundaria"])
        self._blit_alfa(tela, surface, surface.get_rect(
            topright=(l.largura - l.px(20) - dx, l.px(30) + dy)),
            int(255 * alfa))

        n_skin = len(self.jogo.loja.skins)
        desbloqueadas = len(self.jogo.loja.lista_desbloqueadas())
        surface = self.fonte_pequena.render(
            f"{desbloqueadas}/{n_skin} skins desbloqueadas", True,
            (150, 155, 200))
        self._blit_alfa(tela, surface, surface.get_rect(
            topright=(l.largura - l.px(20), l.px(56))), int(255 * alfa))

        rects = self._rects_loja()
        for i, skin in enumerate(self.jogo.loja.skins):
            p = self._frac_sub(0.16 + (i % 4) * 0.05 + (i // 4) * 0.09, 0.35)
            self._desenhar_cartao_skin(
                tela, rects[i], skin, i == self.loja_selecao,
                rects[i].collidepoint(self.mouse), tema, p)

        botoes = self._botoes_loja()
        for i, (nome, botao) in enumerate(botoes.items()):
            botao.atualizar(self.mouse)
            self._desenhar_botao_entrada(
                tela, botao, self.fonte_media, self._frac_sub(0.6 + i * 0.05,
                                                              0.25))
        skin = self.jogo.loja.skins[self.loja_selecao]
        dx, dy, alfa = self._entrada_anim(self._frac_sub(0.62, 0.25),
                                          dy_design=16)
        surface = self.fonte_pequena.render(skin.descricao, True,
                                            (170, 175, 220))
        self._blit_alfa(tela, surface, surface.get_rect(
            center=(l.x(0.5) + dx, l.altura - l.px(36) + dy)),
            int(255 * alfa))

        if self.preview_skin:
            self._desenhar_preview_overlay(tela)

    def _desenhar_cartao_skin(self, tela, rect, skin, selecionada, hover,
                              tema, p):
        """Card de skin com entrada animada (fade + slide)."""
        l = self.layout
        if p <= 0:
            return
        alfa = ease_out(p)
        dy = int((1 - alfa) * l.px(30))
        fundo = (52, 46, 92) if selecionada else (36, 34, 62) if hover \
            else (28, 27, 50)
        borda = (255, 190, 90) if selecionada else tema["secundaria"] \
            if hover else tema["borda_fraco"]
        if p >= 1:
            self._renderizar_cartao_skin(tela, rect, skin, fundo, borda)
            return
        off = pygame.Surface((rect.w + l.px(24), rect.h + l.px(24)),
                             pygame.SRCALPHA)
        local = pygame.Rect(l.px(12), l.px(12), rect.w, rect.h)
        self._renderizar_cartao_skin(off, local, skin, fundo, borda)
        off.set_alpha(int(255 * alfa))
        tela.blit(off, (rect.x - l.px(12), rect.y - l.px(12) + dy))

    def _renderizar_cartao_skin(self, tela, rect, skin, fundo, borda):
        """Desenha o conteudo de um card de skin num rect (tela ou offscreen)."""
        l = self.layout
        tem_alpha = bool(tela.get_flags() & pygame.SRCALPHA)
        if tem_alpha:
            desenhar_glow(tela, borda, rect.center, max(rect.w, rect.h) // 2,
                          0.4)
            retangulo_suave(tela, fundo + (255,), rect, 10)
            retangulo_suave(tela, borda + (255,), rect, 10, 2)
        else:
            retangulo_suave(tela, fundo, rect, 10,
                            glow_cor=borda, glow_raio=10)
            retangulo_suave(tela, borda, rect, 10, 2)
        if skin.id == self.jogo.loja.skin_atual:
            desenhar_cantos(tela, borda, rect, tamanho=l.px(8),
                            espessura=l.px(2))
        self._desenhar_preview_skin(tela, skin, rect.centerx,
                                    rect.y + l.px(62))
        surface = self.fonte_pequena.render(skin.nome, True, BRANCO)
        tela.blit(surface, surface.get_rect(center=(rect.centerx,
                                                    rect.y + l.px(18))))
        if skin.desbloqueada:
            status = ("EQUIPADA" if skin.id == self.jogo.loja.skin_atual
                      else "DESBLOQ.")
            cor = CIANO if skin.id == self.jogo.loja.skin_atual else VERDE
        else:
            status = f"{formatar_pontos(skin.preco)} pts"
            cor = DOURADO
        surface = self.fonte_pequena.render(status, True, cor)
        tela.blit(surface, surface.get_rect(center=(rect.centerx,
                                                    rect.y + l.px(122))))

    def _desenhar_preview_overlay(self, tela):
        l = self.layout
        tema = tema_atual(self.jogo.config["tema"])
        p = self._frac_preview(0.0, 0.3)
        if p <= 0:
            return
        overlay = pygame.Surface((l.largura, l.altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(195 * ease_out(p))))
        tela.blit(overlay, (0, 0))
        skin = self.preview_skin
        self._cabecalho_sub_animado(
            tela, skin.nome.upper(), (170, 120, 255), y=128,
            p=self._frac_preview(0.08, 0.3))
        cx, cy = l.x(0.5), l.y(0.5) - l.px(60)
        self._desenhar_nave_escala(tela, skin, cx, cy, 1.25,
                                   self._frac_preview(0.12, 0.4))
        dx, dy, alfa = self._entrada_anim(self._frac_preview(0.32, 0.3),
                                          dy_design=16)
        surface = self.fonte_media.render(skin.descricao, True,
                                          (200, 205, 240))
        self._blit_alfa(tela, surface, surface.get_rect(
            center=(cx + dx, l.y(0.5) + l.px(90) + dy)), int(255 * alfa))
        if skin.id == self.jogo.loja.skin_atual:
            status, cor = "Equipada", tema["secundaria"]
        elif skin.desbloqueada:
            status, cor = "Desbloqueada", VERDE
        else:
            status, cor = f"Preco: {formatar_pontos(skin.preco)} pts", DOURADO
        surface = self.fonte_media.render(status, True, cor)
        self._blit_alfa(tela, surface, surface.get_rect(
            center=(cx + dx, l.y(0.5) + l.px(130) + dy)), int(255 * alfa))
        botoes = {"equipar": BotaoNeon("EQUIPAR", (l.x(0.5) - l.px(170),
                                                   l.altura - l.px(120),
                                                   l.px(160), l.px(48))),
                  "fechar": BotaoNeon("FECHAR", (l.x(0.5) + l.px(10),
                                                 l.altura - l.px(120),
                                                 l.px(160), l.px(48)))}
        for i, botao in enumerate(botoes.values()):
            botao.atualizar(self.mouse)
            self._desenhar_botao_entrada(
                tela, botao, self.fonte_media,
                self._frac_preview(0.44 + i * 0.06, 0.25))

    def _acao_botao_loja(self, nome):
        loja = self.jogo.loja
        skin = loja.skins[self.loja_selecao]
        if nome == "comprar":
            if skin.desbloqueada:
                self.notificacoes.adicionar("Skin ja desbloqueada!", "info")
                self._som("erro")
            else:
                sucesso, _ = loja.comprar_skin(self.loja_selecao)
                if sucesso:
                    self.notificacoes.adicionar(
                        f"Skin {skin.nome} comprada!", "sucesso")
                    self._som("comprar")
                else:
                    self.notificacoes.adicionar("Moedas insuficientes!", "erro")
                    self._som("erro")
                self.jogo._salvar_tudo()
        elif nome == "equipar":
            if skin.desbloqueada:
                loja.equipar_skin(self.loja_selecao)
                self.notificacoes.adicionar(
                    f"Skin {skin.nome} equipada!", "sucesso")
                self._som("equipar")
                self.jogo._salvar_tudo()
            else:
                self.notificacoes.adicionar(
                    "Compre a skin antes de equipar!", "info")
                self._som("erro")
        elif nome == "preview":
            self.preview_skin = skin
            self.preview_anim = 0.0
            self._som("navegar")
        elif nome == "voltar":
            self._voltar_menu()

    def _acao_loja_principal(self):
        skin = self.jogo.loja.skins[self.loja_selecao]
        if not skin.desbloqueada:
            self._acao_botao_loja("comprar")
        elif skin.id == self.jogo.loja.skin_atual:
            self._acao_botao_loja("preview")
        else:
            self._acao_botao_loja("equipar")

    # ------------------------------------------------------------- recordes

    def _botao_voltar(self):
        l = self.layout
        return BotaoNeon("VOLTAR", (l.x(0.5) - l.px(90), l.altura - l.px(64),
                                    l.px(180), l.px(46)))

    def _desenhar_recordes(self, tela):
        l = self.layout
        tema = tema_atual(self.jogo.config["tema"])
        self._cabecalho_sub_animado(tela, "RECORDES", tema["secundaria"])
        lista = self.jogo.recordes
        painel = self._painel_central(520, 330, -35)
        self._painel_sub(tela, painel, tema)
        self._detalhe_painel(tela, painel, tema, DOURADO)
        dx, dy, alfa = self._entrada_anim(self._frac_sub(0.12, 0.3),
                                          dy_design=-10)
        surface = self.fonte_media.render("5 MELHORES", True, tema["secundaria"])
        self._blit_alfa(tela, surface, surface.get_rect(
            center=(painel.centerx + dx, painel.y + l.px(28) + dy)),
            int(255 * alfa))
        if not lista:
            dx, dy, alfa = self._entrada_anim(self._frac_sub(0.2, 0.35),
                                              dx_design=-18)
            surface = self.fonte_media.render(
                "Nenhum recorde ainda.", True, (200, 205, 240))
            self._blit_alfa(tela, surface, surface.get_rect(
                center=(painel.centerx + dx, painel.centery + dy)),
                int(255 * alfa))
        else:
            y = painel.y + l.px(70)
            for i, reg in enumerate(lista[:5]):
                p = self._frac_sub(0.2 + i * 0.06, 0.35)
                dx, dy, alfa = self._entrada_anim(p, dx_design=-40)
                cor = DOURADO if i == 0 else (205, 210, 235) if i < 3 \
                    else (150, 155, 190)
                texto = (f"MELHOR {i + 1}. {reg['nome']}  "
                         f"{formatar_pontos(reg['pontos'])} pts  "
                         f"(Nivel {reg['nivel']})")
                surface = self.fonte_media.render(texto, True, cor)
                self._blit_alfa(tela, surface, surface.get_rect(
                    center=(painel.centerx + dx, y + dy)), int(255 * alfa))
                y += l.px(52)

        jog = self.jogo.progresso.jogador
        estatisticas = self.jogo.progresso.dados["estatisticas"]
        melhor = formatar_pontos(lista[0]["pontos"]) if lista else "0"
        linha = (f"Seu melhor: {melhor} pts  |  "
                 f"Skins: {len(self.jogo.loja.lista_desbloqueadas())}/10  |  "
                 f"Inimigos: {estatisticas['inimigos_derrotados']}  |  "
                 f"Bosses: {jog['bosses_derrotados']}")
        dx, dy, alfa = self._entrada_anim(self._frac_sub(0.55, 0.3),
                                          dy_design=16)
        surface = self.fonte_media.render(linha, True, (170, 175, 220))
        self._blit_alfa(tela, surface, surface.get_rect(
            center=(l.x(0.5) + dx, l.y(0.72) + dy)), int(255 * alfa))

        botao = self._botao_voltar()
        botao.atualizar(self.mouse)
        self._desenhar_botao_entrada(tela, botao, self.fonte_media,
                                     self._frac_sub(0.6, 0.25))

    # ------------------------------------------------------------ configuracoes

    def _linhas_config(self):
        return [
            ("Musica", "slider"),
            ("Efeitos", "slider"),
            ("Resolucao", "resolucao"),
            ("Tela Cheia", "toggle"),
            ("Sensibilidade", "slider"),
            ("Controles", "controles"),
            ("Tema", "tema"),
            ("Aspecto", "aspecto"),
            ("Ajustar Tela", "ajuste"),
        ]

    _CONFIG_VISIVEIS = 6

    def _config_visiveis(self):
        """Janela (inicio, fim) das linhas visiveis no menu de config."""
        inicio = max(0, min(self.config_scroll,
                            len(self._linhas_config()) - self._CONFIG_VISIVEIS))
        fim = min(len(self._linhas_config()), inicio + self._CONFIG_VISIVEIS)
        return inicio, fim

    def _rolar_config(self, selecao):
        inicio, fim = self._config_visiveis()
        if selecao < inicio:
            self.config_scroll = selecao
        elif selecao >= fim:
            self.config_scroll = selecao - self._CONFIG_VISIVEIS + 1
        else:
            self.config_scroll = inicio

    def _y_linha_config(self, indice):
        return self.layout.px(172) + indice * self.layout.px(54)

    def _track_slider(self):
        """Posicoes x da trilha do slider (proporcionais a superficie)."""
        _, _, inicio, fim, _ = self._grade_config()
        return inicio, fim

    def _grade_config(self):
        """Retorna a grade horizontal centralizada da tela de configuracoes.

        Os cinco pontos mantem rótulos, controles, porcentagens e o indicador
        de selecao alinhados ao painel, independentemente da resolucao.  Isso
        evita que a grade fique deslocada quando o painel e redimensionado.
        """
        painel = self._painel_config()
        l = self.layout
        inicio_controle = painel.centerx
        fim_slider = painel.centerx + l.px(200)
        return (
            painel.centerx - l.px(235),  # inicio justificado dos rotulos
            painel.centerx - l.px(260),  # indicador da linha selecionada
            inicio_controle,
            fim_slider,
            fim_slider + l.px(20),  # percentual do slider
        )

    def _desenhar_slider(self, tela, y, fracao):
        l = self.layout
        x0, x1 = self._track_slider()
        track = pygame.Rect(x0, y - l.px(5), x1 - x0, l.px(12))
        retangulo_suave(tela, (40, 40, 70), track, 6)
        preenchido = int((x1 - x0) * max(0.0, min(1.0, fracao)))
        retangulo_suave(tela, CIANO,
                        pygame.Rect(x0, y - l.px(5), preenchido, l.px(12)), 6,
                        glow_cor=CIANO, glow_raio=8)
        retangulo_suave(tela, BRANCO, track, 6, 1)
        desenhar_circulo_suave(tela, BRANCO, (x0 + preenchido, y), l.px(8),
                               brilho=1.3)

    def _slider_fracao(self, mouse_x):
        x0, x1 = self._track_slider()
        return max(0.0, min(1.0, (mouse_x - x0) / (x1 - x0)))

    def _desenhar_toggle(self, tela, x, y, ligado):
        l = self.layout
        off = pygame.Rect(x, y - l.px(11), l.px(54), l.px(24))
        cor = (50, 100, 60) if ligado else (80, 40, 40)
        retangulo_suave(tela, cor, off, 12, glow_cor=cor if ligado else None,
                        glow_raio=8 if ligado else 0)
        retangulo_suave(tela, BRANCO, off, 12, 1)
        cx = x + (l.px(44) if ligado else l.px(10))
        desenhar_circulo_suave(tela, BRANCO, (cx, y), l.px(10), brilho=1.3)

    def _set_musica(self, valor):
        self.jogo.config["musica_volume"] = round(valor, 2)
        self.jogo.sons.set_volume_musica(valor)
        self.jogo.config.salvar()

    def _set_efeitos(self, valor):
        self.jogo.config["efeitos_volume"] = round(valor, 2)
        self.jogo.sons.set_volume_efeitos(valor)
        self.jogo.config.salvar()

    def _set_sensibilidade(self, valor):
        self.jogo.config["sensibilidade"] = round(valor, 2)
        self.jogo.config.salvar()

    def _ciclar_resolucao(self, delta=1):
        atual = self.jogo.config["resolucao"]
        indice = RESOLUCOES.index(atual) if atual in RESOLUCOES else 0
        indice = (indice + delta) % len(RESOLUCOES)
        self.jogo.config["resolucao"] = RESOLUCOES[indice]
        # A resolução escolhida representa o tamanho da janela. Forçar um
        # modo exclusivo menor que o monitor no Windows causa escala ruim;
        # portanto selecioná-la sai da tela cheia de forma explícita.
        self.jogo.config["tela_cheia"] = False
        self.jogo.config.salvar()
        self.jogo._aplicar_modo_video()
        self.notificacoes.adicionar(
            "Resolucao alterada: " + RESOLUCOES[indice], "info")

    def _toggle_tela_cheia(self):
        self.jogo.config["tela_cheia"] = not self.jogo.config["tela_cheia"]
        self.jogo.config.salvar()
        self.jogo._aplicar_modo_video()
        estado = "LIGADA" if self.jogo.config["tela_cheia"] else "DESLIGADA"
        self.notificacoes.adicionar(f"Tela cheia {estado}", "info")

    def _ciclar_tema(self, delta=1):
        atual = self.jogo.config["tema"]
        indice = TEMAS.index(atual) if atual in TEMAS else 0
        indice = (indice + delta) % len(TEMAS)
        self.jogo.config["tema"] = TEMAS[indice]
        self.jogo.config.salvar()

    def _aplicar_slider(self, indice, fracao):
        if indice == 0:
            self._set_musica(fracao)
        elif indice == 1:
            self._set_efeitos(fracao)
        elif indice == 4:
            self._set_sensibilidade(0.5 + fracao)
        self._som("navegar")

    def _ajustar_config(self, delta):
        indice = self.config_selecao
        if indice == 0:
            valor = self.jogo.config["musica_volume"] + delta * 0.05
            self._set_musica(max(0.0, min(1.0, valor)))
        elif indice == 1:
            valor = self.jogo.config["efeitos_volume"] + delta * 0.05
            self._set_efeitos(max(0.0, min(1.0, valor)))
        elif indice == 2:
            self._ciclar_resolucao(delta)
        elif indice == 3 and delta > 0:
            self._toggle_tela_cheia()
        elif indice == 4:
            valor = self.jogo.config["sensibilidade"] + delta * 0.05
            self._set_sensibilidade(max(0.5, min(1.5, valor)))
        elif indice == 6:
            self._ciclar_tema(delta)
        elif indice == 7:
            atual = self.jogo.config["aspecto"]
            self.jogo.config["aspecto"] = ("PREENCHE" if atual == "AJUSTAR"
                                           else "AJUSTAR")
            self.jogo.config.salvar()
        self._som("navegar")

    def _painel_controles(self):
        return self._painel_central(580, 420, -10)

    def _clique_config(self, pos):
        l = self.layout
        if self.remapando:
            return
        if self.config_submodo == "controles":
            painel = self._painel_controles()
            for i, acao in enumerate(ACOES_CONTROLE):
                rect = pygame.Rect(painel.x + l.px(30),
                                   painel.y + l.px(64) + i * l.px(48),
                                   painel.width - l.px(60), l.px(40))
                if rect.collidepoint(pos):
                    self.controle_selecao = i
                    self.remapando = acao
                    self._som("navegar")
                    return
            if pos[1] > l.altura - l.px(70):
                self.config_submodo = None
                self.sub_anim = 0.0
                self._som("navegar")
            return
        if self.config_submodo == "resolucao":
            self._clique_resolucao(pos)
            return

        linhas = self._linhas_config()
        inicio, fim = self._config_visiveis()
        for k in range(fim - inicio):
            i = inicio + k
            y = self._y_linha_config(k)
            if abs(pos[1] - y) < 24:
                self.config_selecao = i
                if i == 2:
                    self.config_submodo = "resolucao"
                    self.resolucao_selecao = self._indice_resolucao_atual()
                    self.sub_anim = 0.0
                    self._som("navegar")
                elif i == 3:
                    self._toggle_tela_cheia()
                elif i == 5:
                    self.config_submodo = "controles"
                    self.controle_selecao = 0
                    self.sub_anim = 0.0
                    self._som("navegar")
                elif i == 6:
                    self._ciclar_tema()
                elif i == 7:
                    self._ajustar_config(1)
                elif i == 8:
                    self._abrir_ajuste_tela()
                elif linhas[i][1] == "slider":
                    self._aplicar_slider(i, self._slider_fracao(pos[0]))
                return

        b_salvar = pygame.Rect(l.x(0.5) - l.px(190), l.altura - l.px(80),
                               l.px(180), l.px(44))
        b_voltar = pygame.Rect(l.x(0.5) + l.px(10), l.altura - l.px(80),
                               l.px(180), l.px(44))
        if b_salvar.collidepoint(pos):
            self.jogo.config.salvar()
            self.notificacoes.adicionar("Configuracoes salvas!", "sucesso")
            self._som("equipar")
        elif b_voltar.collidepoint(pos):
            self._voltar_menu()

    def _desenhar_controles(self, tela):
        l = self.layout
        tema = tema_atual(self.jogo.config["tema"])
        painel = self._painel_controles()
        self._painel_sub(tela, painel, tema)
        dx, dy, alfa = self._entrada_anim(self._frac_sub(0.06, 0.3),
                                          dy_design=-10)
        surface = self.fonte_media.render("CONTROLES", True,
                                          tema["secundaria"])
        self._blit_alfa(tela, surface, surface.get_rect(
            center=(painel.centerx + dx, painel.y + l.px(28) + dy)),
            int(255 * alfa))
        for i, acao in enumerate(ACOES_CONTROLE):
            p = self._frac_sub(0.14 + i * 0.06, 0.35)
            dx, dy, alfa = self._entrada_anim(p, dx_design=-26)
            y = painel.y + l.px(64) + i * l.px(48) + dy
            rect = pygame.Rect(painel.x + l.px(30) + dx, y,
                               painel.width - l.px(60), l.px(40))
            selecionado = (i == self.controle_selecao)
            if selecionado:
                retangulo_suave(tela, (50, 46, 90), rect, 8)
                retangulo_suave(tela, (255, 200, 100), rect, 8, 2)
            surface = self.fonte_media.render(acao.upper(), True, BRANCO)
            self._blit_alfa(tela, surface, (rect.x + l.px(14),
                                            rect.y + l.px(10)),
                            int(255 * alfa))
            tecla = self.jogo.config.controles.get(acao, 0)
            nome_tecla = pygame.key.name(tecla).upper() or "?"
            cor = DOURADO if selecionado else (170, 175, 220)
            surface = self.fonte_media.render(nome_tecla, True, cor)
            self._blit_alfa(tela, surface, surface.get_rect(
                midright=(rect.right - l.px(14), rect.centery)),
                int(255 * alfa))
        p = self._frac_sub(0.55, 0.25)
        dx, dy, alfa = self._entrada_anim(p, dy_design=14)
        surface = self.fonte_media.render(
            "ENTER: remapear   ESC: voltar", True, (150, 155, 200))
        self._blit_alfa(tela, surface, surface.get_rect(
            center=(l.x(0.5) + dx, l.altura - l.px(60) + dy)),
            int(255 * alfa))

    def _painel_resolucoes(self):
        return self._painel_central(430, 430, -10)

    def _indice_resolucao_atual(self):
        atual = self.jogo.config["resolucao"]
        return RESOLUCOES.index(atual) if atual in RESOLUCOES else 0

    def _resolucoes_visiveis(self):
        """Janela (inicio, fim) das resoluções visiveis no seletor."""
        inicio = max(0, min(self.resolucao_scroll,
                            len(RESOLUCOES) - 9))
        fim = min(len(RESOLUCOES), inicio + 9)
        return inicio, fim

    def _rolar_resolucao(self, selecao):
        """Mantém a selecao dentro da janela visivel (rolagem suave)."""
        inicio, fim = self._resolucoes_visiveis()
        if selecao < inicio:
            self.resolucao_scroll = selecao
        elif selecao >= fim:
            self.resolucao_scroll = selecao - 9 + 1
        else:
            self.resolucao_scroll = inicio

    def _clique_resolucao(self, pos):
        l = self.layout
        painel = self._painel_resolucoes()
        inicio, fim = self._resolucoes_visiveis()
        for k, i in enumerate(range(inicio, fim)):
            rect = pygame.Rect(painel.x + l.px(30),
                               painel.y + l.px(58) + k * l.px(42),
                               painel.width - l.px(60), l.px(36))
            if rect.collidepoint(pos):
                self.resolucao_selecao = i
                self._rolar_resolucao(i)
                self._aplicar_resolucao(i)
                return
        if pos[1] > l.altura - l.px(70):
            self.config_submodo = None
            self.sub_anim = 0.0
            self._som("navegar")

    def _aplicar_resolucao(self, indice):
        self.jogo.config["resolucao"] = RESOLUCOES[indice]
        self.jogo.config["tela_cheia"] = False
        self.jogo.config.salvar()
        self.jogo._aplicar_modo_video()
        self.notificacoes.adicionar(
            "Resolucao: " + RESOLUCOES[indice], "sucesso")
        self._som("equipar")

    def _desenhar_resolucoes(self, tela):
        l = self.layout
        tema = tema_atual(self.jogo.config["tema"])
        painel = self._painel_resolucoes()
        self._painel_sub(tela, painel, tema)
        self._detalhe_painel(tela, painel, tema, tema["secundaria"])
        dx, dy, alfa = self._entrada_anim(self._frac_sub(0.06, 0.3),
                                          dy_design=-10)
        surface = self.fonte_media.render("RESOLUCAO", True,
                                          tema["secundaria"])
        self._blit_alfa(tela, surface, surface.get_rect(
            center=(painel.centerx + dx, painel.y + l.px(28) + dy)),
            int(255 * alfa))
        inicio, fim = self._resolucoes_visiveis()
        for k, i in enumerate(range(inicio, fim)):
            resolucao = RESOLUCOES[i]
            p = self._frac_sub(0.12 + k * 0.04, 0.35)
            dx, dy, alfa = self._entrada_anim(p, dx_design=-22)
            y = painel.y + l.px(58) + k * l.px(42) + dy
            rect = pygame.Rect(painel.x + l.px(30) + dx, y,
                               painel.width - l.px(60), l.px(36))
            selecionada = (i == self.resolucao_selecao)
            if selecionada:
                retangulo_suave(tela, (50, 46, 90), rect, 8)
                retangulo_suave(tela, (255, 200, 100), rect, 8, 2)
            cor = BRANCO if selecionada else (185, 190, 230)
            surface = self.fonte_media.render(resolucao, True, cor)
            self._blit_alfa(tela, surface, surface.get_rect(
                center=(rect.centerx, rect.centery)), int(255 * alfa))
            if resolucao == self.jogo.config["resolucao"]:
                surface = self.fonte_pequena.render("ATUAL", True, VERDE)
                self._blit_alfa(tela, surface, surface.get_rect(
                    midright=(rect.right - l.px(10), rect.centery)),
                    int(255 * alfa))
        if len(RESOLUCOES) > 9:
            self._desenhar_indicador_rolagem(tela, painel, inicio, fim)
        p = self._frac_sub(0.5, 0.25)
        dx, dy, alfa = self._entrada_anim(p, dy_design=14)
        surface = self.fonte_media.render(
            "ENTER: aplicar   ESC: voltar", True, (150, 155, 200))
        self._blit_alfa(tela, surface, surface.get_rect(
            center=(l.x(0.5) + dx, l.altura - l.px(60) + dy)),
            int(255 * alfa))

    def _desenhar_indicador_rolagem(self, tela, painel, inicio, fim):
        """Barra de rolagem lateral do seletor de resolucao."""
        l = self.layout
        total = len(RESOLUCOES)
        y0 = painel.y + l.px(58)
        y1 = painel.y + l.px(58) + 9 * l.px(42)
        linha_suave(tela, (70, 70, 110), (painel.right - l.px(18), y0),
                    (painel.right - l.px(18), y1), 3)
        barra_h = max(l.px(24), int((y1 - y0) * 9 / total))
        frac = inicio / (total - 9)
        by = y0 + int((y1 - y0 - barra_h) * frac)
        cor = tema_atual(self.jogo.config["tema"])["secundaria"]
        desenhar_circulo_suave(tela, cor, (painel.right - l.px(18),
                                           by + barra_h // 2),
                               l.px(5), brilho=1.2)

    def _desenhar_remapando(self, tela):
        l = self.layout
        overlay = pygame.Surface((l.largura, l.altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 205))
        tela.blit(overlay, (0, 0))
        surface = self.fonte_sub.render(
            f"PRESSIONE UMA TECLA PARA {self.remapando.upper()}", True, BRANCO)
        surface.set_alpha(int(180 + 75 * math.sin(pygame.time.get_ticks() * 0.008)))
        tela.blit(surface, surface.get_rect(center=(l.x(0.5),
                                                    l.y(0.5) - l.px(30))))
        surface = self.fonte_media.render("ESC para cancelar", True,
                                          (160, 165, 205))
        tela.blit(surface, surface.get_rect(center=(l.x(0.5),
                                                    l.y(0.5) + l.px(20))))

    def _painel_config(self):
        return self._painel_central(620, 468, -16)

    def _abrir_ajuste_tela(self):
        """Abre a calibracao de tela guardando o estado atual (cancelar)."""
        cfg = self.jogo.config
        self.ajuste_snapshot = (cfg["ajuste_escala"], cfg["ajuste_off_x"],
                                cfg["ajuste_off_y"])
        self.config_submodo = "ajuste"
        self.sub_anim = 0.0
        self._som("navegar")

    def _frame_janela(self):
        """Rect (na superficie logica) da area visivel da janela.

        Projeta a janela atual de volta para a superficie interna usando a
        transformacao vigente (scale-to-fit + ajustes manuais), para desenhar
        a moldura de calibracao no local exato das bordas da imagem.
        """
        w, h = self.jogo.janela.get_size()
        cfg = self.jogo.config
        if cfg["aspecto"] == "PREENCHE":
            e = max(0.5, cfg["ajuste_escala"])
            sw = w * e
            sh = h * e
            vx0 = max(0, cfg["ajuste_off_x"])
            vx1 = min(sw, cfg["ajuste_off_x"] + w)
            vy0 = max(0, cfg["ajuste_off_y"])
            vy1 = min(sh, cfg["ajuste_off_y"] + h)
            if vx1 <= vx0 or vy1 <= vy0:
                return pygame.Rect(0, 0, self.layout.largura,
                                   self.layout.altura)
            return pygame.Rect(int(vx0 / sw * self.layout.largura),
                               int(vy0 / sh * self.layout.altura),
                               max(1, int((vx1 - vx0) / sw *
                                          self.layout.largura)),
                               max(1, int((vy1 - vy0) / sh *
                                          self.layout.altura)))
        escala, off_x, off_y = self.jogo._transformacao_janela()
        vw = w / escala
        vh = h / escala
        cx = (w / 2 - off_x) / escala
        cy = (h / 2 - off_y) / escala
        return pygame.Rect(int(cx - vw / 2), int(cy - vh / 2),
                           max(1, int(vw)), max(1, int(vh)))

    def _tecla_ajuste(self, evento):
        cfg = self.jogo.config
        if evento.key == pygame.K_LEFT:
            cfg["ajuste_off_x"] = max(-400, cfg["ajuste_off_x"] - 4)
        elif evento.key == pygame.K_RIGHT:
            cfg["ajuste_off_x"] = min(400, cfg["ajuste_off_x"] + 4)
        elif evento.key == pygame.K_UP:
            cfg["ajuste_off_y"] = max(-400, cfg["ajuste_off_y"] - 4)
        elif evento.key == pygame.K_DOWN:
            cfg["ajuste_off_y"] = min(400, cfg["ajuste_off_y"] + 4)
        elif evento.key in (pygame.K_w, pygame.K_PLUS, pygame.K_KP_PLUS):
            cfg["ajuste_escala"] = min(1.2, cfg["ajuste_escala"] + 0.01)
        elif evento.key in (pygame.K_s, pygame.K_MINUS, pygame.K_KP_MINUS):
            cfg["ajuste_escala"] = max(0.9, cfg["ajuste_escala"] - 0.01)
        elif evento.key == pygame.K_r:
            cfg["ajuste_escala"] = 1.0
            cfg["ajuste_off_x"] = 0
            cfg["ajuste_off_y"] = 0
            self.notificacoes.adicionar("Ajuste de tela resetado!", "info")
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            cfg.salvar()
            self.config_submodo = None
            self.sub_anim = 0.0
            self.notificacoes.adicionar("Ajuste de tela salvo!", "sucesso")
            self._som("equipar")
            return True
        elif evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            cfg["ajuste_escala"], cfg["ajuste_off_x"], cfg["ajuste_off_y"] = \
                self.ajuste_snapshot
            self.config_submodo = None
            self.sub_anim = 0.0
            self._som("navegar")
            return True
        else:
            return True
        self._som("navegar")
        return True

    def _desenhar_ajuste(self, tela):
        l = self.layout
        tema = tema_atual(self.jogo.config["tema"])
        p = self._frac_sub(0.0, 0.3)
        overlay = pygame.Surface((l.largura, l.altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(140 * ease_out(p))))
        tela.blit(overlay, (0, 0))
        self._cabecalho_sub_animado(tela, "AJUSTAR TELA", tema["primaria"],
                                    p=self._frac_sub(0.0, 0.35))
        frame = self._frame_janela()
        cor = tema["secundaria"]
        retangulo_suave(tela, cor, frame, 1, 1)
        desenhar_cantos(tela, cor, frame, tamanho=l.px(24), espessura=l.px(3))
        desenhar_circulo_suave(tela, cor, frame.center, l.px(5), brilho=1.3)
        linha_suave(tela, (90, 95, 130),
                    (frame.centerx - l.px(70), frame.centery),
                    (frame.centerx + l.px(70), frame.centery), 1)
        linha_suave(tela, (90, 95, 130),
                    (frame.centerx, frame.centery - l.px(70)),
                    (frame.centerx, frame.centery + l.px(70)), 1)

        cfg = self.jogo.config
        escala_pct = cfg["ajuste_escala"] * 100
        dx, dy, alfa = self._entrada_anim(self._frac_sub(0.15, 0.3),
                                          dy_design=16)
        surface = self.fonte_media.render(
            f"ESCALA {escala_pct:.0f}%   |   X {cfg['ajuste_off_x']:+.0f}   "
            f"|   Y {cfg['ajuste_off_y']:+.0f}", True, DOURADO)
        self._blit_alfa(tela, surface, surface.get_rect(
            center=(l.x(0.5) + dx, l.y(0.82) + dy)), int(255 * alfa))
        hint = ("SETAS: mover   |   W/S: zoom   |   R: reset   |   "
                "ENTER: salvar   |   ESC: cancelar")
        surface = self.fonte_pequena.render(hint, True, (150, 155, 200))
        self._blit_alfa(tela, surface, surface.get_rect(
            center=(l.x(0.5), l.altura - l.px(34))), int(255 * alfa))

    def _desenhar_indicador_config(self, tela, painel, inicio, fim):
        """Barra de rolagem lateral do menu de configuracoes."""
        l = self.layout
        linhas = self._linhas_config()
        total = len(linhas)
        y0 = painel.y + l.px(172)
        y1 = y0 + self._CONFIG_VISIVEIS * l.px(54)
        linha_suave(tela, (70, 70, 110), (painel.right - l.px(18), y0),
                    (painel.right - l.px(18), y1), 3)
        barra_h = max(l.px(20), int((y1 - y0) * self._CONFIG_VISIVEIS / total))
        frac = inicio / (total - self._CONFIG_VISIVEIS)
        by = y0 + int((y1 - y0 - barra_h) * frac)
        cor = tema_atual(self.jogo.config["tema"])["secundaria"]
        desenhar_circulo_suave(tela, cor, (painel.right - l.px(18),
                                           by + barra_h // 2),
                               l.px(5), brilho=1.2)

    def _desenhar_config(self, tela):
        l = self.layout
        tema = tema_atual(self.jogo.config["tema"])
        self._cabecalho_sub_animado(tela, "CONFIGURACOES", tema["primaria"])
        if self.remapando:
            self._desenhar_remapando(tela)
            return
        if self.config_submodo == "controles":
            self._desenhar_controles(tela)
            return
        if self.config_submodo == "resolucao":
            self._desenhar_resolucoes(tela)
            return
        if self.config_submodo == "ajuste":
            self._desenhar_ajuste(tela)
            return

        painel = self._painel_config()
        self._painel_sub(tela, painel, tema)
        self._detalhe_painel(tela, painel, tema, tema["secundaria"])

        linhas = self._linhas_config()
        inicio, fim = self._config_visiveis()
        for k in range(fim - inicio):
            i = inicio + k
            rotulo, tipo = linhas[i]
            p = self._frac_sub(0.12 + k * 0.05, 0.35)
            dx, dy, alfa = self._entrada_anim(p, dx_design=30, dy_design=18)
            y = self._y_linha_config(k) + dy
            selecionada = (i == self.config_selecao)
            cor = BRANCO if selecionada else (190, 195, 235)
            surface = self.fonte_media.render(rotulo, True, cor)
            self._blit_alfa(tela, surface, (l.px(190) + dx, y - l.px(12)),
                            int(255 * alfa))
            if selecionada:
                retangulo_suave(tela, (255, 200, 100),
                                 pygame.Rect(l.px(175) + dx, y - l.px(24),
                                             l.px(6), l.px(30)), 3)
            if tipo == "slider":
                if i == 4:
                    fracao = max(0.0, min(1.0,
                                          self.jogo.config["sensibilidade"]
                                          - 0.5))
                    percentual = int((0.5 + fracao) * 100)
                else:
                    chave = "musica_volume" if i == 0 else "efeitos_volume"
                    fracao = max(0.0, min(1.0, self.jogo.config[chave]))
                    percentual = int(fracao * 100)
                self._desenhar_slider(tela, y, fracao)
                surface = self.fonte_media.render(f"{percentual}%", True,
                                                  (170, 175, 220))
                self._blit_alfa(tela, surface,
                                (l.px(720) + dx, y - l.px(12)),
                                int(255 * alfa))
            elif tipo == "resolucao":
                surface = self.fonte_media.render(
                    self.jogo.config["resolucao"], True, tema["secundaria"])
                self._blit_alfa(tela, surface, surface.get_rect(
                    midleft=(l.px(420) + dx, y)), int(255 * alfa))
                surface = self.fonte_pequena.render("ESCOLHER >", True,
                                                    (200, 150, 255)
                                                    if selecionada else
                                                    (150, 155, 200))
                self._blit_alfa(tela, surface, surface.get_rect(
                    midleft=(l.px(540) + dx, y)), int(255 * alfa))
            elif tipo == "toggle":
                self._desenhar_toggle(tela, l.px(420) + dx, y,
                                      self.jogo.config["tela_cheia"])
                estado = self.jogo.config["tela_cheia"]
                surface = self.fonte_media.render(
                    "LIGADO" if estado else "DESLIGADO", True,
                    VERDE if estado else (160, 160, 190))
                self._blit_alfa(tela, surface, surface.get_rect(
                    midleft=(l.px(510) + dx, y)), int(255 * alfa))
            elif tipo == "controles":
                surface = self.fonte_media.render(
                    "PERSONALIZAR >", True,
                    (200, 150, 255) if selecionada else (150, 155, 200))
                self._blit_alfa(tela, surface, surface.get_rect(
                    midleft=(l.px(420) + dx, y)), int(255 * alfa))
            elif tipo == "tema":
                surface = self.fonte_media.render(
                    self.jogo.config["tema"], True, (255, 160, 200))
                self._blit_alfa(tela, surface, surface.get_rect(
                    midleft=(l.px(420) + dx, y)), int(255 * alfa))
            elif tipo == "aspecto":
                surface = self.fonte_media.render(
                    self.jogo.config["aspecto"], True, QUANTUM_CYAN)
                self._blit_alfa(tela, surface, surface.get_rect(
                    midleft=(l.px(420) + dx, y)), int(255 * alfa))
                dica = ("ÁREAS SEGURAS" if self.jogo.config["aspecto"] ==
                        "AJUSTAR" else "ESTICA A TELA")
                surface = self.fonte_pequena.render(dica, True,
                                                    (150, 155, 200))
                self._blit_alfa(tela, surface, surface.get_rect(
                    midleft=(l.px(520) + dx, y)), int(255 * alfa))
            elif tipo == "ajuste":
                escala_pct = int(self.jogo.config["ajuste_escala"] * 100)
                surface = self.fonte_media.render(
                    f"{escala_pct}%", True, tema["secundaria"])
                self._blit_alfa(tela, surface, surface.get_rect(
                    midleft=(l.px(420) + dx, y)), int(255 * alfa))
                surface = self.fonte_pequena.render(
                    "CALIBRAR >", True,
                    (200, 150, 255) if selecionada else (150, 155, 200))
                self._blit_alfa(tela, surface, surface.get_rect(
                    midleft=(l.px(540) + dx, y)), int(255 * alfa))

        if len(linhas) > self._CONFIG_VISIVEIS:
            self._desenhar_indicador_config(tela, painel, inicio, fim)

        b_salvar = BotaoNeon("SALVAR", (l.x(0.5) - l.px(190),
                                        l.altura - l.px(80), l.px(180),
                                        l.px(44)))
        b_voltar = BotaoNeon("VOLTAR", (l.x(0.5) + l.px(10),
                                        l.altura - l.px(80), l.px(180),
                                        l.px(44)))
        for i, botao in enumerate((b_salvar, b_voltar)):
            botao.atualizar(self.mouse)
            self._desenhar_botao_entrada(
                tela, botao, self.fonte_media, self._frac_sub(0.62 + i * 0.06,
                                                              0.25))

    # ------------------------------------------------------ cabecalho e titulo

    def _frac(self, inicio, duracao):
        p = (self.entrada_t - inicio) / duracao
        return 0.0 if p < 0 else 1.0 if p > 1 else p

    def _frac_sub(self, inicio, duracao):
        """Progresso (0-1) de um elemento na entrada dos sub-menus."""
        p = (self.sub_anim - inicio) / duracao
        return 0.0 if p < 0 else 1.0 if p > 1 else p

    def _frac_preview(self, inicio, duracao):
        """Progresso (0-1) de um elemento no overlay de preview da loja."""
        p = (self.preview_anim - inicio) / duracao
        return 0.0 if p < 0 else 1.0 if p > 1 else p

    def _entrada_anim(self, p, dx_design=0, dy_design=0):
        """Progresso de entrada -> (deslocamento_x, deslocamento_y, alfa)."""
        e = ease_out(p)
        return (int((1 - e) * self.layout.px(dx_design)),
                int((1 - e) * self.layout.px(dy_design)), e)

    def _painel_sub(self, tela, rect, tema, raio=14):
        """Painel glass do tema com entrada animada (escala + fade)."""
        l = self.layout
        p = self._frac_sub(0.04, 0.45)
        if p <= 0:
            return
        surf = painel_glass(tema["primaria"], rect,
                            cor_fundo=tema["fundo_painel"], raio_canto=raio,
                            glow_raio=l.px(22))
        escala = 0.9 + 0.1 * ease_out_back(p)
        if abs(escala - 1.0) > 0.01:
            surf = pygame.transform.smoothscale(
                surf, (max(1, int(surf.get_width() * escala)),
                       max(1, int(surf.get_height() * escala))))
        if p < 1.0:
            surf = surf.copy()
            surf.set_alpha(int(255 * ease_out(p)))
        tela.blit(surf, surf.get_rect(
            center=(rect.centerx,
                    rect.centery + int((1 - ease_out(p)) * l.px(22)))))

    def _detalhe_painel(self, tela, rect, tema, cor=None):
        """Linha de varredura superior + cantos em L num painel."""
        l = self.layout
        t = pygame.time.get_ticks() * 0.001
        cor = cor or tema["secundaria"]
        y = rect.y + l.px(4)
        x0 = rect.x + l.px(24)
        compr = rect.w - l.px(48)
        linha_suave(tela, cor, (x0, y), (x0 + compr, y), 2)
        fase = (math.sin(t * 2.2) + 1) / 2
        xv = x0 + int(fase * compr)
        desenhar_glow(tela, cor, (xv, y), l.px(10), 0.6)
        desenhar_cantos(tela, cor, rect, tamanho=l.px(14), espessura=l.px(2))

    def _cabecalho_sub_animado(self, tela, texto, cor, y=58, p=None):
        """Cabecalho de sub-menu com entrada animada (desce + fade)."""
        l = self.layout
        if p is None:
            p = self._frac_sub(0.0, 0.35)
        if p <= 0:
            return
        alfa = ease_out(p)
        dy = int((1 - alfa) * l.px(-28))
        fonte = self.fonte_cabecalho
        surf = self._espacado(fonte, texto, 3, BRANCO)
        cx = l.x(0.5)
        y = l.px(y) + dy
        w = surf.get_width() + l.px(80)
        bloco = self._cabecalho_bloco(cor, w)
        if p < 1.0:
            bloco = bloco.copy()
            bloco.set_alpha(int(255 * alfa))
            surf = surf.copy()
            surf.set_alpha(int(255 * alfa))
        desenhar_glow(tela, cor, (cx, y + l.px(6)), max(l.px(24), w // 8),
                      0.35 * alfa)
        tela.blit(bloco, bloco.get_rect(center=(cx, y + l.px(6))))
        tela.blit(surf, surf.get_rect(center=(cx, y)))

    def _desenhar_botao_entrada(self, tela, botao, fonte, p, dy_design=22):
        """BotaoNeon com entrada animada (fade + slide, sem perder hitbox)."""
        l = self.layout
        if p <= 0:
            return
        alfa = ease_out(p)
        dy = int((1 - alfa) * l.px(dy_design))
        if p >= 1:
            botao.desenhar(tela, fonte)
            return
        marg = l.px(28)
        off = pygame.Surface((botao.rect.w + marg, botao.rect.h + marg),
                             pygame.SRCALPHA)
        b = BotaoNeon(botao.texto,
                      pygame.Rect(marg // 2, marg // 2, botao.rect.w,
                                  botao.rect.h),
                      cor=botao.cor, cor_hover=botao.cor_hover)
        b.hover = botao.hover
        b.desenhar(off, fonte)
        off.set_alpha(int(255 * alfa))
        tela.blit(off, (botao.rect.x - marg // 2,
                        botao.rect.y - marg // 2 + dy))

    def _desenhar_nave_escala(self, tela, skin, x, y, escala, p):
        """Nave do jogador com entrada animada (pop-in + fade)."""
        l = self.layout
        if p <= 0:
            return
        lado = l.px(96)
        off = pygame.Surface((lado, lado), pygame.SRCALPHA)
        prev = Jogador(skin=skin)
        prev.x, prev.y = lado // 2, lado // 2 + l.px(8)
        prev.tilt = 0
        prev.invencivel = 0
        prev.desenhar(off, None)
        escala_final = escala * (0.5 + 0.5 * ease_out_back(p))
        if abs(escala_final - 1.0) > 0.01:
            off = pygame.transform.smoothscale(
                off, (max(1, int(lado * escala_final)),
                      max(1, int(lado * escala_final))))
        alfa = ease_out(p)
        if alfa < 1.0:
            off = off.copy()
            off.set_alpha(int(255 * alfa))
        tela.blit(off, off.get_rect(center=(x, y)))

    def _espacado(self, fonte, texto, espacamento, cor):
        chave = (id(fonte), texto, espacamento, tuple(cor))
        if chave not in self._cache_espacado:
            self._cache_espacado[chave] = texto_espacado(
                fonte, texto, espacamento, cor)
        return self._cache_espacado[chave]

    def _blit_alfa(self, tela, surf, pos, alfa):
        if alfa <= 0:
            return
        if alfa >= 255:
            tela.blit(surf, pos)
        else:
            s = surf.copy()
            s.set_alpha(int(alfa))
            tela.blit(s, pos)

    def _titulo_surfaces(self, tema):
        nome = self.jogo.config["tema"]
        if nome not in self._titulo_cache:
            titulo = texto_suave(self.fonte_logo, "INCARNATE", BRANCO,
                                 tema["primaria"], 16, True)
            titulo_eco = texto_suave(self.fonte_logo, "INCARNATE",
                                     tema["primaria"], None, 0, False)
            sub = self._espacado(self.fonte_legenda, "ENTRE NA FENDA.", 4,
                                 tema["primaria"])
            tag = self._espacado(self.fonte_legenda, "// COMBATE DIMENSIONAL",
                                 2, tema["secundaria"])
            self._titulo_cache[nome] = {
                "incarnate": titulo, "incarnate_eco": titulo_eco,
                "sub": sub, "tag": tag}
        return self._titulo_cache[nome]

    def _bloco_logo(self, tema):
        nome = self.jogo.config["tema"]
        if nome in self._bloco_logo_cache:
            return self._bloco_logo_cache[nome]
        l = self.layout
        w, h, inc = l.px(460), l.px(130), l.px(26)
        surf = pygame.Surface((w, h + inc), pygame.SRCALPHA)
        pts = [(0, inc), (w, 0), (w, h), (0, h + inc)]
        desenhar_poligono(surf, tema["primaria"] + (70,), pts)
        desenhar_poligono(surf, tema["primaria"] + (170,), pts, 2)
        linha_suave(surf, (255, 255, 255, 70), (0, inc + 6), (w, 6), 5)
        desenhar_poligono(surf, tema["secundaria"] + (90,),
                          [(0, h + inc - 10), (70, h + inc - 34),
                           (0, h + inc - 34)])
        # moldura interna em paralelogramo (tom secundario)
        desenhar_poligono(surf, tema["secundaria"] + (110,),
                          [(l.px(10), inc + l.px(10)),
                           (w - l.px(10), l.px(10)),
                           (w - l.px(10), h - l.px(10)),
                           (l.px(10), h + inc - l.px(10))], 1)
        # linha de energia vertical na direita
        linha_suave(surf, tema["secundaria"] + (140,),
                    (w - l.px(16), l.px(8)), (w - l.px(16), h), 2)
        # bracket HUD no canto superior esquerdo
        cx, cy = l.px(16), inc + l.px(14)
        comp = l.px(14)
        linha_suave(surf, tema["secundaria"] + (220,), (cx, cy),
                    (cx + comp, cy), 2)
        linha_suave(surf, tema["secundaria"] + (220,), (cx, cy),
                    (cx, cy + comp), 2)
        self._bloco_logo_cache[nome] = surf
        return surf

    def _cabecalho_bloco(self, cor, largura):
        chave = (tuple(cor), int(largura))
        if chave in self._cabecalho_cache:
            return self._cabecalho_cache[chave]
        l = self.layout
        h, inc = l.px(56), l.px(12)
        surf = pygame.Surface((int(largura), h + inc), pygame.SRCALPHA)
        pts = [(0, inc), (int(largura), 0), (int(largura), h), (0, h + inc)]
        desenhar_poligono(surf, cor + (50,), pts)
        desenhar_poligono(surf, cor + (200,), pts, 2)
        self._cabecalho_cache[chave] = surf
        return surf

    # -------------------------------------------------------------- desenho

    def _desenhar_linhas_diagonais(self, tela, tema):
        if self.entrada_t < 0.12:
            return
        l = self.layout
        prim = tema["primaria"]
        cor1 = tuple(int(c * 0.85) for c in prim)
        linha_suave(tela, cor1, l.ponto(TOPO_ESQUERDA, 30, 470),
                    l.ponto(TOPO_ESQUERDA, 470, 180), 2)
        linha_suave(tela, tema["borda_fraco"],
                    l.ponto(TOPO_ESQUERDA, 66, 470),
                    l.ponto(TOPO_ESQUERDA, 506, 180), 1)
        linha_suave(tela, cor1, l.ponto(TOPO_DIREITA, 0, 330),
                    l.ponto(TOPO_ESQUERDA, 640, 486), 1)

    def _desenhar_linha_titulo(self, tela, tema, x, y, alfa):
        """Linha de acento entre o titulo tipografico e o subtitulo."""
        l = self.layout
        larg = l.px(300)
        surf = pygame.Surface((larg, l.px(14)), pygame.SRCALPHA)
        prim = tema["primaria"]
        for i in range(larg):
            t = i / max(1, larg - 1)
            c = tuple(int(prim[j] * (0.25 + 0.75 * (1 - t)))
                      for j in range(3))
            linha_suave(surf, c + (int(150 * alfa / 255),),
                        (i, l.px(6)), (i, l.px(8)), 1)
        cx, cy = larg // 2, l.px(7)
        desenhar_poligono(surf, tema["secundaria"] + (int(230 * alfa / 255),),
                          [(cx, cy - l.px(4)), (cx + l.px(4), cy),
                           (cx, cy + l.px(4)), (cx - l.px(4), cy)])
        surf.set_alpha(alfa)
        tela.blit(surf, (x, y))

    def _desenhar_bloco_titulo(self, tela, tema):
        l = self.layout
        ts = self._titulo_surfaces(tema)
        p_titulo = self._frac(0.10, 0.5)
        p_bloco = self._frac(0.06, 0.28)
        p_sub = self._frac(0.55, 0.4)
        off = int((1 - ease_out_back(p_titulo)) * -l.px(300))
        alfa = int(255 * ease_out(p_titulo))
        if p_bloco > 0:
            bloco = self._bloco_logo(tema)
            self._blit_alfa(tela, bloco, l.ponto(TOPO_ESQUERDA, 36, 166),
                            255 * ease_out(p_bloco))
        alfa_eco = int(220 * ease_out(p_bloco))
        self._blit_alfa(tela, ts["incarnate_eco"],
                        (l.px(62) + off, l.px(171)), alfa_eco)
        self._blit_alfa(tela, ts["incarnate"],
                        (l.px(56) + off, l.px(165)), alfa)
        alfa_sub = int(255 * ease_out(p_sub))
        self._desenhar_linha_titulo(tela, tema, l.px(60) + off, l.px(280),
                                    alfa_sub)
        self._blit_alfa(tela, ts["sub"],
                        (l.px(60) + off, l.px(302)), alfa_sub)
        self._blit_alfa(tela, ts["tag"],
                        (l.px(60) + off, l.px(334)), alfa_sub)

    def _desenhar_seta(self, tela, tema):
        if self.entrada_t < 0.7:
            return
        op = self.opcoes[self.opcao_selecionada]
        x = self.x_opcoes - self.layout.px(26)
        y = op.y
        desenhar_poligono(tela, tema["secundaria"],
                          [(x, y), (x - 14, y - 9), (x - 14, y + 9)])

    def _desenhar_rodape(self, tela, tema):
        l = self.layout
        p = self._frac(0.85, 0.3)
        if p <= 0:
            return
        alfa = int(255 * ease_out(p))
        f = self.fonte_pequena
        linha = "PILOTO: %s   |   MOEDAS: %s" % (
            self.jogo.nome_jogador.upper(),
            formatar_pontos(self.jogo.loja.moedas))
        surf = self._espacado(f, linha, 1, (176, 186, 224))
        self._blit_alfa(tela, surf, (self.x_opcoes, l.y(0.746)), alfa)
        hint = "SETAS/WASD  NAVEGAR   |   ENTER  CONFIRMAR   |   ESC  SAIR"
        surf2 = self._espacado(f, hint, 1, (118, 130, 170))
        self._blit_alfa(tela, surf2,
                        (l.largura // 2 - surf2.get_width() // 2, l.y(0.78)),
                        int(alfa * 0.75))
        versao = self._espacado(f, "v3.0 // ENTRE NA FENDA", 1,
                                (110, 122, 160))
        self._blit_alfa(tela, versao,
                        (l.largura - l.px(46) - versao.get_width(),
                         l.altura - l.px(32)),
                        int(alfa * 0.7))

    def _desenhar_menu(self, tela):
        tema = tema_atual(self.jogo.config["tema"])
        self._desenhar_linhas_diagonais(tela, tema)
        self._desenhar_bloco_titulo(tela, tema)

        p_rot = self._frac(0.28, 0.3)
        if p_rot > 0:
            rotulo = self._espacado(self.fonte_pequena, "// COMANDO DE VOO", 2,
                                    tema["secundaria"])
            self._blit_alfa(tela, rotulo,
                            (self.x_opcoes, self.layout.px(132)),
                            int(255 * ease_out(p_rot)))

        if self.entrada_t > 0.25:
            self.destaque.desenhar(tela, self.x_opcoes -
                                   self.layout.px(32), tema)

        for i, opcao in enumerate(self.opcoes):
            p = self._frac(0.34 + i * 0.07, 0.42)
            desloc = int((1 - ease_out(p)) * 150)
            opcao.desenhar(tela, self.fonte_opcao, self.fonte_opcao_sel,
                           tema, self.x_opcoes, i == self.opcao_selecionada,
                           desloc, int(255 * ease_out(p)), self.layout)
        self._desenhar_seta(tela, tema)
        self._desenhar_rodape(tela, tema)

    def desenhar(self, tela):
        l = self.layout
        tema = tema_atual(self.jogo.config["tema"])
        self.fundo.desenhar(tela)
        skin = self.jogo.loja.pegar_skin(self.jogo.loja.skin_atual)
        self.nave.desenhar(tela, skin, l.px(856), l.px(560),
                           2.2 * l.escala, tema)
        self.hud.desenhar(tela, tema)
        if self.subestado == "FASES":
            self.phase_screen.draw(tela)
            ship_x, ship_y = self.phase_screen.ship_position()
            self.nave.desenhar(tela, skin, ship_x, ship_y,
                               1.8 * l.escala, tema)
        else:
            self.telas[self.subestado].desenhar(tela)
        self.notificacoes.desenhar(tela, self.fonte_media)
        if self.dialogo and self.dialogo.ativo:
            self.dialogo.desenhar(tela, self.fonte_sub, self.fonte_media,
                                  self.mouse, tema)
        self.transicao.desenhar(tela)
        self.transicao_missao.desenhar(tela, tema)
        if self.alpha_entrada < 255:
            overlay = pygame.Surface((l.largura, l.altura))
            overlay.fill(NEGRO)
            overlay.set_alpha(255 - self.alpha_entrada)
            tela.blit(overlay, (0, 0))

    def atualizar(self):
        self.fundo.atualizar()
        self.hud.atualizar()
        self.nave.atualizar()
        self.destaque.atualizar()
        self.transicao.atualizar()
        self.transicao_missao.atualizar()
        self.notificacoes.atualizar()
        self.alpha_entrada = min(255, self.alpha_entrada + 4)
        if self.preview_skin and self.preview_anim < 0.5:
            self.preview_anim += 1 / 60.0
        if self.subestado != "MENU" and self.sub_anim < self.sub_anim_total:
            self.sub_anim += 1 / 60.0
        if self.subestado == "FASES":
            self.phase_screen.update(pygame.key.get_pressed())
        if self.subestado == "MENU":
            if self.entrada_t < self.entrada_total:
                self.entrada_t += 1 / 60.0
            for opcao in self.opcoes:
                opcao.atualizar(self.mouse, self.x_opcoes, self.fonte_opcao,
                                self.layout)
            for i, opcao in enumerate(self.opcoes):
                if opcao.hover:
                    self._selecionar(i)

    # -------------------------------------------------------------- eventos

    def tratar_eventos(self, evento):
        if self.transicao_missao.em_andamento():
            return True
        if self.dialogo and self.dialogo.ativo:
            pos = self._pos_logica(evento.pos) if hasattr(evento, "pos") else None
            self.dialogo.tratar_evento(evento, pos)
            return True
        if self.remapando:
            return self._tratar_remap(evento)
        if evento.type == pygame.MOUSEMOTION:
            self.mouse = self._pos_logica(evento.pos)
            if self.subestado == "FASES":
                self.phase_screen.handle_event(pygame.event.Event(
                    pygame.MOUSEMOTION, {"pos": self.mouse}))
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._clique(self._pos_logica(evento.pos))
        elif evento.type == pygame.KEYDOWN:
            return self._tecla(evento)
        return True

    def _pos_logica(self, pos):
        """Converte coordenadas da janela para a superficie logica.

        Aplica a transformacao vigente somada aos ajustes manuais de "Ajustar
        Tela". No AJUSTAR usa o scale-to-fit; no PREENCHE considera a
        proporcao da janela. O clique continua alinhado a imagem mesmo apos
        calibrar a tela.
        """
        try:
            if self.jogo.config["aspecto"] == "PREENCHE":
                w, h = self.jogo.janela.get_size()
                e = self.jogo.config["ajuste_escala"]
                return (int((pos[0] - self.jogo.config["ajuste_off_x"]) *
                            self.layout.largura / (w * e)),
                        int((pos[1] - self.jogo.config["ajuste_off_y"]) *
                            self.layout.altura / (h * e)))
            escala, off_x, off_y = self.jogo._transformacao_janela()
        except (AttributeError, TypeError):
            return pos
        return (int((pos[0] - off_x) / escala),
                int((pos[1] - off_y) / escala))

    def _tratar_remap(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self.remapando = None
                self._som("navegar")
                return True
            acao = self.remapando
            tecla = evento.key
            if any(t == tecla for t in self.jogo.config.controles.values()):
                self.notificacoes.adicionar("Tecla ja em uso!", "erro")
                self._som("erro")
                return True
            self.jogo.config.controles[acao] = tecla
            self.remapando = None
            self.jogo.config.salvar()
            self.notificacoes.adicionar(
                f"{acao} -> {pygame.key.name(tecla).upper()}", "sucesso")
            self._som("equipar")
        return True

    def _tecla(self, evento):
        if self.subestado == "FASES":
            self.phase_screen.handle_event(evento)
            return True
        return self.telas[self.subestado].tratar_tecla(evento)

    def _tecla_menu_principal(self, evento):
        """Entrada de teclado exclusiva da tela principal."""
        if evento.key in (pygame.K_UP, pygame.K_w):
            novo = (self.opcao_selecionada - 1) % len(self.opcoes)
            self._selecionar(novo)
        elif evento.key in (pygame.K_DOWN, pygame.K_s):
            novo = (self.opcao_selecionada + 1) % len(self.opcoes)
            self._selecionar(novo)
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.opcoes[self.opcao_selecionada].funcao()
        elif evento.key == pygame.K_BACKSPACE:
            self.jogo.nome_jogador = self.jogo.nome_jogador[:-1]
        elif evento.key == pygame.K_ESCAPE:
            self._sair()
        elif evento.unicode and evento.unicode.isprintable() and len(self.jogo.nome_jogador) < 12:
            self.jogo.nome_jogador += evento.unicode
        return True

    def _tecla_continuar(self, evento):
        """Entrada de teclado exclusiva da tela de continuar."""
        if evento.key in (pygame.K_UP, pygame.K_DOWN):
            self.continuar_selecao = 1 - self.continuar_selecao
            self._som("navegar")
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._acao_continuar(self.continuar_selecao)
        elif evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self._voltar_menu()
        return True

    def _tecla_recordes(self, evento):
        """Entrada de teclado exclusiva da tela de recordes."""
        if evento.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_BACKSPACE):
            self._voltar_menu()
        return True

    def _tecla_loja(self, evento):
        if self.preview_skin:
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._acao_botao_loja("equipar")
                self.preview_skin = None
            elif evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.preview_skin = None
                self._som("navegar")
            return True
        colunas = 4
        n = len(self.jogo.loja.skins)
        if evento.key in (pygame.K_LEFT, pygame.K_a):
            self.loja_selecao = max(0, self.loja_selecao - 1)
            self._som("navegar")
        elif evento.key in (pygame.K_RIGHT, pygame.K_d):
            self.loja_selecao = min(n - 1, self.loja_selecao + 1)
            self._som("navegar")
        elif evento.key in (pygame.K_UP, pygame.K_w):
            self.loja_selecao = max(0, self.loja_selecao - colunas)
            self._som("navegar")
        elif evento.key in (pygame.K_DOWN, pygame.K_s):
            self.loja_selecao = min(n - 1, self.loja_selecao + colunas)
            self._som("navegar")
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._acao_loja_principal()
        elif evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self._voltar_menu()
        return True

    def _tecla_config(self, evento):
        if self.config_submodo == "controles":
            if evento.key == pygame.K_ESCAPE:
                self.config_submodo = None
                self.sub_anim = 0.0
                self._som("navegar")
            elif evento.key in (pygame.K_UP, pygame.K_DOWN):
                n = len(ACOES_CONTROLE)
                passo = 1 if evento.key == pygame.K_DOWN else -1
                self.controle_selecao = (self.controle_selecao + passo) % n
                self._som("navegar")
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.remapando = ACOES_CONTROLE[self.controle_selecao]
                self._som("navegar")
            return True

        if self.config_submodo == "resolucao":
            if evento.key == pygame.K_ESCAPE:
                self.config_submodo = None
                self.sub_anim = 0.0
                self._som("navegar")
            elif evento.key in (pygame.K_UP, pygame.K_DOWN):
                n = len(RESOLUCOES)
                passo = 1 if evento.key == pygame.K_DOWN else -1
                self.resolucao_selecao = (self.resolucao_selecao + passo) % n
                self._rolar_resolucao(self.resolucao_selecao)
                self._som("navegar")
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._aplicar_resolucao(self.resolucao_selecao)
            return True

        if self.config_submodo == "ajuste":
            return self._tecla_ajuste(evento)

        linhas = self._linhas_config()
        n = len(linhas)
        if evento.key in (pygame.K_UP, pygame.K_w):
            self.config_selecao = (self.config_selecao - 1) % n
            self._rolar_config(self.config_selecao)
            self._som("navegar")
        elif evento.key in (pygame.K_DOWN, pygame.K_s):
            self.config_selecao = (self.config_selecao + 1) % n
            self._rolar_config(self.config_selecao)
            self._som("navegar")
        elif evento.key == pygame.K_LEFT:
            self._ajustar_config(-1)
        elif evento.key == pygame.K_RIGHT:
            self._ajustar_config(1)
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.config_selecao == 2:
                self.config_submodo = "resolucao"
                self.resolucao_selecao = self._indice_resolucao_atual()
                self.sub_anim = 0.0
                self._som("navegar")
            elif self.config_selecao == 5:
                self.config_submodo = "controles"
                self.controle_selecao = 0
                self.sub_anim = 0.0
                self._som("navegar")
            elif self.config_selecao == 8:
                self._abrir_ajuste_tela()
            else:
                self._ajustar_config(1)
        elif evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self._voltar_menu()
        return True

    def _clique(self, pos):
        self.mouse = pos
        if self.subestado == "FASES":
            self.phase_screen.handle_event(pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": pos}))
            return
        self.telas[self.subestado].tratar_clique(pos)

    def _clique_menu_principal(self, pos):
        """Clique exclusivo da tela principal."""
        for i, opcao in enumerate(self.opcoes):
            if opcao.get_rect(self.x_opcoes, self.fonte_opcao, self.layout).collidepoint(pos):
                self._selecionar(i)
                opcao.funcao()
                return

    def _clique_continuar(self, pos):
        """Clique exclusivo da tela de continuar."""
        for i, botao in enumerate(self._botoes_continuar()):
            if botao.rect.collidepoint(pos):
                self._acao_continuar(i)
                return

    def _clique_recordes(self, pos):
        """Clique exclusivo da tela de recordes."""
        if self._botao_voltar().rect.collidepoint(pos):
            self._voltar_menu()

    def _clique_loja(self, pos):
        l = self.layout
        if self.preview_skin:
            botoes = {"equipar": pygame.Rect(l.x(0.5) - l.px(170),
                                             l.altura - l.px(120),
                                             l.px(160), l.px(48)),
                      "fechar": pygame.Rect(l.x(0.5) + l.px(10),
                                            l.altura - l.px(120),
                                            l.px(160), l.px(48))}
            if botoes["equipar"].collidepoint(pos):
                self._acao_botao_loja("equipar")
                self.preview_skin = None
            elif botoes["fechar"].collidepoint(pos):
                self.preview_skin = None
                self._som("navegar")
            return
        for i, rect in enumerate(self._rects_loja()):
            if rect.collidepoint(pos):
                self.loja_selecao = i
                return
        for nome, botao in self._botoes_loja().items():
            if botao.rect.collidepoint(pos):
                self._acao_botao_loja(nome)
                return
