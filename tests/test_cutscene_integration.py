"""Cenas não mudam recompensas e controlam a retomada do cenário."""

from unittest.mock import Mock

from src.core.event_bus import GameEventType, publicar_evento
from src.runtime.application.core import Jogo
from src.runtime.domain.world.scroll import EstadoAvanco
from src.runtime.infrastructure.persistence import save_system


def _jogo(tmp_path, monkeypatch):
    monkeypatch.setattr(save_system, "ARQUIVO_SAVE", str(tmp_path / "save.json"))
    monkeypatch.setattr(save_system, "ARQUIVO_RECORDES", str(tmp_path / "records.json"))
    jogo = Jogo(sons=Mock())
    jogo.estado = "JOGANDO"
    return jogo


def test_postboss_espera_cena_pulada_antes_de_acelerar(tmp_path, monkeypatch):
    jogo = _jogo(tmp_path, monkeypatch)
    jogo.progressao_controller.iniciar_nivel(5)
    jogo.avanco_controller.modelo.atualizar(2)
    jogo.cutscene_controller.pular_direto()
    boss = jogo.boss
    jogo.combate_controller.derrotar_boss()
    assert boss is not None and jogo.boss is None
    assert jogo.avanco_controller.modelo.estado is EstadoAvanco.PARADO
    assert jogo.cutscene_controller.ativo
    while jogo.cutscene_controller.ativo:
        jogo.cutscene_controller.pular_direto()
    assert jogo.avanco_controller.modelo.estado is EstadoAvanco.ACELERANDO
    assert jogo.progresso.cenas_vistas


def test_pausa_durante_cena_congela_texto_e_scroll(tmp_path, monkeypatch):
    jogo = _jogo(tmp_path, monkeypatch)
    jogo.progressao_controller.iniciar_nivel(5)
    cena = jogo.cutscene_controller.sequenciador
    antes = (cena.indice, cena.tempo, jogo.avanco_controller.modelo.velocidade)
    jogo.cutscene_controller.pausar()
    jogo.cutscene_controller.atualizar(1.0)
    assert (cena.indice, cena.tempo, jogo.avanco_controller.modelo.velocidade) == antes
    jogo.cutscene_controller.pausar()
    jogo.cutscene_controller.atualizar(1 / 60)
    assert jogo.avanco_controller.modelo.velocidade < antes[2]


def test_sem_cena_posboss_acelera_normalmente(tmp_path, monkeypatch):
    jogo = _jogo(tmp_path, monkeypatch)
    jogo.cutscene_controller.catalogo.cenas.pop("cap1_pos_boss")
    publicar_evento(GameEventType.BOSS_SPAWNED, sessao=jogo, cenario_id=1)
    publicar_evento(GameEventType.BOSS_DEFEATED, sessao=jogo, cenario_id=1)
    assert jogo.avanco_controller.modelo.estado is EstadoAvanco.ACELERANDO


def test_fechar_no_meio_nao_grava_cena(tmp_path, monkeypatch):
    jogo = _jogo(tmp_path, monkeypatch)
    jogo.cutscene_controller.iniciar_gatilho("inicio")
    jogo._salvar_tudo()
    assert "introducao" not in save_system.SistemaProgressao().cenas_vistas


def test_intro_e_replay_do_arquivo_sem_duplicar_flags(tmp_path, monkeypatch):
    import pygame

    jogo = _jogo(tmp_path, monkeypatch)
    jogo.cutscene_controller.iniciar_gatilho("inicio")
    assert jogo.estado.value == "CUTSCENE"
    jogo.render_controller.desenhar()
    jogo.cutscene_controller.pular_direto()
    assert jogo.progresso.cenas_vistas == ["introducao"]
    jogo.estado = "MENU"
    jogo.menu._abrir_arquivo()
    assert "introducao" in jogo.menu.telas["ARQUIVO"]._ids()
    assert jogo.cutscene_controller.rever("introducao")
    jogo.cutscene_controller.tratar_evento(
        pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_BACKSPACE}))
    assert not jogo.cutscene_controller.ativo
    assert jogo.estado.value == "MENU"
    assert jogo.progresso.cenas_vistas == ["introducao"]


def test_segurar_pulo_abre_confirmacao_e_so_entao_marca(tmp_path, monkeypatch):
    import pygame

    jogo = _jogo(tmp_path, monkeypatch)
    jogo.cutscene_controller.iniciar_gatilho("inicio")
    jogo.cutscene_controller.tratar_evento(
        pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_BACKSPACE}))
    jogo.cutscene_controller.atualizar(0.7)
    assert jogo.cutscene_controller.confirmacao_pulo
    assert jogo.progresso.cenas_vistas == []
    jogo.cutscene_controller.tratar_evento(
        pygame.event.Event(pygame.KEYDOWN, {"key": jogo.controles["atirar"]}))
    assert jogo.progresso.cenas_vistas == ["introducao"]


def test_f3_f8_dispara_cena_por_id_sem_desbloqueio(tmp_path, monkeypatch):
    import pygame

    jogo = _jogo(tmp_path, monkeypatch)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F3}))
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F8}))
    jogo.loop_controller.tratar_eventos()
    assert jogo.debug_ativo
    assert jogo.cutscene_controller.seletor_debug
    assert jogo.estado.value == "CUTSCENE"
    jogo.cutscene_controller.tratar_evento(
        pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
    assert jogo.cutscene_controller.ativo
    assert jogo.cutscene_controller.sequenciador.cena.id == "introducao"


def test_apos_encerramento_boss_continua_progressao(tmp_path, monkeypatch):
    jogo = _jogo(tmp_path, monkeypatch)
    jogo.progressao_controller.iniciar_nivel(5)
    jogo.cutscene_controller.pular_direto()
    jogo.combate_controller.derrotar_boss()
    while jogo.cutscene_controller.ativo:
        jogo.cutscene_controller.pular_direto()
    assert jogo.estado.value == "JOGANDO"
    jogo.fila_onda.clear()
    jogo.inimigos.clear()
    jogo.miniboss_controller.cancelar()
    jogo._atualizar_jogando()
    assert jogo.estado.value == "MELHORIA"


def test_miniboss_reproduz_somente_primeiro_encontro_do_tipo(tmp_path, monkeypatch):
    from src.runtime.domain.story import Cena

    jogo = _jogo(tmp_path, monkeypatch)
    cena = Cena("mini_eco", "miniboss:eco", ({"tipo": "fala", "personagem": "eco",
                                             "texto": "Registro."},))
    jogo.cutscene_controller.catalogo.cenas[cena.id] = cena
    publicar_evento(GameEventType.MINIBOSS_SPAWNED, sessao=jogo, chave="eco")
    assert jogo.cutscene_controller.sequenciador.cena.id == "mini_eco"
    jogo.cutscene_controller.pular_direto()
    publicar_evento(GameEventType.MINIBOSS_SPAWNED, sessao=jogo, chave="eco")
    assert not jogo.cutscene_controller.ativo


def test_botao_pular_exige_clique_de_confirmacao(tmp_path, monkeypatch):
    import pygame

    jogo = _jogo(tmp_path, monkeypatch)
    jogo.cutscene_controller.iniciar_gatilho("inicio")

    def clique(x, y):
        escala, off_x, off_y = jogo._transformacao_janela()
        jogo.cutscene_controller.tratar_evento(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1,
                                     "pos": (int(x * escala + off_x),
                                             int(y * escala + off_y))}))

    clique(1100, 40)
    assert jogo.cutscene_controller.confirmacao_pulo
    assert jogo.progresso.cenas_vistas == []
    clique(760, 375)
    assert jogo.cutscene_controller.ativo
    clique(1100, 40)
    clique(480, 375)
    assert jogo.progresso.cenas_vistas == ["introducao"]
