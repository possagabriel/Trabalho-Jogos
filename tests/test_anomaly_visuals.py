"""Regressões dos efeitos de anomalias, sem capturas ou alteração de física."""

import pygame
import pytest

from src.runtime.domain.world.anomalies import CosmicAnomalies


@pytest.fixture(autouse=True)
def inicializar_fontes():
    """Prepara as fontes usadas nas legendas procedurais."""
    pygame.font.init()


@pytest.mark.parametrize("comic", [False, True])
@pytest.mark.parametrize("tipo", ["black_holes", "wormholes"])
def test_efeitos_reduzidos_preservam_imagem_estatica(comic: bool, tipo: str) -> None:
    anomalias = CosmicAnomalies(1)
    alvo = getattr(anomalias, tipo)[0]
    imagens = []
    for tempo in (0.0, 0.6, 1.2):
        tela = pygame.Surface((600, 500))
        anomalias.render(tela, alvo.x - 300, alvo.y - 250, comic,
                         tempo=tempo, reduzido=True)
        imagens.append(pygame.image.tobytes(tela, "RGB"))
    assert imagens[0] == imagens[1] == imagens[2]
    assert any(imagens[0])


@pytest.mark.parametrize("tipo", ["black_holes", "wormholes"])
def test_fluxo_anima_sem_mudar_fisica_ou_imagem_em_cache(tipo: str) -> None:
    anomalias = CosmicAnomalies(1)
    alvo = getattr(anomalias, tipo)[0]
    gravidade = anomalias.gravity(alvo.x - 300, alvo.y)
    destino = anomalias.destination(alvo.x, alvo.y, 0)
    imagens = []
    for tempo in (0.0, 0.6, 0.0):
        tela = pygame.Surface((600, 500))
        anomalias.render(tela, alvo.x - 300, alvo.y - 250, False, tempo=tempo)
        imagens.append(pygame.image.tobytes(tela, "RGB"))
    assert imagens[0] != imagens[1]
    assert imagens[0] == imagens[2]
    assert anomalias.gravity(alvo.x - 300, alvo.y) == gravidade
    assert anomalias.destination(alvo.x, alvo.y, 0) == destino


def test_anomalias_fora_da_camera_nao_desenham() -> None:
    tela = pygame.Surface((600, 500))
    CosmicAnomalies(1).render(tela, -5000, -5000, False, tempo=1)
    assert not any(pygame.image.tobytes(tela, "RGB"))


@pytest.mark.parametrize("efeito", ["REDUZIDO", "DESLIGADO", "NORMAL"])
def test_mundo_encaminha_preferencia_de_efeitos(efeito: str, monkeypatch) -> None:
    from src.runtime.domain.world.open_world import OpenWorldRuntime

    pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))
    mundo = OpenWorldRuntime(visual_config={"intensidade_flash": efeito})
    chamadas = []
    monkeypatch.setattr(mundo.anomalies, "render",
                        lambda *args, **kwargs: chamadas.append(kwargs))
    mundo.render(pygame.Surface((1280, 720)))
    assert chamadas == [{"tempo": mundo.elapsed, "reduzido": efeito != "NORMAL"}]


def test_camadas_sao_reutilizadas_durante_animacao() -> None:
    from src.runtime.infrastructure.graphics.anomaly_visuals import (
        camada_anomalia,
        legenda_anomalia,
    )

    anomalias = CosmicAnomalies(1)
    portal = anomalias.wormholes[0]
    tela = pygame.Surface((600, 500))
    anomalias.render(tela, portal.x - 300, portal.y - 250, False)
    faltas = (camada_anomalia.cache_info().misses, legenda_anomalia.cache_info().misses)
    for tempo in (0.3, 0.7, 1.4):
        anomalias.render(tela, portal.x - 300, portal.y - 250, False, tempo=tempo)
    assert faltas == (camada_anomalia.cache_info().misses, legenda_anomalia.cache_info().misses)
