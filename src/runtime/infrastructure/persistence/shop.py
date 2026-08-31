"""Loja de skins: compra, equipa e persiste desbloqueios."""

import json
import logging
import os

from src.runtime.domain.entities.player import SKINS, Skin

PASTA_DADOS = (os.environ.get("SPACEFURY_DATA_DIR")
               or os.path.join(os.path.dirname(os.path.dirname(
                   os.path.abspath(__file__))), "data"))
LOGGER = logging.getLogger(__name__)


class LojaSkins:
    """Gerencia o catalogo de skins, moedas do jogador e desbloqueios."""

    def __init__(self, moedas=0, desbloqueadas=None, skin_atual=None):
        self.moedas = moedas
        self.skins = self._carregar_catalogo()
        desbloqueadas = desbloqueadas or ["padrao"]
        for skin in self.skins:
            skin.desbloqueada = skin.id in desbloqueadas
        self.skin_atual = skin_atual or "padrao"

    def _carregar_catalogo(self):
        """Carrega o catalogo de skins.json ou usa o padrao embutido."""
        arquivo = os.path.join(PASTA_DADOS, "skins.json")
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
            return [Skin(c) for c in dados]
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self._salvar_catalogo()
            return [Skin(c) for c in SKINS]

    def _salvar_catalogo(self):
        os.makedirs(PASTA_DADOS, exist_ok=True)
        try:
            with open(os.path.join(PASTA_DADOS, "skins.json"), "w",
                      encoding="utf-8") as f:
                json.dump(SKINS, f, ensure_ascii=False, indent=2)
        except OSError as erro:
            LOGGER.warning("Nao foi possivel salvar catalogo de skins: %s", erro)
            return False
        return True

    def pegar_skin(self, skin_id):
        for skin in self.skins:
            if skin.id == skin_id:
                return skin
        return self.skins[0]

    def comprar_skin(self, indice):
        """Tenta comprar a skin. Retorna (sucesso, skin)."""
        skin = self.skins[indice]
        if skin.desbloqueada:
            return False, skin
        if self.moedas >= skin.preco:
            self.moedas -= skin.preco
            skin.desbloqueada = True
            return True, skin
        return False, skin

    def equipar_skin(self, indice):
        skin = self.skins[indice]
        if skin.desbloqueada:
            self.skin_atual = skin.id
            return True
        return False

    def reembolsar_skin(self, indice):
        """Desfaz uma compra e devolve o valor da skin ao jogador.

        A skin padrao nao pode ser removida. Caso a skin reembolsada esteja
        equipada, o jogador volta automaticamente para a skin padrao.

        Returns:
            tuple[bool, Skin]: Sucesso da operacao e a skin solicitada.
        """
        skin = self.skins[indice]
        if skin.id == "padrao" or not skin.desbloqueada:
            return False, skin
        skin.desbloqueada = False
        self.moedas += skin.preco
        if self.skin_atual == skin.id:
            self.skin_atual = "padrao"
        return True, skin

    def lista_desbloqueadas(self):
        return [s.id for s in self.skins if s.desbloqueada]
