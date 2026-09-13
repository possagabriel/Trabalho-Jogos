"""Controlador de ciclo de partida, niveis e transicoes de cenario."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from src.core.constants import CIANO, DIMENSION_GOLD, EstadoJogo, FPS, LARGURA, ALTURA
from src.runtime.domain.entities.bosses import Boss
from src.runtime.domain.entities.enemies import composicao_onda
from src.runtime.domain.world.particles import MensagemFlutuante
from src.runtime.domain.entities.player import Jogador
from src.runtime.domain.world.scenarios import CENARIOS, Cenario, cenario_do_nivel
from src.runtime.domain.entities.weapons import ARMARIA

if TYPE_CHECKING:
    from src.runtime.application.core import Jogo


MELHORIAS = {
    "potencia": ("MUNIÇÃO PESADA", "+1 de dano em todos os disparos"),
    "cadencia": ("CICLO ACELERADO", "12% menos intervalo entre tiros"),
    "motor": ("MOTOR VETORIAL", "+8% de velocidade de movimento"),
    "blindagem": ("BLINDAGEM", "+1 de vida máxima e reparo imediato"),
    "escudo": ("ESCUDO DE FENDA", "Recebe um escudo protetor"),
    "especial": ("REATOR VORTEX", "+25% de carga especial por abate"),
}


class ControladorProgressao:
    """Coordena inicio de partida, ondas, bosses e saltos dimensionais."""

    def __init__(self, jogo: Jogo) -> None:
        self.jogo = jogo

    def novo_jogo(self, nome: str, zerar_estado: bool = True) -> None:
        """Reinicia o estado efemero e prepara o primeiro nivel."""
        jogo = self.jogo
        nome = nome.strip() or "Jogador"
        skin = jogo.loja.pegar_skin(jogo.loja.skin_atual)
        jogo.jogador = Jogador(nome, skin=skin)
        jogo.jogador.velocidade = 5.0 * jogo.sensibilidade
        jogo.inimigos, jogo.projeteis, jogo.powerups = [], [], []
        jogo.boss = None
        jogo.mensagens, jogo.fila_onda, jogo.xs_onda = [], [], []
        jogo.timer_spawn = jogo.inimigos_abates = jogo.bosses_abates = 0
        jogo.boss_intro = jogo.tiros_disparados = jogo.tempo_partida = 0
        jogo.boost, jogo.especial, jogo.energia = 1.0, 0.0, 100.0
        jogo.especial_atual = "bomba"
        jogo.especiais_desbloqueados = ["bomba"]
        jogo.menu_equipamento = False
        jogo.linha_equipamento = 0
        jogo.indice_equipamento = 0
        jogo.particulas.limpar()
        jogo.flash, jogo.fade, jogo.trauma, jogo.hitstop = 0, 255, 0.0, 0
        jogo.novo_recorde = False
        jogo.moedas_ganhas = 0
        jogo.textos_acao = []
        jogo.melhorias_oferecidas = []
        jogo.melhoria_selecionada = 0
        jogo.nivel_pendente = 1
        jogo.cenario = Cenario(1)
        jogo._aplicar_qualidade_grafica()
        self.iniciar_nivel(1)
        jogo.mensagens.append(MensagemFlutuante(
            f"Bem-vindo, {nome}!", LARGURA // 2, ALTURA // 2 + 20, CIANO, 110))
        if zerar_estado:
            jogo.estado = EstadoJogo.JOGANDO

    def preparar_jogo(self) -> None:
        """Inicia a partida com a tela de carregamento."""
        jogo = self.jogo
        self.novo_jogo(jogo.nome_jogador, zerar_estado=False)
        jogo.carregamento = 0
        jogo.estado = EstadoJogo.PREPARANDO

    def salvar_tudo(self) -> None:
        """Sincroniza a loja e persiste o progresso atual."""
        jogo = self.jogo
        jogo.progresso.registrar_checkpoint(jogo.jogador.nivel)
        jogo.progresso.sincronizar_loja(jogo.loja)
        jogo.progresso.salvar_arquivo()

    def iniciar_nivel(self, nivel: int) -> None:
        """Configura as ondas ou o boss correspondente ao nivel."""
        jogo = self.jogo
        jogo.jogador.nivel = nivel
        novo_cenario_id = cenario_do_nivel(nivel)
        if novo_cenario_id != jogo.cenario.id:
            self.transicao_cenario(novo_cenario_id)
        jogo.timer_spawn = 0
        jogo.sons.tocar("nivel")
        jogo.mensagens.append(MensagemFlutuante(
            f"NIVEL {nivel}", LARGURA // 2, ALTURA // 2, CIANO, 80))
        self.verificar_desbloqueio_arma()
        if nivel % 5 == 0:
            jogo.boss = Boss(nivel, jogo.cenario)
            jogo.boss_intro = 130
            jogo.mensagens.append(MensagemFlutuante(
                f"ENTIDADE DA FENDA // {jogo.boss.nome}", LARGURA // 2,
                ALTURA // 2 + 40, DIMENSION_GOLD, 130))
            jogo.sons.tocar("boss")
            return
        jogo.boss = None
        tipos, quantidade, xs = composicao_onda(nivel, jogo.cenario.inimigos)
        jogo.fila_onda = [random.choice(tipos) for _ in range(quantidade)]
        jogo.xs_onda = list(xs)

    def oferecer_melhorias(self, proximo_nivel: int) -> None:
        """Pausa o avanço e sorteia três aprimoramentos para o jogador."""
        jogo = self.jogo
        jogo.nivel_pendente = proximo_nivel
        # O setor já foi conquistado; refletir o avanço imediatamente também
        # mantém checkpoint, telemetria e integrações externas consistentes.
        jogo.jogador.nivel = proximo_nivel
        chaves = random.sample(list(MELHORIAS), 3)
        jogo.melhorias_oferecidas = [
            {
                "id": chave,
                "nome": MELHORIAS[chave][0],
                "descricao": MELHORIAS[chave][1],
                "nivel": jogo.jogador.melhorias.get(chave, 0),
            }
            for chave in chaves
        ]
        jogo.melhoria_selecionada = 0
        jogo.estado = EstadoJogo.MELHORIA

    def selecionar_melhoria(self, indice: int) -> bool:
        """Instala a opção escolhida e começa o nível pendente."""
        jogo = self.jogo
        if not 0 <= indice < len(jogo.melhorias_oferecidas):
            return False
        chave = jogo.melhorias_oferecidas[indice]["id"]
        jogador = jogo.jogador
        jogador.melhorias[chave] = jogador.melhorias.get(chave, 0) + 1
        if chave == "potencia":
            jogador.bonus_dano += 1
        elif chave == "cadencia":
            jogador.multiplicador_cadencia = max(
                0.55, jogador.multiplicador_cadencia * 0.88,
            )
        elif chave == "motor":
            jogador.multiplicador_velocidade *= 1.08
        elif chave == "blindagem":
            jogador.max_vida += 1
            jogador.vida = min(jogador.max_vida, jogador.vida + 1)
        elif chave == "escudo":
            jogador.escudo = True
        elif chave == "especial":
            jogador.multiplicador_especial *= 1.25
        nivel = jogo.nivel_pendente
        jogo.melhorias_oferecidas = []
        jogo.estado = EstadoJogo.JOGANDO
        self.iniciar_nivel(nivel)
        return True

    def verificar_desbloqueio_arma(self) -> None:
        """Libera armas disponiveis para o nivel atual."""
        jogo = self.jogo
        for indice, arma in enumerate(ARMARIA):
            if arma["nivel"] <= jogo.jogador.nivel and indice not in jogo.jogador.armas_desbloqueadas:
                jogo.jogador.armas_desbloqueadas.append(indice)
                jogo.jogador.arma_atual = indice
                jogo.mensagens.append(MensagemFlutuante(
                    f"ARMA NOVA: {arma['nome']}!", LARGURA // 2,
                    ALTURA // 2 + 80, arma["cor"], 130))
                jogo.sons.tocar("arma")

    def transicao_cenario(self, novo_id: int) -> None:
        """Executa o salto visual e troca o cenario ativo."""
        jogo = self.jogo
        jogo.sons.tocar("transicao")
        cfg = CENARIOS[novo_id - 1]
        cor = cfg["cor_transicao"]
        jogo.mensagens.append(MensagemFlutuante(
            f"DIMENSÃO 0{novo_id} // {cfg['nome']}", LARGURA // 2,
            ALTURA // 2, cor, 140))
        jogo.particulas.salto_dimensional(LARGURA // 2, ALTURA // 2, cor)
        for _ in range(24):
            jogo.particulas.atualizar()
            self.frame_transicao()
            jogo.relogio.tick(FPS)
        for alpha in range(0, 255, 12):
            jogo._tela_fade.fill((255, 255, 255))
            jogo._tela_fade.set_alpha(alpha)
            jogo.tela.blit(jogo._tela_fade, (0, 0))
            jogo._apresentar()
            jogo.relogio.tick(FPS)
        jogo.cenario = Cenario(novo_id)
        jogo._aplicar_qualidade_grafica()
        jogo.progresso.desbloquear_cenario(novo_id)
        jogo.particulas.limpar()
        jogo.particulas.espiral_revelacao(LARGURA // 2, ALTURA // 2, cor)
        for _ in range(18):
            jogo.particulas.atualizar()
            self.frame_transicao()
            jogo.relogio.tick(FPS)

    def frame_transicao(self) -> None:
        """Desenha um quadro intermediario da transicao dimensional."""
        jogo = self.jogo
        jogo.cenario.desenhar(jogo.tela)
        jogo.particulas.desenhar(jogo.tela)
        jogo._apresentar()
