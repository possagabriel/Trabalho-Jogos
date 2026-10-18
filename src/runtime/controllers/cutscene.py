"""Integra cenas dirigidas por dados ao loop, eventos e persistência."""

from __future__ import annotations

import logging
import weakref
from collections import deque
from importlib.resources import files
from typing import TYPE_CHECKING, Any

import pygame

from src.core.constants import EstadoJogo
from src.core.event_bus import EventBus, GameEvent, GameEventType
from src.runtime.domain.story import Cena, SequenciadorCena, ler_catalogo
from src.runtime.presentation.dialogue_box import DialogueBox

if TYPE_CHECKING:
    from src.runtime.application.core import Jogo

LOGGER = logging.getLogger(__name__)
TEMPO_SEGURAR_PULO = 0.65


class ControladorCutscene:
    """Agenda e apresenta cenas sem modificar entidades ou regras de combate."""

    def __init__(self, jogo: Jogo) -> None:
        self._jogo = weakref.ref(jogo)
        self.catalogo = ler_catalogo(files("src.runtime.story") / "cenas_pt_BR.json")
        self.sequenciador = SequenciadorCena(
            velocidade=jogo.config["velocidade_dialogo"],
            ao_concluir=self._ao_concluir, ao_entrar=self._ao_entrar,
        )
        self.fila: deque[Cena] = deque()
        self.caixa = DialogueBox(self.catalogo.personagens)
        self.estado_anterior = EstadoJogo.JOGANDO
        self.revisao = False
        self.pausado = False
        self.confirmacao_pulo = False
        self.segurando_pulo = False
        self.tempo_pulo = 0.0
        self.retrato_atual: str | None = None
        self._musica_pausada = False
        self.seletor_debug = False
        self.indice_debug = 0
        self._bus = EventBus()
        referencia = weakref.ref(self)
        bus = self._bus
        tipos = (GameEventType.GAME_START, GameEventType.DIMENSION_CHANGED,
                 GameEventType.BOSS_SPAWNED, GameEventType.BOSS_DEFEATED,
                 GameEventType.MINIBOSS_SPAWNED)

        def escutar(evento: GameEvent) -> None:
            controlador = referencia()
            if controlador is None:
                for tipo in tipos:
                    bus.unsubscribe(tipo, escutar)
            else:
                controlador._ao_evento(evento)

        self._escutar = escutar
        for tipo in tipos:
            self._bus.subscribe(tipo, escutar)

    @property
    def ativo(self) -> bool:
        """Indica se uma cena está visível."""
        return bool(self.sequenciador.ativo)

    def tem_pos_boss(self, cenario_id: int) -> bool:
        """Informa ao avanço se existe cena antes da retomada."""
        return self.catalogo.por_gatilho(f"boss_derrota:{cenario_id}") is not None

    def _ao_evento(self, evento: GameEvent) -> None:
        jogo = self._jogo()
        if jogo is None or evento.data.get("sessao") is not jogo:
            return
        tipo = evento.type
        if tipo is GameEventType.GAME_START:
            self.iniciar_gatilho("inicio")
            self.iniciar_gatilho("capitulo_abertura:1")
        elif tipo is GameEventType.DIMENSION_CHANGED:
            self.iniciar_gatilho(f"capitulo_abertura:{evento.data['cenario_id']}")
        elif tipo is GameEventType.BOSS_SPAWNED:
            self.iniciar_gatilho(f"boss_entrada:{evento.data['cenario_id']}")
        elif tipo is GameEventType.BOSS_DEFEATED:
            cenario_id = evento.data["cenario_id"]
            self.iniciar_gatilho(f"boss_derrota:{cenario_id}")
            self.iniciar_gatilho(f"capitulo_fim:{cenario_id}")
            if cenario_id == 6:
                self.iniciar_gatilho("final")
        elif tipo is GameEventType.MINIBOSS_SPAWNED:
            chave = evento.data.get("chave", "")
            cena = self.catalogo.por_gatilho(f"miniboss:{chave}")
            if cena is not None and cena.id not in jogo.progresso.cenas_vistas:
                self.iniciar_gatilho(cena.gatilho)

    def iniciar_gatilho(self, gatilho: str) -> bool:
        """Agenda uma cena conhecida; gatilhos ausentes são ignorados."""
        cena = self.catalogo.por_gatilho(gatilho)
        if cena is None:
            LOGGER.warning("Cena inexistente para gatilho %s; ignorando", gatilho)
            return False
        self.fila.append(cena)
        if not self.ativo:
            self._iniciar_proxima()
        return True

    def rever(self, identificador: str) -> bool:
        """Reproduz uma cena desbloqueada a partir do Arquivo de Memórias."""
        jogo = self._jogo()
        cena = self.catalogo.cena(identificador)
        if jogo is None or cena is None or identificador not in jogo.progresso.cenas_vistas:
            LOGGER.warning("Cena %s indisponível no Arquivo de Memórias", identificador)
            return False
        self.revisao = True
        self.fila.append(cena)
        if not self.ativo:
            self._iniciar_proxima()
        return True

    def _iniciar_proxima(self) -> None:
        jogo = self._jogo()
        if jogo is None:
            return
        if self.fila:
            if jogo.estado is not EstadoJogo.CUTSCENE:
                self.estado_anterior = jogo.estado
            cena = self.fila.popleft()
            self.retrato_atual = None
            self.pausado = False
            self.confirmacao_pulo = False
            self.segurando_pulo = False
            self.tempo_pulo = 0.0
            self.sequenciador.iniciar(cena)
            jogo.estado = EstadoJogo.CUTSCENE
            return
        self.revisao = False
        self.pausado = False
        self.confirmacao_pulo = False
        self.seletor_debug = False
        if jogo.estado is EstadoJogo.CUTSCENE:
            jogo.estado = self.estado_anterior
        jogo.avanco_controller.liberar_retomada()
        if self._musica_pausada and hasattr(jogo.sons, "retomar_musica"):
            jogo.sons.retomar_musica()
            self._musica_pausada = False

    def _ao_concluir(self, identificador: str) -> None:
        jogo = self._jogo()
        cena = self.catalogo.cena(identificador)
        if (jogo is not None and cena is not None and cena.passos[-1]["tipo"] == "fade"
                and cena.passos[-1].get("direcao") == "saida"):
            jogo.fade = 255
        if jogo is not None and not self.revisao:
            jogo.progresso.marcar_cena_vista(identificador)
        self._iniciar_proxima()

    def _ao_entrar(self, passo: dict[str, Any]) -> None:
        jogo = self._jogo()
        if jogo is None:
            return
        tipo = passo["tipo"]
        if tipo == "retrato":
            self.retrato_atual = passo["icone"]
            self.caixa.obter_retrato(passo["icone"])
        elif tipo == "shake":
            jogo.adicionar_trauma(float(passo.get("intensidade", 0.25)))
        elif tipo == "som":
            jogo.sons.tocar(passo["acao"])
        elif tipo == "musica":
            acao = passo["acao"]
            if acao == "parar" and hasattr(jogo.sons, "pausar_musica"):
                jogo.sons.pausar_musica()
                self._musica_pausada = True
            elif acao == "tocar" and hasattr(jogo.sons, "retomar_musica"):
                jogo.sons.retomar_musica()
                self._musica_pausada = False

    def atualizar(self, dt: float) -> None:
        """Avança apenas narrativa e rolagem visual durante a cena."""
        jogo = self._jogo()
        if jogo is None or self.pausado or not self.ativo:
            return
        if self.segurando_pulo and not self.confirmacao_pulo:
            self.tempo_pulo += dt
            if self.tempo_pulo >= TEMPO_SEGURAR_PULO:
                self.confirmacao_pulo = True
                self.segurando_pulo = False
        self.sequenciador.atualizar(dt)
        if jogo.avanco_controller.modelo.estado.value in ("FREANDO", "PARADO"):
            jogo.avanco_controller.atualizar(jogo.cenario, dt)

    def pausar(self) -> None:
        """Congela ou retoma texto e cenário, mantendo a mesma cena."""
        self.pausado = not self.pausado
        self.sequenciador.pausado = self.pausado

    def pular_direto(self) -> None:
        """Encerra a cena atual; usado após confirmação e em testes."""
        self.sequenciador.pular()

    def tratar_evento(self, evento: pygame.event.Event) -> None:
        """Trata confirmação, pausa, clique e intenção de pular."""
        jogo = self._jogo()
        if jogo is None:
            return
        if self.seletor_debug:
            if evento.type == pygame.KEYDOWN:
                ids = list(self.catalogo.cenas)
                if evento.key == pygame.K_ESCAPE:
                    self.seletor_debug = False
                    jogo.estado = self.estado_anterior
                elif ids and evento.key in (pygame.K_DOWN, pygame.K_s):
                    self.indice_debug = (self.indice_debug + 1) % len(ids)
                elif ids and evento.key in (pygame.K_UP, pygame.K_w):
                    self.indice_debug = (self.indice_debug - 1) % len(ids)
                elif ids and evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.seletor_debug = False
                    self.fila.append(self.catalogo.cenas[ids[self.indice_debug]])
                    self._iniciar_proxima()
            return
        if evento.type == pygame.KEYUP and evento.key == pygame.K_BACKSPACE:
            self.segurando_pulo = False
            self.tempo_pulo = 0.0
            return
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            pos = jogo.menu._pos_logica(evento.pos)
            if pos[0] >= 1050 and pos[1] <= 80:
                if self.sequenciador.cena.id in jogo.progresso.cenas_vistas:
                    self.pular_direto()
                else:
                    self.confirmacao_pulo = True
            elif self.confirmacao_pulo:
                if self.caixa.BOTAO_CONFIRMAR.collidepoint(pos):
                    self.pular_direto()
                elif self.caixa.BOTAO_CANCELAR.collidepoint(pos):
                    self.confirmacao_pulo = False
            elif not self.pausado:
                self.sequenciador.confirmar()
            return
        if evento.type != pygame.KEYDOWN:
            return
        if evento.key in (pygame.K_p, jogo.controles.get("pausar", -1)):
            self.pausar()
        elif evento.key == pygame.K_ESCAPE:
            if self.confirmacao_pulo:
                self.confirmacao_pulo = False
            else:
                self.pausar()
        elif evento.key == pygame.K_BACKSPACE:
            self._pedir_pulo()
        elif self.confirmacao_pulo:
            if evento.key in (pygame.K_RETURN, jogo.controles.get("atirar", -1)):
                self.pular_direto()
        elif not self.pausado and evento.key in (
                pygame.K_RETURN, pygame.K_KP_ENTER, jogo.controles.get("atirar", -1)):
            self.sequenciador.confirmar()

    def _pedir_pulo(self) -> None:
        jogo = self._jogo()
        if not self.ativo or jogo is None:
            return
        if self.sequenciador.cena.id in jogo.progresso.cenas_vistas:
            self.pular_direto()
        elif self.confirmacao_pulo:
            self.pular_direto()
        else:
            self.segurando_pulo = True
            self.tempo_pulo = 0.0

    def abrir_seletor_debug(self) -> None:
        """Abre seletor de cenas somente quando o F3 está ativo."""
        jogo = self._jogo()
        if jogo is not None and jogo.debug_ativo:
            self.seletor_debug = True
            self.estado_anterior = jogo.estado
            jogo.estado = EstadoJogo.CUTSCENE
            LOGGER.info("Cenas disponíveis: %s", ", ".join(self.catalogo.cenas))
