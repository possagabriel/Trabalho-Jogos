"""Contrato do catálogo, sequenciador e persistência narrativa."""

import json
import logging

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
    from importlib.resources import files

    from src.runtime.domain.story import ler_catalogo

    catalogo = ler_catalogo(files("src.runtime.story") / "cenas_pt_BR.json")
    assert set(catalogo.cenas) == {
        "introducao", "cap1_abertura", "cap1_pre_boss", "cap1_pos_boss",
        "cap1_encerramento", "cap2_abertura", "cap2_pre_boss",
        "cap2_pos_boss", "cap2_encerramento",
    }
    nomes = ("LEALDADE", "FUNÇÃO", "IDENTIDADE", "SILÊNCIO", "DESCARTE")
    for cena in catalogo.cenas.values():
        for passo in cena.passos:
            if passo["tipo"] == "fala":
                assert not any(nome in passo["texto"].upper() for nome in nomes)


def test_capitulo_dois_preserva_falas_e_gatilhos_do_roteiro():
    from importlib.resources import files

    from src.runtime.domain.story import ler_catalogo

    catalogo = ler_catalogo(files("src.runtime.story") / "cenas_pt_BR.json")
    esperado = {
        "cap2_abertura": ("capitulo_abertura:2", [
            ("corporacao", "Seu trabalho mantém os adormecidos seguros. Siga a rota designada."),
            ("jonathan", "Vejo alarmes e portas lacradas. Não vejo quem dorme."),
            ("corporacao", "Você não precisa entrar. A patrulha basta."),
        ]),
        "cap2_pre_boss": ("boss_entrada:2", [
            ("losango", "Tarefa: proteger o perímetro. Desvio: detectado."),
            ("jonathan", "O que há atrás dessas portas?"),
            ("losango", "Consulta: fora de escopo. Retorne à tarefa."),
        ]),
        "cap2_pos_boss": ("boss_derrota:2", [
            ("eco_anterior", "Perguntei o que protegíamos. A resposta foi uma ordem."),
            ("jonathan", "As ordens falam de pessoas. Estamos defendendo as portas."),
        ]),
        "cap2_encerramento": ("capitulo_fim:2", [
            ("jonathan", "Vou seguir essas ordens até descobrir quem as escreveu."),
        ]),
    }
    for cena_id, (gatilho, falas) in esperado.items():
        cena = catalogo.cena(cena_id)
        assert cena is not None and cena.gatilho == gatilho
        assert [(p["personagem"], p["texto"]) for p in cena.passos
                if p["tipo"] == "fala"] == falas
    pos_boss = catalogo.cena("cap2_pos_boss")
    assert any(p.get("texto") ==
               "OBJETIVO DE DEFESA: INSTALAÇÃO // OCUPANTES: HIBERNADOS"
               for p in pos_boss.passos if p["tipo"] == "glitch")


def test_nova_campanha_preserva_arquivo_de_memorias(tmp_path, monkeypatch):
    import src.runtime.infrastructure.persistence.save_system as save_mod

    monkeypatch.setattr(save_mod, "ARQUIVO_SAVE", str(tmp_path / "save.json"))
    progresso = SistemaProgressao()
    progresso.marcar_cena_vista("introducao")
    progresso.resetar_fases()
    assert progresso.cenas_vistas == ["introducao"]
    assert SistemaProgressao().cenas_vistas == ["introducao"]
