"""Garante que a reorganização não desloque os recursos visuais."""

from __future__ import annotations

from pathlib import Path

from src.runtime.infrastructure import assets, paths
from src.runtime.infrastructure.graphics import fonts
from src.infrastructure.graphics import fonts as fontes_layout


def test_recursos_do_runtime_continuam_na_raiz_do_projeto() -> None:
    """Menu e entidades usam os arquivos originais, não cópias em ``src``."""
    assert paths.PASTA_IMAGENS == paths.RAIZ_PROJETO / "images"
    assert paths.PASTA_FONTES == paths.RAIZ_PROJETO / "data" / "fonts"
    assert Path(assets.caminho_imagem("fundo-menuprincipal.png")).is_file()
    assert Path(fonts.ARQUIVO_TITULO).is_file()
    assert Path(fonts.ARQUIVO_TEXTO).is_file()
    assert Path(fontes_layout.ARQUIVO_TITULO).is_file()
    assert Path(fontes_layout.ARQUIVO_TEXTO).is_file()
