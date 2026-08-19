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
import os

import pygame

from .config import BRANCO, CIANO, DOURADO, QUANTUM_CYAN, VERDE
from .layout import ALTURA_BASE, CENTRO, LARGURA_BASE, TOPO_DIREITA, \
    TOPO_ESQUERDA, Layout
from .menu_scene import DestaqueMenu, FundoCinematico, HudMenu, NaveMenu, \
    TransicaoMissao, texto_espacado
from .player import Jogador
from .save_system import ARQUIVO_RECORDES, SistemaProgressao
from .settings import ACOES_CONTROLE, RESOLUCOES, TEMAS
from .shop import LojaSkins
from .smooth import desenhar_circulo as desenhar_circulo_suave, \
    desenhar_glow, ease_out, ease_out_back, retangulo_suave, texto_suave
from .theme import tema_atual
from .ui import BotaoNeon

NEGRO = (0, 0, 0)


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
    def _blit(tela, surf, x, y, alfa):
        if alfa >= 255:
            tela.blit(surf, surf.get_rect(center=(x, y)))
        elif alfa > 0:
            s = surf.copy()
            s.set_alpha(int(alfa))
            tela.blit(s, s.get_rect(center=(x, y)))

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
            self._blit(tela, surf, xf + layout.px(3), y + layout.px(2), alfa)
        surf = texto_suave(fonte_ativa, self.texto, cor,
                           primaria if selecionado else None,
                           5 if selecionado else 0, True)
        self._blit(tela, surf, xf, y, alfa)
        if selecionado and alfa >= 255:
            larg = fonte_ativa.size(self.texto)[0]
            pygame.draw.line(tela, primaria,
                             (xf - layout.px(8),
                              y + fonte_ativa.get_height() // 2 + layout.px(4)),
                             (xf + larg - layout.px(4),
                              y + fonte_ativa.get_height() // 2 + layout.px(4)),
                             3)


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
            pygame.draw.rect(fundo, cor + (int(notif["alpha"] * 0.85),),
                             rect, border_radius=8)
            pygame.draw.rect(fundo, BRANCO + (int(notif["alpha"]),),
                             rect, 1, border_radius=8)
            x = l.largura - largura - l.px(20)
            tela.blit(fundo, (x, y))
            texto.set_alpha(notif["alpha"])
            tela.blit(texto, (x + l.px(24), y + l.px(11)))
            y += l.px(54)


class Dialogo:
    """Dialogo modal com confirmar/cancelar (mouse e teclado)."""

    def __init__(self, titulo, mensagem, funcao_confirmar, funcao_cancelar,
                 layout=None):
        self._layout = layout or Layout()
        self.titulo = titulo
        self.mensagem = mensagem
        self.funcao_confirmar = funcao_confirmar
        self.funcao_cancelar = funcao_cancelar
        self.ativo = True
        self._largura, self._altura = self._layout.px(500), self._layout.px(250)
        self._x = self._layout.x(0.5) - self._largura // 2
        self._y = self._layout.y(0.5) - self._altura // 2

    def _retangulos(self):
        l = self._layout
        confirmar = pygame.Rect(self._x + l.px(90),
                                self._y + self._altura - l.px(70),
                                l.px(130), l.px(42))
        cancelar = pygame.Rect(self._x + l.px(280),
                               self._y + self._altura - l.px(70),
                               l.px(130), l.px(42))
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
        self.ativo = False
        self.funcao_confirmar()

    def _cancelar(self):
        self.ativo = False
        self.funcao_cancelar()

    def desenhar(self, tela, fonte_titulo, fonte_texto, mouse_pos=(0, 0)):
        l = self._layout
        overlay = pygame.Surface((l.largura, l.altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        tela.blit(overlay, (0, 0))
        rect = pygame.Rect(self._x, self._y, self._largura, self._altura)
        retangulo_suave(tela, (25, 25, 48), rect, 12)
        retangulo_suave(tela, (120, 90, 220), rect, 12, 2,
                        glow_cor=(120, 90, 220), glow_raio=12)
        titulo = fonte_titulo.render(self.titulo, True, (255, 200, 100))
        tela.blit(titulo, titulo.get_rect(center=(rect.centerx,
                                                  rect.y + l.px(34))))

        palavras = self.mensagem.split()
        linhas, atual = [], []
        for palavra in palavras:
            teste = " ".join(atual + [palavra])
            if fonte_texto.size(teste)[0] > self._largura - l.px(40):
                linhas.append(" ".join(atual))
                atual = [palavra]
            else:
                atual.append(palavra)
        if atual:
            linhas.append(" ".join(atual))
        for i, linha in enumerate(linhas):
            surface = fonte_texto.render(linha, True, (200, 205, 255))
            tela.blit(surface, surface.get_rect(center=(rect.centerx,
                                                        rect.y + l.px(84) +
                                                        i * l.px(30))))

        confirmar, cancelar = self._retangulos()
        mouse = mouse_pos
        cor = (0, 150, 60) if confirmar.collidepoint(mouse) else (0, 80, 40)
        pygame.draw.rect(tela, cor, confirmar, border_radius=8)
        pygame.draw.rect(tela, BRANCO, confirmar, 1, border_radius=8)
        surface = fonte_texto.render("Confirmar", True, BRANCO)
        tela.blit(surface, surface.get_rect(center=confirmar.center))
        cor = (170, 30, 30) if cancelar.collidepoint(mouse) else (90, 20, 20)
        pygame.draw.rect(tela, cor, cancelar, border_radius=8)
        pygame.draw.rect(tela, BRANCO, cancelar, 1, border_radius=8)
        surface = fonte_texto.render("Cancelar", True, BRANCO)
        tela.blit(surface, surface.get_rect(center=cancelar.center))


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

        self.fonte_titulo_grande = self.layout.fonte_titulo(96)
        self.fonte_fury = self.layout.fonte_titulo(92)
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
        self._bloco_fury_cache = {}
        self._cabecalho_cache = {}
        self._cache_espacado = {}

        self.continuar_selecao = 0
        self.loja_selecao = 0
        self.preview_skin = None
        self.config_selecao = 0
        self.config_submodo = None
        self.controle_selecao = 0
        self.remapando = None

    # ------------------------------------------------------------------ sons

    def _som(self, nome):
        self.jogo.sons.tocar(nome)

    # --------------------------------------------------------------- opcoes

    def _construir_opcoes_menu(self):
        itens = [
            ("01 // CONTINUAR", self._abrir_continuar),
            ("02 // NOVA MISSAO", self._novo_jogo_direto),
            ("03 // HANGAR", self._abrir_loja),
            ("04 // RECORDS", self._abrir_recordes),
            ("05 // SETTINGS", self._abrir_config),
            ("06 // EXIT", self._sair),
        ]
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
        self.subestado = "CONTINUAR"
        self.transicao.iniciar()

    def _novo_jogo_direto(self):
        self._iniciar_missao(self.jogo._preparar_jogo)

    def _abrir_loja(self):
        self._som("navegar")
        self.loja_selecao = self._indice_skin_atual()
        self.preview_skin = None
        self.subestado = "LOJA"
        self.transicao.iniciar()

    def _abrir_recordes(self):
        self._som("navegar")
        self.jogo.recordes = SistemaProgressao.carregar_recordes()
        self.subestado = "RECORDES"
        self.transicao.iniciar()

    def _abrir_config(self):
        self._som("navegar")
        self.config_selecao = 0
        self.config_submodo = None
        self.remapando = None
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
        self._som("navegar")
        self.preview_skin = None
        self.config_submodo = None
        self.remapando = None
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
        except OSError:
            pass
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
        self._cabecalho_sub(tela, "CARREGANDO JOGO", (130, 205, 255))
        tem = self._tem_save()
        painel = self._painel_central(520, 330, -35)
        retangulo_suave(tela, (22, 22, 46), painel, 12)
        retangulo_suave(tela, (110, 90, 220), painel, 12, 2,
                        glow_cor=(110, 90, 220), glow_raio=12)
        jog = self.jogo.progresso.jogador
        titulo = ("Save Encontrado" if tem else "Nenhum Save")
        cor = (150, 230, 120) if tem else (230, 120, 120)
        surface = self.fonte_media.render(titulo, True, cor)
        tela.blit(surface, surface.get_rect(center=(painel.centerx,
                                                    painel.y + l.px(28))))
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
            for rotulo, valor in linhas:
                surface = self.fonte_media.render(f"{rotulo}:", True,
                                                  (170, 175, 225))
                tela.blit(surface, (painel.x + l.px(70), y))
                surface = self.fonte_media.render(valor, True, BRANCO)
                tela.blit(surface, surface.get_rect(midleft=(painel.x +
                                                             l.px(250),
                                                             y + l.px(9))))
                y += l.px(36)
        else:
            surface = self.fonte_media.render(
                "Nenhum progresso salvo ainda.", True, (200, 200, 240))
            tela.blit(surface, surface.get_rect(center=painel.center))
        botoes = self._botoes_continuar()
        for botao in botoes:
            botao.atualizar(self.mouse)
            botao.desenhar(tela, self.fonte_media)
        if self.continuar_selecao < 2:
            pygame.draw.rect(tela, (255, 200, 100),
                             botoes[self.continuar_selecao].rect, 3,
                             border_radius=10)

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
        nomes = ["COMPRAR", "EQUIPAR", "PREVIEW", "VOLTAR"]
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
        self._cabecalho_sub(tela, "LOJA DE SKINS", (150, 90, 255))
        surface = self.fonte_media.render(
            f"Moedas: {formatar_pontos(self.jogo.loja.moedas)}", True,
            DOURADO)
        tela.blit(surface, (l.px(20), l.px(30)))
        skin_atual = self.jogo.loja.pegar_skin(self.jogo.loja.skin_atual)
        surface = self.fonte_media.render(
            f"Skin atual: {skin_atual.nome}", True, CIANO)
        tela.blit(surface, surface.get_rect(topright=(l.largura - l.px(20),
                                                      l.px(30))))

        rects = self._rects_loja()
        for i, skin in enumerate(self.jogo.loja.skins):
            rect = rects[i]
            selecionada = (i == self.loja_selecao)
            hover = rect.collidepoint(self.mouse)
            fundo = (52, 46, 92) if selecionada else (36, 34, 62) if hover \
                else (28, 27, 50)
            borda = (255, 190, 90) if selecionada else (150, 130, 255) \
                if hover else (85, 80, 130)
            retangulo_suave(tela, fundo, rect, 10,
                            glow_cor=borda if (selecionada or hover) else None,
                            glow_raio=10 if (selecionada or hover) else 0)
            pygame.draw.rect(tela, borda, rect, 2, border_radius=10)
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

        for botao in self._botoes_loja().values():
            botao.atualizar(self.mouse)
            botao.desenhar(tela, self.fonte_media)
        skin = self.jogo.loja.skins[self.loja_selecao]
        surface = self.fonte_pequena.render(skin.descricao, True,
                                            (170, 175, 220))
        tela.blit(surface, surface.get_rect(center=(l.x(0.5),
                                                    l.altura - l.px(36))))

        if self.preview_skin:
            self._desenhar_preview_overlay(tela)

    def _desenhar_preview_overlay(self, tela):
        l = self.layout
        overlay = pygame.Surface((l.largura, l.altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 195))
        tela.blit(overlay, (0, 0))
        skin = self.preview_skin
        self._cabecalho_sub(tela, skin.nome.upper(), (170, 120, 255),
                            y=l.px(128))
        prev = Jogador(skin=skin)
        prev.x, prev.y = l.x(0.5), l.y(0.5) - l.px(60)
        prev.tilt = 0
        prev.invencivel = 0
        prev.desenhar(tela, None)
        surface = self.fonte_media.render(skin.descricao, True, (200, 205, 240))
        tela.blit(surface, surface.get_rect(center=(l.x(0.5),
                                                    l.y(0.5) + l.px(90))))
        if skin.id == self.jogo.loja.skin_atual:
            status, cor = "Equipada", CIANO
        elif skin.desbloqueada:
            status, cor = "Desbloqueada", VERDE
        else:
            status, cor = f"Preco: {formatar_pontos(skin.preco)} pts", DOURADO
        surface = self.fonte_media.render(status, True, cor)
        tela.blit(surface, surface.get_rect(center=(l.x(0.5),
                                                    l.y(0.5) + l.px(130))))
        botoes = {"equipar": BotaoNeon("EQUIPAR", (l.x(0.5) - l.px(170),
                                                   l.altura - l.px(120),
                                                   l.px(160), l.px(48))),
                  "fechar": BotaoNeon("FECHAR", (l.x(0.5) + l.px(10),
                                                 l.altura - l.px(120),
                                                 l.px(160), l.px(48)))}
        for botao in botoes.values():
            botao.atualizar(self.mouse)
            botao.desenhar(tela, self.fonte_media)

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
        self._cabecalho_sub(tela, "RECORDES", (140, 120, 255))
        lista = self.jogo.recordes
        painel = self._painel_central(520, 330, -35)
        retangulo_suave(tela, (22, 22, 46), painel, 12)
        retangulo_suave(tela, (110, 90, 220), painel, 12, 2,
                        glow_cor=(110, 90, 220), glow_raio=12)
        surface = self.fonte_media.render("TOP 5", True, CIANO)
        tela.blit(surface, surface.get_rect(center=(painel.centerx,
                                                    painel.y + l.px(28))))
        if not lista:
            surface = self.fonte_media.render(
                "Nenhum recorde ainda.", True, (200, 205, 240))
            tela.blit(surface, surface.get_rect(center=painel.center))
        else:
            y = painel.y + l.px(70)
            for i, reg in enumerate(lista[:5]):
                cor = DOURADO if i == 0 else (205, 210, 235) if i < 3 \
                    else (150, 155, 190)
                texto = (f"TOP {i + 1}. {reg['nome']}  "
                         f"{formatar_pontos(reg['pontos'])} pts  "
                         f"(Nivel {reg['nivel']})")
                surface = self.fonte_media.render(texto, True, cor)
                tela.blit(surface, surface.get_rect(center=(painel.centerx,
                                                            y)))
                y += l.px(52)

        jog = self.jogo.progresso.jogador
        estatisticas = self.jogo.progresso.dados["estatisticas"]
        melhor = formatar_pontos(lista[0]["pontos"]) if lista else "0"
        linha = (f"Seu melhor: {melhor} pts  |  "
                 f"Skins: {len(self.jogo.loja.lista_desbloqueadas())}/10  |  "
                 f"Inimigos: {estatisticas['inimigos_derrotados']}  |  "
                 f"Bosses: {jog['bosses_derrotados']}")
        surface = self.fonte_media.render(linha, True, (170, 175, 220))
        tela.blit(surface, surface.get_rect(center=(l.x(0.5), l.y(0.72))))

        botao = self._botao_voltar()
        botao.atualizar(self.mouse)
        botao.desenhar(tela, self.fonte_media)

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
        ]

    def _y_linha_config(self, indice):
        return self.layout.px(172) + indice * self.layout.px(54)

    def _track_slider(self):
        """Posicoes x da trilha do slider (proporcionais a superficie)."""
        return self.layout.px(400), self.layout.px(700)

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
                self._som("navegar")
            return

        linhas = self._linhas_config()
        for i in range(len(linhas)):
            y = self._y_linha_config(i)
            if abs(pos[1] - y) < 24:
                self.config_selecao = i
                if i == 2:
                    self._ciclar_resolucao()
                elif i == 3:
                    self._toggle_tela_cheia()
                elif i == 5:
                    self.config_submodo = "controles"
                    self.controle_selecao = 0
                    self._som("navegar")
                elif i == 6:
                    self._ciclar_tema()
                elif i == 7:
                    self._ajustar_config(1)
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
        painel = self._painel_controles()
        retangulo_suave(tela, (20, 20, 42), painel, 12)
        retangulo_suave(tela, (110, 90, 220), painel, 12, 2,
                        glow_cor=(110, 90, 220), glow_raio=12)
        surface = self.fonte_media.render("CONTROLES", True, CIANO)
        tela.blit(surface, surface.get_rect(center=(painel.centerx,
                                                    painel.y + l.px(28))))
        for i, acao in enumerate(ACOES_CONTROLE):
            y = painel.y + l.px(64) + i * l.px(48)
            rect = pygame.Rect(painel.x + l.px(30), y,
                               painel.width - l.px(60), l.px(40))
            selecionado = (i == self.controle_selecao)
            if selecionado:
                pygame.draw.rect(tela, (50, 46, 90), rect, border_radius=8)
                pygame.draw.rect(tela, (255, 200, 100), rect, 2,
                                 border_radius=8)
            surface = self.fonte_media.render(acao.upper(), True, BRANCO)
            tela.blit(surface, (rect.x + l.px(14), rect.y + l.px(10)))
            tecla = self.jogo.config.controles.get(acao, 0)
            nome_tecla = pygame.key.name(tecla).upper() or "?"
            cor = DOURADO if selecionado else (170, 175, 220)
            surface = self.fonte_media.render(nome_tecla, True, cor)
            tela.blit(surface, surface.get_rect(midright=(rect.right -
                                                          l.px(14),
                                                          rect.centery)))
        surface = self.fonte_media.render(
            "ENTER: remapear   ESC: voltar", True, (150, 155, 200))
        tela.blit(surface, surface.get_rect(center=(l.x(0.5),
                                                    l.altura - l.px(60))))

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

    def _desenhar_config(self, tela):
        l = self.layout
        self._cabecalho_sub(tela, "CONFIGURACOES", (120, 160, 255))
        if self.remapando:
            self._desenhar_remapando(tela)
            return
        if self.config_submodo == "controles":
            self._desenhar_controles(tela)
            return

        painel = self._painel_config()
        retangulo_suave(tela, (20, 20, 42), painel, 12)
        retangulo_suave(tela, (110, 90, 220), painel, 12, 2,
                        glow_cor=(110, 90, 220), glow_raio=12)

        for i, (rotulo, tipo) in enumerate(self._linhas_config()):
            y = self._y_linha_config(i)
            selecionada = (i == self.config_selecao)
            cor = BRANCO if selecionada else (190, 195, 235)
            surface = self.fonte_media.render(rotulo, True, cor)
            tela.blit(surface, (l.px(190), y - l.px(12)))
            if selecionada:
                pygame.draw.rect(tela, (255, 200, 100),
                                 (l.px(175), y - l.px(24), l.px(6), l.px(30)),
                                 border_radius=3)
            if tipo == "slider":
                if i == 4:
                    fracao = max(0.0, min(1.0,
                                          self.jogo.config["sensibilidade"] - 0.5))
                    percentual = int((0.5 + fracao) * 100)
                else:
                    chave = "musica_volume" if i == 0 else "efeitos_volume"
                    fracao = max(0.0, min(1.0, self.jogo.config[chave]))
                    percentual = int(fracao * 100)
                self._desenhar_slider(tela, y, fracao)
                surface = self.fonte_media.render(f"{percentual}%", True,
                                                  (170, 175, 220))
                tela.blit(surface, (l.px(720), y - l.px(12)))
            elif tipo == "resolucao":
                surface = self.fonte_media.render(
                    self.jogo.config["resolucao"], True, CIANO)
                tela.blit(surface, surface.get_rect(midleft=(l.px(420), y)))
            elif tipo == "toggle":
                self._desenhar_toggle(tela, l.px(420), y,
                                      self.jogo.config["tela_cheia"])
                estado = self.jogo.config["tela_cheia"]
                surface = self.fonte_media.render(
                    "LIGADO" if estado else "DESLIGADO", True,
                    VERDE if estado else (160, 160, 190))
                tela.blit(surface, surface.get_rect(midleft=(l.px(510), y)))
            elif tipo == "controles":
                surface = self.fonte_media.render(
                    "PERSONALIZAR >", True,
                    (200, 150, 255) if selecionada else (150, 155, 200))
                tela.blit(surface, surface.get_rect(midleft=(l.px(420), y)))
            elif tipo == "tema":
                surface = self.fonte_media.render(
                    self.jogo.config["tema"], True, (255, 160, 200))
                tela.blit(surface, surface.get_rect(midleft=(l.px(420), y)))
            elif tipo == "aspecto":
                surface = self.fonte_media.render(
                    self.jogo.config["aspecto"], True, QUANTUM_CYAN)
                tela.blit(surface, surface.get_rect(midleft=(l.px(420), y)))
                dica = ("SAFE AREAS" if self.jogo.config["aspecto"] ==
                        "AJUSTAR" else "ESTICA TELA")
                surface = self.fonte_pequena.render(dica, True,
                                                    (150, 155, 200))
                tela.blit(surface, surface.get_rect(midleft=(l.px(520), y)))

        b_salvar = BotaoNeon("SALVAR", (l.x(0.5) - l.px(190),
                                        l.altura - l.px(80), l.px(180),
                                        l.px(44)))
        b_voltar = BotaoNeon("VOLTAR", (l.x(0.5) + l.px(10),
                                        l.altura - l.px(80), l.px(180),
                                        l.px(44)))
        for botao in (b_salvar, b_voltar):
            botao.atualizar(self.mouse)
            botao.desenhar(tela, self.fonte_media)

    # ------------------------------------------------------ cabecalho e titulo

    def _frac(self, inicio, duracao):
        p = (self.entrada_t - inicio) / duracao
        return 0.0 if p < 0 else 1.0 if p > 1 else p

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
            void = texto_suave(self.fonte_titulo_grande, "VOID", BRANCO,
                               None, 0, True)
            shift = texto_suave(self.fonte_fury, "//SHIFT", tema["primaria"],
                                tema["primaria"], 8, True)
            shift = pygame.transform.rotate(shift, -2)
            sub = self._espacado(self.fonte_legenda, "ENTER THE RIFT.", 4,
                                 tema["primaria"])
            tag = self._espacado(self.fonte_legenda, "// DIMENSIONAL COMBAT",
                                 2, tema["secundaria"])
            self._titulo_cache[nome] = {
                "void": void, "shift": shift, "sub": sub, "tag": tag}
        return self._titulo_cache[nome]

    def _bloco_fury(self, tema):
        nome = self.jogo.config["tema"]
        if nome in self._bloco_fury_cache:
            return self._bloco_fury_cache[nome]
        l = self.layout
        w, h, inc = l.px(430), l.px(130), l.px(26)
        surf = pygame.Surface((w, h + inc), pygame.SRCALPHA)
        pts = [(0, inc), (w, 0), (w, h), (0, h + inc)]
        pygame.draw.polygon(surf, tema["primaria"] + (70,), pts)
        pygame.draw.polygon(surf, tema["primaria"] + (170,), pts, 2)
        pygame.draw.line(surf, (255, 255, 255, 70), (0, inc + 6), (w, 6), 5)
        pygame.draw.polygon(surf, tema["secundaria"] + (90,),
                            [(0, h + inc - 10), (70, h + inc - 34),
                             (0, h + inc - 34)])
        self._bloco_fury_cache[nome] = surf
        return surf

    def _cabecalho_bloco(self, cor, largura):
        chave = (tuple(cor), int(largura))
        if chave in self._cabecalho_cache:
            return self._cabecalho_cache[chave]
        l = self.layout
        h, inc = l.px(56), l.px(12)
        surf = pygame.Surface((int(largura), h + inc), pygame.SRCALPHA)
        pts = [(0, inc), (int(largura), 0), (int(largura), h), (0, h + inc)]
        pygame.draw.polygon(surf, cor + (50,), pts)
        pygame.draw.polygon(surf, cor + (200,), pts, 2)
        self._cabecalho_cache[chave] = surf
        return surf

    def _cabecalho_sub(self, tela, texto, cor, y=58):
        l = self.layout
        fonte = self.fonte_cabecalho
        surf = self._espacado(fonte, texto, 3, BRANCO)
        cx = l.x(0.5)
        y = l.px(y)
        w = surf.get_width() + l.px(80)
        bloco = self._cabecalho_bloco(cor, w)
        desenhar_glow(tela, cor, (cx, y + l.px(6)), max(l.px(24), w // 8),
                      0.35)
        tela.blit(bloco, bloco.get_rect(center=(cx, y + l.px(6))))
        tela.blit(surf, surf.get_rect(center=(cx, y)))

    # -------------------------------------------------------------- desenho

    def _desenhar_linhas_diagonais(self, tela, tema):
        if self.entrada_t < 0.12:
            return
        l = self.layout
        prim = tema["primaria"]
        cor1 = tuple(int(c * 0.85) for c in prim)
        pygame.draw.aaline(tela, cor1, l.ponto(TOPO_ESQUERDA, 30, 470),
                           l.ponto(TOPO_ESQUERDA, 470, 180), 2)
        pygame.draw.aaline(tela, tema["borda_fraco"],
                           l.ponto(TOPO_ESQUERDA, 66, 470),
                           l.ponto(TOPO_ESQUERDA, 506, 180), 1)
        pygame.draw.aaline(tela, cor1, l.ponto(TOPO_DIREITA, 0, 330),
                           l.ponto(TOPO_ESQUERDA, 640, 486), 1)

    def _desenhar_bloco_titulo(self, tela, tema):
        l = self.layout
        ts = self._titulo_surfaces(tema)
        p_titulo = self._frac(0.10, 0.5)
        p_bloco = self._frac(0.06, 0.28)
        p_sub = self._frac(0.55, 0.4)
        off = int((1 - ease_out_back(p_titulo)) * -l.px(300))
        alfa = int(255 * ease_out(p_titulo))
        if p_bloco > 0:
            bloco = self._bloco_fury(tema)
            self._blit_alfa(tela, bloco, l.ponto(TOPO_ESQUERDA, 36, 166),
                            255 * ease_out(p_bloco))
        self._blit_alfa(tela, ts["void"],
                        (l.px(56) + off, l.px(118)), alfa)
        self._blit_alfa(tela, ts["shift"],
                        (l.px(48) + off, l.px(208)), alfa)
        alfa_sub = int(255 * ease_out(p_sub))
        self._blit_alfa(tela, ts["sub"],
                        (l.px(60) + off, l.px(340)), alfa_sub)
        self._blit_alfa(tela, ts["tag"],
                        (l.px(60) + off, l.px(372)), alfa_sub)

    def _desenhar_seta(self, tela, tema):
        if self.entrada_t < 0.7:
            return
        op = self.opcoes[self.opcao_selecionada]
        x = self.x_opcoes - self.layout.px(58)
        y = op.y
        pygame.draw.polygon(tela, tema["secundaria"],
                            [(x, y), (x + 15, y - 9), (x + 15, y + 9)])
        pygame.draw.polygon(tela, tema["primaria"],
                            [(x - 9, y), (x - 1, y - 5), (x - 1, y + 5)])

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
        self._blit_alfa(tela, surf2, (self.x_opcoes, l.y(0.78)),
                        int(alfa * 0.75))
        versao = self._espacado(f, "v3.0 // ENTER THE RIFT", 1,
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
        if self.subestado == "MENU":
            self._desenhar_menu(tela)
        elif self.subestado == "CONTINUAR":
            self._desenhar_continuar(tela)
        elif self.subestado == "LOJA":
            self._desenhar_loja(tela)
        elif self.subestado == "RECORDES":
            self._desenhar_recordes(tela)
        elif self.subestado == "CONFIG":
            self._desenhar_config(tela)
        self.notificacoes.desenhar(tela, self.fonte_media)
        if self.dialogo and self.dialogo.ativo:
            self.dialogo.desenhar(tela, self.fonte_sub, self.fonte_media,
                                  self.mouse)
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
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._clique(self._pos_logica(evento.pos))
        elif evento.type == pygame.KEYDOWN:
            return self._tecla(evento)
        return True

    def _pos_logica(self, pos):
        """Converte coordenadas da janela para a superficie logica.

        No modo AJUSTAR aplica escala proporcional e offsets do letterbox
        (safe areas); no PREENCHE usa a proporcao direta da janela. A
        superficie logica e a grade do ``Layout`` atual.
        """
        try:
            if self.jogo.config["aspecto"] == "PREENCHE":
                w, h = self.jogo.janela.get_size()
                return (int(pos[0] * self.layout.largura / w),
                        int(pos[1] * self.layout.altura / h))
            escala, off_x, off_y = self.jogo._escala_janela()
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
        if self.subestado == "MENU":
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
            else:
                if (evento.unicode and evento.unicode.isprintable() and
                        len(self.jogo.nome_jogador) < 12):
                    self.jogo.nome_jogador += evento.unicode
            return True

        if self.subestado == "CONTINUAR":
            if evento.key in (pygame.K_UP, pygame.K_DOWN):
                self.continuar_selecao = 1 - self.continuar_selecao
                self._som("navegar")
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._acao_continuar(self.continuar_selecao)
            elif evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self._voltar_menu()
            return True

        if self.subestado == "LOJA":
            return self._tecla_loja(evento)

        if self.subestado == "RECORDES":
            if evento.key in (pygame.K_ESCAPE, pygame.K_RETURN,
                              pygame.K_BACKSPACE):
                self._voltar_menu()
            return True

        if self.subestado == "CONFIG":
            return self._tecla_config(evento)
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

        linhas = self._linhas_config()
        n = len(linhas)
        if evento.key in (pygame.K_UP, pygame.K_w):
            self.config_selecao = (self.config_selecao - 1) % n
            self._som("navegar")
        elif evento.key in (pygame.K_DOWN, pygame.K_s):
            self.config_selecao = (self.config_selecao + 1) % n
            self._som("navegar")
        elif evento.key == pygame.K_LEFT:
            self._ajustar_config(-1)
        elif evento.key == pygame.K_RIGHT:
            self._ajustar_config(1)
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.config_selecao == 5:
                self.config_submodo = "controles"
                self.controle_selecao = 0
                self._som("navegar")
            else:
                self._ajustar_config(1)
        elif evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self._voltar_menu()
        return True

    def _clique(self, pos):
        self.mouse = pos
        if self.subestado == "MENU":
            for i, opcao in enumerate(self.opcoes):
                if opcao.get_rect(self.x_opcoes, self.fonte_opcao,
                                  self.layout).collidepoint(pos):
                    self._selecionar(i)
                    opcao.funcao()
                    return
            return
        if self.subestado == "CONTINUAR":
            for i, botao in enumerate(self._botoes_continuar()):
                if botao.rect.collidepoint(pos):
                    self._acao_continuar(i)
                    return
            return
        if self.subestado == "LOJA":
            self._clique_loja(pos)
            return
        if self.subestado == "RECORDES":
            if self._botao_voltar().rect.collidepoint(pos):
                self._voltar_menu()
            return
        if self.subestado == "CONFIG":
            self._clique_config(pos)
            return

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
