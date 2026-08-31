"""Garantias de que modulos migrados possuem uma unica fonte em ``src``."""

from game import config as config_legado
from game import layout as layout_legado
from game import settings as settings_legado
from game import theme as theme_legado
from src.core import constants
from src.core import settings
from src.infrastructure.graphics import theme
from src.infrastructure.ui import layout


def test_config_legado_e_fachada_das_constantes_canonicas():
    """Consumidores antigos observam os mesmos objetos definidos em ``src``."""
    assert config_legado.EstadoJogo is constants.EstadoJogo
    assert config_legado.LARGURA == constants.LARGURA
    assert config_legado.INCREMENTO_CARREGAMENTO == constants.INCREMENTO_CARREGAMENTO
    assert config_legado.COOLDOWN_ATAQUE_INIMIGO_MAXIMO == (
        constants.COOLDOWN_ATAQUE_INIMIGO_MAXIMO)


def test_tema_legado_e_fachada_da_infraestrutura_canonica():
    """Tema e funcoes de cor continuam unicos apos a migracao."""
    assert theme_legado.TEMAS_CORES is theme.TEMAS_CORES
    assert theme_legado.tema_atual is theme.tema_atual
    assert theme_legado.cor_misturar is theme.cor_misturar


def test_layout_legado_e_fachada_da_infraestrutura_canonica():
    """O mesmo motor responsivo atende consumidores novos e antigos."""
    assert layout_legado.Layout is layout.Layout
    assert layout_legado.CENTRO == layout.CENTRO
    assert layout_legado.TOPO_ESQUERDA == layout.TOPO_ESQUERDA


def test_configuracoes_legadas_apontam_para_o_mesmo_modulo_canonico():
    """Patches de persistencia tambem atingem a implementacao em ``src``."""
    assert settings_legado is settings
