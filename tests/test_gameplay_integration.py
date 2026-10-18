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
    monkeypatch.setenv("INCARNATE_DATA_DIR", str(tmp_path))
    jogo = Jogo()
    perfil = jogo.profile_service.create("Integracao")
    jogo.ativar_perfil(perfil.id)
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
    assert jogo.loja.moedas == 100
    assert jogo.profile_service.repository.load(perfil.id).progress["moedas"] == 100

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
    assert jogo.profile_service.repository.profile_path(perfil.id).exists()
    assert not os.path.exists(save_system.ARQUIVO_SAVE)
    reiniciado = Jogo()
    reiniciado.ativar_perfil(perfil.id)
    assert reiniciado.progresso.jogador["bosses_derrotados"] == 1
    assert reiniciado.loja.moedas == jogo.moedas_ganhas

    reiniciado._novo_jogo("Integracao")
    assert reiniciado.estado is EstadoJogo.JOGANDO
    assert reiniciado.jogador.nivel == 1
    assert reiniciado.loja.moedas == jogo.moedas_ganhas
