"""Contrato do catálogo, sequenciador e persistência narrativa."""

import json
import logging

from src.runtime.domain.story import TIPOS_PASSO, SequenciadorCena, carregar_catalogo
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


def test_roteiro_ids_referencias_tipos_e_falas_validos():
    from importlib.resources import files

    caminho = files("src.runtime.story") / "cenas_pt_BR.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    ids = [cena["id"] for cena in dados["cenas"]]
    personagens = dados["personagens"]
    assert len(ids) == len(set(ids))

    proibidas = (
        "lealdade", "função", "identidade", "silêncio", "descarte",
        "protocolo restrito",
    )
    for cena in dados["cenas"]:
        assert cena["passos"]
        for passo in cena["passos"]:
            assert passo["tipo"] in TIPOS_PASSO
            if passo["tipo"] == "fala":
                assert passo["personagem"] in personagens
                texto = passo["texto"].casefold()
                assert not any(termo in texto for termo in proibidas)
            elif passo["tipo"] == "retrato":
                assert passo["personagem"] in personagens

    catalogo = carregar_catalogo(dados)
    assert set(catalogo.cenas) == set(ids)


def test_capitulo_tres_tem_gatilhos_e_texto_fornecidos():
    from importlib.resources import files

    from src.runtime.domain.story import ler_catalogo

    catalogo = ler_catalogo(files("src.runtime.story") / "cenas_pt_BR.json")
    ids = ("cap3_abertura", "cap3_pre_boss", "cap3_pos_boss", "cap3_encerramento")
    scenes = [catalogo.cena(identificador) for identificador in ids]
    assert all(scene is not None for scene in scenes)
    cenas = [scene for scene in scenes if scene is not None]
    assert [cena.gatilho for cena in cenas] == [
        "capitulo_abertura:3", "boss_entrada:3", "boss_derrota:3",
        "capitulo_fim:3",
    ]
    assert [passo.get("texto") for passo in cenas[0].passos
            if passo["tipo"] == "glitch" and "texto" in passo] == [
        "JONATHAN // EU TINHA MÃOS",
    ]


def test_falas_de_miniboss_usam_primeiro_encontro_por_tipo():
    from importlib.resources import files

    from src.runtime.domain.story import ler_catalogo

    catalogo = ler_catalogo(files("src.runtime.story") / "cenas_pt_BR.json")
    tipos = ("bastiao", "espectro", "matriz", "cartografo", "eco", "cronista", "censor")
    for tipo in tipos:
        cena = catalogo.por_gatilho(f"miniboss:{tipo}")
        assert cena is not None
        falantes = [passo["personagem"] for passo in cena.passos
                    if passo["tipo"] == "fala"]
        assert falantes[0] == "unidade_patrulha"
        assert "jonathan" in falantes
        assert set(falantes) <= {"unidade_patrulha", "jonathan"}


def test_capitulo_quatro_usa_gatilhos_do_capitulo():
    from importlib.resources import files

    from src.runtime.domain.story import ler_catalogo

    catalogo = ler_catalogo(files("src.runtime.story") / "cenas_pt_BR.json")
    ids = ("cap4_abertura", "cap4_pre_boss", "cap4_pos_boss", "cap4_encerramento")
    cenas = [catalogo.cena(identificador) for identificador in ids]
    assert all(cena is not None for cena in cenas)
    assert [cena.gatilho for cena in cenas if cena is not None] == [
        "capitulo_abertura:4", "boss_entrada:4", "boss_derrota:4",
        "capitulo_fim:4",
    ]


def test_nova_campanha_preserva_arquivo_de_memorias(tmp_path, monkeypatch):
    import src.runtime.infrastructure.persistence.save_system as save_mod

    monkeypatch.setattr(save_mod, "ARQUIVO_SAVE", str(tmp_path / "save.json"))
    progresso = SistemaProgressao()
    progresso.marcar_cena_vista("introducao")
    progresso.resetar_fases()
    assert progresso.cenas_vistas == ["introducao"]
    assert SistemaProgressao().cenas_vistas == ["introducao"]
