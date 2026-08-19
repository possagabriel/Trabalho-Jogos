"""Classe principal do jogo: estados, loop, transicoes e gerenciamento."""

import math
import random
import sys

import pygame

from .config import ALTURA, AMARELO, AZUL, BRANCO, CIANO, DIMENSION_GOLD, \
    DOURADO, FPS, LARGURA, NEGRO, QUANTUM_CYAN, RIFT_MAGENTA, TITULO, VERDE, \
    VOID_BLACK
from .bosses import Boss
from .enemies import Inimigo, InimigoEspecial, composicao_onda, \
    sortear_inimigo_especial
from .fonts import fonte_texto, fonte_titulo
from .menu import MenuPrincipal
from .particles import MensagemFlutuante, SistemaParticulas
from .player import Jogador
from .powerups import PowerUp, sortear_tipo
from .save_system import SistemaProgressao
from .scenarios import CENARIOS, Cenario, cenario_do_nivel
from .settings import Configuracoes
from .shop import LojaSkins
from .sounds import Sons
from .smooth import desenhar_circulo, desenhar_glow, desenhar_painel, \
    desenhar_poligono, desenhar_vignette, retangulo_suave
from .theme import tema_atual
from .ui import desenhar_barra, desenhar_cantos, desenhar_coracoes, \
    desenhar_texto, desenhar_titulo
from .weapons import ARMARIA

DICAS_CARREGAMENTO = [
    "Prepare-se para atravessar a fenda!",
    "Use combos para ganhar mais pontos!",
    "Troque de arma com as teclas 1 a 7.",
    "Derrote entidades RIFT para abrir novas dimensoes.",
    "Skins raras caem dos inimigos cristalinos.",
    "Junte moedas para expandir o hangar.",
    "A cada 5 niveis surge uma entidade RIFT.",
    "Cada dimensao tem inimigos e armadilhas proprios.",
]


class Jogo:
    """Controla o fluxo do jogo: menu, loja, partida, pausa e game over."""

    def __init__(self):
        pygame.init()
        self.config = Configuracoes()
        self.janela = self._aplicar_modo_video()
        self.tela = pygame.Surface((LARGURA, ALTURA))
        pygame.display.set_caption(TITULO)
        pygame.display.set_icon(self._criar_icone())
        self.relogio = pygame.time.Clock()
        self.sons = Sons()
        self.sons.set_volume_musica(self.config["musica_volume"])
        self.sons.set_volume_efeitos(self.config["efeitos_volume"])
        self.controles = self.config.controles
        self.sensibilidade = self.config["sensibilidade"]
        self.fonte_pequena = fonte_texto(22)
        self.fonte_media = fonte_texto(32)
        self.fonte_grande = fonte_titulo(64)
        self.fonte_titulo = fonte_titulo(84)
        self.fontes = {22: self.fonte_pequena, 32: self.fonte_media,
                       64: self.fonte_grande, 84: self.fonte_titulo}

        self.progresso = SistemaProgressao()
        self.loja = LojaSkins(
            moedas=self.progresso.jogador["moedas"],
            desbloqueadas=self.progresso.jogador["skins_desbloqueadas"],
            skin_atual=self.progresso.jogador["skin_atual"])

        self.estado = "MENU"
        self.rodando = True
        self.nome_jogador = self.progresso.jogador["nome"]
        self.carregamento = 0
        self.novo_recorde = False
        self.moedas_ganhas = 0
        self.bosses_abates = 0
        self.boss_intro = 0
        self.fade = 0
        self.flash = 0
        self.cenario = Cenario(1)
        self.particulas = SistemaParticulas()
        # superficies reutilizadas por frame (evita alocar a cada desenho)
        self._tela_sombra = pygame.Surface((LARGURA, ALTURA),
                                           pygame.SRCALPHA)
        self._tela_flash = pygame.Surface((LARGURA, ALTURA),
                                          pygame.SRCALPHA)
        self._tela_fade = pygame.Surface((LARGURA, ALTURA))
        self.recordes = SistemaProgressao.carregar_recordes()
        self.menu = MenuPrincipal(self)
        self._novo_jogo("Jogador", zerar_estado=False)
        self.estado = "MENU"

    # ----- modo de video -----

    def _escala_janela(self):
        """Fator de escala e offsets para encaixar a tela 900x700 na janela.

        Usa scale-to-fit (proporcao preservada) e centraliza a cena, criando
        as "safe areas" (letterbox) nos lados. Com isso o menu e o jogo ficam
        identicos e proporcionais em qualquer resolucao/formato de janela.
        Retorna (escala, offset_x, offset_y).
        """
        w, h = self.janela.get_size()
        escala = min(w / LARGURA, h / ALTURA)
        return escala, (w - LARGURA * escala) / 2, (h - ALTURA * escala) / 2

    def _aplicar_modo_video(self):
        """Reconfigura a janela: tela cheia (resolucao nativa) ou escolhida."""
        from .settings import parse_resolucao
        if self.config["tela_cheia"]:
            try:
                w, h = pygame.display.get_desktop_sizes()[0]
            except (IndexError, pygame.error):
                w, h = parse_resolucao(self.config["resolucao"])
            self.janela = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
        else:
            self.janela = pygame.display.set_mode(
                parse_resolucao(self.config["resolucao"]))
        return self.janela

    def _apresentar(self):
        """Redimensiona a superficie interna para a janela e atualiza a tela.

        No modo AJUSTAR preserva as proporcoes com safe areas (letterbox) em
        qualquer resolucao; no modo PREENCHE estica a cena para a janela.
        """
        w, h = self.janela.get_size()
        if (w, h) == (LARGURA, ALTURA):
            self.janela.blit(self.tela, (0, 0))
            pygame.display.flip()
            return
        if self.config["aspecto"] == "PREENCHE":
            superficie = pygame.transform.smoothscale(self.tela, (w, h))
            self.janela.blit(superficie, (0, 0))
            pygame.display.flip()
            return
        escala, off_x, off_y = self._escala_janela()
        superficie = pygame.transform.smoothscale(
            self.tela,
            (max(1, int(LARGURA * escala)), max(1, int(ALTURA * escala))))
        self.janela.fill(VOID_BLACK)
        self.janela.blit(superficie, (int(off_x), int(off_y)))
        cor_safe = (32, 28, 48)
        pygame.draw.aaline(self.janela, cor_safe,
                           (int(off_x), int(off_y)),
                           (int(off_x + LARGURA * escala), int(off_y)), 1)
        pygame.draw.aaline(
            self.janela, cor_safe,
            (int(off_x), int(off_y + ALTURA * escala)),
            (int(off_x + LARGURA * escala),
             int(off_y + ALTURA * escala)), 1)
        pygame.display.flip()

    # ----- utilidades -----

    def _criar_icone(self):
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        desenhar_glow(surf, RIFT_MAGENTA, (16, 16), 16, 0.7)
        desenhar_poligono(surf, RIFT_MAGENTA,
                          [(8, 4), (12, 4), (16, 20), (20, 4), (24, 4),
                           (16, 26)])
        pygame.draw.line(surf, QUANTUM_CYAN, (26, 6), (22, 24), 2)
        pygame.draw.line(surf, QUANTUM_CYAN, (30, 6), (26, 24), 2)
        return surf

    def _novo_jogo(self, nome, zerar_estado=True):
        nome = nome.strip() or "Jogador"
        skin = self.loja.pegar_skin(self.loja.skin_atual)
        self.jogador = Jogador(nome, skin=skin)
        self.jogador.velocidade = 5.0 * self.sensibilidade
        self.inimigos = []
        self.boss = None
        self.projeteis = []
        self.powerups = []
        self.mensagens = []
        self.fila_onda = []
        self.timer_spawn = 0
        self.inimigos_abates = 0
        self.bosses_abates = 0
        self.boss_intro = 0
        self.tiros_disparados = 0
        self.tempo_partida = 0
        self.particulas.limpar()
        self.flash = 0
        self.fade = 255
        self.novo_recorde = False
        self.moedas_ganhas = 0
        self.cenario = Cenario(1)
        self._iniciar_nivel(1)
        self.mensagens.append(MensagemFlutuante(f"Bem-vindo, {nome}!",
                                                LARGURA // 2, ALTURA // 2 + 20,
                                                CIANO, 110))
        if zerar_estado:
            self.estado = "JOGANDO"

    def _preparar_jogo(self):
        """Inicia a partida com a tela de carregamento."""
        self._novo_jogo(self.nome_jogador, zerar_estado=False)
        self.carregamento = 0
        self.estado = "PREPARANDO"

    def _salvar_tudo(self):
        self.progresso.sincronizar_loja(self.loja)
        self.progresso.salvar_arquivo()

    # ----- niveis e ondas -----

    def _iniciar_nivel(self, nivel):
        self.jogador.nivel = nivel
        novo_cenario_id = cenario_do_nivel(nivel)
        if novo_cenario_id != self.cenario.id:
            self._transicao_cenario(novo_cenario_id)
        self.timer_spawn = 0
        self.sons.tocar("nivel")
        self.mensagens.append(MensagemFlutuante(f"NIVEL {nivel}",
                                                LARGURA // 2, ALTURA // 2,
                                                CIANO, 80))
        self._verificar_desbloqueio_arma()
        if nivel % 5 == 0:
            self.boss = Boss(nivel, self.cenario)
            self.boss_intro = 130
            self.mensagens.append(MensagemFlutuante(
                f"RIFT ENTITY // {self.boss.nome}", LARGURA // 2,
                ALTURA // 2 + 40, DIMENSION_GOLD, 130))
            self.sons.tocar("boss")
        else:
            tipos, quantidade = composicao_onda(nivel, self.cenario.inimigos)
            self.fila_onda = [random.choice(tipos)
                              for _ in range(quantidade)]

    def _verificar_desbloqueio_arma(self):
        for indice, arma in enumerate(ARMARIA):
            if (arma["nivel"] <= self.jogador.nivel and
                    indice not in self.jogador.armas_desbloqueadas):
                self.jogador.armas_desbloqueadas.append(indice)
                self.jogador.arma_atual = indice
                self.mensagens.append(MensagemFlutuante(
                    f"ARMA NOVA: {arma['nome']}!", LARGURA // 2,
                    ALTURA // 2 + 80, arma["cor"], 130))
                self.sons.tocar("coleta")

    def _transicao_cenario(self, novo_id):
        """Transicao de salto dimensional entre cenarios."""
        self.sons.tocar("transicao")
        cfg = CENARIOS[novo_id - 1]
        cor = cfg["cor_transicao"]

        self.mensagens.append(MensagemFlutuante(
            f"DIMENSION 0{novo_id} // {cfg['nome']}", LARGURA // 2,
            ALTURA // 2, cor, 140))

        # 1. particulas em espiral do salto dimensional
        self.particulas.salto_dimensional(LARGURA // 2, ALTURA // 2, cor)
        for _ in range(24):
            self.particulas.atualizar()
            self._frame_transicao()
            self.relogio.tick(FPS)

        # 2. flash branco
        for alpha in range(0, 255, 12):
            self._tela_fade.fill((255, 255, 255))
            self._tela_fade.set_alpha(alpha)
            self.tela.blit(self._tela_fade, (0, 0))
            self._apresentar()
            self.relogio.tick(FPS)

        # 3. troca efetiva do cenario
        self.cenario = Cenario(novo_id)
        self.progresso.desbloquear_cenario(novo_id)
        self.particulas.limpar()

        # 4. revelacao com particulas do novo cenario
        self.particulas.espiral_revelacao(LARGURA // 2, ALTURA // 2, cor)
        for _ in range(18):
            self.particulas.atualizar()
            self._frame_transicao()
            self.relogio.tick(FPS)

    def _frame_transicao(self):
        self.cenario.desenhar(self.tela)
        self.particulas.desenhar(self.tela)
        self._apresentar()

    # ----- combate -----

    def _explodir_inimigo(self, inimigo):
        bonus = self.jogador.combo.combo_atual * 5
        multiplicador = self.jogador.combo.get_bonus()
        total = int((inimigo.pontos + bonus) * multiplicador)
        self.jogador.pontuacao += total
        self.mensagens.append(MensagemFlutuante(f"+{total}", inimigo.x,
                                                inimigo.y, inimigo.cor))
        self.particulas.explosao(inimigo.x, inimigo.y, inimigo.cor, 18, 6)
        self.sons.tocar("explosao")
        self.inimigos_abates += 1
        if isinstance(inimigo, InimigoEspecial):
            self._drop_especial(inimigo)
        elif random.random() < 0.08:
            self.powerups.append(PowerUp(sortear_tipo(), inimigo.x,
                                         inimigo.y))
        self.inimigos.remove(inimigo)

    def _drop_especial(self, inimigo):
        """Quedas especiais de acordo com o tipo de inimigo especial."""
        tipo = inimigo.tipo_especial
        chance = {"acumulador": 0.50, "esponja": 0.30, "condutor": 0.40,
                  "mutante": 0.80, "cristalino": 0.05}[tipo]
        if random.random() > chance:
            return
        if tipo == "acumulador":
            drop = "arma"
        elif tipo == "esponja":
            drop = "vida"
        elif tipo == "condutor":
            drop = "escudo"
        elif tipo == "mutante":
            drop = "moedas"
        else:
            drop = "skin"
        self.powerups.append(PowerUp(drop, inimigo.x, inimigo.y))

    def _derrotar_boss(self):
        boss = self.boss
        self.boss = None
        multiplicador = self.jogador.combo.get_bonus()
        total = int(boss.pontos * multiplicador)
        self.jogador.pontuacao += total
        self.progresso.registrar_boss()
        self.bosses_abates += 1
        self.mensagens.append(MensagemFlutuante(
            f"BOSS DERROTADO! +{total}", boss.x, boss.y, boss.cor, 110))
        if boss.efeito == "explosao":
            self.particulas.explosao(boss.x, boss.y, boss.cor,
                                     qtd=boss.part_qtd, forca=8)
        elif boss.efeito == "mega":
            self.particulas.mega(boss.x, boss.y)
        elif boss.efeito == "espiral":
            self.particulas.espiral(boss.x, boss.y, boss.cor, boss.part_qtd)
        elif boss.efeito == "estrela":
            self.particulas.estrela(boss.x, boss.y, boss.cor, boss.part_qtd)
        elif boss.efeito == "pulsacao":
            self.particulas.pulsacao(boss.x, boss.y, boss.cor, boss.part_qtd)
        self.sons.tocar("explosao")
        for _ in range(3):
            self.powerups.append(PowerUp(sortear_tipo(), boss.x,
                                         boss.y + random.randint(-20, 20)))

    def _ao_dano(self):
        self.jogador.combo.zerar()
        self.flash = 10
        self.sons.tocar("dano")

    def _fim_de_jogo(self):
        melhor_anterior = SistemaProgressao.melhor_pontuacao()
        nome_skin = self.jogador.skin.nome
        self.recordes = SistemaProgressao.salvar_recorde(
            self.jogador.nome, self.jogador.pontuacao, self.jogador.nivel,
            nome_skin)
        self.novo_recorde = self.jogador.pontuacao > melhor_anterior
        self.moedas_ganhas = (self.jogador.moedas_jogo +
                              self.progresso._moedas_fim_jogo(
                                  self.cenario.id, self.bosses_abates))
        self.progresso.registrar_fim_jogo(self.jogador, self.tempo_partida,
                                          self.inimigos_abates,
                                          self.cenario.id, self.bosses_abates)
        self.loja.moedas += self.moedas_ganhas
        self._salvar_tudo()
        self.sons.tocar("gameover")
        self.particulas.explosao_dupla(self.jogador.x, self.jogador.y)
        self.estado = "GAME_OVER"

    def _desbloquear_skin_jogo(self, skin_id):
        """Desbloqueia uma skin (ex.: drop raro do cristalino)."""
        if self.progresso.desbloquear_skin(skin_id):
            for skin in self.loja.skins:
                if skin.id == skin_id:
                    skin.desbloqueada = True
            self._salvar_tudo()
            return True
        return False

    # ----- atualizacao da partida -----

    def _atualizar_jogando(self):
        teclas = pygame.key.get_pressed()
        self.jogador.atualizar(teclas, self.controles)
        tecla_atirar = self.controles.get("atirar", 0)
        if teclas[pygame.K_SPACE] or teclas[pygame.K_z] or teclas[tecla_atirar]:
            novos = self.jogador.atirar()
            if novos:
                self.projeteis.extend(novos)
                self.tiros_disparados += 1
                self.sons.tocar("tiro")

        if self.fila_onda:
            self.timer_spawn += 1
            if self.timer_spawn >= 35:
                self.timer_spawn = 0
                tipo = self.fila_onda.pop(0)
                self.inimigos.append(Inimigo(tipo, self.jogador.nivel))
                # chance de 10-15% de surgir um inimigo especial ao lado
                especial = sortear_inimigo_especial(self.jogador.nivel,
                                                    self.cenario.especiais)
                if especial:
                    self.inimigos.append(InimigoEspecial(
                        especial, self.jogador.nivel, self.cenario.id))

        for inimigo in self.inimigos[:]:
            if (isinstance(inimigo, InimigoEspecial) and inimigo.carregado and
                    not inimigo.e_feito_ja_atirado()):
                acoes = inimigo.acoes_carregado()
                if acoes:
                    self.projeteis.extend(acoes["projeteis"])
                    self.inimigos.extend(acoes["inimigos"])
                    if acoes["mensagem"]:
                        self.mensagens.append(MensagemFlutuante(
                            acoes["mensagem"], inimigo.x, inimigo.y,
                            inimigo.cor, 90))
                    if acoes["morrer"]:
                        self._explodir_inimigo(inimigo)
                        continue
            novos = inimigo.atualizar(self.jogador)
            self.projeteis.extend(novos)
            if inimigo.y > ALTURA + 60:
                self.inimigos.remove(inimigo)

        if self.boss:
            novos = self.boss.atualizar(self.jogador)
            self.projeteis.extend(novos)

        self._atualizar_projeteis()
        self._atualizar_powerups()

        for inimigo in self.inimigos[:]:
            if inimigo.rect.colliderect(self.jogador.rect):
                if self.jogador.sofrer_dano():
                    self._ao_dano()
                if not isinstance(inimigo, InimigoEspecial):
                    self._explodir_inimigo(inimigo)

        if self.boss and self.boss.rect.colliderect(self.jogador.rect):
            if self.jogador.sofrer_dano():
                self._ao_dano()

        if random.random() < 0.5:
            self.particulas.rastro(self.jogador.x + random.uniform(-4, 4),
                                   self.jogador.y + 20, (140, 160, 180), 1.2)

        if not self.fila_onda and not self.inimigos and not self.boss:
            bonus = int((100 + 50 * self.jogador.nivel) *
                        self.jogador.combo.get_bonus())
            self.jogador.pontuacao += bonus
            self.mensagens.append(MensagemFlutuante(
                f"NIVEL {self.jogador.nivel} CONCLUIDO! +{bonus}",
                LARGURA // 2, ALTURA // 2 + 30, VERDE, 90))
            self._iniciar_nivel(self.jogador.nivel + 1)

        if not self.jogador.vivo:
            self._fim_de_jogo()

    def _atualizar_projeteis(self):
        for proj in self.projeteis[:]:
            if proj.teleguiado:
                proj.atualizar_teleguiado(self.jogador.x, self.jogador.y)
            else:
                proj.atualizar()
            if proj.saiu_da_tela():
                self.projeteis.remove(proj)
                continue

            if proj.origem == "jogador":
                # campo gravitacional da Distorcao e do Condutor
                for inimigo in self.inimigos:
                    atrai = (inimigo.tipo == "distorcao" or
                             (isinstance(inimigo, InimigoEspecial) and
                              inimigo.tipo_especial == "condutor"))
                    if atrai:
                        dx = inimigo.x - proj.x
                        dy = inimigo.y - proj.y
                        dist = math.hypot(dx, dy)
                        if dist < 150 and dist > 1:
                            proj.vel_x += dx / dist * 0.35
                            proj.vel_y += dy / dist * 0.35
                acertou = self._projetil_jogador_atinge(proj)
                if acertou and proj.tipo != "ion" and proj.origem == "jogador":
                    self.projeteis.remove(proj)
            elif proj.rect.colliderect(self.jogador.rect):
                self.projeteis.remove(proj)
                if self.jogador.sofrer_dano():
                    self._ao_dano()

    def _projetil_jogador_atinge(self, proj):
        """Aplica dano do projetil do jogador. Retorna True se acertou algo.

        Projeteis ``ion`` atravessam (acertam todos os inimigos na coluna);
        os demais param no primeiro alvo.
        """
        penetrante = proj.tipo == "ion"
        acertou = False
        for inimigo in self.inimigos[:]:
            if not proj.rect.colliderect(inimigo.rect):
                continue
            if (isinstance(inimigo, InimigoEspecial) and
                    inimigo.campo_forca):
                # campo de forca reflete o tiro (e bloqueia o raio ion)
                if proj.tipo != "ion":
                    proj.refletir()
                    self.sons.tocar("coleta")
                return True
            if isinstance(inimigo, InimigoEspecial):
                morreu = inimigo.receber_tiro(proj.dano)
                self.sons.tocar("carga")
                if morreu:
                    self._explodir_inimigo(inimigo)
            else:
                if inimigo.sofrer_dano(proj.dano):
                    self._explodir_inimigo(inimigo)
            acertou = True
            if not penetrante:
                return True
        if self.boss and proj.rect.colliderect(self.boss.rect):
            if self.boss.sofrer_dano(proj.dano):
                self._derrotar_boss()
            acertou = True
        return acertou

    def _atualizar_powerups(self):
        for powerup in self.powerups[:]:
            powerup.atualizar()
            if powerup.y > ALTURA + 30:
                self.powerups.remove(powerup)
            elif powerup.rect.colliderect(self.jogador.rect):
                self.powerups.remove(powerup)
                mensagem = powerup.aplicar(self.jogador,
                                           self._desbloquear_skin_jogo)
                self.mensagens.append(MensagemFlutuante(
                    mensagem, powerup.x, powerup.y,
                    PowerUp.CORES[powerup.tipo]))
                self.sons.tocar("coleta")

    def _atualizar(self):
        if self.estado == "JOGANDO":
            self.tempo_partida += 1 / FPS
            self._atualizar_jogando()
        elif self.estado == "PREPARANDO":
            self.carregamento += 2.6
            if self.carregamento >= 100:
                self.carregamento = 100
                self.estado = "JOGANDO"
        elif self.estado in ("MENU", "CONTINUAR", "LOJA", "RECORDES",
                             "CONFIG"):
            self.menu.atualizar()
        self.particulas.atualizar()
        self.cenario.atualizar()
        for mensagem in self.mensagens[:]:
            mensagem.atualizar()
            if not mensagem.viva:
                self.mensagens.remove(mensagem)
        if self.fade > 0:
            self.fade = max(0, self.fade - 18)
        if self.flash > 0:
            self.flash -= 1
        if self.boss_intro > 0:
            self.boss_intro -= 1

    # ----- eventos -----

    def _tratar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self._salvar_tudo()
                return False
            if self.estado in ("MENU", "CONTINUAR", "LOJA", "RECORDES",
                               "CONFIG"):
                if not self.menu.tratar_eventos(evento):
                    return False
                continue
            if evento.type != pygame.KEYDOWN:
                continue
            if self.estado == "JOGANDO":
                tecla_pausar = self.controles.get("pausar", 0)
                if (evento.key == pygame.K_p or
                        evento.key == pygame.K_ESCAPE or
                        evento.key == tecla_pausar):
                    self.estado = "PAUSA"
                elif pygame.K_1 <= evento.key <= pygame.K_7:
                    self.jogador.selecionar_arma(evento.key - pygame.K_1)
            elif self.estado == "PAUSA":
                if evento.key in (pygame.K_p, pygame.K_ESCAPE):
                    self.estado = "JOGANDO"
                elif evento.key == pygame.K_m:
                    self.estado = "MENU"
                    self.fade = 255
                    self._salvar_tudo()
            elif self.estado == "GAME_OVER":
                if evento.key == pygame.K_RETURN:
                    self._preparar_jogo()
                elif evento.key == pygame.K_ESCAPE:
                    self.estado = "MENU"
                    self.fade = 255
        return self.rodando

    # ----- desenho -----

    def _desenhar_hud(self):
        tema = tema_atual(self.config["tema"])
        cor_acento = tema["primaria"]
        cor_painel = tema["fundo_painel"]

        # painel superior de vidro
        painel = pygame.Rect(8, 8, LARGURA - 16, 92)
        desenhar_painel(self.tela, cor_acento, painel,
                        cor_fundo=cor_painel, raio_canto=14, alpha=170,
                        glow_raio=12)
        desenhar_cantos(self.tela, tema["borda_forte"], painel, tamanho=10)

        # ---- esquerda: vida + escudo ----
        desenhar_texto(self.tela, "VIDA", (30, 26), (200, 205, 235), 16,
                       "esquerda", self.fontes)
        desenhar_coracoes(self.tela, self.jogador.vida, 30, 52)
        if self.jogador.escudo:
            desenhar_circulo(self.tela, AZUL, (30, 80), 8, 2, brilho=1.2)
            desenhar_texto(self.tela, "ESCUDO", (44, 76), AZUL, 16,
                           "esquerda", self.fontes)

        # ---- centro: nivel + dimensao ----
        desenhar_texto(self.tela, f"NIVEL {self.jogador.nivel}",
                       (LARGURA // 2, 34), BRANCO, 26, "centro", self.fontes)
        desenhar_texto(self.tela, f"DIMENSION 0{self.cenario.id} // "
                       f"{self.cenario.nome}", (LARGURA // 2, 62),
                       self.cenario.cor_transicao, 18, "centro", self.fontes)

        # ---- direita: pontuacao, arma, skin, combo ----
        x = LARGURA - 30
        desenhar_texto(self.tela, "PONTOS", (x, 26), (200, 205, 235), 16,
                       "direita", self.fontes)
        desenhar_texto(self.tela, f"{self.jogador.pontuacao:,}".replace(",", "."),
                       (x, 48), DOURADO, 26, "direita", self.fontes)
        arma = ARMARIA[self.jogador.arma_atual]
        cor_arma = arma["cor"]
        desenhar_texto(self.tela, arma["nome"], (x, 74), cor_arma, 18,
                       "direita", self.fontes)
        desenhar_glow(self.tela, cor_arma, (x - 10, 74), 6, 0.8)
        desenhar_circulo(self.tela, cor_arma, (x - 22, 74), 4, brilho=1.4)

        # ---- combo ----
        combo = self.jogador.combo.combo_atual
        if combo > 1:
            mult = self.jogador.combo.get_bonus()
            fracao = min(1.0, combo / 20.0)
            largura = 170
            y = 118
            desenhar_texto(self.tela,
                           f"COMBO x{combo}", (LARGURA - 30, y), AMARELO,
                           20, "direita", self.fontes)
            desenhar_texto(self.tela, f"{mult:.1f}x", (LARGURA - 30, y + 24),
                           AMARELO, 16, "direita", self.fontes)
            barra_x = LARGURA - 30 - largura
            desenhar_barra(self.tela, barra_x, y + 8, largura, 10, fracao,
                           AMARELO)

        # ---- barra do boss (entidade RIFT) ----
        if self.boss:
            largura = 420
            x = (LARGURA - largura) // 2
            fracao = max(0.0, self.boss.vida / self.boss.vida_max)
            desenhar_texto(self.tela, f"RIFT ENTITY // {self.boss.nome}",
                           (LARGURA // 2, 103), DIMENSION_GOLD, 16, "centro",
                           self.fontes)
            desenhar_painel(self.tela, DIMENSION_GOLD,
                            pygame.Rect(x - 8, 116, largura + 16, 26),
                            cor_fundo=(24, 16, 6), raio_canto=10, alpha=190,
                            glow_raio=10)
            desenhar_barra(self.tela, x, 122, largura, 14, fracao,
                           DIMENSION_GOLD)

    def _desenhar_jogo(self):
        self.cenario.desenhar(self.tela)
        for powerup in self.powerups:
            powerup.desenhar(self.tela)
        for inimigo in self.inimigos:
            inimigo.desenhar(self.tela)
        if self.boss:
            self.boss.desenhar(self.tela)
        for proj in self.projeteis:
            proj.desenhar(self.tela)
        self.jogador.desenhar(self.tela, self.particulas)
        for mensagem in self.mensagens:
            mensagem.desenhar(self.tela)
        self.particulas.desenhar(self.tela)
        desenhar_vignette(self.tela, intensidade=0.45, raio_interno=0.5)
        if self.boss_intro > 0:
            self._desenhar_boss_intro()

    def _desenhar_boss_intro(self):
        """Overlay de apresentacao da entidade RIFT ao entrar num boss."""
        boss = self.boss
        alfa = max(0.0, min(1.0, self.boss_intro / 45.0))
        if alfa <= 0 or boss is None:
            return
        largura, altura = 460, 240
        x = LARGURA // 2 - largura // 2
        y = ALTURA // 2 - altura // 2
        painel = pygame.Rect(x, y, largura, altura)
        desenhar_painel(self.tela, DIMENSION_GOLD, painel,
                        cor_fundo=(16, 12, 6), raio_canto=12,
                        alpha=int(215 * alfa), glow_raio=24)
        desenhar_cantos(self.tela, DIMENSION_GOLD, painel, tamanho=16)

        desenhar_texto(self.tela, "RIFT ENTITY DETECTED",
                       (LARGURA // 2, y + 30), DIMENSION_GOLD, 24, "centro",
                       self.fontes)
        desenhar_texto(self.tela, f"ENTITY // {boss.nivel // 5:02d}",
                       (LARGURA // 2, y + 64), QUANTUM_CYAN, 20, "centro",
                       self.fontes)
        desenhar_texto(self.tela, boss.nome, (LARGURA // 2, y + 102), BRANCO,
                       34, "centro", self.fontes)
        desenhar_texto(self.tela, "THREAT LEVEL", (LARGURA // 2, y + 150),
                       (220, 190, 130), 16, "centro", self.fontes)
        desenhar_barra(self.tela, x + 120, y + 172, largura - 240, 12, 0.8,
                       DIMENSION_GOLD)
        desenhar_texto(self.tela, f"DIMENSION 0{boss.cenario_id}",
                       (LARGURA // 2, y + 206), boss.cor, 18, "centro",
                       self.fontes)

    def _desenhar_pausa(self):
        self._tela_sombra.fill((0, 0, 0, 190))
        self.tela.blit(self._tela_sombra, (0, 0))
        desenhar_vignette(self.tela, intensidade=0.6, raio_interno=0.35)

        painel = pygame.Rect(LARGURA // 2 - 240, ALTURA // 2 - 160, 480, 320)
        tema = tema_atual(self.config["tema"])
        desenhar_painel(self.tela, tema["primaria"], painel,
                        cor_fundo=tema["fundo_painel"], raio_canto=18,
                        alpha=235, glow_raio=30)
        desenhar_cantos(self.tela, tema["borda_forte"], painel, tamanho=18)

        desenhar_titulo(self.tela, "PAUSADO", (LARGURA // 2, ALTURA // 2 - 96),
                        tema["primaria"], 44)
        t = pygame.time.get_ticks() * 0.001
        pulso = 0.6 + 0.4 * math.sin(t * 4)
        cor_pulso = tuple(int(c * pulso) for c in tema["secundaria"])
        desenhar_texto(self.tela, "P / ESC  continuar", (LARGURA // 2,
                                                         ALTURA // 2 - 30),
                       cor_pulso, 28, "centro", self.fontes)
        desenhar_texto(self.tela, "M  voltar ao menu", (LARGURA // 2,
                                                        ALTURA // 2 + 20),
                       (210, 215, 240), 28, "centro", self.fontes)

        info = (f"NIVEL {self.jogador.nivel}   |   "
                f"{self.jogador.pontuacao} pts")
        desenhar_texto(self.tela, info, (LARGURA // 2, ALTURA // 2 + 80),
                       DOURADO, 22, "centro", self.fontes)

    def _formatar_tempo(self, segundos):
        m, s = divmod(int(segundos), 60)
        return f"{m:02d}:{s:02d}"

    def _desenhar_game_over(self):
        self._tela_sombra.fill((0, 0, 0, 185))
        self.tela.blit(self._tela_sombra, (0, 0))
        desenhar_vignette(self.tela, intensidade=0.7, raio_interno=0.4)
        tema = tema_atual(self.config["tema"])

        t = pygame.time.get_ticks() * 0.001
        desenhar_glow(self.tela, RIFT_MAGENTA, (LARGURA // 2, 76), 120, 0.5)
        desenhar_titulo(self.tela, "RIFT COLLAPSED", (LARGURA // 2, 84),
                        RIFT_MAGENTA, 48)

        painel = pygame.Rect(LARGURA // 2 - 250, 140, 500, 300)
        desenhar_painel(self.tela, tema["secundaria"], painel,
                        cor_fundo=tema["fundo_painel"], raio_canto=16,
                        alpha=225, glow_raio=20)
        desenhar_cantos(self.tela, tema["borda_forte"], painel, tamanho=14)

        desenhar_texto(self.tela, "ESTATISTICAS DA MISSAO",
                       (LARGURA // 2, painel.y + 24), tema["primaria"], 20,
                       "centro", self.fontes)
        estatisticas = [
            ("Pontuacao", f"{self.jogador.pontuacao} pts"),
            ("Nivel", str(self.jogador.nivel)),
            ("Bosses Derrotados", str(self.bosses_abates)),
            ("Moedas Ganhas", f"+{self.moedas_ganhas}"),
            ("Inimigos Mortos", str(self.inimigos_abates)),
            ("Combo Maximo", f"{self.jogador.combo.combo_maximo}x"),
            ("Tempo de Jogo", self._formatar_tempo(self.tempo_partida)),
        ]
        y = painel.y + 56
        for rotulo, valor in estatisticas:
            desenhar_texto(self.tela, rotulo, (painel.x + 36, y),
                           (185, 190, 225), 22, "esquerda", self.fontes)
            desenhar_texto(self.tela, valor, (painel.right - 36, y), BRANCO,
                           22, "direita", self.fontes)
            y += 36
        if self.novo_recorde:
            pulso = 0.7 + 0.3 * math.sin(t * 6)
            cor_recorde = tuple(int(c * pulso) for c in AMARELO)
            desenhar_glow(self.tela, AMARELO, (LARGURA // 2, 452), 60, 0.6)
            desenhar_texto(self.tela, "NOVO RECORDE!", (LARGURA // 2, 452),
                           cor_recorde, 34, "centro", self.fontes)

        desenhar_texto(self.tela, "TOP 5", (LARGURA // 2, 504),
                       tema["terciaria"], 24, "centro", self.fontes)
        self._desenhar_recordes(self.recordes[:5], 534)

        desenhar_glow(self.tela, VERDE, (LARGURA // 2, ALTURA - 50), 40, 0.4)
        desenhar_texto(self.tela, "ENTER: jogar de novo   ESC: menu",
                       (LARGURA // 2, ALTURA - 50), VERDE, 22, "centro",
                       self.fontes)

    def _desenhar_carregando(self):
        self.cenario.desenhar(self.tela)
        self._tela_sombra.fill((0, 0, 0, 175))
        self.tela.blit(self._tela_sombra, (0, 0))
        desenhar_vignette(self.tela, intensidade=0.7, raio_interno=0.45)
        tema = tema_atual(self.config["tema"])

        desenhar_titulo(self.tela, "VOID//SHIFT",
                        (LARGURA // 2, ALTURA // 2 - 130), RIFT_MAGENTA, 44)
        desenhar_texto(self.tela, "DIMENSIONAL TRANSIT",
                       (LARGURA // 2, ALTURA // 2 - 92), QUANTUM_CYAN, 22,
                       "centro", self.fontes)

        painel = pygame.Rect(LARGURA // 2 - 250, ALTURA // 2 - 60, 500, 120)
        desenhar_painel(self.tela, tema["primaria"], painel,
                        cor_fundo=tema["fundo_painel"], raio_canto=14,
                        alpha=200, glow_raio=16)
        desenhar_cantos(self.tela, tema["borda_forte"], painel, tamanho=12)

        desenhar_texto(self.tela, "CALIBRATING RIFT...",
                       (LARGURA // 2, ALTURA // 2 - 44), (200, 205, 235), 18,
                       "centro", self.fontes)

        barra = pygame.Rect(LARGURA // 2 - 210, ALTURA // 2 - 26, 420, 28)
        retangulo_suave(self.tela, (40, 40, 70), barra, 8)
        preenchido = int(420 * max(0.0, min(1.0, self.carregamento / 100)))
        retangulo_suave(self.tela, tema["primaria"],
                        pygame.Rect(barra.x, barra.y, preenchido, 28), 8,
                        glow_cor=tema["primaria"], glow_raio=16)
        retangulo_suave(self.tela, BRANCO, barra, 8, 2)
        desenhar_texto(self.tela, f"{int(self.carregamento)}%",
                       (LARGURA // 2, ALTURA // 2 + 12), BRANCO, 22, "centro",
                       self.fontes)
        desenhar_texto(self.tela,
                       f"RIFT STABILITY  {self.carregamento * 0.8742:.2f}%",
                       (LARGURA // 2, ALTURA // 2 + 46), QUANTUM_CYAN, 18,
                       "centro", self.fontes)
        dica = random.choice(DICAS_CARREGAMENTO)
        desenhar_texto(self.tela, dica, (LARGURA // 2, ALTURA // 2 + 78),
                       (200, 205, 235), 22, "centro", self.fontes)

    def _desenhar_recordes(self, lista, y_inicio):
        if not lista:
            desenhar_texto(self.tela, "Nenhum recorde ainda.",
                           (LARGURA // 2, y_inicio), BRANCO, 22, "centro",
                           self.fontes)
            return
        for i, reg in enumerate(lista):
            cor = DOURADO if i == 0 else BRANCO if i < 3 else (150, 150, 170)
            linha = (f"{i + 1}. {reg['nome']} - {reg['pontos']} pts "
                     f"(Nivel {reg['nivel']}, {reg['skin']})")
            desenhar_texto(self.tela, linha, (LARGURA // 2,
                                              y_inicio + i * 24), cor, 22,
                           "centro", self.fontes)

    def _desenhar(self):
        if self.estado in ("MENU", "CONTINUAR", "LOJA", "RECORDES", "CONFIG"):
            self.menu.desenhar(self.tela)
        elif self.estado == "PREPARANDO":
            self._desenhar_carregando()
        elif self.estado in ("JOGANDO", "PAUSA"):
            self._desenhar_jogo()
            self._desenhar_hud()
            if self.estado == "PAUSA":
                self._desenhar_pausa()
        elif self.estado == "GAME_OVER":
            self._desenhar_jogo()
            self._desenhar_hud()
            self._desenhar_game_over()

        if self.flash > 0:
            self._tela_flash.fill((255, 0, 0, self.flash * 18))
            self.tela.blit(self._tela_flash, (0, 0))
        if self.fade > 0:
            self._tela_fade.fill(NEGRO)
            self._tela_fade.set_alpha(self.fade)
            self.tela.blit(self._tela_fade, (0, 0))

        self._apresentar()

    def executar(self):
        rodando = True
        while rodando:
            rodando = self._tratar_eventos()
            if not rodando:
                break
            self._atualizar()
            self._desenhar()
            self.relogio.tick(FPS)
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    Jogo().executar()