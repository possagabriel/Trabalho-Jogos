"""Integração real de minibosses com colisão, progressão, desenho e save."""

from types import SimpleNamespace
from unittest.mock import Mock

import pygame
import pytest

from src.core.constants import CIANO, EstadoJogo
from src.runtime.application.core import Jogo
from src.runtime.domain.entities.minibosses import criar_miniboss
from src.runtime.domain.entities.minibosses.config import CATALOGO
from src.runtime.domain.entities.minibosses.states import Ataque
from src.runtime.domain.entities.weapons import Projetil
from src.runtime.domain.systems.miniboss_spawner import MinibossSpawner
from src.runtime.infrastructure.persistence import save_system


@pytest.fixture
def jogo(tmp_path, monkeypatch):
    """Sessão com save isolado e efeitos sonoros substituídos."""
    monkeypatch.setattr(save_system, "ARQUIVO_SAVE", str(tmp_path / "save.json"))
    monkeypatch.setattr(save_system, "ARQUIVO_RECORDES", str(tmp_path / "records.json"))
    monkeypatch.setattr(save_system, "PASTA_DADOS", str(tmp_path))
    j = Jogo(sons=Mock())
    j.estado = EstadoJogo.JOGANDO
    j.inimigos, j.fila_onda, j.projeteis = [], [], []
    return j


def colocar(jogo, chave="eco"):
    """Insere um miniboss pela mesma referência compartilhada com o spawner."""
    b = criar_miniboss(chave, 1, SimpleNamespace(id=1))
    b.x, b.y, b.entrando = 500, 180, False
    jogo.miniboss = jogo.miniboss_spawner.ativo = b
    return b


def test_derrota_por_colisao_recompensa_uma_vez_e_persiste(jogo) -> None:
    b = colocar(jogo)
    b.vida = 1
    moedas = jogo.loja.moedas
    proj = Projetil(b.x, b.y, 0, 0, 10, CIANO, 5)
    assert jogo.combate_controller.projetil_jogador_atinge(proj)
    jogo.miniboss_controller.derrotar()
    assert jogo.miniboss is None and jogo.miniboss_spawner.ativo is None
    assert jogo.jogador.pontuacao == b.pontos
    assert jogo.loja.moedas == moedas + b.cfg["moedas"]
    assert jogo.jogador.moedas_jogo == 0  # recompensa imediata não duplica no game over
    assert len(jogo.powerups) == 1
    salvo = save_system.SistemaProgressao()
    assert salvo.jogador["minibosses_derrotados"] == 1
    assert salvo.jogador["moedas"] == jogo.loja.moedas
    assert salvo.jogador["bosses_derrotados"] == 0
    assert salvo.campanha["fases_concluidas"] == []


@pytest.mark.parametrize("tipo", ["padrao", "plasma", "ion", "gauss", "nova", "bomba"])
def test_armas_atingem_miniboss_no_controlador_real(jogo, tipo) -> None:
    b = colocar(jogo)
    antes = b.vida
    p = Projetil(b.x, b.y, 0, 0, 2, CIANO, 5, tipo=tipo)
    assert jogo.combate_controller.projetil_jogador_atinge(p)
    assert b.vida < antes


def test_bomba_respeita_escudo_e_pontos_fracos_fora_do_casco(jogo) -> None:
    b = colocar(jogo, "bastiao")
    antes = b.vida
    p = Projetil(b.x, b.y, 0, 0, 100, CIANO, 5, tipo="bomba")
    jogo.combate_controller.projetil_jogador_atinge(p)
    assert b.vida == antes
    for rect in b.estrategia.pontos_fracos(b):
        assert jogo.combate_controller.projetil_jogador_atinge(
            Projetil(*rect.center, 0, 0, 100, CIANO, 5))
    assert not b.estrategia.pontos_fracos(b)


def test_miniboss_impede_avanco_e_novo_jogo_limpa_efeitos(jogo) -> None:
    b = colocar(jogo, "censor")
    b.estado = Ataque(2)
    jogo._atualizar_jogando()
    assert jogo.estado == EstadoJogo.JOGANDO
    assert jogo.miniboss.inverte_controles
    jogo._novo_jogo("IA")
    assert jogo.miniboss is None and jogo.miniboss_spawner.ativo is None


def test_spawn_ocorre_na_terceira_onda_e_boss_regular_tem_prioridade(jogo) -> None:
    jogo.miniboss_spawner = MinibossSpawner(modo="ondas", intervalo=3, seed=10)
    jogo._iniciar_nivel(2)
    jogo._atualizar_jogando()
    assert jogo.miniboss is None
    jogo._iniciar_nivel(3)
    jogo._atualizar_jogando()
    assert jogo.miniboss is not None
    jogo._iniciar_nivel(5)
    assert jogo.miniboss is None and jogo.boss is not None
    jogo._atualizar_jogando()
    assert jogo.miniboss is None


def test_pausa_e_equipamento_congelam_temporizador(jogo) -> None:
    jogo.miniboss_spawner = MinibossSpawner(modo="segundos", intervalo=2)
    jogo.estado = EstadoJogo.PAUSA
    jogo.loop_controller.atualizar()
    assert jogo.miniboss_spawner.tempo == 0
    jogo.estado = EstadoJogo.JOGANDO
    jogo.menu_equipamento = True
    jogo._atualizar_jogando()
    assert jogo.miniboss_spawner.tempo == 0


def test_game_over_remove_inversao_e_zonas(jogo) -> None:
    colocar(jogo, "censor").estado = Ataque(2)
    jogo._fim_de_jogo()
    assert jogo.miniboss is None
    assert jogo.miniboss_spawner.ativo is None


def test_zona_ativa_usa_invencibilidade_existente(jogo) -> None:
    b = colocar(jogo, "cartografo")
    jogo.miniboss_controller.atualizar(0)
    vida = jogo.jogador.vida
    jogo.miniboss_controller.colidir_jogador()
    assert jogo.jogador.vida == vida
    jogo.miniboss_controller.atualizar(b.cfg["aviso"])
    jogo.miniboss_controller.colidir_jogador()
    jogo.miniboss_controller.colidir_jogador()
    assert jogo.jogador.vida == vida - 1


def test_lacaios_entram_na_colisao_e_sao_limpos_ao_derrotar(jogo) -> None:
    b = colocar(jogo, "matriz")
    jogo.miniboss_controller.atualizar(b.cfg["aviso"])
    assert len(jogo.inimigos) == 3
    lacaio = jogo.inimigos[0]
    jogo.combate_controller.explodir_inimigo(lacaio)
    jogo.miniboss_controller.atualizar(0)
    assert len(b.lacaios) == 2
    b.vida = 0
    jogo.miniboss_controller.derrotar()
    assert not jogo.inimigos


@pytest.mark.parametrize("chave", CATALOGO)
def test_todos_os_protocolos_desenham_aviso_ataque_recuperacao(jogo, chave) -> None:
    b = colocar(jogo, chave)
    for dt in (0, b.cfg["aviso"], b.cfg["ativo"]):
        b.atualizar(jogo.jogador, dt)
        b.desenhar(jogo.tela)
    assert pygame.display.get_init()


@pytest.mark.parametrize("tipo", ["bomba", "nova", "gauss", "padrao"])
def test_derrota_da_matriz_remove_lacaios_da_grade_no_mesmo_lote(jogo, tipo) -> None:
    """Tiros posteriores não atingem escoltas removidas durante o mesmo quadro."""
    b = colocar(jogo, "matriz")
    jogo.miniboss_controller.atualizar(b.cfg["aviso"])
    lacaios = list(jogo.inimigos)
    b.vida = 1
    jogo.projeteis = [Projetil(b.x, b.y, 0, 0, 100, CIANO, 5, tipo=tipo)]
    jogo.projeteis.extend(
        Projetil(lacaio.x, lacaio.y, 0, 0, 100, CIANO, 5) for lacaio in lacaios
    )

    jogo.combate_controller.atualizar_projeteis()

    assert jogo.miniboss is None
    assert not jogo.inimigos
    assert jogo.inimigos_abates == 0
    assert jogo.progresso.jogador["minibosses_derrotados"] == 1
    assert jogo.jogador.pontuacao == b.pontos
