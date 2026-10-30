"""Contratos do kit de UI.

Os protocolos documentam a superfície mínima que cada componente deve
expor. Implementações entram junto da primeira tela que precisa delas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import pygame

if TYPE_CHECKING:
    from src.infrastructure.ui.layout import Layout


@runtime_checkable
class ComponenteUI(Protocol):
    """Componente desenhável com rect próprio."""

    rect: pygame.Rect

    def desenhar(self, tela: pygame.Surface, layout: Layout, **kwargs: Any) -> None:
        """Desenha o componente na superfície lógica."""


@runtime_checkable
class AtualizavelUI(Protocol):
    """Componente que reage à posição do mouse."""

    def atualizar(self, mouse_pos: tuple[int, int]) -> None:
        """Atualiza hover e estados transitórios."""


@runtime_checkable
class ContratoPainel(ComponenteUI, Protocol):
    """Painel com área de conteúdo interna."""

    def area_conteudo(self, layout: Layout) -> pygame.Rect:
        """Retorna a área reservada ao conteúdo."""


@runtime_checkable
class ContratoBotao(ComponenteUI, AtualizavelUI, Protocol):
    """Botão com texto, foco e estado habilitado."""

    texto: str
    habilitado: bool
    foco: bool


@runtime_checkable
class ContratoLista(ComponenteUI, Protocol):
    """Lista com itens, seleção e rolagem."""

    itens: list

    def rolar(self, delta: int, layout: Layout, tokens: Any = None) -> None:
        """Rola o conteúdo em pixels."""

    def mover_selecao(
        self,
        delta: int,
        layout: Layout,
        tokens: Any = None,
    ) -> None:
        """Move a seleção e mantém a linha visível."""


@runtime_checkable
class ContratoBarraRolagem(ComponenteUI, Protocol):
    """Barra proporcional ao conteúdo visível."""

    def geometria(
        self,
        area: pygame.Rect,
        total: int,
        visivel: int,
        offset: int,
        layout: Layout,
    ) -> tuple[pygame.Rect, pygame.Rect | None]:
        """Retorna trilho e polegar."""


@runtime_checkable
class ContratoAbas(ComponenteUI, Protocol):
    """Navegação por abas."""

    indice: int

    def selecionar(self, indice: int) -> None:
        """Seleciona uma aba."""


@runtime_checkable
class ContratoAlternador(ComponenteUI, AtualizavelUI, Protocol):
    """Chave liga/desliga."""

    ativo: bool

    def alternar(self) -> None:
        """Inverte o estado."""


@runtime_checkable
class ContratoSlider(ComponenteUI, AtualizavelUI, Protocol):
    """Controle contínuo com mínimo, máximo e valor atual."""

    valor: float
    minimo: float
    maximo: float

    def definir_valor(self, valor: float) -> None:
        """Atualiza o valor respeitando os limites."""


@runtime_checkable
class ContratoCampoTexto(ComponenteUI, AtualizavelUI, Protocol):
    """Entrada de texto com foco."""

    texto: str
    ativo: bool

    def tratar_evento(self, evento: pygame.event.Event) -> bool:
        """Consome o evento quando o campo está ativo."""


@runtime_checkable
class ContratoDialogo(ComponenteUI, Protocol):
    """Confirmação modal com duas ações."""

    aberto: bool

    def confirmar(self) -> None:
        """Executa a ação principal."""

    def cancelar(self) -> None:
        """Fecha sem executar a ação principal."""


@runtime_checkable
class ContratoAviso(ComponenteUI, Protocol):
    """Notificação transitória."""

    def mostrar(self, texto: str) -> None:
        """Exibe uma mensagem."""

    def fechar(self) -> None:
        """Remove a mensagem da tela."""
