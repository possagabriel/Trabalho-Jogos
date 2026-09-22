"""Contratos dos encontros aleatórios e de suas mecânicas, sem janela."""

import json
import random
from collections import Counter
from types import SimpleNamespace

import pygame
import pytest

from src.core.constants import ALTURA, CIANO, LARGURA
from src.runtime.domain.entities.minibosses import criar_miniboss
from src.runtime.domain.entities.minibosses.config import CATALOGO
from src.runtime.domain.entities.minibosses.states import Recuperacao
from src.runtime.domain.entities.player import Jogador
from src.runtime.domain.entities.weapons import Projetil
from src.runtime.domain.systems.miniboss_spawner import MinibossSpawner
from src.runtime.infrastructure.persistence import save_system


def criar(chave: str):
    """Cria um alvo já posicionado na arena."""
    alvo = criar_miniboss(chave, 1, SimpleNamespace(id=1), random.Random(4))
    alvo.entrando = False
    alvo.y = alvo.alvo_y
    return alvo


def tiro(x: float, y: float, dano: int = 10, tipo: str = "padrao"):
    """Cria um disparo real do runtime."""
    return Projetil(x, y, 0, -6, dano, CIANO, 5, tipo=tipo)


def test_seed_pesos_e_nao_repeticao() -> None:
    pesos = {chave: 1 for chave in CATALOGO}
    pesos["bastiao"] = 20

    def sequencia(seed):
        spawner = MinibossSpawner(seed=seed, pesos=pesos)
        return [spawner.sortear(1) for _ in range(4000)]

    a = sequencia(43)
    assert a == sequencia(43)
    assert a != sequencia(44)
    assert all(x != y for x, y in zip(a, a[1:]))
    contagens = Counter(a)
    assert contagens["bastiao"] > 2 * contagens["matriz"]


def test_filtro_peso_zero_e_unico_elegivel_adiam_repeticao() -> None:
    spawner = MinibossSpawner(pesos={chave: int(chave == "espectro") for chave in CATALOGO})
    assert spawner.sortear(1) is None
    assert spawner.sortear(5) == "espectro"
    assert spawner.sortear(5) is None
    assert MinibossSpawner(pesos=dict.fromkeys(CATALOGO, 0)).sortear(1) is None


def test_tempo_um_vivo_bloqueio_e_intervalo_apos_derrota() -> None:
    s = MinibossSpawner(modo="segundos", intervalo=2, seed=2)
    c = SimpleNamespace(id=1)
    assert s.atualizar(10, 1, c, bloqueado=True) is None
    assert s.atualizar(1, 1, c) is None
    primeiro = s.atualizar(1, 1, c)
    assert primeiro is not None
    assert s.atualizar(100, 1, c) is None
    assert s.ativo is primeiro
    s.liberar()
    assert s.atualizar(1, 1, c) is None
    segundo = s.atualizar(1, 1, c)
    assert segundo is not None and segundo.chave != primeiro.chave


def test_ondas_nao_contam_frames_e_boss_adia_spawn() -> None:
    s = MinibossSpawner(modo="ondas", intervalo=3, seed=1)
    c = SimpleNamespace(id=1)
    for _ in range(100):
        assert s.atualizar(1, 1, c, onda=2) is None
    assert s.atualizar(1, 5, c, onda=3, bloqueado=True) is None
    assert s.atualizar(0, 6, c, onda=3) is not None
    s.liberar()
    assert s.atualizar(0, 6, c, onda=3) is None
    assert s.atualizar(0, 9, c, onda=6) is not None


@pytest.mark.parametrize("kwargs", [
    {"intervalo": 0}, {"intervalo": float("nan")}, {"modo": "invalido"},
    {"modo": "ondas", "intervalo": 1.5}, {"pesos": {"bastiao": -1}},
    {"pesos": {"bastiao": float("inf")}}, {"pesos": {"inexistente": 1}},
])
def test_configuracoes_invalidas(kwargs) -> None:
    with pytest.raises(ValueError):
        MinibossSpawner(**kwargs)


def test_bastiao_so_perde_escudo_pelos_dois_nucleos() -> None:
    b = criar("bastiao")
    vida = b.vida
    b.receber_tiro(tiro(b.x, b.y, 10000))
    b.receber_area(10000, b.x, b.y, 150)
    assert b.vida == vida
    for rect in b.estrategia.pontos_fracos(b):
        b.receber_tiro(tiro(*rect.center, dano=100))
    b.receber_tiro(tiro(b.x, b.y))
    assert b.vida == vida - 10


def test_espectro_avisa_teleporta_atras_e_retorna_ao_alcance() -> None:
    b, j = criar("espectro"), Jogador()
    j.x, j.y = LARGURA / 2, ALTURA / 2
    tiros = b.atualizar(j, b.cfg["aviso"])
    assert b.y > j.y
    assert tiros and all(p.vel_y < 0 for p in tiros)
    assert b.estrategia.destino is not None
    b.atualizar(j, b.cfg["ativo"])
    assert b.y == b.alvo_y
    assert isinstance(b.estado, Recuperacao)


def test_matriz_invoca_lacaios_limitados_e_expoe_nucleo() -> None:
    b, j = criar("matriz"), Jogador()
    b.atualizar(j, b.cfg["aviso"])
    assert len(b.lacaios) == b.cfg["limite_lacaios"]
    assert all(i.y >= b.y for i in b.lacaios)
    for _ in range(4):
        b.estrategia.ativar(b, j)
    assert len(b.lacaios) == b.cfg["limite_lacaios"]
    b.lacaios.clear()
    b.estrategia.ativar(b, j)
    assert len(b.lacaios) == b.cfg["limite_lacaios"]


def test_censor_inverte_vetor_sem_alterar_configuracao_e_expira() -> None:
    b, j = criar("censor"), Jogador()
    b.atualizar(j, b.cfg["aviso"])
    assert b.inverte_controles
    controles = {"esquerda": pygame.K_j}
    teclas = {k: False for k in (
        pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
        pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_x, pygame.K_j,
    )}
    teclas[pygame.K_j] = True
    x = j.x
    j.atualizar(teclas, controles, inverter_movimento=b.inverte_controles)
    assert j.x > x and controles == {"esquerda": pygame.K_j}
    b.atualizar(j, b.cfg["ativo"])
    assert not b.inverte_controles


def test_cartografo_zonas_avisadas_depois_danificam_e_expiram() -> None:
    b, j = criar("cartografo"), Jogador()
    b.atualizar(j, 0.1)
    assert b.zonas and not b.perigo(j.rect)
    posicao = b.zonas[0].center
    j.x += 160
    b.atualizar(j, b.cfg["aviso"] - 0.1)
    assert b.zonas[0].center == posicao
    assert b.perigo(pygame.Rect(posicao[0], posicao[1], 1, 1))
    b.atualizar(j, b.cfg["ativo"])
    assert not b.perigo(pygame.Rect(posicao[0], posicao[1], 1, 1))


def test_eco_copia_ultimo_disparo_real_sem_mutar_nem_criar_laser_instantaneo() -> None:
    b, j = criar("eco"), Jogador()
    p = tiro(j.x, j.y, 9, "plasma")
    b.observar_tiros([p])
    j.arma_atual = 0
    copia = b.atualizar(j, b.cfg["aviso"])[0]
    assert copia.tipo == "plasma" and copia.origem == "inimigo"
    assert copia.vel_y > 0 and p.vel_y < 0 and p.origem == "jogador"
    b.observar_tiros([tiro(j.x, j.y, 5, "ion")])
    b.estrategia.ativar(b, j)
    copia = b.drenar_projeteis()[0]
    assert copia.tipo == "padrao" and copia.rect.height < ALTURA


def test_cronista_alterna_invulneravel_e_vulneravel() -> None:
    b, j = criar("cronista"), Jogador()
    vida = b.vida
    b.sofrer_dano(20)
    assert b.vida == vida
    b.atualizar(j, b.cfg["aviso"] + b.cfg["ativo"])
    assert isinstance(b.estado, Recuperacao)
    b.sofrer_dano(20)
    assert b.vida == vida - 20
    b.atualizar(j, b.cfg["recuperacao"])
    b.sofrer_dano(20)
    assert b.vida == vida - 20


def test_estado_consistente_com_dt_dividido() -> None:
    a, b, j = criar("cronista"), criar("cronista"), Jogador()
    a.atualizar(j, 7)
    for _ in range(70):
        b.atualizar(j, 0.1)
    assert type(a.estado) is type(b.estado)
    assert a.estado.restante == pytest.approx(b.estado.restante)


def test_save_antigo_recebe_contagens_sem_perder_campos(tmp_path, monkeypatch) -> None:
    arquivo = tmp_path / "save.json"
    arquivo.write_text(json.dumps({"versao": 2, "jogador": {
        "nome": "IA", "moedas": 75, "campo_futuro": 123,
    }}))
    monkeypatch.setattr(save_system, "ARQUIVO_SAVE", str(arquivo))
    monkeypatch.setattr(save_system, "PASTA_DADOS", str(tmp_path))
    p = save_system.SistemaProgressao()
    assert p.jogador["minibosses_derrotados"] == 0
    p.registrar_miniboss("eco")
    p.salvar_arquivo()
    p = save_system.SistemaProgressao()
    assert p.jogador["moedas"] == 75 and p.jogador["campo_futuro"] == 123
    assert p.jogador["minibosses_derrotados"] == 1
    assert p.dados["estatisticas"]["minibosses_por_tipo"] == {"eco": 1}
    assert p.jogador["bosses_derrotados"] == 0
