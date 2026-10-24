"""Contrato do catálogo, sequenciador e persistência narrativa."""

import json
import logging
from collections import deque
from importlib.resources import files
from types import SimpleNamespace

import pytest

from src.runtime.domain.story import SequenciadorCena, carregar_catalogo
from src.runtime.infrastructure.persistence.save_system import SistemaProgressao


def _dados():
    return {
        "personagens": {"jonathan": {"nome": "Jonathan", "retrato": "nave"}},
        "cenas": [{"id": "teste", "gatilho": "inicio", "passos": [
            {"tipo": "fala", "personagem": "jonathan", "texto": "Acordei."},
            {"tipo": "espera", "duracao": 0.5},
            {"tipo": "titulo", "texto": "Capítulo", "duracao": 0.2},
        ]}],
    }


def test_catalogo_e_referencias_invalidas_sao_ignorados(caplog):
    dados = _dados()
    dados["cenas"].append({"id": "ruim", "gatilho": "boss:1", "passos": [
        {"tipo": "fala", "personagem": "ausente", "texto": "Erro"},
    ]})
    with caplog.at_level(logging.WARNING):
        catalogo = carregar_catalogo(dados)
    assert catalogo.cena("teste") is not None
    assert catalogo.cena("ruim") is None
    assert catalogo.por_gatilho("boss:1") is None
    assert "ausente" in caplog.text


def test_json_invalido_nao_derruba(tmp_path, caplog):
    from src.runtime.domain.story import ler_catalogo

    caminho = tmp_path / "cenas.json"
    caminho.write_text("{quebrado", encoding="utf-8")
    with caplog.at_level(logging.WARNING):
        catalogo = ler_catalogo(caminho)
    assert catalogo.cenas == {}
    assert "cenas.json" in caplog.text


def test_sequenciador_revela_texto_e_marca_so_ao_concluir():
    cena = carregar_catalogo(_dados()).cena("teste")
    concluidas = []
    sequenciador = SequenciadorCena(velocidade=4, ao_concluir=concluidas.append)
    sequenciador.iniciar(cena)
    sequenciador.atualizar(0.5)
    assert sequenciador.texto_visivel == "Ac"
    assert concluidas == []
    sequenciador.confirmar()
    assert sequenciador.texto_visivel == "Acordei."
    assert sequenciador.indice == 0
    sequenciador.confirmar()
    assert sequenciador.indice == 1
    sequenciador.atualizar(0.5)
    sequenciador.atualizar(0.2)
    assert concluidas == ["teste"]
    assert not sequenciador.ativo


def test_pular_conclui_mas_interromper_nao_grava():
    cena = carregar_catalogo(_dados()).cena("teste")
    concluidas = []
    sequenciador = SequenciadorCena(ao_concluir=concluidas.append)
    sequenciador.iniciar(cena)
    sequenciador.interromper()
    assert concluidas == []
    sequenciador.iniciar(cena)
    sequenciador.pular()
    assert concluidas == ["teste"]


def test_pausa_congela_passo():
    cena = carregar_catalogo(_dados()).cena("teste")
    sequenciador = SequenciadorCena(velocidade=10)
    sequenciador.iniciar(cena)
    sequenciador.pausado = True
    sequenciador.atualizar(2)
    assert sequenciador.texto_visivel == ""
    sequenciador.pausado = False
    sequenciador.atualizar(0.2)
    assert sequenciador.texto_visivel == "Ac"


def test_save_antigo_recebe_flags_e_so_persiste_cena_concluida(tmp_path, monkeypatch):
    import src.runtime.infrastructure.persistence.save_system as save_mod

    caminho = tmp_path / "save.json"
    caminho.write_text(json.dumps({"jogador": {"nome": "Antigo", "moedas": 9}}),
                       encoding="utf-8")
    monkeypatch.setattr(save_mod, "ARQUIVO_SAVE", str(caminho))
    progresso = SistemaProgressao()
    assert progresso.cenas_vistas == []
    assert progresso.jogador["moedas"] == 9
    progresso.marcar_cena_vista("teste")
    assert SistemaProgressao().cenas_vistas == ["teste"]
    progresso.marcar_cena_vista("teste")
    assert progresso.cenas_vistas == ["teste"]


def test_comandos_entram_uma_vez_e_cena_seguinte_nao_duplica():
    dados = _dados()
    dados["cenas"] = [{"id": "comandos", "gatilho": "teste", "passos": [
        {"tipo": "som", "acao": "boss"},
        {"tipo": "musica", "acao": "parar"},
        {"tipo": "retrato", "personagem": "jonathan", "icone": "glitch"},
        {"tipo": "fade", "duracao": 0.1},
        {"tipo": "glitch", "duracao": 0.1},
        {"tipo": "shake", "duracao": 0.1},
        {"tipo": "fala", "personagem": "jonathan", "texto": "Fim."},
    ]}]
    entradas = []
    cena = carregar_catalogo(dados).cena("comandos")
    seq = SequenciadorCena(ao_entrar=lambda p: entradas.append(p["tipo"]))
    seq.iniciar(cena)
    for _ in range(3):
        seq.atualizar(0.1)
    seq.confirmar()
    seq.confirmar()
    assert entradas == ["som", "musica", "retrato", "fade", "glitch", "shake", "fala"]


def test_capitulos_nao_pronunciam_protocolos_restritos():
    from src.runtime.domain.story import ler_catalogo

    catalogo = ler_catalogo(files("src.runtime.story") / "cenas_pt_BR.json")
    assert {
        "introducao", "cap1_abertura", "cap1_pre_boss", "cap1_pos_boss",
        "cap1_encerramento",
    } <= set(catalogo.cenas)
    nomes = ("LEALDADE", "FUNÇÃO", "IDENTIDADE", "SILÊNCIO", "DESCARTE")
    for cena in catalogo.cenas.values():
        for passo in cena.passos:
            if passo["tipo"] == "fala":
                assert not any(nome in passo["texto"].upper() for nome in nomes)


def test_nova_campanha_preserva_arquivo_de_memorias(tmp_path, monkeypatch):
    import src.runtime.infrastructure.persistence.save_system as save_mod

    monkeypatch.setattr(save_mod, "ARQUIVO_SAVE", str(tmp_path / "save.json"))
    progresso = SistemaProgressao()
    progresso.marcar_cena_vista("introducao")
    progresso.resetar_fases()
    assert progresso.cenas_vistas == ["introducao"]
    assert SistemaProgressao().cenas_vistas == ["introducao"]


def _catalogo_producao():
    dados = json.loads((files("src.runtime.story") / "cenas_pt_BR.json").read_text("utf-8"))
    return dados, carregar_catalogo(dados)


def test_producao_ids_gatilhos_referencias_e_tipos_validos(caplog):
    from src.runtime.domain.story import TIPOS_PASSO

    with caplog.at_level(logging.WARNING):
        dados, catalogo = _catalogo_producao()
    cenas = dados["cenas"]
    assert len(cenas) == len({cena["id"] for cena in cenas}) == len(catalogo.cenas)
    assert len(cenas) == len({cena["gatilho"] for cena in cenas})
    assert not caplog.records
    for cena in cenas:
        assert cena["nome"].strip()
        for passo in cena["passos"]:
            assert passo["tipo"] in TIPOS_PASSO
            if passo["tipo"] in {"fala", "retrato"}:
                assert passo["personagem"] in dados["personagens"]


@pytest.mark.parametrize("capitulo,boss,titulo", [
    (3, "estrela", "IDENTIDADE"), (4, "pentagono", "SILÊNCIO"),
    (5, "aneis", "DESCARTE"), (6, "aneis_dourado", "ORIGEM"),
])
def test_capitulos_aprovados_tem_quatro_cenas_e_boss(capitulo, boss, titulo):
    _, catalogo = _catalogo_producao()
    for sufixo, gatilho in (
        ("abertura", "capitulo_abertura"), ("pre_boss", "boss_entrada"),
        ("pos_boss", "boss_derrota"), ("encerramento", "capitulo_fim"),
    ):
        cena = catalogo.por_gatilho(f"{gatilho}:{capitulo}")
        assert cena is not None
        assert cena.id == f"cap{capitulo}_{sufixo}"
    abertura = catalogo.cena(f"cap{capitulo}_abertura").passos[0]
    assert abertura["tipo"] == "titulo"
    assert abertura["texto"] == f"CAPÍTULO {capitulo} // {titulo}"
    falas = [p for p in catalogo.cena(f"cap{capitulo}_pre_boss").passos
             if p["tipo"] == "fala"]
    assert falas[0]["personagem"] == boss
    assert {p["personagem"] for p in falas} == {boss, "jonathan"}


@pytest.mark.parametrize("cena_id,texto", [
    ("cap3_abertura", "Assina aqui, Jonathan. É só um sono."),
    ("cap3_pos_boss", "Vai lá, Samurai."),
    ("cap4_abertura", "Se alguém ouve isto, não está só... eles não..."),
    ("cap5_pos_boss", "Eu recusei. Fizeram outra. Não lembra de mim."),
    ("cap6_pos_boss", "Vai ficar tudo bem, Samurai. É só um sono."),
])
def test_falas_de_memoria_preservadas_com_interferencia(cena_id, texto):
    _, catalogo = _catalogo_producao()
    cena = catalogo.cena(cena_id)
    assert cena is not None
    indices = [i for i, passo in enumerate(cena.passos) if passo.get("texto") == texto]
    assert len(indices) == 1
    indice = indices[0]
    assert cena.passos[indice]["tipo"] == "fala"
    assert indice > 0 and cena.passos[indice - 1]["tipo"] == "glitch"
    if cena_id == "cap5_pos_boss":
        personagem = catalogo.personagens[cena.passos[indice]["personagem"]]
        assert personagem["nome"] == "Eco de IA anterior"
        assert personagem["retrato"] == catalogo.personagens["jonathan"]["retrato"]


@pytest.mark.parametrize("numero", range(1, 8))
def test_miniboss_so_agenda_antes_de_cena_vista(numero, tmp_path, monkeypatch):
    import src.runtime.infrastructure.persistence.save_system as save_mod
    from src.core.event_bus import GameEventType
    from src.runtime.controllers.cutscene import ControladorCutscene

    monkeypatch.setattr(save_mod, "ARQUIVO_SAVE", str(tmp_path / "save.json"))
    _, catalogo = _catalogo_producao()
    gatilho = f"miniboss:mini_{numero}"
    cena = catalogo.por_gatilho(gatilho)
    assert cena is not None
    assert cena.id == f"mini_{numero}"
    assert len(cena.passos) == (3 if numero == 4 else 2)
    assert all(p["tipo"] == "fala" for p in cena.passos)
    assert catalogo.personagens[cena.passos[0]["personagem"]]["nome"] == "Unidade de patrulha"
    jogo = SimpleNamespace(progresso=SistemaProgressao())
    agendados = []
    controle = ControladorCutscene.__new__(ControladorCutscene)
    controle._jogo = lambda: jogo
    controle.catalogo = catalogo
    controle.iniciar_gatilho = agendados.append
    evento = SimpleNamespace(type=GameEventType.MINIBOSS_SPAWNED,
                             data={"sessao": jogo, "chave": f"mini_{numero}"})
    controle._ao_evento(evento)
    assert agendados == [gatilho]
    jogo.progresso.marcar_cena_vista(cena.id)
    jogo.progresso = SistemaProgressao()
    controle._ao_evento(evento)
    assert agendados == [gatilho]


def test_boss_seis_agenda_final_e_retorna_ao_jogo():
    from src.core.constants import EstadoJogo
    from src.core.event_bus import GameEventType
    from src.runtime.controllers.cutscene import ControladorCutscene

    _, catalogo = _catalogo_producao()
    conclusoes, retomadas = [], []
    jogo = SimpleNamespace(
        estado=EstadoJogo.JOGANDO,
        progresso=SimpleNamespace(marcar_cena_vista=conclusoes.append),
        avanco_controller=SimpleNamespace(liberar_retomada=lambda: retomadas.append(True)),
    )
    controle = ControladorCutscene.__new__(ControladorCutscene)
    controle._jogo = lambda: jogo
    controle.catalogo = catalogo
    controle.fila = deque()
    controle.revisao = False
    controle._musica_pausada = False
    controle.sequenciador = SequenciadorCena(ao_concluir=controle._ao_concluir)
    controle._ao_evento(SimpleNamespace(type=GameEventType.BOSS_DEFEATED,
                                       data={"sessao": jogo, "cenario_id": 6}))
    assert controle.sequenciador.cena.id == "cap6_pos_boss"
    assert [c.id for c in controle.fila] == ["cap6_encerramento", "final"]
    assert catalogo.cena("final").passos[0]["texto"] == "// A BUSCA CONTINUA"
    # Executa os passos reais, sem pular o final nem gerar um evento de fim de jogo.
    for _ in range(100):
        if not controle.ativo:
            break
        controle.sequenciador.atualizar(100)
        controle.sequenciador.confirmar()
    assert not controle.ativo
    assert conclusoes == ["cap6_pos_boss", "cap6_encerramento", "final"]
    assert jogo.estado is EstadoJogo.JOGANDO
    assert retomadas == [True]
