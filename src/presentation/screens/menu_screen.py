"""Main menu screen with all sub-screens (menu, continue, shop, records, config).

Migrated from game/menu.py:
  OpcaoMenu, SistemaNotificacao, Dialogo, TransicaoTela, MenuPrincipal.

The screen manages its own sub-state and delegates rendering to
``menu_scene`` components for the cinematic background, HUD and ship.
"""

from __future__ import annotations

import math
import os
from typing import TYPE_CHECKING, Any, Optional

import pygame

from src.core.constants import (
    BRANCO, CIANO, DOURADO, LARANJA, NEGRO, VERDE, VERMELHO,
)

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Formatacao
# ---------------------------------------------------------------------------

def formatar_pontos(n: int) -> str:
    """Formata numeros com separador de milhar no padrao brasileiro."""
    return f"{n:,}".replace(",", ".")


# ---------------------------------------------------------------------------
# OpcaoMenu
# ---------------------------------------------------------------------------

class OpcaoMenu:
    """Opcao do menu principal com identidade visual forte na selecao."""

    def __init__(self, texto: str, y: int, funcao: callable) -> None:
        self.texto = texto
        self.y = y
        self.funcao = funcao
        self.hover: bool = False

    def get_rect(self, x: int, fonte: pygame.font.Font) -> pygame.Rect:
        larg = fonte.size(self.texto)[0]
        alt = fonte.get_height()
        pad_x, pad_y = 46, 16
        return pygame.Rect(x - pad_x, self.y - alt // 2 - pad_y,
                           larg + pad_x * 2, alt + pad_y * 2)

    def atualizar(self, mouse_pos: tuple[int, int], x: int,
                  fonte: pygame.font.Font) -> None:
        self.hover = self.get_rect(x, fonte).collidepoint(mouse_pos)

    def desenhar(self, tela: pygame.Surface, fonte: pygame.font.Font,
                 fonte_sel: pygame.font.Font, tema: dict, x: int,
                 selecionado: bool, deslocamento: float,
                 alfa: int) -> None:
        primaria = tema["primaria"]
        fonte_ativa = fonte_sel if selecionado else fonte
        cor = BRANCO if selecionado else (172, 182, 222)
        xf = x + deslocamento
        y = self.y
        if selecionado:
            # glow / shadow
            surf = fonte_ativa.render(self.texto, True,
                                      tema["secundaria"])
            s = surf.copy()
            s.set_alpha(max(0, min(255, int(alfa * 0.5))))
            tela.blit(s, (xf + 4, y + 2))
        surf = fonte_ativa.render(self.texto, True, cor)
        if alfa < 255:
            surf.set_alpha(alfa)
        tela.blit(surf, (xf, y))
        if selecionado and alfa >= 255:
            larg = fonte_ativa.size(self.texto)[0]
            pygame.draw.line(
                tela, primaria,
                (xf, y + fonte_ativa.get_height() // 2 + 4),
                (xf + larg, y + fonte_ativa.get_height() // 2 + 4), 3,
            )


# ---------------------------------------------------------------------------
# SistemaNotificacao
# ---------------------------------------------------------------------------

class SistemaNotificacao:
    """Notificacoes temporarias (toasts) no canto superior direito."""

    CORES: dict[str, tuple[int, int, int]] = {
        "sucesso": (0, 130, 60),
        "erro": (150, 20, 20),
        "conquista": (150, 100, 0),
        "info": (30, 60, 130),
    }

    def __init__(self, largura: int = 900, altura: int = 700) -> None:
        self._largura = largura
        self._altura = altura
        self.notificacoes: list[dict] = []

    def adicionar(self, mensagem: str, tipo: str = "info",
                  duracao: int = 3000) -> None:
        self.notificacoes.append({
            "mensagem": mensagem, "tipo": tipo, "duracao": duracao,
            "inicio": pygame.time.get_ticks(), "alpha": 255,
        })

    def atualizar(self) -> None:
        for notif in self.notificacoes[:]:
            decorrido = pygame.time.get_ticks() - notif["inicio"]
            if decorrido > notif["duracao"]:
                notif["alpha"] -= 6
                if notif["alpha"] <= 0:
                    self.notificacoes.remove(notif)

    def desenhar(self, tela: pygame.Surface,
                 fonte: pygame.font.Font) -> None:
        y = 24
        altura_toast = 44
        for notif in self.notificacoes[:]:
            texto = fonte.render(notif["mensagem"], True, BRANCO)
            largura = texto.get_width() + 48
            fundo = pygame.Surface((largura, altura_toast), pygame.SRCALPHA)
            cor = self.CORES.get(notif["tipo"], self.CORES["info"])
            rect = pygame.Rect(0, 0, largura, altura_toast)
            pygame.draw.rect(
                fundo, cor + (int(notif["alpha"] * 0.85),),
                rect, border_radius=8,
            )
            pygame.draw.rect(
                fundo, BRANCO + (int(notif["alpha"]),),
                rect, 1, border_radius=8,
            )
            x = self._largura - largura - 20
            tela.blit(fundo, (x, y))
            texto.set_alpha(notif["alpha"])
            tela.blit(texto, (x + 24, y + 11))
            y += 54


# ---------------------------------------------------------------------------
# Dialogo
# ---------------------------------------------------------------------------

class Dialogo:
    """Dialogo modal de confirmacao com visual cartoon."""

    def __init__(self, titulo: str, mensagem: str,
                 funcao_confirmar: callable,
                 funcao_cancelar: callable,
                 largura: int = 900, altura: int = 700) -> None:
        self._largura_tela = largura
        self._altura_tela = altura
        self.titulo = titulo
        self.mensagem = mensagem
        self.funcao_confirmar = funcao_confirmar
        self.funcao_cancelar = funcao_cancelar
        self.ativo: bool = True
        self._t0 = pygame.time.get_ticks()
        self._pw, self._ph = 540, 320
        self._x = largura // 2 - self._pw // 2
        self._y = altura // 2 - self._ph // 2

    def _retangulos(self) -> tuple[pygame.Rect, pygame.Rect]:
        pw, ph = self._pw, self._ph
        x = self._largura_tela // 2 - pw // 2
        y = self._altura_tela // 2 - ph // 2
        btn_w, btn_h = 170, 50
        confirmar = pygame.Rect(
            x + pw // 2 - btn_w - 12, y + ph - 82, btn_w, btn_h,
        )
        cancelar = pygame.Rect(
            x + pw // 2 + 12, y + ph - 82, btn_w, btn_h,
        )
        return confirmar, cancelar

    def tratar_evento(self, evento: pygame.event.Event,
                      mouse_pos: tuple[int, int] | None = None) -> None:
        if not self.ativo:
            return
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._confirmar()
            elif evento.key == pygame.K_ESCAPE:
                self._cancelar()
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            confirmar, cancelar = self._retangulos()
            pos = mouse_pos or evento.pos
            if confirmar.collidepoint(pos):
                self._confirmar()
            elif cancelar.collidepoint(pos):
                self._cancelar()

    def _confirmar(self) -> None:
        if self.ativo:
            self.ativo = False
            self.funcao_confirmar()

    def _cancelar(self) -> None:
        if self.ativo:
            self.ativo = False
            self.funcao_cancelar()

    def _animacao(self) -> tuple[float, float]:
        t = (pygame.time.get_ticks() - self._t0) / 250.0
        p = max(0.0, min(1.0, t))
        c1 = 1.70158
        c3 = c1 + 1
        escala = 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2
        return p, escala

    def desenhar(self, tela: pygame.Surface,
                 fonte_titulo: pygame.font.Font,
                 fonte_texto: pygame.font.Font,
                 mouse_pos: tuple[int, int] = (0, 0),
                 tema: dict | None = None) -> None:
        tema = tema or {
            "primaria": (120, 90, 220), "secundaria": (0, 200, 120),
            "terciaria": (255, 70, 90), "fundo_painel": (12, 14, 32),
            "borda_forte": (200, 200, 230),
        }
        p, escala = self._animacao()
        t = pygame.time.get_ticks() * 0.001
        larg, alt = self._largura_tela, self._altura_tela

        # overlay
        overlay = pygame.Surface((larg, alt), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(190 * p)))
        tela.blit(overlay, (0, 0))

        # painel
        pw = int(self._pw * (0.92 + 0.08 * escala))
        ph = int(self._ph * (0.92 + 0.08 * escala))
        px = larg // 2 - pw // 2
        py = alt // 2 - ph // 2
        rect = pygame.Rect(px, py, pw, ph)

        # fundo
        painel_bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(painel_bg, (14, 14, 30, 245),
                         (0, 0, pw, ph), border_radius=24)
        tela.blit(painel_bg, rect.topleft)
        pygame.draw.rect(tela, tema["primaria"], rect, 6, border_radius=24)

        alfa = int(255 * p)
        pulso = 0.6 + 0.4 * math.sin(t * 3.0)

        # icone alerta
        ix, iy = rect.centerx, rect.y + 50
        raio_icone = 24 + int(2 * pulso)
        pygame.draw.circle(tela, tema["terciaria"], (ix, iy), raio_icone)
        pygame.draw.circle(tela, (0, 0, 0), (ix, iy), raio_icone, 3)
        pygame.draw.rect(tela, BRANCO, (ix - 2, iy - 10, 5, 12))
        pygame.draw.circle(tela, BRANCO, (ix, iy + 7), 3)

        # titulo
        sombra = fonte_titulo.render(self.titulo, True, (0, 0, 0))
        sombra.set_alpha(int(160 * p))
        tela.blit(sombra, sombra.get_rect(
            center=(rect.centerx + 3, rect.y + 100 + 3)))
        titulo_surf = fonte_titulo.render(self.titulo, True, tema["primaria"])
        titulo_surf.set_alpha(alfa)
        tela.blit(titulo_surf, titulo_surf.get_rect(
            center=(rect.centerx, rect.y + 100)))

        # mensagem
        palavras = self.mensagem.split()
        linhas: list[str] = []
        atual: list[str] = []
        for palavra in palavras:
            teste = " ".join(atual + [palavra])
            if fonte_texto.size(teste)[0] > pw - 70:
                linhas.append(" ".join(atual))
                atual = [palavra]
            else:
                atual.append(palavra)
        if atual:
            linhas.append(" ".join(atual))
        y_texto = rect.y + 136
        for linha in linhas:
            s = fonte_texto.render(linha, True, (220, 225, 250))
            s.set_alpha(alfa)
            tela.blit(s, s.get_rect(center=(rect.centerx, y_texto)))
            y_texto += 32

        # botoes
        confirmar, cancelar = self._retangulos()
        self._desenhar_botao(tela, confirmar, "SIM, TENHO!",
                             fonte_texto, (30, 160, 80), mouse_pos, alfa)
        self._desenhar_botao(tela, cancelar, "CANCELAR",
                             fonte_texto, (180, 40, 50), mouse_pos, alfa)

        # dica
        dica = fonte_texto.render(
            "ENTER confirmar  |  ESC cancelar", True, (170, 175, 210))
        dica.set_alpha(int(210 * p))
        tela.blit(dica, dica.get_rect(center=(rect.centerx,
                                               rect.bottom - 22)))

    def _desenhar_botao(self, tela: pygame.Surface, rect: pygame.Rect,
                        texto: str, fonte: pygame.font.Font,
                        cor_fundo: tuple, mouse_pos: tuple,
                        alfa: int) -> None:
        hover = rect.collidepoint(mouse_pos)
        sombra = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (0, 0, 0, 100),
                         (0, 0, rect.w, rect.h), border_radius=rect.h // 2)
        tela.blit(sombra, (rect.x + 3, rect.y + 4))
        cor = tuple(min(255, c + 25) for c in cor_fundo) if hover else cor_fundo
        fundo = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(fundo, tuple(cor[:3]) + (int(240 * alfa / 255),),
                         (0, 0, rect.w, rect.h), border_radius=rect.h // 2)
        tela.blit(fundo, rect.topleft)
        pygame.draw.rect(tela, (0, 0, 0), rect, 4,
                         border_radius=rect.h // 2)
        pygame.draw.rect(tela, cor_fundo, rect, 2,
                         border_radius=rect.h // 2)
        txt = fonte.render(texto, True, (255, 255, 255))
        txt.set_alpha(int(255 * alfa / 255))
        tela.blit(txt, (rect.centerx - txt.get_width() // 2,
                        rect.centery - txt.get_height() // 2))


# ---------------------------------------------------------------------------
# TransicaoTela
# ---------------------------------------------------------------------------

class TransicaoTela:
    """Fade suave de entrada/saida entre telas."""

    def __init__(self, duracao: int = 450) -> None:
        self.duracao = duracao
        self.ativo: bool = False
        self.inicio: int = 0
        self.alpha: int = 0

    def iniciar(self) -> None:
        self.ativo = True
        self.inicio = pygame.time.get_ticks()

    def atualizar(self) -> None:
        if self.ativo:
            progresso = (pygame.time.get_ticks() - self.inicio) / self.duracao
            if progresso >= 1:
                self.ativo = False
                self.alpha = 0
            else:
                self.alpha = int(255 * abs(math.sin(progresso * math.pi)))

    def desenhar(self, tela: pygame.Surface) -> None:
        if self.ativo and self.alpha > 0:
            overlay = pygame.Surface(tela.get_size())
            overlay.fill(NEGRO)
            overlay.set_alpha(self.alpha)
            tela.blit(overlay, (0, 0))
