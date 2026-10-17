"""Controlador de ciclo de partida, niveis e transicoes de cenario."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from src.core.constants import ALTURA, CIANO, DIMENSION_GOLD, LARGURA, EstadoJogo
from src.core.event_bus import GameEventType, publicar_evento
from src.core.settings import escala_visual
from src.runtime.application.timing import PASSO_FIXO
from src.runtime.domain.entities.bosses import Boss
from src.runtime.domain.entities.enemies import composicao_onda
from src.runtime.domain.entities.player import Jogador
from src.runtime.domain.entities.weapons import ARMARIA
from src.runtime.domain.systems.upgrades import MELHORIAS, aplicar_melhoria, sortear_melhorias
from src.runtime.domain.world.particles import MensagemFlutuante
from src.runtime.domain.world.scenarios import CENARIOS, Cenario, cenario_do_nivel
from src.runtime.presentation.dimension_transition import (
    INICIO_REVELACAO, TransicaoDimensional,
)

if TYPE_CHECKING:
    from src.runtime.application.core import Jogo


class ControladorProgressao:
    """Coordena inicio de partida, ondas, bosses e saltos dimensionais."""

    def __init__(self, jogo: Jogo) -> None:
        self.jogo = jogo
        self.transicao: TransicaoDimensional | None = None

    def novo_jogo(self, nome: str, zerar_estado: bool = True) -> None:
        """Reinicia o estado efemero e prepara o primeiro nivel."""
        jogo = self.jogo
        self.transicao = None
        nome = nome.strip() or "Jogador"
        skin = jogo.loja.pegar_skin(jogo.loja.skin_atual)
        jogo.jogador = Jogador(nome, skin=skin)
        jogo.jogador.velocidade = 5.0 * jogo.sensibilidade
        jogo.inimigos, jogo.projeteis, jogo.powerups = [], [], []
        jogo.boss = None
        jogo.miniboss_controller.reiniciar()
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
        jogo.avanco_controller.reiniciar(jogo.cenario)
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
        jogo.miniboss_controller.cancelar()
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
            publicar_evento(GameEventType.BOSS_SPAWNED, sessao=jogo,
                            boss=jogo.boss, nivel=nivel, cenario_id=jogo.cenario.id)
            return
        jogo.boss = None
        jogo.ondas_miniboss += 1
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
        chaves = sortear_melhorias(jogo.jogador)
        jogo.melhorias_oferecidas = [
            {
                "id": chave,
                "nome": MELHORIAS[chave].nome,
                "descricao": MELHORIAS[chave].descricao,
                "custo": MELHORIAS[chave].custo,
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
        if not aplicar_melhoria(jogo.jogador, chave):
            return False
        nivel = jogo.nivel_pendente
        jogo.melhorias_oferecidas = []
        jogo.estado = EstadoJogo.JOGANDO
        self.iniciar_nivel(nivel)
        return True

    def verificar_desbloqueio_arma(self) -> None:
        """Libera armas disponiveis para o nivel atual."""
        jogo = self.jogo
        for indice, arma in enumerate(ARMARIA):
            if (arma["nivel"] <= jogo.jogador.nivel
                    and indice not in jogo.jogador.armas_desbloqueadas):
                jogo.jogador.armas_desbloqueadas.append(indice)
                jogo.jogador.arma_atual = indice
                jogo.mensagens.append(MensagemFlutuante(
                    f"ARMA NOVA: {arma['nome']}!", LARGURA // 2,
                    ALTURA // 2 + 80, arma["cor"], 130))
                jogo.sons.tocar("arma")

    def transicao_cenario(self, novo_id: int) -> None:
        """Agenda o salto visual sem interromper a fila de eventos."""
        jogo = self.jogo
        jogo.sons.tocar("transicao")
        cfg = CENARIOS[novo_id - 1]
        cor = cfg["cor_transicao"]
        jogo.mensagens.append(MensagemFlutuante(
            f"DIMENSÃO 0{novo_id} // {cfg['nome']}", LARGURA // 2,
            ALTURA // 2, cor, 140))
        jogo.particulas.salto_dimensional(LARGURA // 2, ALTURA // 2, cor)
        self.transicao = TransicaoDimensional(jogo.cenario, cor)
        jogo.cenario = Cenario(novo_id)
        jogo._aplicar_qualidade_grafica()
        jogo.avanco_controller.trocar_dimensao(jogo.cenario)
        jogo.progresso.desbloquear_cenario(novo_id)

    def atualizar_transicao(self) -> None:
        """Avança uma etapa do salto por passo fixo de simulação."""
        transicao = self.transicao
        if transicao is None:
            return
        cenario_visivel = (transicao.cenario_anterior if transicao.quadro < INICIO_REVELACAO
                           else self.jogo.cenario)
        self.jogo.avanco_controller.atualizar(cenario_visivel, PASSO_FIXO)
        if transicao.atualizar(self.jogo.cenario, self.jogo.particulas):
            self.transicao = None
            publicar_evento(GameEventType.DIMENSION_CHANGED, sessao=self.jogo,
                            cenario_id=self.jogo.cenario.id)

    def frame_transicao(self) -> None:
        """Desenha o quadro atual da transição na superfície lógica."""
        jogo = self.jogo
        transicao = self.transicao
        if transicao is None:
            return
        transicao.desenhar(
            jogo.tela, jogo.cenario, jogo.particulas, jogo._tela_fade,
            escala_visual(jogo.config["intensidade_flash"]),
        )
