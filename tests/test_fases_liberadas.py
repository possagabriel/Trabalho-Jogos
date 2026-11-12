"""Fases conquistadas permanecem acessíveis no lobby e em novas campanhas."""

from unittest.mock import Mock

from game.phase_select import PhaseStatus, get_phase_status
from src.runtime.application.core import Jogo
from src.runtime.domain.campaign_catalog import fases_liberadas


def test_catalogo_recupera_fases_de_saves_antigos_sem_mutar_dados():
    dados = {'nivel_maximo': 13, 'progresso_campanha': {'fases_concluidas': [1]}}
    assert fases_liberadas(dados) == (1, 2, 3)
    assert 'fases_liberadas' not in dados
    assert fases_liberadas({'progresso_campanha': {'fases_concluidas': ['descarte']}}) == (
        1, 2, 3, 4, 5, 6)


def test_linear_abre_lobby_com_fases_conquistadas(tmp_path, monkeypatch):
    monkeypatch.setenv('INCARNATE_DATA_DIR', str(tmp_path))
    jogo = Jogo(sons=Mock())
    perfil = jogo.profile_service.create('Piloto')
    jogo.ativar_perfil(perfil.id)
    jogo.progresso.registrar_fase_concluida(5)
    jogo.progresso.registrar_fase_concluida(10)
    jogo.progresso.salvar_arquivo()
    assert jogo.menu.mode_strategies['linear'].start_new(jogo)
    tela = jogo.menu.phase_screen
    assert not tela.nova_campanha_pendente
    assert tela.statuses['lealdade'] is PhaseStatus.COMPLETED
    assert tela.statuses['funcao'] is PhaseStatus.COMPLETED
    assert tela.statuses['identidade'] is PhaseStatus.AVAILABLE
    assert tela.statuses['silencio'] is PhaseStatus.LOCKED
    jogo.menu._novo_jogo_direto()
    assert tela.statuses['identidade'] is PhaseStatus.AVAILABLE
    jogo.menu._voltar_menu()
    jogo.progresso.resetar_fases()
    tela.refresh()
    for fase in tela.phases[:3]:
        assert get_phase_status(fase.id, jogo.progresso.jogador,
                                tela.phases) is PhaseStatus.AVAILABLE
    reiniciado = Jogo(sons=Mock())
    reiniciado.ativar_perfil(perfil.id)
    reiniciado.menu._abrir_lobby()
    assert reiniciado.menu.phase_screen.statuses['identidade'] is PhaseStatus.AVAILABLE
