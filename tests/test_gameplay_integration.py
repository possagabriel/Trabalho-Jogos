"""Fluxo integrado de uma partida, do combate ao carregamento do save."""

from __future__ import annotations

import os

from game import save_system, shop
from game.config import EstadoJogo
from game.core import Jogo
from game.enemies import Inimigo
from game.powerups import PowerUp
from game.weapons import Projetil


def _isolar_persistencia(monkeypatch, pasta) -> None:
    """Redireciona save, recordes e catalogo para o diretorio do teste."""
    monkeypatch.setattr(save_system, "PASTA_DADOS", str(pasta))
    monkeypatch.setattr(save_system, "ARQUIVO_SAVE", os.path.join(pasta, "save.json"))
    monkeypatch.setattr(
        save_system, "ARQUIVO_RECORDES", os.path.join(pasta, "records.json"))
    monkeypatch.setattr(shop, "PASTA_DADOS", str(pasta))


def test_partida_completa_persiste_progresso_e_reinicia(tmp_path, monkeypatch):
    """Inicia, luta, coleta, enfrenta boss, salva e reinicia a partida."""
    _isolar_persistencia(monkeypatch, tmp_path)
    jogo = Jogo()
    jogo._novo_jogo("Integracao")
    jogo.estado = EstadoJogo.JOGANDO

    # Derrota real por projetil: a colisao passa pelo ControladorCombate.
    inimigo = Inimigo("scout", 1, x=450, y=200)
    jogo.inimigos = [inimigo]
    jogo.projeteis = [Projetil(450, 200, 0, 0, 1, (255, 255, 255), 4)]
    jogo._atualizar_projeteis()
    assert jogo.inimigos == []
    assert jogo.inimigos_abates == 1

    # Coleta real: o item cruza a hitbox do jogador e aplica o efeito.
    jogo.powerups = [PowerUp("moedas", jogo.jogador.x, jogo.jogador.y)]
    jogo._atualizar_powerups()
    assert jogo.powerups == []
    assert jogo.jogador.moedas_jogo == 100

    # A progressao cria ondas nos niveis intermediarios e um boss no nivel 5.
    for nivel in range(2, 6):
        jogo._iniciar_nivel(nivel)
    assert jogo.jogador.nivel == 5
    assert jogo.boss is not None

    # Derrota do boss pela mesma rota de colisao usada durante a partida.
    jogo.boss.x, jogo.boss.y = 450, 200
    jogo.boss.vida = 1
    jogo.projeteis = [Projetil(450, 200, 0, 0, 999, (255, 255, 255), 4)]
    jogo._atualizar_projeteis()
    assert jogo.boss is None
    assert jogo.bosses_abates == 1

    # Fim de jogo persiste pontuacao, moedas e boss; nova instancia le o save.
    jogo._fim_de_jogo()
    assert os.path.exists(save_system.ARQUIVO_SAVE)
    reiniciado = Jogo()
    assert reiniciado.progresso.jogador["bosses_derrotados"] == 1
    assert reiniciado.loja.moedas == jogo.moedas_ganhas

    reiniciado._novo_jogo("Integracao")
    assert reiniciado.estado is EstadoJogo.JOGANDO
    assert reiniciado.jogador.nivel == 1
    assert reiniciado.loja.moedas == jogo.moedas_ganhas
