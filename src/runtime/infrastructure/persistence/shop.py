"""Loja de skins: compra, equipa e persiste desbloqueios."""

import json
import os

from src.runtime.domain.entities.player import SKINS, Skin
from src.shared.persistence import carregar_json_resiliente, salvar_json_atomico
from src.shared.user_data import diretorio_dados

PASTA_DADOS = diretorio_dados()
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
            dados = carregar_json_resiliente(arquivo)
            return [Skin(c) for c in dados]
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self._salvar_catalogo()
            return [Skin(c) for c in SKINS]

    def _salvar_catalogo(self):
        caminho = os.path.join(PASTA_DADOS, "skins.json")
        return salvar_json_atomico(caminho, SKINS)

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
