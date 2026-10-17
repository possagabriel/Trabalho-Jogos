"""Contrato do catálogo, sequenciador e persistência narrativa."""

import json
import logging

from src.runtime.domain.story import carregar_catalogo, SequenciadorCena
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
