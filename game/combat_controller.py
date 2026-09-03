"""Controlador de projeteis, colisao e coleta durante a partida."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from .config import ALTURA, LARANJA
from .enemies import InimigoEspecial
from .cel_shading import TextoAcao
from .particles import MensagemFlutuante
from .powerups import PowerUp, sortear_tipo
from .weapons import Projetil

if TYPE_CHECKING:
    from .core import Jogo


class ControladorCombate:
    """Coordena o fluxo de combate sem possuir o estado global do jogo."""

    def __init__(self, jogo: Jogo) -> None:
        self.jogo = jogo

    def ativar_especial(self) -> bool:
        """Lanca a Bomba Vortex se a carga especial estiver completa."""
        jogo = self.jogo
        if jogo.especial < 1.0 or jogo.estado != "JOGANDO":
            return False
        jogo.especial = 0.0
        x, y = jogo.jogador.x, jogo.jogador.y - 24
        jogo.projeteis.append(Projetil(x, y, 0, -3.5, 25, LARANJA, 20,
                                       tipo="bomba"))
        jogo.flash = 10
        jogo.sons.tocar("especial")
        jogo._adicionar_trauma(0.3)
        return True

    def aplicar_dano_jogador(self) -> bool:
        """Aplica dano, escudo e feedback audiovisual ao jogador."""
        jogo = self.jogo
        tinha_escudo = jogo.jogador.escudo
        if not jogo.jogador.sofrer_dano():
            return False
        jogo.jogador.combo.zerar()
        jogo.flash = 10
        jogo.sons.tocar("dano")
        jogo._adicionar_trauma(0.5)
        if tinha_escudo:
            jogo.sons.tocar("escudo")
            jogo._adicionar_trauma(0.3)
        return True

    @staticmethod
    def distancia(entidade, proj) -> float:
        """Calcula a distancia euclidiana entre uma entidade e um projetil."""
        return math.hypot(entidade.x - proj.x, entidade.y - proj.y)

    def explodir_em_area(self, proj, raio: float, y_limite: float,
                          efeitos, flash_inimigo: int = 8) -> bool:
        """Aplica uma explosao a inimigos e boss dentro de um raio."""
        jogo = self.jogo
        tem_alvo = any(self.distancia(inimigo, proj) < raio for inimigo in jogo.inimigos)
        tem_alvo = tem_alvo or bool(jogo.boss and self.distancia(jogo.boss, proj) < raio)
        if not tem_alvo and proj.y > y_limite:
            return False
        efeitos(proj)
        for inimigo in jogo.inimigos[:]:
            if self.distancia(inimigo, proj) < raio:
                if inimigo.sofrer_dano(proj.dano):
                    self.explodir_inimigo(inimigo)
                else:
                    inimigo.flash = flash_inimigo
        if jogo.boss and self.distancia(jogo.boss, proj) < raio:
            if jogo.boss.sofrer_dano(proj.dano):
                self.derrotar_boss()
            else:
                jogo._adicionar_trauma(0.15)
        return True

    def efeitos_nova(self, proj) -> None:
        """Emite os efeitos da explosao da arma Nova."""
        jogo = self.jogo
        jogo.sons.tocar("nova")
        jogo.particulas.explosao(proj.x, proj.y, LARANJA, 26, 7)
        jogo.particulas.explosao(proj.x, proj.y, (255, 220, 120), 14, 4)
        jogo._adicionar_trauma(0.35)
        jogo._congelar(2)

    def efeitos_bomba(self, proj) -> None:
        """Emite os efeitos da Bomba Vortex."""
        jogo = self.jogo
        jogo.sons.tocar("especial")
        jogo.particulas.explosao(proj.x, proj.y, (255, 90, 30), 42, 9)
        jogo.particulas.explosao(proj.x, proj.y, (255, 220, 120), 20, 5)
        jogo.particulas.mega(proj.x, proj.y)
        jogo.flash = 16
        jogo._adicionar_trauma(0.7)
        jogo._congelar(4)

    def explodir_nova(self, proj) -> bool:
        """Executa a explosao de area da arma Nova."""
        return self.explodir_em_area(proj, 90, 40, self.efeitos_nova, 8)

    def explodir_bomba(self, proj) -> bool:
        """Executa a explosao de area da Bomba Vortex."""
        return self.explodir_em_area(proj, 150, 60, self.efeitos_bomba, 10)

    def explodir_inimigo(self, inimigo) -> None:
        """Resolve pontos, efeitos e quedas da derrota de um inimigo."""
        jogo = self.jogo
        bonus = jogo.jogador.combo.combo_atual * 5
        total = int((inimigo.pontos + bonus) * jogo.jogador.combo.get_bonus())
        jogo.jogador.pontuacao += total
        jogo.mensagens.append(MensagemFlutuante(f"+{total}", inimigo.x, inimigo.y, inimigo.cor))
        jogo.particulas.explosao(inimigo.x, inimigo.y, inimigo.cor, 18, 6)
        if random.random() < 0.35:
            jogo.textos_acao.append(TextoAcao(
                inimigo.x, inimigo.y - 20,
                cor=random.choice([(255, 200, 50), (255, 100, 50),
                                   (255, 50, 100), (100, 255, 100)])))
        jogo.sons.tocar("explosao")
        jogo._adicionar_trauma(0.2)
        jogo.inimigos_abates += 1
        jogo.especial = min(1.0, jogo.especial + 0.02)
        if inimigo.tipo == "bomba":
            jogo.particulas.explosao(inimigo.x, inimigo.y, (255, 120, 40), 24, 6.5)
            jogo._adicionar_trauma(0.35)
            if math.hypot(jogo.jogador.x - inimigo.x, jogo.jogador.y - inimigo.y) < 70:
                self.aplicar_dano_jogador()
        if isinstance(inimigo, InimigoEspecial):
            self.drop_especial(inimigo)
        elif random.random() < 0.08 + min(0.12, jogo.jogador.combo.combo_atual * 0.004):
            jogo.powerups.append(PowerUp(sortear_tipo(), inimigo.x, inimigo.y))
        jogo.inimigos.remove(inimigo)

    def drop_especial(self, inimigo) -> None:
        """Gera a queda correspondente a um inimigo especial."""
        chances = {"acumulador": 0.50, "esponja": 0.30, "condutor": 0.40,
                   "mutante": 0.80, "cristalino": 0.05, "evocador": 0.30}
        tipo = inimigo.tipo_especial
        if random.random() > chances[tipo]:
            return
        queda = {"acumulador": "arma", "esponja": "vida", "condutor": "escudo",
                 "mutante": "moedas", "cristalino": "skin", "evocador": "arma"}[tipo]
        self.jogo.powerups.append(PowerUp(queda, inimigo.x, inimigo.y))

    def derrotar_boss(self) -> None:
        """Resolve pontuacao, particulas e quedas pela derrota de um boss."""
        jogo = self.jogo
        boss = jogo.boss
        jogo.boss = None
        total = int(boss.pontos * jogo.jogador.combo.get_bonus())
        jogo.jogador.pontuacao += total
        jogo.progresso.registrar_boss()
        jogo.bosses_abates += 1
        jogo.mensagens.append(MensagemFlutuante(f"BOSS DERROTADO! +{total}",
                                                boss.x, boss.y, boss.cor, 110))
        efeitos = {
            "explosao": lambda: jogo.particulas.explosao(boss.x, boss.y, boss.cor, qtd=boss.part_qtd, forca=8),
            "mega": lambda: jogo.particulas.mega(boss.x, boss.y),
            "espiral": lambda: jogo.particulas.espiral(boss.x, boss.y, boss.cor, boss.part_qtd),
            "estrela": lambda: jogo.particulas.estrela(boss.x, boss.y, boss.cor, boss.part_qtd),
            "pulsacao": lambda: jogo.particulas.pulsacao(boss.x, boss.y, boss.cor, boss.part_qtd),
        }
        efeitos[boss.efeito]()
        jogo.sons.tocar("explosao")
        jogo._adicionar_trauma(0.8)
        jogo._congelar(3)
        for _ in range(3):
            jogo.powerups.append(PowerUp(sortear_tipo(), boss.x, boss.y + random.randint(-20, 20)))

    def atualizar_projeteis(self) -> None:
        """Atualiza movimento, colisao e remocao de todos os projeteis."""
        jogo = self.jogo
        for proj in jogo.projeteis[:]:
            if proj.teleguiado:
                proj.atualizar_teleguiado(jogo.jogador.x, jogo.jogador.y)
            else:
                proj.atualizar()
            if proj.saiu_da_tela():
                jogo.projeteis.remove(proj)
                continue
            if proj.origem == "jogador":
                self._aplicar_atracao_gravitacional(proj)
                acertou = self.projetil_jogador_atinge(proj)
                if acertou and proj.tipo not in ("ion", "gauss") and proj.origem == "jogador":
                    jogo.projeteis.remove(proj)
            elif proj.rect.colliderect(jogo.jogador.rect):
                jogo.projeteis.remove(proj)
                jogo._aplicar_dano_jogador()

    def _aplicar_atracao_gravitacional(self, proj: Projetil) -> None:
        """Curva tiros proximos de inimigos com campo gravitacional."""
        for inimigo in self.jogo.inimigos:
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
        jogo = self.jogo
        if proj.tipo == "nova":
            return jogo._explodir_nova(proj)
        if proj.tipo == "bomba":
            return jogo._explodir_bomba(proj)
        penetrante = proj.tipo in ("ion", "gauss")
        acertou = False
        for inimigo in jogo.inimigos[:]:
            if not proj.rect.colliderect(inimigo.rect):
                continue
            if isinstance(inimigo, InimigoEspecial) and inimigo.campo_forca:
                if proj.tipo != "ion":
                    proj.refletir()
                    jogo.sons.tocar("coleta")
                return True
            if isinstance(inimigo, InimigoEspecial):
                morreu = inimigo.receber_tiro(proj.dano)
                jogo.sons.tocar("carga")
                jogo.particulas.faiscas(proj.x, proj.y, proj.cor, 5)
                if morreu:
                    jogo._explodir_inimigo(inimigo)
            elif inimigo.sofrer_dano(proj.dano):
                jogo._explodir_inimigo(inimigo)
            else:
                jogo.sons.tocar("acerto")
                jogo.particulas.faiscas(proj.x, proj.y, proj.cor, 5)
            acertou = True
            if not penetrante:
                return True
        if jogo.boss and proj.rect.colliderect(jogo.boss.rect):
            if jogo.boss.sofrer_dano(proj.dano):
                jogo._derrotar_boss()
            else:
                jogo.sons.tocar("acerto")
                jogo.particulas.faiscas(proj.x, proj.y, proj.cor, 6)
                jogo._adicionar_trauma(0.15)
            acertou = True
        return acertou

    def atualizar_powerups(self) -> None:
        """Atualiza quedas e aplica as coletas do jogador."""
        jogo = self.jogo
        for powerup in jogo.powerups[:]:
            powerup.atualizar()
            if powerup.y > ALTURA + 30:
                jogo.powerups.remove(powerup)
            elif powerup.rect.colliderect(jogo.jogador.rect):
                jogo.powerups.remove(powerup)
                mensagem = powerup.aplicar(jogo.jogador, jogo._desbloquear_skin_jogo)
                jogo.mensagens.append(MensagemFlutuante(
                    mensagem, powerup.x, powerup.y, PowerUp.CORES[powerup.tipo]))
                jogo.sons.tocar("coleta")
