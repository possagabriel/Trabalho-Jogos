"""Renderizacao e entrada da tela de configuracoes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.core.constants import QUANTUM_CYAN, VERDE
from src.core.settings import ACOES_CONTROLE, RESOLUCOES
from src.runtime.presentation.screens.settings_view import (
    CATEGORIAS_CONFIG,
    PainelConfiguracoesOriginal,
    categoria_config,
)

if TYPE_CHECKING:
    from src.runtime.presentation.menu import MenuPrincipal


class TelaConfiguracoesJogo:
    """Coordena a apresentacao dos submodos de configuracao."""

    def __init__(self, menu: MenuPrincipal) -> None:
        self.menu = menu
        self.original = PainelConfiguracoesOriginal(self)
        self._arraste: tuple[int, float] | None = None

    def indices_visiveis_original(self) -> tuple[int, ...]:
        """Mantém a opção selecionada visível dentro de sua categoria."""
        selecao = self.menu.config_selecao
        grupo = CATEGORIAS_CONFIG[categoria_config(selecao)][1]
        inicio = min(max(0, grupo.index(selecao) - 3), max(0, len(grupo) - 6))
        return grupo[inicio:inicio + 6]

    def desenhar(self, tela: pygame.Surface) -> None:
        """Renderiza abas e subtelas com o acabamento visual ativo."""
        self.original.desenhar(tela)

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        """Trata navegacao e abertura dos submodos de configuracao."""
        menu = self.menu
        self._arraste = None
        if not menu.config_submodo:
            return self._tecla_original(evento)
        if menu.config_submodo == "controles":
            if evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                menu.config_submodo, menu.sub_anim = None, 0.0
            elif evento.key in (pygame.K_UP, pygame.K_DOWN):
                passo = 1 if evento.key == pygame.K_DOWN else -1
                menu.controle_selecao = (menu.controle_selecao + passo) % len(ACOES_CONTROLE)
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                menu.remapando = ACOES_CONTROLE[menu.controle_selecao]
            else:
                return True
            menu._som("navegar")
            return True
        if menu.config_submodo == "resolucao":
            if evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                menu.config_submodo, menu.sub_anim = None, 0.0
            elif evento.key in (pygame.K_UP, pygame.K_DOWN):
                passo = 1 if evento.key == pygame.K_DOWN else -1
                menu.resolucao_selecao = (menu.resolucao_selecao + passo) % len(RESOLUCOES)
                menu._rolar_resolucao(menu.resolucao_selecao)
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                menu._aplicar_resolucao(menu.resolucao_selecao)
            else:
                return True
            return True
        if menu.config_submodo == "ajuste":
            return menu._tecla_ajuste(evento)
        quantidade = len(menu._linhas_config())
        if evento.key in (pygame.K_UP, pygame.K_w):
            menu.config_selecao = (menu.config_selecao - 1) % quantidade
            menu._rolar_config(menu.config_selecao)
        elif evento.key in (pygame.K_DOWN, pygame.K_s):
            menu.config_selecao = (menu.config_selecao + 1) % quantidade
            menu._rolar_config(menu.config_selecao)
        elif evento.key == pygame.K_LEFT:
            menu._ajustar_config(-1)
            return True
        elif evento.key == pygame.K_RIGHT:
            menu._ajustar_config(1)
            return True
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._abrir_selecao()
            return True
        elif evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            menu._voltar_menu()
            return True
        else:
            return True
        menu._som("navegar")
        return True

    def _mover_original(self, passo: int, circular: bool = True) -> None:
        menu = self.menu
        grupo = CATEGORIAS_CONFIG[categoria_config(menu.config_selecao)][1]
        posicao = grupo.index(menu.config_selecao) + passo
        posicao = posicao % len(grupo) if circular else max(0, min(len(grupo) - 1, posicao))
        menu.config_selecao = grupo[posicao]
        menu._rolar_config(menu.config_selecao)
        menu._som("navegar")

    def _trocar_categoria(self, indice: int) -> None:
        self.menu.config_selecao = CATEGORIAS_CONFIG[indice % len(CATEGORIAS_CONFIG)][1][0]
        self.menu._rolar_config(self.menu.config_selecao)
        self.menu._som("navegar")

    def _ajustar_original(self, passo: int) -> None:
        self.menu._ajustar_config(1 if self.menu.config_selecao in (3, 10) else passo)

    def _salvar(self) -> None:
        sucesso = self.menu.jogo.config.salvar() is not False
        self.menu.notificacoes.adicionar(
            "Configurações salvas!" if sucesso else "Não foi possível salvar as configurações.",
            "sucesso" if sucesso else "erro")
        self.menu._som("equipar" if sucesso else "erro")

    def _tecla_original(self, evento: pygame.event.Event) -> bool:
        menu = self.menu
        if evento.key in (pygame.K_TAB, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
            passo = -1 if evento.key == pygame.K_PAGEUP or (
                evento.key == pygame.K_TAB and getattr(evento, "mod", 0) & pygame.KMOD_SHIFT) else 1
            self._trocar_categoria(categoria_config(menu.config_selecao) + passo)
        elif evento.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
            if evento.key == pygame.K_s and getattr(evento, "mod", 0) & pygame.KMOD_CTRL:
                self._salvar()
            else:
                self._mover_original(-1 if evento.key in (pygame.K_UP, pygame.K_w) else 1)
        elif evento.key in (pygame.K_LEFT, pygame.K_RIGHT):
            self._ajustar_original(-1 if evento.key == pygame.K_LEFT else 1)
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._abrir_selecao()
        elif evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            menu._voltar_menu()
        return True

    def tratar_ponteiro(self, evento: pygame.event.Event) -> bool:
        """Trata rolagem e prévia do arraste, aplicando o slider ao soltar."""
        menu = self.menu
        if menu.subestado != "CONFIG" or menu.config_submodo == "ajuste":
            self._arraste = None
            return False
        if evento.type == pygame.MOUSEWHEEL:
            self._arraste = None
            if menu.config_submodo in ("resolucao", "controles"):
                resolucao = menu.config_submodo == "resolucao"
                atributo = "resolucao_selecao" if resolucao else "controle_selecao"
                total = len(RESOLUCOES if resolucao else ACOES_CONTROLE)
                selecao = max(0, min(total - 1, getattr(menu, atributo) - evento.y))
                setattr(menu, atributo, selecao)
                if resolucao:
                    menu._rolar_resolucao(selecao)
                menu._som("navegar")
            else:
                self._mover_original(-evento.y, circular=False)
            return True
        if self._arraste is None:
            return False
        if evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
            if evento.type == pygame.MOUSEBUTTONUP and evento.button != 1:
                return False
            menu.mouse = menu._pos_logica(evento.pos)
            indice, _fracao = self._arraste
            self._arraste = (indice, menu._slider_fracao(menu.mouse[0]))
            if evento.type == pygame.MOUSEBUTTONUP:
                menu._aplicar_slider(*self._arraste)
                self._arraste = None
            return True
        return False

    def _abrir_selecao(self) -> None:
        """Abre ou ajusta o controle atualmente selecionado."""
        menu = self.menu
        if menu.config_selecao == 2:
            menu.config_submodo = "resolucao"
            menu.resolucao_selecao = menu._indice_resolucao_atual()
            menu.sub_anim = 0.0
        elif menu.config_selecao == 5:
            menu.config_submodo = "controles"
            menu.controle_selecao = 0
            menu.sub_anim = 0.0
        elif menu.config_selecao == 8:
            menu._abrir_ajuste_tela()
        elif menu.config_selecao == 9:
            menu._ciclar_qualidade_grafica()
        elif menu.config_selecao == 10:
            menu._toggle_monitor_desempenho()
        else:
            menu._ajustar_config(1)

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        """Trata os controles compartilhados nas coordenadas lógicas."""
        self._clique_original(pos)

    def _clique_original(self, pos: tuple[int, int]) -> None:
        menu = self.menu
        self._arraste = None
        if menu.remapando or menu.config_submodo == "ajuste":
            return
        if menu.config_submodo:
            self._clique_submodo_original(pos)
            return
        for indice, aba in enumerate(self.original.geometria().abas):
            if aba.collidepoint(pos):
                self._trocar_categoria(indice)
                return
        for indice, rect in self.original.linhas():
            if rect.collidepoint(pos):
                menu.config_selecao = indice
                tipo = menu._linhas_config()[indice][1]
                x0, x1 = self.original.trilha_slider()
                if menu._eh_slider_config(tipo):
                    if x0 - menu.layout.px(8) <= pos[0] <= x1 + menu.layout.px(8):
                        fracao = menu._slider_fracao(pos[0])
                        menu._aplicar_slider(indice, fracao)
                        self._arraste = (indice, fracao)
                elif pos[0] >= x0:
                    if tipo in ("resolucao", "controles", "ajuste"):
                        self._abrir_selecao()
                    else:
                        self._ajustar_original(-1 if pos[0] < x0 + menu.layout.px(24) else 1)
                return
        salvar, voltar = menu._botoes_rodape(["SALVAR", "VOLTAR"])
        if salvar.rect.collidepoint(pos):
            self._salvar()
        elif voltar.rect.collidepoint(pos):
            menu._voltar_menu()

    def _clique_submodo_original(self, pos: tuple[int, int]) -> None:
        menu = self.menu
        for indice, rect in self.original.linhas_submodo(menu.config_submodo):
            if rect.collidepoint(pos):
                if menu.config_submodo == "controles":
                    menu.controle_selecao, menu.remapando = indice, ACOES_CONTROLE[indice]
                    menu._som("navegar")
                else:
                    menu.resolucao_selecao = indice
                    menu._rolar_resolucao(indice)
                    menu._aplicar_resolucao(indice)
                return
        if menu._botoes_rodape(["VOLTAR"])[0].rect.collidepoint(pos):
            menu.config_submodo, menu.sub_anim = None, 0.0
            menu._som("navegar")

    def fracao_slider(self, indice: int) -> float:
        """Lê a posição do slider, incluindo a prévia de um arraste ativo."""
        if self._arraste is not None and self._arraste[0] == indice:
            return self._arraste[1]
        config = self.menu.jogo.config
        tipo = self.menu._linhas_config()[indice][1]
        if self.menu._eh_slider_shader(tipo):
            valor = self.menu._fracao_controle_shader(tipo)
        elif indice == 4:
            valor = config["sensibilidade"] - .5
        else:
            valor = config["musica_volume" if indice == 0 else "efeitos_volume"]
        return max(0.0, min(1.0, valor))

    def valor_opcao(self, indice: int) -> str:
        """Formata o valor e o estado efetivo de qualquer opção do catálogo."""
        menu, config = self.menu, self.menu.jogo.config
        tipo = menu._linhas_config()[indice][1]
        if menu._eh_slider_config(tipo):
            base = self.fracao_slider(indice)
            if indice == 4 or tipo == "saturacao_shader":
                base += .5
            return f"{round(base * 100)}%"
        valores = {
            "resolucao": config["resolucao"],
            "tema": config["tema"],
            "aspecto": "FUNDO NAS BORDAS" if config["aspecto"] == "PREENCHE" else "ÁREAS SEGURAS",
            "controles": "PERSONALIZAR",
            "ajuste": "CALIBRAR",
            "qualidade": config["qualidade_grafica"],
            "toggle": "LIGADO" if config["tela_cheia"] else "DESLIGADO",
            "desempenho": "LIGADO" if config["mostrar_desempenho"] else "DESLIGADO",
            "shader_comic": menu.jogo.status_shader_comic(),
            "tons_shader": f"{config['tons_shader']} TONS",
        }
        for chave in ("estilo_visual", "qualidade_comic",
                       "intensidade_flash", "intensidade_tremor"):
            valores[chave] = config[chave]
        for chave in ("hachuras_shader", "preservar_interface", "comic_papel", "comic_halftone",
                       "comic_hachuras", "line_boil", "mostrar_hitbox", "mira_ativa"):
            valores[chave] = "LIGADO" if config[chave] else "DESLIGADO"
        if config["qualidade_comic"] == "BAIXA":
            for chave in ("comic_papel", "comic_halftone", "comic_hachuras"):
                valores[chave] = "INATIVO (BAIXA)"
        if config["qualidade_comic"] != "ALTA":
            valores["line_boil"] = "INATIVO (ALTA)"
        return valores.get(tipo, "")

    def _desenhar_valor(
        self, tela, indice, tipo, y, dx, alfa, tema, controle_x, percentual_x,
    ) -> None:
        """Desenha o controle correspondente a uma linha de configuracao."""
        menu, layout = self.menu, self.menu.layout
        if menu._eh_slider_config(tipo):
            if menu._eh_slider_shader(tipo):
                valor = menu._fracao_controle_shader(tipo)
            elif indice == 4:
                valor = menu.jogo.config["sensibilidade"] - 0.5
            else:
                chave_volume = "musica_volume" if indice == 0 else "efeitos_volume"
                valor = menu.jogo.config[chave_volume]
            fracao = max(0.0, min(1.0, valor))
            menu._desenhar_slider(tela, y, fracao)
            base = 0.5 + fracao if (indice == 4 or
                                    tipo == "saturacao_shader") else fracao
            percentual = int(base * 100)
            texto = menu.fonte_media.render(
                f"{percentual}%", True, (170, 175, 220))
            menu._blit_alfa(
                tela, texto, texto.get_rect(midleft=(percentual_x + dx, y)),
                int(255 * alfa))
        elif tipo == "toggle":
            estado = menu.jogo.config["tela_cheia"]
            menu._desenhar_toggle(tela, controle_x + dx, y, estado)
            texto = menu.fonte_media.render(
                "LIGADO" if estado else "DESLIGADO", True,
                VERDE if estado else (160, 160, 190))
            posicao = (controle_x + layout.px(90) + dx, y)
            menu._blit_alfa(
                tela, texto, texto.get_rect(midleft=posicao), int(255 * alfa))
        else:
            valor = self.valor_opcao(indice)
            if tipo in ("controles", "ajuste"):
                valor += " >"
            cor = (tema["secundaria"] if tipo in ("resolucao", "qualidade")
                   else QUANTUM_CYAN if tipo in ("aspecto", "desempenho")
                   else (200, 150, 255))
            texto = menu.fonte_media.render(valor, True, cor)
            menu._blit_alfa(
                tela, texto, texto.get_rect(midleft=(controle_x + dx, y)),
                int(255 * alfa))
