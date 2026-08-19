"""Menu profissional: telas, animacoes, notificacoes e dialogos.

Implementa o menu principal com fundo animado (parallax + nebulosas), titulo
com glow pulsante, opcoes com hover/animacao, tela de continuar, loja de
skins, recordes, configuracoes (com tela cheia) e transicoes suaves.
"""

import math
import os
import random

import pygame

from .config import ALTURA, BRANCO, CIANO, DOURADO, LARGURA, VERDE
from .fonts import fonte_texto, fonte_titulo
from .player import Jogador
from .save_system import ARQUIVO_RECORDES, SistemaProgressao
from .settings import ACOES_CONTROLE, RESOLUCOES, TEMAS
from .shop import LojaSkins
from .smooth import desenhar_circulo as desenhar_circulo_suave, \
    desenhar_texto_suave, retangulo_suave
from .theme import cor_tema

NEGRO = (0, 0, 0)


def formatar_pontos(n):
    """Formata numeros com separador de milhar no padrao brasileiro."""
    return f"{n:,}".replace(",", ".")


def desenhar_texto_com_glow(tela, texto, fonte, cor, pos, glow_cor=None):
    """Desenha texto com efeito de glow/brilho e pulsacao."""
    if glow_cor is None:
        glow_cor = cor_tema(chave="secundaria")
    desenhar_texto_suave(tela, fonte, texto, pos, cor, glow_cor=glow_cor,
                         glow_raio=5, sombra=True)
    pulse = int(60 + 50 * math.sin(pygame.time.get_ticks() / 900))
    surf = fonte.render(texto, True, BRANCO)
    surf.set_alpha(pulse)
    tela.blit(surf, surf.get_rect(center=pos))


class FundoAnimado:
    """Fundo cosmic com camadas de estrelas (parallax), nebulosas e meteoros."""

    def __init__(self):
        self.camadas = [
            {"velocidade": 0.4, "cor": (110, 110, 175), "estrelas": []},
            {"velocidade": 1.0, "cor": (185, 185, 235), "estrelas": []},
            {"velocidade": 2.2, "cor": (255, 255, 255), "estrelas": []},
        ]
        for camada in self.camadas:
            for _ in range(55):
                camada["estrelas"].append([
                    random.randint(0, LARGURA),
                    random.randint(0, ALTURA),
                    random.uniform(0.6, 1.9),
                ])
        self.gradiente = self._criar_gradiente((14, 9, 36), (3, 2, 15))
        self.nebulosas = self._criar_nebulosas([
            (95, 40, 170), (35, 75, 170), (170, 45, 135), (45, 145, 170)])
        self.meteoros = [self._novo_meteoro() for _ in range(3)]
        self.onda = 0.0

    def _novo_meteoro(self):
        return {
            "x": random.uniform(0, LARGURA), "y": random.uniform(0, 130),
            "vx": random.uniform(-3.2, -1.4),
            "vy": random.uniform(2.2, 3.6),
            "vida": random.uniform(45, 95), "t": 0,
        }

    def _criar_gradiente(self, topo, base):
        surf = pygame.Surface((LARGURA, ALTURA))
        for y in range(ALTURA):
            t = y / ALTURA
            cor = tuple(int(topo[i] + (base[i] - topo[i]) * t) for i in range(3))
            pygame.draw.line(surf, cor, (0, y), (LARGURA, y))
        return surf

    def _criar_nebulosas(self, cores):
        nebulosas = []
        for _ in range(6):
            surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            x = random.randint(0, LARGURA)
            y = random.randint(0, ALTURA)
            raio = random.randint(140, 280)
            cor = random.choice(cores)
            for r in range(raio, 0, -1):
                alfa = int(13 * (1 - r / raio) ** 2)
                pygame.draw.circle(surf, cor + (alfa,), (x, y), r)
            nebulosas.append((surf, random.uniform(-0.2, 0.2),
                              random.uniform(-0.1, 0.1)))
        return nebulosas

    def atualizar(self):
        self.onda += 0.02
        for camada in self.camadas:
            for estrela in camada["estrelas"]:
                estrela[1] += camada["velocidade"]
                if estrela[1] > ALTURA + 5:
                    estrela[1] = -5
                    estrela[0] = random.randint(0, LARGURA)
        for m in self.meteoros[:]:
            m["x"] += m["vx"]
            m["y"] += m["vy"]
            m["t"] += 1
            if m["t"] >= m["vida"]:
                self.meteoros.remove(m)
                self.meteoros.append(self._novo_meteoro())

    def desenhar(self, tela):
        tela.blit(self.gradiente, (0, 0))
        t = pygame.time.get_ticks() * 0.001
        for surf, dx, dy in self.nebulosas:
            off_x = int(math.sin(t * 0.1 + dx) * 22)
            off_y = int(math.cos(t * 0.08 + dy) * 14)
            tela.blit(surf, (off_x, off_y))
        for camada in self.camadas:
            for x, y, tam in camada["estrelas"]:
                brilho = 0.5 + 0.5 * math.sin(y / 40 + self.onda * 2 + x * 0.2)
                cor = tuple(int(c * brilho) for c in camada["cor"])
                pygame.draw.circle(tela, cor, (int(x), int(y)),
                                   max(1, int(tam)))
        for m in self.meteoros:
            fade = 1 - m["t"] / m["vida"]
            cor = tuple(int(230 * fade) for _ in range(3))
            pygame.draw.line(tela, cor, (int(m["x"]), int(m["y"])),
                             (int(m["x"] - m["vx"] * 7),
                              int(m["y"] - m["vy"] * 7)), 1)


class OpcaoMenu:
    """Opcao do menu com hover, escala e seta animada."""

    def __init__(self, texto, pos, funcao, cor_normal=(190, 195, 255),
                 cor_hover=(255, 255, 255)):
        self.texto = texto
        self.pos = pos
        self.funcao = funcao
        self.cor_normal = cor_normal
        self.cor_hover = cor_hover
        self.hover = False
        self.animacao = 0.0

    def get_rect(self, fonte):
        larg = fonte.size(self.texto)[0]
        alt = fonte.get_height()
        return pygame.Rect(self.pos[0] - larg // 2 - 12,
                           self.pos[1] - alt // 2, larg + 24, alt)

    def atualizar(self, mouse_pos, fonte):
        self.hover = self.get_rect(fonte).collidepoint(mouse_pos)
        alvo = 1.0 if self.hover else 0.0
        self.animacao += (alvo - self.animacao) * 0.2

    def desenhar(self, tela, fonte, selecionado=False):
        cor = tuple(int(a + (b - a) * self.animacao)
                    for a, b in zip(self.cor_normal, self.cor_hover))
        rect = self.get_rect(fonte)
        if self.animacao > 0.02:
            surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            alfa = int(60 * self.animacao)
            pygame.draw.rect(surf, (130, 85, 255, alfa), surf.get_rect(),
                             border_radius=10)
            tela.blit(surf, rect.topleft)
            pygame.draw.rect(tela, (150, 115, 255), rect, 1,
                             border_radius=10)
        surface = fonte.render(self.texto, True, cor)
        tela.blit(surface, surface.get_rect(center=self.pos))
        if selecionado or self.hover:
            pulso = (pygame.time.get_ticks() // 450) % 2
            if selecionado or pulso:
                self._desenhar_seta(tela, rect.left - 30, self.pos[1])
                self._desenhar_seta(tela, rect.right + 14, self.pos[1],
                                    invertida=True)

    def _desenhar_seta(self, tela, x, y, invertida=False):
        if invertida:
            pontos = [(x, y), (x - 16, y - 9), (x - 16, y + 9)]
        else:
            pontos = [(x, y), (x + 16, y - 9), (x + 16, y + 9)]
        pygame.draw.polygon(tela, (255, 100, 255), pontos)


class BotaoNeon:
    """Botao com hover para as telas internas do menu."""

    def __init__(self, texto, rect, cor=(48, 44, 105), cor_hover=(92, 76, 190)):
        self.texto = texto
        self.rect = pygame.Rect(rect)
        self.cor = cor
        self.cor_hover = cor_hover
        self.hover = False

    def atualizar(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)

    def desenhar(self, tela, fonte):
        cor = self.cor_hover if self.hover else self.cor
        borda = BRANCO if self.hover else (150, 130, 255)
        retangulo_suave(tela, cor, self.rect, 10,
                        glow_cor=cor if self.hover else None,
                        glow_raio=max(4, self.rect.h) if self.hover else 0)
        pygame.draw.rect(tela, borda, self.rect, 2, border_radius=10)
        desenhar_texto_suave(tela, fonte, self.texto, self.rect.center, BRANCO,
                             glow_raio=2)


class SistemaNotificacao:
    """Notificacoes temporarias (toasts) no canto superior direito."""

    CORES = {"sucesso": (0, 130, 60), "erro": (150, 20, 20),
             "conquista": (150, 100, 0), "info": (30, 60, 130)}

    def __init__(self):
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
        y = 24
        for notif in self.notificacoes[:]:
            texto = fonte.render(notif["mensagem"], True, BRANCO)
            largura = texto.get_width() + 48
            fundo = pygame.Surface((largura, 44), pygame.SRCALPHA)
            cor = self.CORES[notif["tipo"]]
            rect = pygame.Rect(0, 0, largura, 44)
            pygame.draw.rect(fundo, cor + (int(notif["alpha"] * 0.85),),
                             rect, border_radius=8)
            pygame.draw.rect(fundo, BRANCO + (int(notif["alpha"]),),
                             rect, 1, border_radius=8)
            x = LARGURA - largura - 20
            tela.blit(fundo, (x, y))
            texto.set_alpha(notif["alpha"])
            tela.blit(texto, (x + 24, y + 11))
            y += 54


class Dialogo:
    """Dialogo modal com confirmar/cancelar (mouse e teclado)."""

    def __init__(self, titulo, mensagem, funcao_confirmar, funcao_cancelar):
        self.titulo = titulo
        self.mensagem = mensagem
        self.funcao_confirmar = funcao_confirmar
        self.funcao_cancelar = funcao_cancelar
        self.ativo = True
        self._largura, self._altura = 500, 250
        self._x = LARGURA // 2 - self._largura // 2
        self._y = ALTURA // 2 - self._altura // 2

    def _retangulos(self):
        confirmar = pygame.Rect(self._x + 90, self._y + self._altura - 70,
                                130, 42)
        cancelar = pygame.Rect(self._x + 280, self._y + self._altura - 70,
                               130, 42)
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
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        tela.blit(overlay, (0, 0))
        rect = pygame.Rect(self._x, self._y, self._largura, self._altura)
        retangulo_suave(tela, (25, 25, 48), rect, 12)
        retangulo_suave(tela, (120, 90, 220), rect, 12, 2,
                        glow_cor=(120, 90, 220), glow_raio=12)
        titulo = fonte_titulo.render(self.titulo, True, (255, 200, 100))
        tela.blit(titulo, titulo.get_rect(center=(rect.centerx, rect.y + 34)))

        palavras = self.mensagem.split()
        linhas, atual = [], []
        for palavra in palavras:
            teste = " ".join(atual + [palavra])
            if fonte_texto.size(teste)[0] > self._largura - 40:
                linhas.append(" ".join(atual))
                atual = [palavra]
            else:
                atual.append(palavra)
        if atual:
            linhas.append(" ".join(atual))
        for i, linha in enumerate(linhas):
            surface = fonte_texto.render(linha, True, (200, 205, 255))
            tela.blit(surface, surface.get_rect(center=(rect.centerx,
                                                        rect.y + 84 + i * 30)))

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

    def __init__(self, duracao=450):
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
            overlay = pygame.Surface((LARGURA, ALTURA))
            overlay.fill(NEGRO)
            overlay.set_alpha(self.alpha)
            tela.blit(overlay, (0, 0))


class MenuPrincipal:
    """Controla todas as telas do menu (menu, continuar, loja, recordes, config)."""

    def __init__(self, jogo):
        self.jogo = jogo
        self.subestado = "MENU"
        self.fundo = FundoAnimado()
        self.notificacoes = SistemaNotificacao()
        self.dialogo = None
        self.transicao = TransicaoTela()
        self.alpha_entrada = 0
        self.mouse = (0, 0)

        self.fonte_titulo = fonte_titulo(88)
        self.fonte_sub = fonte_texto(44)
        self.fonte_opcao = fonte_titulo(34)
        self.fonte_media = fonte_texto(26)
        self.fonte_pequena = fonte_texto(20)

        self.opcao_selecionada = 0
        self.opcoes = []
        self._construir_opcoes_menu()

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
            ("CONTINUAR", self._abrir_continuar),
            ("NOVO JOGO", self._novo_jogo_direto),
            ("LOJA DE SKINS", self._abrir_loja),
            ("RECORDES", self._abrir_recordes),
            ("CONFIGURACOES", self._abrir_config),
            ("SAIR", self._sair),
        ]
        y = 336
        self.opcoes = []
        for texto, funcao in itens:
            self.opcoes.append(OpcaoMenu(texto, (LARGURA // 2, y), funcao))
            y += 52
        self.opcao_selecionada = 0

    def _abrir_continuar(self):
        self._som("navegar")
        self.continuar_selecao = 0
        self.subestado = "CONTINUAR"
        self.transicao.iniciar()

    def _novo_jogo_direto(self):
        self._som("navegar")
        self.jogo._preparar_jogo()

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

    def _mostrar_dialogo(self, titulo, mensagem, confirmar, cancelar):
        self.dialogo = Dialogo(titulo, mensagem, confirmar, cancelar)

    # ----------------------------------------------------------- continuar

    def _tem_save(self):
        return self.jogo.progresso.existe_save()

    def _acao_continuar(self, indice):
        if indice == 0:
            if self._tem_save():
                self.jogo._preparar_jogo()
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
        self.jogo._preparar_jogo()

    def _botoes_continuar(self):
        largura = 205
        x1 = LARGURA // 2 - largura - 15
        x2 = LARGURA // 2 + 15
        b0 = BotaoNeon("CONTINUAR", (x1, ALTURA - 118, largura, 48))
        b1 = BotaoNeon("NOVO JOGO", (x2, ALTURA - 118, largura, 48))
        b2 = BotaoNeon("VOLTAR", (LARGURA // 2 - 90, ALTURA - 60, 180, 42))
        return [b0, b1, b2]

    def _desenhar_continuar(self, tela):
        desenhar_texto_com_glow(tela, "CARREGANDO JOGO...", self.fonte_sub,
                                (130, 205, 255), (LARGURA // 2, 85),
                                glow_cor=(60, 120, 255))
        tem = self._tem_save()
        painel = pygame.Rect(LARGURA // 2 - 260, 150, 520, 330)
        retangulo_suave(tela, (22, 22, 46), painel, 12)
        retangulo_suave(tela, (110, 90, 220), painel, 12, 2,
                        glow_cor=(110, 90, 220), glow_raio=12)
        jog = self.jogo.progresso.jogador
        titulo = ("Save Encontrado" if tem else "Nenhum Save")
        cor = (150, 230, 120) if tem else (230, 120, 120)
        surface = self.fonte_media.render(titulo, True, cor)
        tela.blit(surface, surface.get_rect(center=(painel.centerx,
                                                    painel.y + 28)))
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
            y = painel.y + 62
            for rotulo, valor in linhas:
                surface = self.fonte_media.render(f"{rotulo}:", True,
                                                  (170, 175, 225))
                tela.blit(surface, (painel.x + 70, y))
                surface = self.fonte_media.render(valor, True, BRANCO)
                tela.blit(surface, surface.get_rect(midleft=(painel.x + 250,
                                                             y + 9)))
                y += 36
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
        colunas, celula = 4, 205
        x_inicio = (LARGURA - colunas * celula) // 2
        y_inicio = 122
        return [pygame.Rect(x_inicio + (i % colunas) * celula,
                            y_inicio + (i // colunas) * 150,
                            celula - 10, 138)
                for i in range(len(self.jogo.loja.skins))]

    def _botoes_loja(self):
        nomes = ["COMPRAR", "EQUIPAR", "PREVIEW", "VOLTAR"]
        largura, espaco = 140, 18
        total = largura * 4 + espaco * 3
        x = (LARGURA - total) // 2
        y = ALTURA - 94
        return {nome.lower(): BotaoNeon(nome, (x + i * (largura + espaco),
                                               y, largura, 46))
                for i, nome in enumerate(nomes)}

    def _desenhar_preview_skin(self, tela, skin, x, y):
        prev = Jogador(skin=skin)
        prev.x, prev.y = x, y
        prev.tilt = 0
        prev.invencivel = 0
        prev.desenhar(tela, None)

    def _desenhar_loja(self, tela):
        desenhar_texto_com_glow(tela, "LOJA DE SKINS", self.fonte_sub,
                                (150, 90, 255), (LARGURA // 2, 55),
                                glow_cor=(255, 255, 255))
        surface = self.fonte_media.render(
            f"Moedas: {formatar_pontos(self.jogo.loja.moedas)}", True,
            DOURADO)
        tela.blit(surface, (20, 30))
        skin_atual = self.jogo.loja.pegar_skin(self.jogo.loja.skin_atual)
        surface = self.fonte_media.render(
            f"Skin atual: {skin_atual.nome}", True, CIANO)
        tela.blit(surface, surface.get_rect(topright=(LARGURA - 20, 30)))

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
            self._desenhar_preview_skin(tela, skin, rect.centerx, rect.y + 62)
            surface = self.fonte_pequena.render(skin.nome, True, BRANCO)
            tela.blit(surface, surface.get_rect(center=(rect.centerx,
                                                        rect.y + 18)))
            if skin.desbloqueada:
                status = ("EQUIPADA" if skin.id == self.jogo.loja.skin_atual
                          else "DESBLOQ.")
                cor = CIANO if skin.id == self.jogo.loja.skin_atual else VERDE
            else:
                status = f"{formatar_pontos(skin.preco)} pts"
                cor = DOURADO
            surface = self.fonte_pequena.render(status, True, cor)
            tela.blit(surface, surface.get_rect(center=(rect.centerx,
                                                        rect.y + 122)))

        for botao in self._botoes_loja().values():
            botao.atualizar(self.mouse)
            botao.desenhar(tela, self.fonte_media)
        skin = self.jogo.loja.skins[self.loja_selecao]
        surface = self.fonte_pequena.render(skin.descricao, True,
                                            (170, 175, 220))
        tela.blit(surface, surface.get_rect(center=(LARGURA // 2, ALTURA - 36)))

        if self.preview_skin:
            self._desenhar_preview_overlay(tela)

    def _desenhar_preview_overlay(self, tela):
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 195))
        tela.blit(overlay, (0, 0))
        skin = self.preview_skin
        desenhar_texto_com_glow(tela, skin.nome, self.fonte_sub,
                                (170, 120, 255), (LARGURA // 2, 130),
                                glow_cor=(255, 255, 255))
        prev = Jogador(skin=skin)
        prev.x, prev.y = LARGURA // 2, ALTURA // 2 - 60
        prev.tilt = 0
        prev.invencivel = 0
        prev.desenhar(tela, None)
        surface = self.fonte_media.render(skin.descricao, True, (200, 205, 240))
        tela.blit(surface, surface.get_rect(center=(LARGURA // 2,
                                                    ALTURA // 2 + 90)))
        if skin.id == self.jogo.loja.skin_atual:
            status, cor = "Equipada", CIANO
        elif skin.desbloqueada:
            status, cor = "Desbloqueada", VERDE
        else:
            status, cor = f"Preco: {formatar_pontos(skin.preco)} pts", DOURADO
        surface = self.fonte_media.render(status, True, cor)
        tela.blit(surface, surface.get_rect(center=(LARGURA // 2,
                                                    ALTURA // 2 + 130)))
        botoes = {"equipar": BotaoNeon("EQUIPAR", (LARGURA // 2 - 170,
                                                   ALTURA - 120, 160, 48)),
                  "fechar": BotaoNeon("FECHAR", (LARGURA // 2 + 10,
                                                 ALTURA - 120, 160, 48))}
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
        return BotaoNeon("VOLTAR", (LARGURA // 2 - 90, ALTURA - 64, 180, 46))

    def _desenhar_recordes(self, tela):
        desenhar_texto_com_glow(tela, "RECORDES", self.fonte_sub,
                                (140, 120, 255), (LARGURA // 2, 80),
                                glow_cor=(255, 215, 0))
        lista = self.jogo.recordes
        painel = pygame.Rect(LARGURA // 2 - 260, 150, 520, 330)
        retangulo_suave(tela, (22, 22, 46), painel, 12)
        retangulo_suave(tela, (110, 90, 220), painel, 12, 2,
                        glow_cor=(110, 90, 220), glow_raio=12)
        surface = self.fonte_media.render("TOP 5", True, CIANO)
        tela.blit(surface, surface.get_rect(center=(painel.centerx,
                                                    painel.y + 28)))
        if not lista:
            surface = self.fonte_media.render(
                "Nenhum recorde ainda.", True, (200, 205, 240))
            tela.blit(surface, surface.get_rect(center=painel.center))
        else:
            y = painel.y + 70
            for i, reg in enumerate(lista[:5]):
                cor = DOURADO if i == 0 else (205, 210, 235) if i < 3 \
                    else (150, 155, 190)
                texto = (f"TOP {i + 1}. {reg['nome']}  "
                         f"{formatar_pontos(reg['pontos'])} pts  "
                         f"(Nivel {reg['nivel']})")
                surface = self.fonte_media.render(texto, True, cor)
                tela.blit(surface, surface.get_rect(center=(painel.centerx,
                                                            y)))
                y += 52

        jog = self.jogo.progresso.jogador
        estatisticas = self.jogo.progresso.dados["estatisticas"]
        melhor = formatar_pontos(lista[0]["pontos"]) if lista else "0"
        linha = (f"Seu melhor: {melhor} pts  |  "
                 f"Skins: {len(self.jogo.loja.lista_desbloqueadas())}/10  |  "
                 f"Inimigos: {estatisticas['inimigos_derrotados']}  |  "
                 f"Bosses: {jog['bosses_derrotados']}")
        surface = self.fonte_media.render(linha, True, (170, 175, 220))
        tela.blit(surface, surface.get_rect(center=(LARGURA // 2, 505)))

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
        ]

    def _y_linha_config(self, indice):
        return 172 + indice * 54

    def _desenhar_slider(self, tela, y, fracao):
        x0, x1 = 400, 700
        track = pygame.Rect(x0, y - 5, x1 - x0, 12)
        retangulo_suave(tela, (40, 40, 70), track, 6)
        preenchido = int((x1 - x0) * max(0.0, min(1.0, fracao)))
        retangulo_suave(tela, CIANO,
                        pygame.Rect(x0, y - 5, preenchido, 12), 6,
                        glow_cor=CIANO, glow_raio=8)
        retangulo_suave(tela, BRANCO, track, 6, 1)
        desenhar_circulo_suave(tela, BRANCO, (x0 + preenchido, y), 8,
                               brilho=1.3)

    def _slider_fracao(self, mouse_x):
        return max(0.0, min(1.0, (mouse_x - 400) / 300))

    def _desenhar_toggle(self, tela, x, y, ligado):
        off = pygame.Rect(x, y - 11, 54, 24)
        cor = (50, 100, 60) if ligado else (80, 40, 40)
        retangulo_suave(tela, cor, off, 12, glow_cor=cor if ligado else None,
                        glow_raio=8 if ligado else 0)
        retangulo_suave(tela, BRANCO, off, 12, 1)
        cx = x + (44 if ligado else 10)
        desenhar_circulo_suave(tela, BRANCO, (cx, y), 10, brilho=1.3)

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
        self._som("navegar")

    def _clique_config(self, pos):
        if self.remapando:
            return
        if self.config_submodo == "controles":
            painel = pygame.Rect(160, 130, LARGURA - 320, 420)
            for i, acao in enumerate(ACOES_CONTROLE):
                rect = pygame.Rect(painel.x + 30, painel.y + 64 + i * 48,
                                   painel.width - 60, 40)
                if rect.collidepoint(pos):
                    self.controle_selecao = i
                    self.remapando = acao
                    self._som("navegar")
                    return
            if pos[1] > ALTURA - 70:
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
                elif linhas[i][1] == "slider":
                    self._aplicar_slider(i, self._slider_fracao(pos[0]))
                return

        b_salvar = pygame.Rect(LARGURA // 2 - 190, ALTURA - 80, 180, 44)
        b_voltar = pygame.Rect(LARGURA // 2 + 10, ALTURA - 80, 180, 44)
        if b_salvar.collidepoint(pos):
            self.jogo.config.salvar()
            self.notificacoes.adicionar("Configuracoes salvas!", "sucesso")
            self._som("equipar")
        elif b_voltar.collidepoint(pos):
            self._voltar_menu()

    def _desenhar_controles(self, tela):
        painel = pygame.Rect(160, 130, LARGURA - 320, 420)
        retangulo_suave(tela, (20, 20, 42), painel, 12)
        retangulo_suave(tela, (110, 90, 220), painel, 12, 2,
                        glow_cor=(110, 90, 220), glow_raio=12)
        surface = self.fonte_media.render("CONTROLES", True, CIANO)
        tela.blit(surface, surface.get_rect(center=(painel.centerx,
                                                    painel.y + 28)))
        for i, acao in enumerate(ACOES_CONTROLE):
            y = painel.y + 64 + i * 48
            rect = pygame.Rect(painel.x + 30, y, painel.width - 60, 40)
            selecionado = (i == self.controle_selecao)
            if selecionado:
                pygame.draw.rect(tela, (50, 46, 90), rect, border_radius=8)
                pygame.draw.rect(tela, (255, 200, 100), rect, 2,
                                 border_radius=8)
            surface = self.fonte_media.render(acao.upper(), True, BRANCO)
            tela.blit(surface, (rect.x + 14, rect.y + 10))
            tecla = self.jogo.config.controles.get(acao, 0)
            nome_tecla = pygame.key.name(tecla).upper() or "?"
            cor = DOURADO if selecionado else (170, 175, 220)
            surface = self.fonte_media.render(nome_tecla, True, cor)
            tela.blit(surface, surface.get_rect(midright=(rect.right - 14,
                                                          rect.centery)))
        surface = self.fonte_media.render(
            "ENTER: remapear   ESC: voltar", True, (150, 155, 200))
        tela.blit(surface, surface.get_rect(center=(LARGURA // 2,
                                                    ALTURA - 60)))

    def _desenhar_remapando(self, tela):
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 205))
        tela.blit(overlay, (0, 0))
        surface = self.fonte_sub.render(
            f"PRESSIONE UMA TECLA PARA {self.remapando.upper()}", True, BRANCO)
        surface.set_alpha(int(180 + 75 * math.sin(pygame.time.get_ticks() * 0.008)))
        tela.blit(surface, surface.get_rect(center=(LARGURA // 2,
                                                    ALTURA // 2 - 30)))
        surface = self.fonte_media.render("ESC para cancelar", True,
                                          (160, 165, 205))
        tela.blit(surface, surface.get_rect(center=(LARGURA // 2,
                                                    ALTURA // 2 + 20)))

    def _desenhar_config(self, tela):
        desenhar_texto_com_glow(tela, "CONFIGURACOES", self.fonte_sub,
                                (120, 160, 255), (LARGURA // 2, 55),
                                glow_cor=(0, 200, 255))
        if self.remapando:
            self._desenhar_remapando(tela)
            return
        if self.config_submodo == "controles":
            self._desenhar_controles(tela)
            return

        painel = pygame.Rect(140, 100, LARGURA - 280, 468)
        retangulo_suave(tela, (20, 20, 42), painel, 12)
        retangulo_suave(tela, (110, 90, 220), painel, 12, 2,
                        glow_cor=(110, 90, 220), glow_raio=12)

        for i, (rotulo, tipo) in enumerate(self._linhas_config()):
            y = self._y_linha_config(i)
            selecionada = (i == self.config_selecao)
            cor = BRANCO if selecionada else (190, 195, 235)
            surface = self.fonte_media.render(rotulo, True, cor)
            tela.blit(surface, (190, y - 12))
            if selecionada:
                pygame.draw.rect(tela, (255, 200, 100),
                                 (175, y - 24, 6, 30), border_radius=3)
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
                tela.blit(surface, (720, y - 12))
            elif tipo == "resolucao":
                surface = self.fonte_media.render(
                    self.jogo.config["resolucao"], True, CIANO)
                tela.blit(surface, surface.get_rect(midleft=(420, y)))
            elif tipo == "toggle":
                self._desenhar_toggle(tela, 420, y,
                                      self.jogo.config["tela_cheia"])
                estado = self.jogo.config["tela_cheia"]
                surface = self.fonte_media.render(
                    "LIGADO" if estado else "DESLIGADO", True,
                    VERDE if estado else (160, 160, 190))
                tela.blit(surface, surface.get_rect(midleft=(510, y)))
            elif tipo == "controles":
                surface = self.fonte_media.render(
                    "PERSONALIZAR >", True,
                    (200, 150, 255) if selecionada else (150, 155, 200))
                tela.blit(surface, surface.get_rect(midleft=(420, y)))
            elif tipo == "tema":
                surface = self.fonte_media.render(
                    self.jogo.config["tema"], True, (255, 160, 200))
                tela.blit(surface, surface.get_rect(midleft=(420, y)))

        b_salvar = BotaoNeon("SALVAR", (LARGURA // 2 - 190, ALTURA - 80,
                                        180, 44))
        b_voltar = BotaoNeon("VOLTAR", (LARGURA // 2 + 10, ALTURA - 80,
                                        180, 44))
        for botao in (b_salvar, b_voltar):
            botao.atualizar(self.mouse)
            botao.desenhar(tela, self.fonte_media)

    # ------------------------------------------------------------- desenho

    def _linha_decorativa(self, tela, y):
        t = pygame.time.get_ticks() * 0.002
        for x in range(0, LARGURA, 12):
            brilho = 0.35 + 0.65 * abs(math.sin(x / 50 + t))
            cor = tuple(int(c * brilho) for c in (150, 60, 255))
            pygame.draw.line(tela, cor, (x, y), (x + 6, y + 8), 2)

    def _ultimo_boss(self):
        from .scenarios import CENARIOS, cenario_do_nivel
        nivel = self.jogo.progresso.jogador["nivel_maximo"]
        return CENARIOS[cenario_do_nivel(nivel) - 1]["nome"].title()

    def _desenhar_menu(self, tela):
        desenhar_texto_com_glow(tela, "SPACE FURY", self.fonte_titulo,
                                (185, 120, 255), (LARGURA // 2, 105))
        surface = self.fonte_sub.render("EDICAO DIMENSIONAL", True,
                                        (220, 180, 255))
        surface.set_alpha(int(190 + 60 * math.sin(pygame.time.get_ticks() * 0.004)))
        tela.blit(surface, surface.get_rect(center=(LARGURA // 2, 178)))
        self._linha_decorativa(tela, 215)

        for i, opcao in enumerate(self.opcoes):
            opcao.desenhar(tela, self.fonte_opcao,
                           selecionado=(i == self.opcao_selecionada))

        linha = (f"Jogador: {self.jogo.nome_jogador}  |  "
                 f"Moedas: {formatar_pontos(self.jogo.loja.moedas)}  |  "
                 f"Ultimo Boss: {self._ultimo_boss()}")
        surface = self.fonte_media.render(linha, True, (160, 170, 220))
        surface.set_alpha(195)
        tela.blit(surface, surface.get_rect(center=(LARGURA // 2,
                                                    ALTURA - 62)))
        surface = self.fonte_pequena.render(
            "Setas/WASD: navegar   ENTER: confirmar   ESC: sair   "
            "Digite para alterar o nome", True, (120, 130, 180))
        surface.set_alpha(180)
        tela.blit(surface, surface.get_rect(center=(LARGURA // 2,
                                                    ALTURA - 34)))
        surface = self.fonte_pequena.render("v2.0", True, (120, 130, 180))
        surface.set_alpha(150)
        tela.blit(surface, (LARGURA - 58, ALTURA - 30))

    def desenhar(self, tela):
        self.fundo.desenhar(tela)
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
        if self.alpha_entrada < 255:
            overlay = pygame.Surface((LARGURA, ALTURA))
            overlay.fill(NEGRO)
            overlay.set_alpha(255 - self.alpha_entrada)
            tela.blit(overlay, (0, 0))

    def atualizar(self):
        self.fundo.atualizar()
        self.transicao.atualizar()
        self.notificacoes.atualizar()
        self.alpha_entrada = min(255, self.alpha_entrada + 4)
        if self.subestado == "MENU":
            for opcao in self.opcoes:
                opcao.atualizar(self.mouse, self.fonte_opcao)
            for i, opcao in enumerate(self.opcoes):
                if opcao.hover:
                    self.opcao_selecionada = i

    # -------------------------------------------------------------- eventos

    def tratar_eventos(self, evento):
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
        """Converte coordenadas da janela para a superficie logica (900x700)."""
        try:
            largura, altura = self.jogo.janela.get_size()
        except (AttributeError, TypeError):
            return pos
        if (largura, altura) == (LARGURA, ALTURA):
            return pos
        return (int(pos[0] * LARGURA / largura),
                int(pos[1] * ALTURA / altura))

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
                self.opcao_selecionada = (self.opcao_selecionada - 1) % \
                    len(self.opcoes)
                self._som("navegar")
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                self.opcao_selecionada = (self.opcao_selecionada + 1) % \
                    len(self.opcoes)
                self._som("navegar")
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
                if opcao.get_rect(self.fonte_opcao).collidepoint(pos):
                    self.opcao_selecionada = i
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
        if self.preview_skin:
            botoes = {"equipar": pygame.Rect(LARGURA // 2 - 170, ALTURA - 120,
                                             160, 48),
                      "fechar": pygame.Rect(LARGURA // 2 + 10, ALTURA - 120,
                                            160, 48)}
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