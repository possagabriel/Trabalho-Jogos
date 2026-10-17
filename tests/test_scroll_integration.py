"""Integração visual e eventos sem mudar combate, recompensas ou hitboxes."""

import random
from unittest.mock import Mock

import pygame
import pytest

from src.core.constants import ALTURA, LARGURA
from src.core.event_bus import EventBus, GameEventType, publicar_evento
from src.core.settings import Configuracoes
from src.infrastructure.graphics.comic_theme import usar_visual
from src.runtime.application.core import Jogo
from src.runtime.domain.entities.bosses import Boss
from src.runtime.domain.world.scenarios import Cenario
from src.runtime.domain.world.scroll import EstadoAvanco
from src.runtime.infrastructure.graphics.parallax import (
    ParallaxBackground, ScrollingLayer, SpeedLines, _espelhar,
)
from src.runtime.infrastructure.persistence import save_system


def test_tile_espelhado_fecha_bordas_e_rola_sem_lacunas() -> None:
    base = pygame.Surface((4, 3))
    for y in range(3):
        for x in range(4):
            base.set_at((x, y), (x * 40, y * 60, 10))
    tile = _espelhar(base)
    assert all(tile.get_at((0, y)) == tile.get_at((7, y)) for y in range(6))
    assert all(tile.get_at((x, 0)) == tile.get_at((x, 5)) for x in range(8))
    camada = ScrollingLayer(tile, 1)
    tela = pygame.Surface((4, 3))
    for deslocamento in (0, 1, 5, 6, 17):
        camada.y = deslocamento
        camada.desenhar(tela)
        assert tela.get_at((0, 0)).a == 255


def test_linhas_preparadas_crescem_com_a_velocidade_sem_corte() -> None:
    linhas = SpeedLines(12, (180, 210, 255), (0, 1), 42)
    curta = linhas._sprites[2, 1]
    longa = linhas._sprites[2, 4]
    assert longa.get_height() > curta.get_height()
    pontos = pygame.mask.from_surface(longa).get_bounding_rects()
    assert max(rect.bottom for rect in pontos) - min(rect.top for rect in pontos) > 30


@pytest.mark.parametrize("qualidade,esperado", [("BAIXA", 3), ("MEDIA", 4), ("ALTA", 5)])
def test_camadas_por_qualidade_e_pool_limitado(qualidade: str, esperado: int) -> None:
    cenario = Cenario(1)
    fundo = ParallaxBackground(cenario, qualidade, (0, 1))
    assert fundo.numero_camadas == esperado
    fundo.atualizar(120, 120, 1 / 60, None, 0.015, 1)
    assert 0 < fundo.particulas_ativas <= fundo._limite
    fundo.atualizar(0, 120, 1 / 60, None, 0.015, 1)
    assert fundo.particulas_ativas == 0


def test_boss_publica_eventos_sem_alterar_vida_ataques_e_recompensas(
    tmp_path, monkeypatch,
) -> None:
    monkeypatch.setattr(save_system, "ARQUIVO_SAVE", str(tmp_path / "save.json"))
    monkeypatch.setattr(save_system, "ARQUIVO_RECORDES", str(tmp_path / "records.json"))
    monkeypatch.setattr(save_system, "PASTA_DADOS", str(tmp_path))
    jogo = Jogo(sons=Mock())
    jogo.estado = "JOGANDO"
    eventos = []

    def receber(evento):
        eventos.append(evento)

    bus = EventBus()
    bus.subscribe(GameEventType.BOSS_SPAWNED, receber)
    bus.subscribe(GameEventType.BOSS_DEFEATED, receber)
    try:
        jogo.progressao_controller.iniciar_nivel(5)
        boss = jogo.boss
        assert boss is not None
        assert len(eventos) == 1
        assert jogo.avanco_controller.modelo.estado is EstadoAvanco.FREANDO
        assert eventos[0].data["boss"] is boss
        referencia = Boss(5, jogo.cenario)
        assert (boss.vida, boss.ataques, boss.pontos) == (
            referencia.vida, referencia.ataques, referencia.pontos)
        boss.entrando = referencia.entrando = False
        boss.y = referencia.y = boss.alvo_y
        boss.timer_ataque = referencia.timer_ataque = 1
        estado_aleatorio = random.getstate()
        try:
            random.seed(777)
            tiros = boss.atualizar(jogo.jogador)
            random.seed(777)
            tiros_referencia = referencia.atualizar(jogo.jogador)
        finally:
            random.setstate(estado_aleatorio)
        assert [(t.vel_x, t.vel_y) for t in tiros] == [
            (t.vel_x, t.vel_y) for t in tiros_referencia]
        vida_antes = jogo.jogador.pontuacao
        drops_antes = len(jogo.powerups)
        jogo.combate_controller.derrotar_boss()
        assert [e.type for e in eventos] == [
            GameEventType.BOSS_SPAWNED, GameEventType.BOSS_DEFEATED]
        assert eventos[-1].data["boss"] is boss
        assert jogo.boss is None
        assert jogo.avanco_controller.modelo.estado is EstadoAvanco.ACELERANDO
        assert jogo.jogador.pontuacao == vida_antes + int(
            boss.pontos * jogo.jogador.combo.get_bonus())
        assert len(jogo.powerups) == drops_antes + 3
        assert jogo.bosses_abates == 1
    finally:
        bus.unsubscribe(GameEventType.BOSS_SPAWNED, receber)
        bus.unsubscribe(GameEventType.BOSS_DEFEATED, receber)


def test_cenario_rolando_nao_muda_posicao_da_nave() -> None:
    jogo = Jogo(sons=Mock())
    jogo.estado = "JOGANDO"
    posicao = jogo.jogador.rect.copy()
    jogo.jogador.atualizar_mira((jogo.jogador.x + 150, jogo.jogador.y))
    for _ in range(30):
        jogo.avanco_controller.atualizar(jogo.cenario, 1 / 60)
    assert jogo.jogador.rect == posicao
    assert jogo.avanco_controller.direcao == (0, 1)
    tela = pygame.Surface((LARGURA, ALTURA))
    jogo.cenario.desenhar(tela)


def test_seis_dimensoes_rolam_nos_dois_estilos() -> None:
    config = Configuracoes()
    tela = pygame.Surface((LARGURA, ALTURA))
    for cenario_id in range(1, 7):
        cenario = Cenario(cenario_id)
        cenario.configurar_avanco("MEDIA", (0, 1), True)
        for estilo in ("ORIGINAL", "COMIC"):
            config["estilo_visual"] = estilo
            with usar_visual(config):
                cenario.parallax.atualizar(120, 120, 1 / 60, None, 0.015, 1)
                cenario.desenhar(tela)
                assert tela.get_size() == (LARGURA, ALTURA)


def test_miniboss_usa_percentual_por_tipo_e_pausa_congela_avanco() -> None:
    jogo = Jogo(sons=Mock())
    jogo.config["avanco_miniboss_tipos"] = {"eco": 0.25}
    publicar_evento(GameEventType.MINIBOSS_SPAWNED, sessao=jogo, chave="eco")
    jogo.avanco_controller.modelo.atualizar(1.5)
    assert jogo.avanco_controller.modelo.velocidade == pytest.approx(30)
    jogo.estado = "PAUSA"
    jogo.loop_controller.atualizar()
    assert jogo.avanco_controller.modelo.velocidade == pytest.approx(30)
    publicar_evento(GameEventType.MINIBOSS_DEFEATED, sessao=jogo, chave="eco")
    jogo.avanco_controller.modelo.atualizar(1.2)
    assert jogo.avanco_controller.modelo.velocidade >= 120
