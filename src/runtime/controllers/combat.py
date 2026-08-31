"""Controlador de projeteis, colisao e coleta durante a partida."""

from __future__ import annotations

import math
import random
from typing import Callable, Protocol

from src.runtime.controllers.session import SessaoCombate
from src.core.constants import ALTURA, EstadoJogo, LARANJA
from src.runtime.domain.entities.enemies import Inimigo, InimigoEspecial
from src.runtime.infrastructure.graphics.cel_shading import TextoAcao
from src.runtime.domain.world.particles import MensagemFlutuante
from src.runtime.domain.entities.powerups import PowerUp, sortear_tipo
from src.runtime.domain.entities.weapons import Projetil


class EntidadePosicionada(Protocol):
    """Contrato minimo para entidades que participam de calculos espaciais."""

    x: float
    y: float


class ControladorCombate:
    """Coordena o fluxo de combate sem possuir o estado global do jogo."""

    def __init__(self, sessao: SessaoCombate) -> None:
        self.sessao = sessao

    def ativar_especial(self) -> bool:
        """Lanca a Bomba Vortex se a carga especial estiver completa."""
        sessao = self.sessao
        if sessao.especial < 1.0 or sessao.estado is not EstadoJogo.JOGANDO:
            return False
        sessao.especial = 0.0
        x, y = sessao.jogador.x, sessao.jogador.y - 24
        sessao.projeteis.append(Projetil(x, y, 0, -3.5, 25, LARANJA, 20,
                                         tipo="bomba"))
        sessao.flash = 10
        sessao.sons.tocar("especial")
        sessao.adicionar_trauma(0.3)
        return True

    def aplicar_dano_jogador(self) -> bool:
        """Aplica dano, escudo e feedback audiovisual ao jogador."""
        sessao = self.sessao
        tinha_escudo = sessao.jogador.escudo
        if not sessao.jogador.sofrer_dano():
            return False
        sessao.jogador.combo.zerar()
        sessao.flash = 10
        sessao.sons.tocar("dano")
        sessao.adicionar_trauma(0.5)
        if tinha_escudo:
            sessao.sons.tocar("escudo")
            sessao.adicionar_trauma(0.3)
        return True

    @staticmethod
    def distancia(entidade: EntidadePosicionada, proj: Projetil) -> float:
        """Calcula a distancia euclidiana entre uma entidade e um projetil."""
        return math.hypot(entidade.x - proj.x, entidade.y - proj.y)

    def explodir_em_area(self, proj: Projetil, raio: float, y_limite: float,
                          efeitos: Callable[[Projetil], None],
                          flash_inimigo: int = 8) -> bool:
        """Aplica uma explosao a inimigos e boss dentro de um raio."""
        sessao = self.sessao
        tem_alvo = any(
            self.distancia(inimigo, proj) < raio for inimigo in sessao.inimigos)
        tem_alvo = tem_alvo or bool(
            sessao.boss and self.distancia(sessao.boss, proj) < raio)
        if not tem_alvo and proj.y > y_limite:
            return False
        efeitos(proj)
        for inimigo in sessao.inimigos[:]:
            if self.distancia(inimigo, proj) < raio:
                if inimigo.sofrer_dano(proj.dano):
                    self.explodir_inimigo(inimigo)
                else:
                    inimigo.flash = flash_inimigo
        if sessao.boss and self.distancia(sessao.boss, proj) < raio:
            if sessao.boss.sofrer_dano(proj.dano):
                self.derrotar_boss()
            else:
                sessao.adicionar_trauma(0.15)
        return True

    def efeitos_nova(self, proj: Projetil) -> None:
        """Emite os efeitos da explosao da arma Nova."""
        sessao = self.sessao
        sessao.sons.tocar("nova")
        sessao.particulas.explosao(proj.x, proj.y, LARANJA, 26, 7)
        sessao.particulas.explosao(proj.x, proj.y, (255, 220, 120), 14, 4)
        sessao.adicionar_trauma(0.35)
        sessao.congelar(2)

    def efeitos_bomba(self, proj: Projetil) -> None:
        """Emite os efeitos da Bomba Vortex."""
        sessao = self.sessao
        sessao.sons.tocar("especial")
        sessao.particulas.explosao(proj.x, proj.y, (255, 90, 30), 42, 9)
        sessao.particulas.explosao(proj.x, proj.y, (255, 220, 120), 20, 5)
        sessao.particulas.mega(proj.x, proj.y)
        sessao.flash = 16
        sessao.adicionar_trauma(0.7)
        sessao.congelar(4)

    def explodir_nova(self, proj: Projetil) -> bool:
        """Executa a explosao de area da arma Nova."""
        return self.explodir_em_area(proj, 90, 40, self.efeitos_nova, 8)

    def explodir_bomba(self, proj: Projetil) -> bool:
        """Executa a explosao de area da Bomba Vortex."""
        return self.explodir_em_area(proj, 150, 60, self.efeitos_bomba, 10)

    def explodir_inimigo(self, inimigo: Inimigo) -> None:
        """Resolve pontos, efeitos e quedas da derrota de um inimigo."""
        sessao = self.sessao
        bonus = sessao.jogador.combo.combo_atual * 5
        total = int((inimigo.pontos + bonus) * sessao.jogador.combo.get_bonus())
        sessao.jogador.pontuacao += total
        sessao.mensagens.append(
            MensagemFlutuante(f"+{total}", inimigo.x, inimigo.y, inimigo.cor))
        sessao.particulas.explosao(inimigo.x, inimigo.y, inimigo.cor, 18, 6)
        if random.random() < 0.35:
            sessao.textos_acao.append(TextoAcao(
                inimigo.x, inimigo.y - 20,
                cor=random.choice([(255, 200, 50), (255, 100, 50),
                                   (255, 50, 100), (100, 255, 100)])))
        sessao.sons.tocar("explosao")
        sessao.adicionar_trauma(0.2)
        sessao.inimigos_abates += 1
        sessao.especial = min(1.0, sessao.especial + 0.02)
        if inimigo.tipo == "bomba":
            sessao.particulas.explosao(
                inimigo.x, inimigo.y, (255, 120, 40), 24, 6.5)
            sessao.adicionar_trauma(0.35)
            if math.hypot(
                    sessao.jogador.x - inimigo.x, sessao.jogador.y - inimigo.y) < 70:
                self.aplicar_dano_jogador()
        if isinstance(inimigo, InimigoEspecial):
            self.drop_especial(inimigo)
        elif random.random() < 0.08 + min(
                0.12, sessao.jogador.combo.combo_atual * 0.004):
            sessao.powerups.append(PowerUp(sortear_tipo(), inimigo.x, inimigo.y))
        sessao.inimigos.remove(inimigo)

    def drop_especial(self, inimigo: InimigoEspecial) -> None:
        """Gera a queda correspondente a um inimigo especial."""
        chances = {"acumulador": 0.50, "esponja": 0.30, "condutor": 0.40,
                   "mutante": 0.80, "cristalino": 0.05, "evocador": 0.30}
        tipo = inimigo.tipo_especial
        if random.random() > chances[tipo]:
            return
        queda = {"acumulador": "arma", "esponja": "vida", "condutor": "escudo",
                 "mutante": "moedas", "cristalino": "skin", "evocador": "arma"}[tipo]
        self.sessao.powerups.append(PowerUp(queda, inimigo.x, inimigo.y))

    def derrotar_boss(self) -> None:
        """Resolve pontuacao, particulas e quedas pela derrota de um boss."""
        sessao = self.sessao
        boss = sessao.boss
        if boss is None:
            return
        sessao.boss = None
        total = int(boss.pontos * sessao.jogador.combo.get_bonus())
        sessao.jogador.pontuacao += total
        sessao.progresso.registrar_boss()
        sessao.bosses_abates += 1
        sessao.mensagens.append(MensagemFlutuante(
            f"BOSS DERROTADO! +{total}", boss.x, boss.y, boss.cor, 110))
        efeitos = {
            "explosao": lambda: sessao.particulas.explosao(
                boss.x, boss.y, boss.cor, qtd=boss.part_qtd, forca=8),
            "mega": lambda: sessao.particulas.mega(boss.x, boss.y),
            "espiral": lambda: sessao.particulas.espiral(
                boss.x, boss.y, boss.cor, boss.part_qtd),
            "estrela": lambda: sessao.particulas.estrela(
                boss.x, boss.y, boss.cor, boss.part_qtd),
            "pulsacao": lambda: sessao.particulas.pulsacao(
                boss.x, boss.y, boss.cor, boss.part_qtd),
        }
        efeitos[boss.efeito]()
        sessao.sons.tocar("explosao")
        sessao.adicionar_trauma(0.8)
        sessao.congelar(3)
        for _ in range(3):
            sessao.powerups.append(
                PowerUp(sortear_tipo(), boss.x, boss.y + random.randint(-20, 20)))

    def atualizar_projeteis(self) -> None:
        """Atualiza movimento, colisao e remocao de todos os projeteis."""
        sessao = self.sessao
        for proj in sessao.projeteis[:]:
            if proj.teleguiado:
                proj.atualizar_teleguiado(sessao.jogador.x, sessao.jogador.y)
            else:
                proj.atualizar()
            if proj.saiu_da_tela():
                sessao.projeteis.remove(proj)
                continue
            if proj.origem == "jogador":
                self._aplicar_atracao_gravitacional(proj)
                acertou = self.projetil_jogador_atinge(proj)
                if (acertou and proj.tipo not in ("ion", "gauss")
                        and proj.origem == "jogador"):
                    sessao.projeteis.remove(proj)
            elif proj.rect.colliderect(sessao.jogador.rect):
                sessao.projeteis.remove(proj)
                self.aplicar_dano_jogador()

    def _aplicar_atracao_gravitacional(self, proj: Projetil) -> None:
        """Curva tiros proximos de inimigos com campo gravitacional."""
        for inimigo in self.sessao.inimigos:
            atrai = inimigo.tipo == "distorcao" or (
                isinstance(inimigo, InimigoEspecial) and inimigo.tipo_especial == "condutor")
            if not atrai:
                continue
            dx = inimigo.x - proj.x
            dy = inimigo.y - proj.y
            distancia = math.hypot(dx, dy)
            if 1 < distancia < 150:
                proj.vel_x += dx / distancia * 0.35
                proj.vel_y += dy / distancia * 0.35

    def projetil_jogador_atinge(self, proj: Projetil) -> bool:
        """Aplica dano de um tiro do jogador e informa se houve acerto."""
        sessao = self.sessao
        if proj.tipo == "nova":
            return self.explodir_nova(proj)
        if proj.tipo == "bomba":
            return self.explodir_bomba(proj)
        penetrante = proj.tipo in ("ion", "gauss")
        acertou = False
        for inimigo in sessao.inimigos[:]:
            if not proj.rect.colliderect(inimigo.rect):
                continue
            if isinstance(inimigo, InimigoEspecial) and inimigo.campo_forca:
                if proj.tipo != "ion":
                    proj.refletir()
                    sessao.sons.tocar("coleta")
                return True
            if isinstance(inimigo, InimigoEspecial):
                morreu = inimigo.receber_tiro(proj.dano)
                sessao.sons.tocar("carga")
                sessao.particulas.faiscas(proj.x, proj.y, proj.cor, 5)
                if morreu:
                    self.explodir_inimigo(inimigo)
            elif inimigo.sofrer_dano(proj.dano):
                self.explodir_inimigo(inimigo)
            else:
                sessao.sons.tocar("acerto")
                sessao.particulas.faiscas(proj.x, proj.y, proj.cor, 5)
            acertou = True
            if not penetrante:
                return True
        if sessao.boss and proj.rect.colliderect(sessao.boss.rect):
            if sessao.boss.sofrer_dano(proj.dano):
                self.derrotar_boss()
            else:
                sessao.sons.tocar("acerto")
                sessao.particulas.faiscas(proj.x, proj.y, proj.cor, 6)
                sessao.adicionar_trauma(0.15)
            acertou = True
        return acertou

    def atualizar_powerups(self) -> None:
        """Atualiza quedas e aplica as coletas do jogador."""
        sessao = self.sessao
        for powerup in sessao.powerups[:]:
            powerup.atualizar()
            if powerup.y > ALTURA + 30:
                sessao.powerups.remove(powerup)
            elif powerup.rect.colliderect(sessao.jogador.rect):
                sessao.powerups.remove(powerup)
                mensagem = powerup.aplicar(sessao.jogador, sessao.desbloquear_skin)
                sessao.mensagens.append(MensagemFlutuante(
                    mensagem, powerup.x, powerup.y, PowerUp.CORES[powerup.tipo]))
                sessao.sons.tocar("coleta")
