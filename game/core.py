"""Classe principal do jogo: estados, loop, transicoes e gerenciamento."""

import math
import random
import sys

import pygame

from .config import ALTURA, AMARELO, BRANCO, CIANO, DIMENSION_GOLD, \
    DOURADO, FPS, LARGURA, LARANJA, NEGRO, QUANTUM_CYAN, RIFT_MAGENTA, \
    TITULO, VERDE, VOID_BLACK
from .bosses import Boss
from .cel_shading import TextoAcao
from .enemies import Inimigo, InimigoEspecial, composicao_onda, \
    sortear_inimigo_especial
from .fonts import fonte_texto, fonte_titulo
from .hud import HudJogo
from .menu import Dialogo, MenuPrincipal
from .particles import MensagemFlutuante, SistemaParticulas
from .player import Jogador
from .powerups import PowerUp, sortear_tipo
from .save_system import SistemaProgressao
from .scenarios import CENARIOS, Cenario, cenario_do_nivel
from .settings import Configuracoes, TEMAS
from .shop import LojaSkins
from .sounds import Sons
from .smooth import desenhar_glow, desenhar_painel, desenhar_poligono, \
    desenhar_vignette, retangulo_suave, \
    desenhar_painel_cartoon, desenhar_botao_cartoon, desenhar_estrela
from .theme import tema_atual
from .ui import desenhar_barra, desenhar_cantos, desenhar_texto, \
    desenhar_titulo
from .weapons import ARMARIA, Projetil

DICAS_CARREGAMENTO = [
    "Prepare-se para atravessar a fenda!",
    "Use combos para ganhar mais pontos!",
    "Troque de arma com as teclas 1 a 9.",
    "Abates carregam a Bomba Vortex (tecla E).",
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
        self._tela_shake = pygame.Surface((LARGURA, ALTURA))
        self.trauma = 0.0
        self.hitstop = 0
        self.recordes = SistemaProgressao.carregar_recordes()
        self.hud = HudJogo()
        self.menu = MenuPrincipal(self)
        # --- estado do menu de pausa ---
        self._pausa_selecao = 0
        self._pausa_config_selecao = 0
        self._pausa_config_scroll = 0
        self._pausa_mostrando_config = False
        self._pausa_dialogo = None
        self._pausa_mouse = (0, 0)
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

    def _transformacao_janela(self):
        """(escala, off_x, off_y) aplicando os ajustes manuais do usuario.

        Combina o scale-to-fit com o zoom e deslocamentos configurados em
        "Ajustar Tela" (``ajuste_escala``, ``ajuste_off_x/y``), permitindo
        calibrar a imagem para o monitor (overscan, TVs, etc.). Usada tanto
        no ``_apresentar`` quanto na conversao de mouse (``_pos_logica``).
        """
        if self.config["aspecto"] == "PREENCHE":
            return (self.config["ajuste_escala"],
                    self.config["ajuste_off_x"], self.config["ajuste_off_y"])
        escala, off_x, off_y = self._escala_janela()
        escala *= max(0.5, self.config["ajuste_escala"])
        off_x += self.config["ajuste_off_x"]
        off_y += self.config["ajuste_off_y"]
        return escala, off_x, off_y

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
            escala = max(0.5, self.config["ajuste_escala"])
            superficie = pygame.transform.smoothscale(
                self.tela,
                (max(1, int(w * escala)), max(1, int(h * escala))))
            self.janela.fill(VOID_BLACK)
            self.janela.blit(superficie, (int(self.config["ajuste_off_x"]),
                                          int(self.config["ajuste_off_y"])))
            pygame.display.flip()
            return
        escala, off_x, off_y = self._transformacao_janela()
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
        self.xs_onda = []
        self.timer_spawn = 0
        self.inimigos_abates = 0
        self.bosses_abates = 0
        self.boss_intro = 0
        self.tiros_disparados = 0
        self.tempo_partida = 0
        self.boost = 1.0            # medidor de boost (0..1)
        self.especial = 0.0         # carga do especial (0..1)
        self.energia = 100.0        # energia de sistemas (0..100)
        self.particulas.limpar()
        self.flash = 0
        self.fade = 255
        self.trauma = 0.0
        self.hitstop = 0
        self.novo_recorde = False
        self.moedas_ganhas = 0
        self.textos_acao = []
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
            self.boss = None
            tipos, quantidade, xs = composicao_onda(
                nivel, self.cenario.inimigos)
            self.fila_onda = [random.choice(tipos)
                              for _ in range(quantidade)]
            self.xs_onda = list(xs)

    def _verificar_desbloqueio_arma(self):
        for indice, arma in enumerate(ARMARIA):
            if (arma["nivel"] <= self.jogador.nivel and
                    indice not in self.jogador.armas_desbloqueadas):
                self.jogador.armas_desbloqueadas.append(indice)
                self.jogador.arma_atual = indice
                self.mensagens.append(MensagemFlutuante(
                    f"ARMA NOVA: {arma['nome']}!", LARGURA // 2,
                    ALTURA // 2 + 80, arma["cor"], 130))
                self.sons.tocar("arma")

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

    def _adicionar_trauma(self, qtd):
        """Adiciona intensidade ao screen shake (0..1, decai a cada frame)."""
        self.trauma = min(1.0, self.trauma + qtd)

    def _congelar(self, quadros):
        """Pausa breve o mundo (hit-stop) para dar peso a acoes grandes."""
        self.hitstop = max(self.hitstop, quadros)

    def _aplicar_shake(self):
        """Desloca a cena desenhada conforme o trauma restante."""
        if self.trauma <= 0:
            return
        mag = self.trauma ** 2 * 16
        off = (random.uniform(-mag, mag), random.uniform(-mag, mag))
        self._tela_shake.fill(NEGRO)
        self._tela_shake.blit(self.tela, (int(off[0]), int(off[1])))
        self.tela.blit(self._tela_shake, (0, 0))
        self.trauma = max(0.0, self.trauma - 0.035)

    def _aplicar_dano_jogador(self):
        """Centraliza o dano ao jogador, tratando escudo e feedback."""
        tinha_escudo = self.jogador.escudo
        if not self.jogador.sofrer_dano():
            return False
        self._ao_dano()
        if tinha_escudo:
            self.sons.tocar("escudo")
            self._adicionar_trauma(0.3)
        return True

    def _distancia(self, entidade, proj):
        """Distancia euclidiana entre uma entidade e um projetil."""
        return math.hypot(entidade.x - proj.x, entidade.y - proj.y)

    def _explodir_em_area(self, proj, raio, y_limite, efeitos_fn,
                          flash_inimigo=8):
        """Explosao generica em area.

        Detecta alvos no raio, aplica efeitos (sons, particulas, etc.)
        via callback, e causa dano a todos no raio. Retorna True se
        explodiu (consumindo o projetil).
        """
        tem_alvo = any(self._distancia(i, proj) < raio
                       for i in self.inimigos)
        if not tem_alvo and self.boss and \
                self._distancia(self.boss, proj) < raio:
            tem_alvo = True
        if not tem_alvo and proj.y > y_limite:
            return False
        efeitos_fn(proj)
        for inimigo in self.inimigos[:]:
            if self._distancia(inimigo, proj) < raio:
                if inimigo.sofrer_dano(proj.dano):
                    self._explodir_inimigo(inimigo)
                else:
                    inimigo.flash = flash_inimigo
        if self.boss and self._distancia(self.boss, proj) < raio:
            if self.boss.sofrer_dano(proj.dano):
                self._derrotar_boss()
            else:
                self._adicionar_trauma(0.15)
        return True

    def _efeitos_nova(self, proj):
        self.sons.tocar("nova")
        self.particulas.explosao(proj.x, proj.y, LARANJA, 26, 7)
        self.particulas.explosao(proj.x, proj.y, (255, 220, 120), 14, 4)
        self._adicionar_trauma(0.35)
        self._congelar(2)

    def _efeitos_bomba(self, proj):
        self.sons.tocar("especial")
        self.particulas.explosao(proj.x, proj.y, (255, 90, 30), 42, 9)
        self.particulas.explosao(proj.x, proj.y, (255, 220, 120), 20, 5)
        self.particulas.mega(proj.x, proj.y)
        self.flash = 16
        self._adicionar_trauma(0.7)
        self._congelar(4)

    def _explodir_nova(self, proj):
        """Explosao de area da arma Nova: dano a todos os alvos proximos.

        So explode quando um alvo esta no raio ou a orbita chega ao topo da
        tela. Retorna True se explodiu (consumindo o projetil).
        """
        return self._explodir_em_area(proj, raio=90, y_limite=40,
                                      efeitos_fn=self._efeitos_nova,
                                      flash_inimigo=8)

    def _explodir_bomba(self, proj):
        """Explosao da Bomba Vortex: area enorme com dano massivo.

        A bomba explode quando um alvo entra no raio ou ao chegar ao topo
        da tela, destruindo tudo proximo (incluindo o boss). Retorna True
        se explodiu (consumindo o projetil).
        """
        return self._explodir_em_area(proj, raio=150, y_limite=60,
                                      efeitos_fn=self._efeitos_bomba,
                                      flash_inimigo=10)

    def _explodir_inimigo(self, inimigo):
        bonus = self.jogador.combo.combo_atual * 5
        multiplicador = self.jogador.combo.get_bonus()
        total = int((inimigo.pontos + bonus) * multiplicador)
        self.jogador.pontuacao += total
        self.mensagens.append(MensagemFlutuante(f"+{total}", inimigo.x,
                                                inimigo.y, inimigo.cor))
        self.particulas.explosao(inimigo.x, inimigo.y, inimigo.cor, 18, 6)
        if random.random() < 0.35:
            texto_cor = random.choice([(255, 200, 50), (255, 100, 50),
                                       (255, 50, 100), (100, 255, 100)])
            self.textos_acao.append(TextoAcao(inimigo.x, inimigo.y - 20,
                                              cor=texto_cor))
        self.sons.tocar("explosao")
        self._adicionar_trauma(0.2)
        self.inimigos_abates += 1
        # carga do especial: mais lenta agora (bomba pesada demora mais)
        self.especial = min(1.0, self.especial + 0.02)
        if inimigo.tipo == "bomba":
            self.particulas.explosao(inimigo.x, inimigo.y, (255, 120, 40),
                                     24, 6.5)
            self._adicionar_trauma(0.35)
            if math.hypot(self.jogador.x - inimigo.x,
                          self.jogador.y - inimigo.y) < 70:
                self._aplicar_dano_jogador()
        if isinstance(inimigo, InimigoEspecial):
            self._drop_especial(inimigo)
        else:
            chance = 0.08 + min(0.12, self.jogador.combo.combo_atual * 0.004)
            if random.random() < chance:
                self.powerups.append(PowerUp(sortear_tipo(), inimigo.x,
                                             inimigo.y))
        self.inimigos.remove(inimigo)

    def _drop_especial(self, inimigo):
        """Quedas especiais de acordo com o tipo de inimigo especial."""
        tipo = inimigo.tipo_especial
        chance = {"acumulador": 0.50, "esponja": 0.30, "condutor": 0.40,
                  "mutante": 0.80, "cristalino": 0.05, "evocador": 0.30}[tipo]
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
        elif tipo == "evocador":
            drop = "arma"
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
        self._adicionar_trauma(0.8)
        self._congelar(3)
        for _ in range(3):
            self.powerups.append(PowerUp(sortear_tipo(), boss.x,
                                         boss.y + random.randint(-20, 20)))

    def _ao_dano(self):
        self.jogador.combo.zerar()
        self.flash = 10
        self.sons.tocar("dano")
        self._adicionar_trauma(0.5)

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
        usando_boost = (teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]
                        or teclas[pygame.K_LCTRL] or teclas[pygame.K_RCTRL])
        if usando_boost and self.boost > 0 and self.jogador.vivo:
            self.boost = max(0.0, self.boost - 0.008)
            self.jogador.velocidade = 5.0 * self.sensibilidade * 2.1
        else:
            self.boost = min(1.0, self.boost + 0.006)
            self.jogador.velocidade = 5.0 * self.sensibilidade
        # energia: esgota ao turbinar, regenera aos poucos
        if usando_boost and self.boost > 0:
            self.energia = max(0.0, self.energia - 1.6)
        else:
            self.energia = min(100.0, self.energia + 0.7)

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
            intervalo = max(18, 35 - self.jogador.nivel // 3)
            if self.timer_spawn >= intervalo:
                self.timer_spawn = 0
                tipo = self.fila_onda.pop(0)
                x = (self.xs_onda.pop(0) if self.xs_onda else None)
                self.inimigos.append(Inimigo(tipo, self.jogador.nivel, x=x))
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
                self._aplicar_dano_jogador()
                if not isinstance(inimigo, InimigoEspecial):
                    self._explodir_inimigo(inimigo)

        if self.boss and self.boss.rect.colliderect(self.jogador.rect):
            self._aplicar_dano_jogador()

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

    def _ativar_especial(self):
        """Dispara o especial (tecla E): lança a Bomba Vortex.

        Consome a carga do medidor (SPECIAL READY). A bomba é grande, viaja
        devagar e explode em área enorme causando dano massivo. Não afeta o
        boss diretamente por colisão, mas a explosão em área sim.
        """
        if self.especial < 1.0 or self.estado != "JOGANDO":
            return False
        self.especial = 0.0
        x, y = self.jogador.x, self.jogador.y - 24
        self.projeteis.append(Projetil(x, y, 0, -3.5, 25, LARANJA, 20,
                                       tipo="bomba"))
        self.flash = 10
        self.sons.tocar("especial")
        self._adicionar_trauma(0.3)
        return True

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
                if acertou and proj.tipo not in ("ion", "gauss") and \
                        proj.origem == "jogador":
                    self.projeteis.remove(proj)
            elif proj.rect.colliderect(self.jogador.rect):
                self.projeteis.remove(proj)
                self._aplicar_dano_jogador()

    def _projetil_jogador_atinge(self, proj):
        """Aplica dano do projetil do jogador. Retorna True se acertou algo.

        Projeteis ``ion`` e ``gauss`` atravessam (acertam todos os inimigos na
        coluna); a ``nova`` explode em area; os demais param no primeiro alvo.
        """
        if proj.tipo == "nova":
            return self._explodir_nova(proj)
        if proj.tipo == "bomba":
            return self._explodir_bomba(proj)
        penetrante = proj.tipo in ("ion", "gauss")
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
                self.particulas.faiscas(proj.x, proj.y, proj.cor, 5)
                if morreu:
                    self._explodir_inimigo(inimigo)
            else:
                if inimigo.sofrer_dano(proj.dano):
                    self._explodir_inimigo(inimigo)
                else:
                    self.sons.tocar("acerto")
                    self.particulas.faiscas(proj.x, proj.y, proj.cor, 5)
            acertou = True
            if not penetrante:
                return True
        if self.boss and proj.rect.colliderect(self.boss.rect):
            if self.boss.sofrer_dano(proj.dano):
                self._derrotar_boss()
            else:
                self.sons.tocar("acerto")
                self.particulas.faiscas(proj.x, proj.y, proj.cor, 6)
                self._adicionar_trauma(0.15)
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
        for texto in self.textos_acao[:]:
            texto.atualizar()
            if not texto.ativo:
                self.textos_acao.remove(texto)
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
                elif evento.key == pygame.K_e:
                    self._ativar_especial()
                elif pygame.K_1 <= evento.key <= pygame.K_9:
                    self.jogador.selecionar_arma(evento.key - pygame.K_1)
            elif self.estado == "PAUSA":
                self._tratar_eventos_pausa(evento)
            elif self.estado == "GAME_OVER":
                if evento.key == pygame.K_RETURN:
                    self._preparar_jogo()
                elif evento.key == pygame.K_ESCAPE:
                    self.estado = "MENU"
                    self.fade = 255
        return self.rodando

    # ----- desenho -----

    def _desenhar_hud(self):
        self.hud.desenhar(self.tela, self)

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
        for texto in self.textos_acao:
            texto.desenhar(self.tela)
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
        self._tela_sombra.fill((0, 0, 0, 210))
        self.tela.blit(self._tela_sombra, (0, 0))
        desenhar_vignette(self.tela, intensidade=0.7, raio_interno=0.3)

        tema = tema_atual(self.config["tema"])
        t = pygame.time.get_ticks() * 0.001

        if self._pausa_mostrando_config:
            self._desenhar_pausa_config(tema, t)
        else:
            self._desenhar_pausa_principal(tema, t)

        # dialogo de confirmacao por cima de tudo
        if self._pausa_dialogo and self._pausa_dialogo.ativo:
            self._pausa_dialogo.desenhar(
                self.tela,
                self.fontes.get(36) or fonte_titulo(36),
                self.fontes.get(22) or fonte_texto(22),
                mouse_pos=self._pausa_mouse,
                tema=tema)

    def _desenhar_pausa_principal(self, tema, t):
        """Menu de pausa principal com 3 opcoes interativas."""
        pw, ph = 440, 420
        painel = pygame.Rect(LARGURA // 2 - pw // 2, ALTURA // 2 - ph // 2,
                             pw, ph)
        desenhar_painel_cartoon(self.tela, tema["primaria"], painel,
                                cor_fundo=(10, 10, 26), raio_canto=28,
                                espessura_borda=6, alpha=248, glow_raio=32)

        # --- cabecalho com icone e titulo ---
        # icone de pause (duas barras verticais)
        ix, iy = LARGURA // 2, painel.y + 36
        barra_w, barra_h = 10, 28
        espaco_barra = 16
        pygame.draw.rect(self.tela, tema["primaria"],
                         (ix - espaco_barra - barra_w, iy - barra_h // 2,
                          barra_w, barra_h), border_radius=4)
        pygame.draw.rect(self.tela, tema["primaria"],
                         (ix + espaco_barra, iy - barra_h // 2,
                          barra_w, barra_h), border_radius=4)
        # contorno preto nas barras
        pygame.draw.rect(self.tela, (0, 0, 0),
                         (ix - espaco_barra - barra_w, iy - barra_h // 2,
                          barra_w, barra_h), 2, border_radius=4)
        pygame.draw.rect(self.tela, (0, 0, 0),
                         (ix + espaco_barra, iy - barra_h // 2,
                          barra_w, barra_h), 2, border_radius=4)

        desenhar_titulo(self.tela, "PAUSADO",
                        (LARGURA // 2, painel.y + 76), tema["primaria"], 38)

        # linha separadora animada
        sep_y = painel.y + 100
        sep_w = 260
        desenhar_glow(self.tela, tema["primaria"],
                      (LARGURA // 2, sep_y), 16, 0.3)
        for i in range(0, sep_w, 5):
            brilho = 0.3 + 0.7 * abs(math.sin(i / 30 + t * 2))
            cor_linha = tuple(int(c * brilho) for c in tema["primaria"])
            pygame.draw.line(self.tela, cor_linha,
                             (LARGURA // 2 - sep_w // 2 + i, sep_y),
                             (LARGURA // 2 - sep_w // 2 + i + 3, sep_y), 2)

        # estrelas decorativas animadas
        for i, (sx, sy, sr) in enumerate([
            (painel.x + 24, painel.y + 24, 9),
            (painel.right - 24, painel.y + 24, 7),
            (painel.x + 20, painel.bottom - 24, 8),
            (painel.right - 20, painel.bottom - 24, 10),
        ]):
            rot = t * 45 + i * 90
            cor_e = tema["secundaria"] if i % 2 == 0 else tema["terciaria"]
            desenhar_estrela(self.tela, (sx, sy), sr, cor_e, pontas=4,
                             rotacao=rot)

        # --- botoes de opcao ---
        opcoes = [
            ("CONTINUAR", (25, 150, 75), "retomar a missao"),
            ("CONFIGURACOES", (50, 90, 170), "ajustar opcoes"),
            ("SAIR DA MISSAO", (170, 50, 55), "voltar ao menu"),
        ]
        btn_w, btn_h = 320, 54
        btn_x = LARGURA // 2 - btn_w // 2
        btn_y_inicio = painel.y + 118
        espaco = 74

        for i, (texto, cor_fundo, dica) in enumerate(opcoes):
            by = btn_y_inicio + i * espaco
            rect = pygame.Rect(btn_x, by, btn_w, btn_h)
            hover = (i == self._pausa_selecao)
            desenhar_botao_cartoon(self.tela, texto, rect, cor_fundo,
                                   fonte=self.fontes.get(24) or
                                   fonte_texto(24),
                                   hover=hover)
            # dica abaixo do botao
            if hover:
                dica_surf = (self.fontes.get(16) or fonte_texto(16)).render(
                    dica, True, (180, 185, 220))
                self.tela.blit(dica_surf, dica_surf.get_rect(
                    center=(LARGURA // 2, by + btn_h + 10)))

        # --- info do jogador em painel separado ---
        info_y = painel.bottom - 80
        info_rect = pygame.Rect(painel.x + 30, info_y, pw - 60, 48)
        pygame.draw.rect(self.tela, (20, 20, 40, 120), info_rect,
                         border_radius=12)
        pygame.draw.rect(self.tela, tema["borda_fraco"], info_rect, 1,
                         border_radius=12)

        info_texto = (f"NIVEL {self.jogador.nivel}   |   "
                      f"{self.jogador.pontuacao} PTS   |   "
                      f"SKIN {self.jogador.skin}")
        desenhar_texto(self.tela, info_texto,
                       (LARGURA // 2, info_y + 24), DOURADO, 18, "centro",
                       self.fontes)

        # dica de teclado
        pulso = 0.4 + 0.6 * math.sin(t * 2.5)
        cor_dica = tuple(int(c * pulso) for c in (160, 165, 200))
        desenhar_texto(self.tela,
                       "UP/DOWN navegar   |   ENTER selecionar   "
                       "|   ESC retomar",
                       (LARGURA // 2, painel.bottom - 18), cor_dica, 14,
                       "centro", self.fontes)

    def _desenhar_pausa_config(self, tema, t):
        """Sub-painel de configuracoes dentro da pausa."""
        pw, ph = 540, 430
        painel = pygame.Rect(LARGURA // 2 - pw // 2, ALTURA // 2 - ph // 2,
                             pw, ph)
        desenhar_painel_cartoon(self.tela, tema["primaria"], painel,
                                cor_fundo=(10, 10, 26), raio_canto=24,
                                espessura_borda=5, alpha=248, glow_raio=26)

        # titulo com seta de voltar
        desenhar_titulo(self.tela, "CONFIGURACOES",
                        (LARGURA // 2, painel.y + 34), tema["primaria"], 30)
        # seta voltar (indicacao visual de que ESC volta)
        seta_x = painel.x + 30
        seta_y = painel.y + 34
        pygame.draw.polygon(self.tela, tema["secundaria"],
                            [(seta_x, seta_y), (seta_x + 14, seta_y - 8),
                             (seta_x + 14, seta_y + 8)])

        # linha separadora
        sep_y = painel.y + 58
        pygame.draw.line(self.tela, tema["borda_fraco"],
                         (painel.x + 40, sep_y),
                         (painel.right - 40, sep_y), 1)

        # linhas de config
        cfg_itens = [
            ("Musica", "slider", self.config["musica_volume"]),
            ("Efeitos", "slider", self.config["efeitos_volume"]),
            ("Tema", "tema", self.config["tema"]),
            ("Tela Cheia", "toggle", self.config["tela_cheia"]),
        ]
        btn_h = 44
        y_inicio = painel.y + 76
        espaco = 70

        for i, (rotulo, tipo, valor) in enumerate(cfg_itens):
            by = y_inicio + i * espaco
            selecionada = (i == self._pausa_config_selecao)

            # fundo da linha selecionada
            linha_rect = pygame.Rect(painel.x + 24, by - 6, pw - 48, btn_h)
            if selecionada:
                hl_surf = pygame.Surface((pw - 48, btn_h), pygame.SRCALPHA)
                pygame.draw.rect(hl_surf, (255, 255, 255, 25),
                                 (0, 0, pw - 48, btn_h), border_radius=12)
                self.tela.blit(hl_surf, (painel.x + 24, by - 6))
                pygame.draw.rect(self.tela, tema["primaria"], linha_rect, 2,
                                 border_radius=12)
                # indicador lateral
                pygame.draw.rect(self.tela, tema["primaria"],
                                 (painel.x + 24, by + 4, 5, btn_h - 8),
                                 border_radius=3)

            # rotulo
            cor_rotulo = BRANCO if selecionada else (170, 175, 215)
            fonte_item = self.fontes.get(22) or fonte_texto(22)
            surface = fonte_item.render(rotulo, True, cor_rotulo)
            self.tela.blit(surface, (painel.x + 44, by + 10))

            # valor / controle
            if tipo == "slider":
                fracao = max(0.0, min(1.0, valor))
                percentual = int(fracao * 100)
                track_x = painel.x + 280
                track_y = by + 14
                track_w = 170
                track_h = 16
                track_rect = pygame.Rect(track_x, track_y, track_w, track_h)
                retangulo_suave(self.tela, (35, 35, 65), track_rect, 8)
                if fracao > 0:
                    preenchido = max(16, int(track_w * fracao))
                    fill_rect = pygame.Rect(track_x, track_y,
                                            preenchido, track_h)
                    retangulo_suave(self.tela, CIANO, fill_rect, 8,
                                    glow_cor=CIANO, glow_raio=6)
                retangulo_suave(self.tela, BRANCO, track_rect, 8, 1)
                knob_x = track_x + preenchido
                pygame.draw.circle(self.tela, (0, 0, 0),
                                   (knob_x, track_y + 8), 8)
                pygame.draw.circle(self.tela, BRANCO,
                                   (knob_x, track_y + 8), 7)
                pygame.draw.circle(self.tela, CIANO,
                                   (knob_x, track_y + 8), 4)
                pct_surf = fonte_item.render(f"{percentual}%", True,
                                             (160, 165, 210))
                self.tela.blit(pct_surf, (track_x + track_w + 12, by + 8))

            elif tipo == "tema":
                nome = valor
                seta_cor = tema["secundaria"]
                # seta esquerda
                lx = painel.x + 280
                pygame.draw.polygon(self.tela, seta_cor,
                                    [(lx, by + 18), (lx + 14, by + 8),
                                     (lx + 14, by + 28)])
                pygame.draw.polygon(self.tela, (0, 0, 0),
                                    [(lx, by + 18), (lx + 14, by + 8),
                                     (lx + 14, by + 28)], 2)
                # nome do tema
                tema_fonte = self.fontes.get(24) or fonte_texto(24)
                ts = tema_fonte.render(nome, True, seta_cor)
                self.tela.blit(ts, ts.get_rect(
                    center=(LARGURA // 2, by + 16)))
                # seta direita
                rx = painel.x + pw - 294
                pygame.draw.polygon(self.tela, seta_cor,
                                    [(rx, by + 8), (rx + 14, by + 18),
                                     (rx, by + 28)])
                pygame.draw.polygon(self.tela, (0, 0, 0),
                                    [(rx, by + 8), (rx + 14, by + 18),
                                     (rx, by + 28)], 2)

            elif tipo == "toggle":
                ligado = valor
                tx = painel.x + 310
                tw, th = 56, 28
                toggle_rect = pygame.Rect(tx, by + 6, tw, th)
                cor_toggle = (35, 130, 65) if ligado else (100, 45, 45)
                retangulo_suave(self.tela, cor_toggle, toggle_rect, 14)
                retangulo_suave(self.tela, BRANCO, toggle_rect, 14, 1)
                knob_cx = tx + (42 if ligado else 14)
                pygame.draw.circle(self.tela, (0, 0, 0),
                                   (knob_cx, by + 20), 11)
                pygame.draw.circle(self.tela, BRANCO,
                                   (knob_cx, by + 20), 10)
                estado = "ON" if ligado else "OFF"
                cor_estado = VERDE if ligado else (160, 90, 90)
                est_surf = fonte_item.render(estado, True, cor_estado)
                self.tela.blit(est_surf, (tx + tw + 14, by + 8))

        # botoes de acao
        b_voltar_rect = pygame.Rect(painel.x + 30, painel.bottom - 56,
                                    150, 42)
        b_reset_rect = pygame.Rect(painel.right - 180, painel.bottom - 56,
                                   150, 42)
        desenhar_botao_cartoon(self.tela, "VOLTAR", b_voltar_rect,
                               (70, 70, 95),
                               fonte=self.fontes.get(20) or fonte_texto(20),
                               hover=False)
        desenhar_botao_cartoon(self.tela, "RESETAR", b_reset_rect,
                               (130, 45, 50),
                               fonte=self.fontes.get(20) or fonte_texto(20),
                               hover=False)

        # dica
        pulso = 0.4 + 0.6 * math.sin(t * 2.5)
        cor_dica = tuple(int(c * pulso) for c in (160, 165, 200))
        desenhar_texto(self.tela,
                       "UP/DOWN navegar  |  LEFT/RIGHT ajustar  |  ESC voltar",
                       (LARGURA // 2, painel.bottom - 14), cor_dica, 13,
                       "centro", self.fontes)

    # -------- eventos da pausa --------

    def _tratar_eventos_pausa(self, evento):
        """Trata eventos do menu de pausa interativo."""
        # dialogo de confirmacao tem prioridade
        if self._pausa_dialogo and self._pausa_dialogo.ativo:
            self._pausa_dialogo.tratar_evento(evento,
                                             mouse_pos=self._pausa_mouse)
            if not self._pausa_dialogo.ativo:
                self._pausa_dialogo = None
            return

        if self._pausa_mostrando_config:
            self._tratar_eventos_pausa_config(evento)
            return

        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_p, pygame.K_ESCAPE):
                self.estado = "JOGANDO"
            elif evento.key == pygame.K_m:
                self._pausa_sair_para_menu()
            elif evento.key == pygame.K_UP:
                self._pausa_selecao = (self._pausa_selecao - 1) % 3
            elif evento.key == pygame.K_DOWN:
                self._pausa_selecao = (self._pausa_selecao + 1) % 3
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._acao_pausa(self._pausa_selecao)

        elif evento.type == pygame.MOUSEMOTION:
            self._pausa_mouse = evento.pos
            self._atualizar_hover_pausa(evento.pos)

        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self._colidir_pausa(evento.pos) is not None:
                self._acao_pausa(self._pausa_selecao)

    def _tratar_eventos_pausa_config(self, evento):
        """Trata eventos do sub-painel de configuracoes da pausa."""
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self._pausa_mostrando_config = False
            elif evento.key == pygame.K_UP:
                self._pausa_config_selecao = (
                    self._pausa_config_selecao - 1) % 4
            elif evento.key == pygame.K_DOWN:
                self._pausa_config_selecao = (
                    self._pausa_config_selecao + 1) % 4
            elif evento.key in (pygame.K_LEFT, pygame.K_RIGHT):
                delta = 1 if evento.key == pygame.K_RIGHT else -1
                self._ajustar_config_pausa(self._pausa_config_selecao, delta)

        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._clique_pausa_config(evento.pos)

    def _ajustar_config_pausa(self, indice, delta):
        """Ajusta um item de configuracao na pausa."""
        if indice == 0:
            v = self.config["musica_volume"] + delta * 0.05
            v = max(0.0, min(1.0, v))
            self.config["musica_volume"] = round(v, 2)
            self.sons.set_volume_musica(v)
        elif indice == 1:
            v = self.config["efeitos_volume"] + delta * 0.05
            v = max(0.0, min(1.0, v))
            self.config["efeitos_volume"] = round(v, 2)
            self.sons.set_volume_efeitos(v)
        elif indice == 2:
            atual = self.config["tema"]
            idx = TEMAS.index(atual) if atual in TEMAS else 0
            idx = (idx + delta) % len(TEMAS)
            self.config["tema"] = TEMAS[idx]
        elif indice == 3 and delta > 0:
            self.config["tela_cheia"] = not self.config["tela_cheia"]
            self._aplicar_modo_video()
        self.config.salvar()

    def _clique_pausa_config(self, pos):
        """Trata clique no sub-painel de configuracoes da pausa."""
        pw, ph = 540, 430
        painel = pygame.Rect(LARGURA // 2 - pw // 2, ALTURA // 2 - ph // 2,
                             pw, ph)
        btn_h = 44
        y_inicio = painel.y + 76
        espaco = 70

        for i in range(4):
            by = y_inicio + i * espaco
            linha_rect = pygame.Rect(painel.x + 24, by - 6, pw - 48, btn_h)
            if linha_rect.collidepoint(pos):
                self._pausa_config_selecao = i
                self._ajustar_config_pausa(i, 1)
                return

        b_voltar_rect = pygame.Rect(painel.x + 30, painel.bottom - 56,
                                    150, 42)
        if b_voltar_rect.collidepoint(pos):
            self._pausa_mostrando_config = False
            return

        b_reset_rect = pygame.Rect(painel.right - 180, painel.bottom - 56,
                                   150, 42)
        if b_reset_rect.collidepoint(pos):
            self.config["musica_volume"] = 0.8
            self.config["efeitos_volume"] = 0.8
            self.config["tema"] = "NEON"
            self.config["tela_cheia"] = False
            self.config.salvar()
            self.sons.set_volume_musica(0.8)
            self.sons.set_volume_efeitos(0.8)
            self._aplicar_modo_video()

    def _colidir_pausa(self, pos):
        """Retorna o indice da opcao de pausa sob o mouse, ou None."""
        pw, ph = 440, 420
        painel = pygame.Rect(LARGURA // 2 - pw // 2, ALTURA // 2 - ph // 2,
                             pw, ph)
        btn_w, btn_h = 320, 54
        btn_x = LARGURA // 2 - btn_w // 2
        btn_y_inicio = painel.y + 118
        espaco = 74
        for i in range(3):
            by = btn_y_inicio + i * espaco
            rect = pygame.Rect(btn_x, by, btn_w, btn_h)
            if rect.collidepoint(pos):
                return i
        return None

    def _atualizar_hover_pausa(self, pos):
        """Atualiza selecao baseado no hover do mouse."""
        idx = self._colidir_pausa(pos)
        if idx is not None:
            self._pausa_selecao = idx

    def _acao_pausa(self, indice):
        """Executa a acao da opcao de pausa selecionada."""
        if indice == 0:  # CONTINUAR
            self.estado = "JOGANDO"
        elif indice == 1:  # CONFIGURACOES
            self._pausa_mostrando_config = True
            self._pausa_config_selecao = 0
        elif indice == 2:  # SAIR DA MISSAO
            self._pausa_sair_para_menu()

    def _pausa_sair_para_menu(self):
        """Abre dialogo de confirmacao para voltar ao menu."""
        self._pausa_dialogo = Dialogo(
            "Sair da Missao",
            "Tem certeza que deseja voltar ao menu? "
            "O progresso desta sessao sera salvo.",
            self._confirmar_sair_pausa,
            lambda: None)

    def _confirmar_sair_pausa(self):
        """Confirmou saida: salva e volta ao menu."""
        self.estado = "MENU"
        self.fade = 255
        self._salvar_tudo()

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

        self._aplicar_shake()
        self._apresentar()

    def executar(self):
        rodando = True
        while rodando:
            rodando = self._tratar_eventos()
            if not rodando:
                break
            if self.hitstop > 0:
                self.hitstop -= 1
            else:
                self._atualizar()
            self._desenhar()
            self.relogio.tick(FPS)
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    Jogo().executar()