"""Integra encontros ao runtime sem acoplar as estratégias ao objeto Jogo."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.constants import ALTURA, FPS
from src.runtime.domain.entities.minibosses.config import SPAWN
from src.runtime.domain.entities.powerups import PowerUp
from src.runtime.domain.entities.weapons import Projetil
from src.runtime.domain.systems.miniboss_spawner import MinibossSpawner
from src.runtime.domain.world.particles import MensagemFlutuante
from src.runtime.presentation.damage_feedback import registrar_impacto

if TYPE_CHECKING:
    from src.runtime.application.core import Jogo


class ControladorMiniboss:
    """Coordena agendamento, lacaios, colisões especiais e recompensas."""

    def __init__(self, jogo: Jogo) -> None:
        self.jogo = jogo

    def reiniciar(self) -> None:
        """Limpa referências e cria o relógio de uma nova partida."""
        self.cancelar()
        self.jogo.miniboss_spawner = MinibossSpawner(**SPAWN)
        self.jogo.ondas_miniboss = 0

    def cancelar(self) -> None:
        """Remove efeitos e lacaios sem conceder recompensa de derrota."""
        jogo = self.jogo
        boss = getattr(jogo, "miniboss", None)
        if boss is not None:
            jogo.combate_controller.remover_inimigos(boss.lacaios)
            boss.zonas.clear()
            boss.lacaios.clear()
            boss.novos_lacaios.clear()
        jogo.miniboss = None
        if boss is not None and hasattr(jogo, "miniboss_spawner"):
            jogo.miniboss_spawner.liberar()

    def atualizar(self, dt: float = 1 / FPS) -> None:
        """Executa apenas durante gameplay; bosses principais têm prioridade."""
        jogo = self.jogo
        novo = jogo.miniboss_spawner.atualizar(
            dt, jogo.jogador.nivel, jogo.cenario, onda=jogo.ondas_miniboss,
            bloqueado=jogo.boss is not None or not jogo.jogador.vivo,
        )
        if novo is not None:
            jogo.miniboss = novo
            jogo.mensagens.append(MensagemFlutuante(
                novo.nome, novo.x, novo.alvo_y, novo.cor, 150))
            jogo.sons.tocar("boss")
        boss = jogo.miniboss
        if boss is None:
            return
        if boss.vida <= 0:
            self.derrotar()
            return
        boss.lacaios[:] = [i for i in boss.lacaios
                          if i in jogo.inimigos and i.vida > 0 and i.y <= ALTURA + 60]
        jogo.projeteis.extend(boss.atualizar(jogo.jogador, dt))
        jogo.inimigos.extend(boss.novos_lacaios)
        boss.novos_lacaios.clear()

    def colidir_jogador(self) -> None:
        """Dano por contato e zonas usa escudo e invencibilidade existentes."""
        jogo, boss = self.jogo, self.jogo.miniboss
        if boss is not None and not boss.entrando and (
                boss.rect.colliderect(jogo.jogador.rect) or boss.perigo(jogo.jogador.rect)):
            jogo.combate_controller.aplicar_dano_jogador()

    def receber_tiro(self, proj: Projetil) -> bool:
        """Encaminha tiros diretos, incluindo hitboxes fora do casco."""
        boss = self.jogo.miniboss
        if boss is None:
            return False
        antes = boss.vida
        acertou = boss.receber_tiro(proj)
        registrar_impacto(self.jogo, boss, proj, antes)
        if boss.vida <= 0:
            self.derrotar()
        return bool(acertou)

    def receber_area(self, proj: Projetil, raio: float, dano: int | None = None) -> None:
        """Explosões e plasma respeitam o estado defensivo do alvo."""
        boss = self.jogo.miniboss
        if boss is None:
            return
        antes = boss.vida
        boss.receber_area(proj.dano if dano is None else dano, proj.x, proj.y, raio)
        registrar_impacto(self.jogo, boss, proj, antes)
        if boss.vida <= 0:
            self.derrotar()

    def derrotar(self) -> None:
        """Recompensa uma vez e persiste sem avançar a campanha principal."""
        jogo, boss = self.jogo, self.jogo.miniboss
        if boss is None or boss.vida > 0:
            return
        self.cancelar()
        total = int(boss.pontos * jogo.jogador.combo.get_bonus())
        jogo.jogador.pontuacao += total
        jogo.loja.moedas += boss.cfg["moedas"]
        jogo.progresso.registrar_miniboss(boss.chave)
        jogo.progresso.sincronizar_loja(jogo.loja)
        jogo.progresso.salvar_arquivo()
        jogo.mensagens.append(MensagemFlutuante(
            f"PROTOCOLO ENCERRADO +{total} / {boss.cfg['moedas']} MOEDAS",
            boss.x, boss.y, boss.cor, 110))
        jogo.powerups.append(PowerUp(boss.cfg["drop"], boss.x, boss.y))
        jogo.particulas.explosao(boss.x, boss.y, boss.cor, 24, 7)
        jogo.sons.tocar("explosao")
        jogo.adicionar_trauma(0.4)
        jogo.congelar(2)
