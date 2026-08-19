"""Testes de configuracao, persistencia de progresso e loja.

Cobre ``settings`` (parse de resolucao e persistencia em JSON),
``save_system`` (progressao, recordes) e ``shop`` (catalogo, compra,
equipamento).

Os testes redirecionam as constantes de caminho (ARQUIVO_CONFIG,
ARQUIVO_SAVE, ARQUIVO_RECORDES, PASTA_DADOS) para diretorios temporarios
para nao tocar nos dados reais do jogo.

Roda headless:

    python tests/test_settings_save_shop.py   # standalone
    pytest tests/test_settings_save_shop.py -v
"""

import json
import os
import sys
import tempfile
from unittest import mock

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

from game import save_system  # noqa: E402
from game import settings  # noqa: E402
from game import shop  # noqa: E402
from game.config import ALTURA, LARGURA  # noqa: E402
from game.player import Jogador, SKINS, Skin  # noqa: E402


def _tmp_dados(prefix="spacefury_persist_"):
    return tempfile.mkdtemp(prefix=prefix)


def _patches(dados):
    """Contexto redirecionando os caminhos de dados do save para `dados`."""
    return mock.patch.multiple(
        save_system,
        PASTA_DADOS=dados,
        ARQUIVO_SAVE=os.path.join(dados, "save.json"),
        ARQUIVO_RECORDES=os.path.join(dados, "records.json"))


def _patch_config(dados):
    return mock.patch.object(settings, "ARQUIVO_CONFIG",
                             os.path.join(dados, "settings.json"))


def _patch_shop(dados):
    return mock.patch.object(shop, "PASTA_DADOS", dados)


# ---------------------------------------------------------------------------
# settings.parse_resolucao
# ---------------------------------------------------------------------------

def test_parse_resolucao():
    assert settings.parse_resolucao("1280x720") == (1280, 720)
    assert settings.parse_resolucao("1920X1080") == (1920, 1080)
    assert settings.parse_resolucao("  900x700 ") == (900, 700)
    assert settings.parse_resolucao("invalido") == (LARGURA, ALTURA)
    assert settings.parse_resolucao(None) == (LARGURA, ALTURA)
    assert settings.parse_resolucao("") == (LARGURA, ALTURA)


# ---------------------------------------------------------------------------
# settings.Configuracoes
# ---------------------------------------------------------------------------

def test_configuracoes_carregar_defaults():
    dados = _tmp_dados()
    with _patch_config(dados):
        cfg = settings.Configuracoes()
        assert cfg["musica_volume"] == 0.8
        assert cfg["resolucao"] == "900x700"
        assert cfg["tela_cheia"] is False
        assert cfg["sensibilidade"] == 1.0
        assert cfg["tema"] == "NEON"
        assert cfg["aspecto"] == "AJUSTAR"
        assert cfg["ajuste_escala"] == 1.0
        assert cfg["ajuste_off_x"] == 0
        assert cfg.controles["atirar"] == pygame.K_SPACE


def test_configuracoes_salvar_e_recarregar():
    dados = _tmp_dados()
    with _patch_config(dados):
        cfg = settings.Configuracoes()
        cfg["musica_volume"] = 0.25
        cfg["sensibilidade"] = 1.5
        cfg["tema"] = "AURORA"
        cfg.salvar()
        assert os.path.exists(os.path.join(dados, "settings.json"))

        cfg2 = settings.Configuracoes()
        assert cfg2["musica_volume"] == 0.25
        assert cfg2["sensibilidade"] == 1.5
        assert cfg2["tema"] == "AURORA"


def test_configuracoes_arquivo_corrompido_usa_defaults():
    dados = _tmp_dados()
    caminho = os.path.join(dados, "settings.json")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("{ isto nao e json")
    with _patch_config(dados):
        cfg = settings.Configuracoes()
        assert cfg["musica_volume"] == 0.8
        assert cfg["tema"] == "NEON"


def test_configuracoes_controles_parciais_mesclam():
    dados = _tmp_dados()
    caminho = os.path.join(dados, "settings.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump({"controles": {"atirar": pygame.K_x}}, f)
    with _patch_config(dados):
        cfg = settings.Configuracoes()
        assert cfg.controles["atirar"] == pygame.K_x
        assert cfg.controles["cima"] == pygame.K_UP


# ---------------------------------------------------------------------------
# save_system.SistemaProgressao
# ---------------------------------------------------------------------------

def test_save_novo_dados():
    dados = _tmp_dados()
    with _patches(dados):
        prog = save_system.SistemaProgressao()
        assert prog.jogador["moedas"] == 0
        assert prog.jogador["skins_desbloqueadas"] == ["padrao"]
        assert prog.jogador["cenarios_desbloqueados"] == [1]
        assert prog.dados["estatisticas"]["tiros_disparados"] == 0


def test_save_adicionar_moedas_e_pontos():
    dados = _tmp_dados()
    with _patches(dados):
        prog = save_system.SistemaProgressao()
        prog.adicionar_moedas(150)
        prog.adicionar_pontos(300)
        assert prog.jogador["moedas"] == 150
        assert prog.jogador["total_pontos"] == 300


def test_save_registrar_fim_jogo():
    dados = _tmp_dados()
    with _patches(dados):
        prog = save_system.SistemaProgressao()
        jog = Jogador()
        jog.nivel = 6
        jog.pontuacao = 1200
        jog.moedas_jogo = 80
        prog.registrar_fim_jogo(jog, tempo_partida=75, inimigos_abates=12,
                                cenario_atual=2, bosses_abates=1)
        assert prog.jogador["nivel_maximo"] == 6
        assert prog.jogador["total_pontos"] == 1200
        # moedas = moedas_jogo + (50 * cenario + 100 * bosses)
        assert prog.jogador["moedas"] == 80 + 50 * 2 + 100 * 1
        assert prog.dados["estatisticas"]["inimigos_derrotados"] == 12
        assert prog.dados["estatisticas"]["tempo_total"] == 75


def test_save_registrar_boss_e_desbloqueios():
    dados = _tmp_dados()
    with _patches(dados):
        prog = save_system.SistemaProgressao()
        prog.registrar_boss()
        assert prog.jogador["bosses_derrotados"] == 1
        assert prog.dados["estatisticas"]["bosses_derrotados"] == 1
        prog.desbloquear_cenario(2)
        prog.desbloquear_cenario(2)
        assert prog.jogador["cenarios_desbloqueados"] == [1, 2]
        assert prog.desbloquear_skin("fenix") is True
        assert prog.desbloquear_skin("fenix") is False


def test_save_persistencia_em_disco():
    dados = _tmp_dados()
    with _patches(dados):
        prog = save_system.SistemaProgressao()
        prog.adicionar_moedas(500)
        prog.salvar_arquivo()
        assert os.path.exists(os.path.join(dados, "save.json"))
        prog2 = save_system.SistemaProgressao()
        assert prog2.jogador["moedas"] == 500


def test_save_existe_e_resetar():
    dados = _tmp_dados()
    with _patches(dados):
        prog = save_system.SistemaProgressao()
        assert prog.existe_save() is False
        prog.adicionar_moedas(10)
        prog.salvar_arquivo()
        assert save_system.SistemaProgressao().existe_save() is True
        prog.resetar_progresso()
        assert prog.jogador["moedas"] == 0


def test_save_recordes_ordena_e_limita_10():
    dados = _tmp_dados()
    with _patches(dados):
        assert save_system.SistemaProgressao.carregar_recordes() == []
        assert save_system.SistemaProgressao.melhor_pontuacao() == 0
        for i in range(12):
            save_system.SistemaProgressao.salvar_recorde(f"J{i}", i * 10, 1, "Padrao")
        lista = save_system.SistemaProgressao.carregar_recordes()
        assert len(lista) == 10
        pontos = [r["pontos"] for r in lista]
        assert pontos == sorted(pontos, reverse=True)
        assert save_system.SistemaProgressao.melhor_pontuacao() == max(pontos)


def test_save_moedas_fim_jogo():
    dados = _tmp_dados()
    with _patches(dados):
        prog = save_system.SistemaProgressao()
        assert prog._moedas_fim_jogo(1, 0) == 50
        assert prog._moedas_fim_jogo(6, 3) == 300 + 300


# ---------------------------------------------------------------------------
# shop.LojaSkins
# ---------------------------------------------------------------------------

def test_loja_catalogo_e_padrao():
    dados = _tmp_dados()
    with _patch_shop(dados):
        loja = shop.LojaSkins(moedas=0)
        assert len(loja.skins) == len(SKINS)
        assert loja.skin_atual == "padrao"
        assert loja.pegar_skin("padrao").desbloqueada is True
        assert loja.pegar_skin("void").desbloqueada is False


def test_loja_comprar_skin():
    dados = _tmp_dados()
    with _patch_shop(dados):
        loja = shop.LojaSkins(moedas=2000)
        ok, skin = loja.comprar_skin(1)  # fenix custa 500
        assert ok is True
        assert skin.desbloqueada is True
        assert loja.moedas == 1500
        # ja desbloqueada nao compra de novo
        ok2, _ = loja.comprar_skin(1)
        assert ok2 is False


def test_loja_compra_sem_moedas():
    dados = _tmp_dados()
    with _patch_shop(dados):
        loja = shop.LojaSkins(moedas=10)
        ok, skin = loja.comprar_skin(9)  # void custa 10000
        assert ok is False
        assert skin.desbloqueada is False
        assert loja.moedas == 10


def test_loja_equipar_skin():
    dados = _tmp_dados()
    with _patch_shop(dados):
        loja = shop.LojaSkins(moedas=500, desbloqueadas=["padrao", "fenix"])
        assert loja.equipar_skin(1) is True
        assert loja.skin_atual == "fenix"
        assert loja.equipar_skin(2) is False
        assert loja.skin_atual == "fenix"
        assert loja.lista_desbloqueadas() == ["padrao", "fenix"]


def test_loja_sincronizar_com_save():
    dados = _tmp_dados()
    with _patch_shop(dados), _patches(dados):
        loja = shop.LojaSkins(moedas=300, desbloqueadas=["padrao", "sombra"],
                              skin_atual="sombra")
        prog = save_system.SistemaProgressao()
        prog.sincronizar_loja(loja)
        assert prog.jogador["moedas"] == 300
        assert prog.jogador["skin_atual"] == "sombra"
        assert "sombra" in prog.jogador["skins_desbloqueadas"]


def test_loja_persistencia_catalogo():
    dados = _tmp_dados()
    with _patch_shop(dados):
        loja = shop.LojaSkins(moedas=0)
        arquivo = os.path.join(dados, "skins.json")
        assert os.path.exists(arquivo)
        with open(arquivo, "r", encoding="utf-8") as f:
            catalogo = json.load(f)
        assert len(catalogo) == len(SKINS)


def test_skin_construtor():
    skin = Skin(SKINS[0])
    assert skin.id == "padrao"
    assert skin.preco == 0
    assert skin.desbloqueada is True
    assert skin.cor == tuple(SKINS[0]["cor"])
    cara = Skin(SKINS[9])
    assert cara.desbloqueada is False


def main():
    funcoes = [v for k, v in sorted(globals().items())
               if k.startswith("test_") and callable(v)]
    falhas = 0
    for funcao in funcoes:
        try:
            funcao()
            print(f"OK   {funcao.__name__}")
        except Exception as erro:  # noqa: BLE001
            falhas += 1
            import traceback
            traceback.print_exc()
            print(f"FAIL {funcao.__name__}: {erro}")
    print(f"\n{len(funcoes) - falhas}/{len(funcoes)} testes passaram")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()