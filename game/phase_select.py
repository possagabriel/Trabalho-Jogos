"""Modelo e tela de seleção de fases (INCARNATE)."""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Optional

import pygame

from src.infrastructure.graphics.comic_pipeline import posterizar
from src.infrastructure.graphics.comic_render import (
    desenhar_fundo,
    texto_tinta,
)
from src.infrastructure.graphics.comic_theme import (
    LARANJA,
    opcoes_atuais,
)
from src.runtime.domain.campaign_catalog import FASES_CAMPANHA, fases_liberadas
from src.runtime.infrastructure.graphics.menu_panels import (
    ACENTO_ORIGINAL,
    FUNDO_ORIGINAL,
    TEXTO_ATIVO_ORIGINAL,
    TEXTO_ORIGINAL,
    linhas_painel,
    painel_menu,
    texto_painel,
)

from .assets import carregar_imagem
from .layout import Layout

CUSTO_MELHORIA_LOBBY = 300


class PhaseStatus(str, Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    COMPLETED = "completed"


@dataclass(frozen=True)
class PhaseData:
    id: str
    nome: str
    background: str
    ordem: int
    requisito: Optional[str] = None


def load_phases(folder: str | Path) -> List[PhaseData]:
    """Lê JSONs individuais, ignora arquivos inválidos e ordena por ordem."""
    result = []
    for path in sorted(Path(folder).glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            result.append(PhaseData(data["phase_id"], data["display_name"],
                                    data["background"], int(data["order"]),
                                    data.get("unlocked_by")))
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            continue
    return sorted(result, key=lambda phase: phase.ordem)


def get_phase_status(phase_id: str, save_data: dict,
                     phases: Optional[Iterable[PhaseData]] = None) -> PhaseStatus:
    """Calcula o estado sem pygame, aceitando formatos de save antigos."""
    catalog = list(phases or [])
    completed = save_data.get("fases_concluidas")
    if completed is None:
        completed = save_data.get("progresso_campanha", {}).get("fases_concluidas", [])
    completed = set(completed or [])
    current = next((p for p in catalog if p.id == phase_id), None)
    if phase_id in completed or (current and current.ordem in completed):
        return PhaseStatus.COMPLETED
    if current is None:
        return PhaseStatus.LOCKED
    if current.ordem in fases_liberadas(save_data):
        return PhaseStatus.AVAILABLE
    req = current.requisito
    if req is None and current.ordem > 1:
        previous = next((p for p in catalog if p.ordem == current.ordem - 1), None)
        req = previous.id if previous else None
    req_completed = req in completed
    if not req_completed and req:
        req_data = next((p for p in catalog if p.id == req), None)
        req_completed = bool(req_data and req_data.ordem in completed)
    return PhaseStatus.AVAILABLE if req is None or req_completed else PhaseStatus.LOCKED


class PhaseSelectScreen:
    """Tela leve, compatível com o padrão de subestados do menu principal."""
    def __init__(self, jogo, phases: Optional[List[PhaseData]] = None,
                 layout: Optional[Layout] = None):
        self.jogo = jogo
        self.layout = layout or Layout()
        self.phases = phases or self._default_phases()
        self.selected = 0
        self.statuses = {}
        self.mouse = (0, 0)
        self._thumbs = {}
        self.ship_x, self.ship_y = 450, 570
        self.index_open = False
        self.shop_open = False
        self.phase_menu_open = False
        self.phase_menu_selection = 0
        self.interaction_phase = None
        self.nova_campanha_pendente = False
        self._fontes = {}
        self._thumbs_escaladas = {}
        self._overlays = {}
        self.refresh()

    def set_layout(self, layout):
        """Atualiza a geometria e invalida caches dependentes da resolucao."""
        if (self.layout.largura, self.layout.altura) == (layout.largura,
                                                         layout.altura):
            self.layout = layout
            return
        self.layout = layout
        self._fontes.clear()
        self._thumbs_escaladas.clear()
        self._overlays.clear()

    def _origem_design(self):
        escala = self.layout.escala
        return ((self.layout.largura - 900 * escala) / 2,
                (self.layout.altura - 700 * escala) / 2)

    def _ponto(self, x, y):
        ox, oy = self._origem_design()
        escala = self.layout.escala
        return int(round(ox + x * escala)), int(round(oy + y * escala))

    def _rect(self, x, y, largura, altura):
        px, py = self._ponto(x, y)
        escala = self.layout.escala
        return pygame.Rect(px, py, max(1, int(round(largura * escala))),
                           max(1, int(round(altura * escala))))

    def _fonte(self, chave, tamanho, titulo=False):
        cache_key = (chave, tamanho, titulo)
        if cache_key not in self._fontes:
            self._fontes[cache_key] = self.layout.fonte(tamanho, titulo=titulo)
        return self._fontes[cache_key]

    def _overlay(self, tamanho, cor):
        chave = (tamanho, cor)
        if chave not in self._overlays:
            superficie = pygame.Surface(tamanho, pygame.SRCALPHA)
            superficie.fill(cor)
            self._overlays[chave] = superficie
        return self._overlays[chave]

    def _texto(self, texto: str, tamanho: int, cor: tuple,
               fonte: pygame.font.Font) -> pygame.Surface:
        """Usa lettering de tinta no comic e preserva a fonte no Original."""
        if opcoes_atuais().ativo:
            return texto_tinta(texto, max(10, self.layout.px(tamanho)), cor)
        return fonte.render(texto, True, cor)

    def _painel(self, surface: pygame.Surface, rect: pygame.Rect,
                fundo: tuple, destaque: tuple, espessura: int = 2) -> None:
        """Desenha uma placa angular comic ou o painel legado equivalente."""
        if opcoes_atuais().ativo:
            placa = painel_menu(rect.size, fundo, destaque)
            surface.blit(placa, rect)
            return
        pygame.draw.rect(surface, fundo, rect, border_radius=10)
        pygame.draw.rect(surface, destaque, rect, espessura, border_radius=10)

    def _saldo_moedas(self) -> int:
        """Consulta a carteira viva usada pelo Hangar e pelas recompensas."""
        try:
            return max(0, int(self.jogo.loja.moedas))
        except (AttributeError, TypeError, ValueError):
            return 0

    @staticmethod
    def _formatar_moedas(valor: int) -> str:
        return f"{valor:,}".replace(",", ".")

    @staticmethod
    def _nivel_melhoria(melhorias: dict, chave: str) -> int:
        try:
            return max(0, int(melhorias.get(chave, 0)))
        except (AttributeError, TypeError, ValueError):
            return 0

    def _draw_wallet(self, surface: pygame.Surface,
                     small: pygame.font.Font) -> None:
        """Mantém o saldo visível no lobby usando a fonte de verdade da loja."""
        rect = self._rect(670, 20, 205, 48)
        self._painel(surface, rect, (24, 28, 48), LARANJA, 2)
        saldo = self._formatar_moedas(self._saldo_moedas())
        self._legenda(surface, f"OFICINA · {saldo} MOEDAS", rect, tamanho=17)

    def _default_phases(self):
        names = [(identificador, f"Fase {indice} — {nome}", fundo)
                 for indice, (identificador, nome, fundo) in enumerate(FASES_CAMPANHA, 1)]
        return [PhaseData(i, n, bg, k, None if k == 1 else names[k-2][0])
                for k, (i, n, bg) in enumerate(names, 1)]

    def refresh(self):
        save = self.jogo.progresso.jogador
        self.statuses = {p.id: get_phase_status(p.id, save, self.phases)
                         for p in self.phases}
        ultima = save.get("progresso_campanha", {}).get("fase_atual")
        if ultima:
            for i, phase in enumerate(self.phases):
                if phase.id == ultima or phase.ordem == ultima:
                    self.selected = i
                    break
        if self.statuses.get(self.phases[self.selected].id) == PhaseStatus.LOCKED:
            self.selected = next((i for i, p in enumerate(self.phases)
                                  if self.statuses[p.id] != PhaseStatus.LOCKED), 0)

    def iniciar_nova_campanha(self):
        """Prepara o lobby sem alterar o save antes da confirmacao."""
        self.nova_campanha_pendente = True
        self.selected = 0
        self.ship_x, self.ship_y = 450, 570
        self.phase_menu_open = False
        self.index_open = False
        self.shop_open = False
        self.interaction_phase = None
        self.statuses = {
            phase.id: (PhaseStatus.AVAILABLE if phase.ordem in fases_liberadas(
                self.jogo.progresso.jogador) else PhaseStatus.LOCKED)
            for phase in self.phases
        }

    def cancelar_nova_campanha(self):
        self.nova_campanha_pendente = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mudou = self.mouse != event.pos
            self.mouse = event.pos
            if mudou and not (self.phase_menu_open or self.index_open or self.shop_open):
                for indice in range(len(self.phases)):
                    if self.card_rect(indice).collidepoint(event.pos):
                        self.selected = indice
                        break
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.index_open:
                if self._index_back_rect().collidepoint(event.pos):
                    self.index_open = False
                    self.phase_menu_open = True
                return
            if self.phase_menu_open:
                for indice in range(3):
                    if self._option_rect(indice).collidepoint(event.pos):
                        self.phase_menu_selection = indice
                        self.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
                        break
                return
            if self._rect(670, 20, 205, 48).collidepoint(event.pos):
                self.shop_open = not self.shop_open
                return
            if self.shop_open:
                return
            if self._rect(25, 650, 180, 38).collidepoint(event.pos):
                self.jogo.menu._voltar_menu()
            elif self._play_rect().collidepoint(event.pos):
                self._abrir_opcoes()
            else:
                for indice in range(len(self.phases)):
                    if self.card_rect(indice).collidepoint(event.pos):
                        self.selected = indice
                        break
            return
        if event.type != pygame.KEYDOWN:
            return

        if self.index_open:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE,
                             pygame.K_RETURN, pygame.K_KP_ENTER):
                self.index_open = False
                self.phase_menu_open = True
            return

        if self.phase_menu_open:
            if event.key == pygame.K_TAB:
                passo = -1 if getattr(event, "mod", 0) & pygame.KMOD_SHIFT else 1
                self.phase_menu_selection = (self.phase_menu_selection + passo) % 3
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.phase_menu_selection = (self.phase_menu_selection - 1) % 3
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.phase_menu_selection = (self.phase_menu_selection + 1) % 3
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.phase_menu_open = False
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.phase_menu_selection == 0:
                    self.confirm()
                elif self.phase_menu_selection == 1:
                    self.phase_menu_open = False
                    self.index_open = True
                else:
                    self.phase_menu_open = False
            return

        if event.key == pygame.K_l:
            self.shop_open = not self.shop_open
            self.index_open = False
            return
        if self.shop_open and event.key in (pygame.K_1, pygame.K_2):
            indice = 0 if event.key == pygame.K_1 else 1
            if self._buy_upgrade(indice):
                nomes = ("Blindagem instalada!", "Motor aprimorado!")
                self.jogo.menu.notificacoes.adicionar(
                    nomes[indice], "sucesso")
                self.jogo.sons.tocar("comprar")
            else:
                self.jogo.menu.notificacoes.adicionar(
                    "Moedas insuficientes ou falha ao salvar.", "erro")
                self.jogo.sons.tocar("erro")
            return
        if self.shop_open:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.shop_open = False
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.jogo.menu._voltar_menu()
        elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s, pygame.K_TAB):
            passo = -1 if event.key in (pygame.K_UP, pygame.K_w) else 1
            if event.key == pygame.K_TAB and getattr(event, "mod", 0) & pygame.KMOD_SHIFT:
                passo = -1
            self.selected = (self.selected + passo) % len(self.phases)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._abrir_opcoes()

    def _abrir_opcoes(self) -> None:
        if self.statuses[self.phases[self.selected].id] != PhaseStatus.LOCKED:
            self.phase_menu_open = True
            self.phase_menu_selection = 0

    def update(self, keys) -> None:
        """Mantém a API do menu; a lista responde a eventos discretos de seleção."""

    def card_rect(self, index: int) -> pygame.Rect:
        """Retorna uma linha da lista lateral de capítulos."""
        passo = min(74, 390 // max(1, len(self.phases)))
        return self._rect(30, 145 + index * passo, 220, passo - 4)

    def _preview_rect(self) -> pygame.Rect:
        return self._rect(280, 130, 590, 370)

    def _play_rect(self) -> pygame.Rect:
        return self._rect(650, 548, 220, 44)

    def _option_rect(self, indice: int) -> pygame.Rect:
        return self._rect(313, 280 + indice * 66, 274, 48)

    def ship_position(self):
        return self._ponto(self.ship_x, self.ship_y)

    def confirm(self):
        phase = self.phases[self.selected]
        if self.statuses[phase.id] == PhaseStatus.LOCKED:
            return False
        campanha = self.jogo.progresso.jogador.setdefault("progresso_campanha", {})
        retomando = not self.nova_campanha_pendente and \
            campanha.get("fase_atual") == phase.id
        nivel_salvo = campanha.get("nivel_atual")
        if self.nova_campanha_pendente:
            self.jogo.progresso.resetar_fases()
            self.nova_campanha_pendente = False
            campanha = self.jogo.progresso.jogador.setdefault(
                "progresso_campanha", {})
        self.jogo._preparar_jogo()
        # Ao repetir uma fase, somente as armas já encontradas naquela fase
        # são restauradas; o inventário de outras fases não vaza para ela.
        nomes = campanha.get("indice_fases", {}).get(phase.id, {}).get("armas", [])
        from .weapons import ARMARIA
        self.jogo.jogador.armas_desbloqueadas = [0]
        for i, arma in enumerate(ARMARIA):
            if arma["nome"] in nomes and i not in self.jogo.jogador.armas_desbloqueadas:
                self.jogo.jogador.armas_desbloqueadas.append(i)
        # Cada protocolo ocupa um bloco de cinco níveis: entrada, três
        # sub-bosses e o boss principal no último nível do bloco.
        nivel_inicial = (phase.ordem - 1) * 5 + 1
        if retomando:
            try:
                nivel_inicial = int(nivel_salvo)
            except (TypeError, ValueError):
                nivel_inicial = (phase.ordem - 1) * 5 + 1
            # Um checkpoint de outra fase nao pode iniciar esta fase em um
            # nivel invalido, mesmo que o arquivo tenha sido editado.
            inicio, fim = (phase.ordem - 1) * 5 + 1, phase.ordem * 5
            nivel_inicial = max(inicio, min(fim, nivel_inicial))
        if nivel_inicial != 1:
            self.jogo._iniciar_nivel(nivel_inicial)
        campanha["fase_atual"] = phase.id
        campanha["nivel_atual"] = nivel_inicial
        self.jogo.progresso.salvar_arquivo()
        return True

    def _legenda(self, surface: pygame.Surface, texto: str, rect: pygame.Rect,
                 *, destaque: bool = False, tamanho: int = 20) -> None:
        fonte = self._fonte("legenda", tamanho)
        arte = texto_painel(fonte, texto,
                            TEXTO_ATIVO_ORIGINAL if destaque else TEXTO_ORIGINAL,
                            max(1, rect.w - self.layout.px(12)),
                            max(1, rect.h - self.layout.px(4)))
        surface.blit(arte, arte.get_rect(center=rect.center))

    def _draw_preview(self, surface: pygame.Surface) -> None:
        rect = self._preview_rect()
        phase = self.phases[self.selected]
        visual = opcoes_atuais()
        nome = phase.background.replace(".png", "-comic.png") if visual.ativo else phase.background
        chave = (nome, rect.size, visual.ativo, visual.hachuras)
        if chave not in self._thumbs_escaladas:
            if nome not in self._thumbs:
                if phase.background.startswith("procedural:"):
                    from src.runtime.domain.world.scenarios import Cenario
                    self._thumbs[nome] = Cenario(phase.ordem).fundo_estatico
                else:
                    self._thumbs[nome] = carregar_imagem(nome)
            imagem = self._thumbs[nome]
            comic_proprio = (visual.ativo and imagem is not None
                             and not phase.background.startswith("procedural:"))
            if imagem is None and visual.ativo:
                if phase.background not in self._thumbs:
                    self._thumbs[phase.background] = carregar_imagem(phase.background)
                imagem = self._thumbs[phase.background]
            if imagem is not None:
                escala = max(rect.w / imagem.get_width(), rect.h / imagem.get_height())
                arte = pygame.transform.smoothscale(imagem, (
                    max(rect.w, round(imagem.get_width() * escala)),
                    max(rect.h, round(imagem.get_height() * escala))))
                recorte = pygame.Rect(0, 0, *rect.size)
                recorte.center = arte.get_rect().center
                arte = arte.subsurface(recorte).copy()
                if visual.ativo and not comic_proprio:
                    arte = posterizar(arte, visual.hachuras)
                self._thumbs_escaladas[chave] = arte
        arte = self._thumbs_escaladas.get(chave)
        if arte is None:
            surface.blit(painel_menu(rect.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL), rect)
            self._legenda(surface, "PRÉVIA INDISPONÍVEL", rect)
        else:
            surface.blit(arte, rect)

    def _draw_comic_background(self, surface: pygame.Surface) -> None:
        nome = "fases/lobby-comic.png"
        chave = (nome, surface.get_size())
        if nome not in self._thumbs:
            self._thumbs[nome] = carregar_imagem(nome)
        imagem = self._thumbs[nome]
        if imagem is None:
            desenhar_fundo(surface, self.selected + 1)
            return
        if chave not in self._thumbs_escaladas:
            largura, altura = surface.get_size()
            escala = max(largura / imagem.get_width(), altura / imagem.get_height())
            arte = pygame.transform.smoothscale(imagem, (
                max(largura, round(imagem.get_width() * escala)),
                max(altura, round(imagem.get_height() * escala))))
            recorte = pygame.Rect(0, 0, largura, altura)
            recorte.center = arte.get_rect().center
            self._thumbs_escaladas[chave] = arte.subsurface(recorte).copy()
        surface.blit(self._thumbs_escaladas[chave], (0, 0))

    def draw(self, surface: pygame.Surface) -> None:
        """Apresenta uma lista curta e uma única prévia ampla, sem diagrama de rotas."""
        if opcoes_atuais().ativo:
            self._draw_comic_background(surface)
            surface.blit(self._overlay(surface.get_size(), (*FUNDO_ORIGINAL, 70)), (0, 0))
        else:
            surface.fill(FUNDO_ORIGINAL)
        font = self._fonte("normal", 27)
        small = self._fonte("pequena", 21)
        self._legenda(surface, "CAMPANHA", self._rect(30, 30, 280, 46), tamanho=34)
        self._draw_wallet(surface, small)
        self._legenda(surface, "ESCOLHA UMA FASE", self._rect(30, 104, 220, 25), tamanho=16)
        for indice, phase in enumerate(self.phases):
            rect = self.card_rect(indice)
            selecionado = indice == self.selected
            # Somente a seleção recebe preenchimento; os demais itens respiram no fundo.
            if selecionado:
                surface.blit(painel_menu(rect.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL,
                                         selecionado=True, botao=True, segmentado=False), rect)
            nome = phase.nome.split("—")[-1].strip().upper()
            self._legenda(surface, f"{phase.ordem:02d}  {nome}", pygame.Rect(
                rect.x, rect.y + self.layout.px(1), rect.w, self.layout.px(23)),
                destaque=selecionado, tamanho=17 if len(self.phases) > 5 else 20)
            estado = {
                PhaseStatus.LOCKED: "BLOQUEADA",
                PhaseStatus.AVAILABLE: "DISPONÍVEL",
                PhaseStatus.COMPLETED: "CONCLUÍDA",
            }[self.statuses[phase.id]]
            self._legenda(surface, estado, pygame.Rect(
                rect.x, rect.bottom - self.layout.px(17), rect.w, self.layout.px(16)),
                destaque=selecionado, tamanho=12)
        self._draw_preview(surface)
        phase = self.phases[self.selected]
        self._legenda(surface, f"CAPÍTULO {phase.ordem:02d} / {len(self.phases):02d}",
                      self._rect(280, 104, 590, 22), tamanho=16)
        concluidas = sum(estado == PhaseStatus.COMPLETED for estado in self.statuses.values())
        self._legenda(surface, f"CAMPANHA {concluidas}/{len(self.phases)}",
                      self._rect(30, 552, 220, 32), tamanho=17)
        self._legenda(surface, phase.nome.upper(), self._rect(280, 515, 590, 30), tamanho=26)
        bloqueada = self.statuses[phase.id] == PhaseStatus.LOCKED
        detalhe = "CONCLUA A FASE ANTERIOR" if bloqueada else "PRONTA PARA INICIAR"
        self._legenda(surface, detalhe, self._rect(280, 552, 350, 32), tamanho=17)
        botao = self._play_rect()
        surface.blit(painel_menu(botao.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL,
                                 selecionado=not bloqueada, botao=True, segmentado=False), botao)
        self._legenda(surface, "BLOQUEADA" if bloqueada else "ENTER  OPÇÕES", botao,
                      destaque=not bloqueada)
        self._legenda(surface, "↑↓ / TAB SELECIONAR · L OFICINA", self._rect(225, 650, 650, 38),
                      tamanho=17)
        voltar = self._rect(25, 650, 180, 38)
        surface.blit(painel_menu(voltar.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL,
                                 botao=True, segmentado=False), voltar)
        self._legenda(surface, "ESC  VOLTAR", voltar, tamanho=17)
        if self.phase_menu_open:
            self._draw_phase_menu(surface, font, small)
        if self.index_open:
            self._draw_index(surface, phase, font, small)
        if self.shop_open:
            self._draw_shop(surface, font, small)

    def _draw_phase_menu(self, surface, font, small):
        """Apresenta ações com uma descrição curta para a opção em foco."""
        surface.blit(self._overlay(surface.get_size(), (*FUNDO_ORIGINAL, 220)), (0, 0))
        panel = self._rect(245, 160, 410, 380)
        surface.blit(painel_menu(panel.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL), panel)
        phase = self.phases[self.selected]
        self._legenda(surface, "AÇÕES DA FASE", self._rect(265, 177, 370, 25), tamanho=16)
        self._legenda(surface, phase.nome.upper(), self._rect(265, 211, 370, 38), tamanho=24)
        for i, text in enumerate(("JOGAR FASE", "VER ÍNDICE", "VOLTAR AO LOBBY")):
            rect = self._option_rect(i)
            selected = i == self.phase_menu_selection
            surface.blit(painel_menu(rect.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL,
                                     selecionado=selected, botao=True, segmentado=False), rect)
            self._legenda(surface, text, rect, destaque=selected)
        descricao = ("Inicia ou retoma o checkpoint desta fase.",
                     "Consulte armas, chefes e itens encontrados.",
                     "Feche este painel e escolha outra fase.")[self.phase_menu_selection]
        self._legenda(surface, descricao, self._rect(262, 474, 376, 24), tamanho=15)
        self._legenda(surface, "TAB / ↑↓ ESCOLHER · ENTER CONFIRMAR · ESC FECHAR",
                      self._rect(260, 509, 380, 20), tamanho=13)

    def _index_back_rect(self) -> pygame.Rect:
        return self._rect(290, 573, 320, 36)

    def _draw_index(self, surface, phase, font, small):
        """Separa rótulos e conteúdo em cartões, com nomes extensos em duas linhas."""
        stats = self.jogo.progresso.jogador.get("progresso_campanha", {}).get(
            "indice_fases", {}).get(phase.id, {})
        surface.blit(self._overlay(surface.get_size(), (*FUNDO_ORIGINAL, 235)), (0, 0))
        panel = self._rect(105, 80, 690, 550)
        surface.blit(painel_menu(panel.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL), panel)
        self._legenda(surface, "ARQUIVO DA FASE", self._rect(135, 96, 630, 24), tamanho=16)
        self._legenda(surface, phase.nome.upper(), self._rect(135, 127, 630, 38), tamanho=25)
        armas, minibosses = stats.get("armas", []), stats.get("minibosses", [])
        rows = (("INIMIGOS ABATIDOS", str(stats.get("inimigos", 0))),
                ("MINICHEFES", ", ".join(minibosses) or "Nenhum registrado"),
                ("CHEFE PRINCIPAL", "Derrotado" if stats.get("boss") else "Não derrotado"),
                (f"ARMAS ENCONTRADAS · {len(armas)}/3", ", ".join(armas) or "Nenhuma encontrada"),
                ("ITENS COLETÁVEIS", f"{len(stats.get('itens', []))} / 3 encontrados"))
        for i, (label, value) in enumerate(rows):
            rect = self._rect(135, 180 + i * 76, 630, 68)
            surface.blit(painel_menu(rect.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL), rect)
            self._legenda(surface, label, pygame.Rect(rect.x, rect.y + self.layout.px(3),
                          rect.w, self.layout.px(20)), tamanho=14)
            fonte = self._fonte("indice", 18)
            linhas = linhas_painel(fonte, value, rect.w - self.layout.px(32))
            # A área do conteúdo permanece separada do rótulo mesmo com listas extensas.
            for linha, texto in enumerate(linhas[:2]):
                if linha == 1 and len(linhas) > 2:
                    texto += "…"
                self._legenda(surface, texto, pygame.Rect(
                    rect.x + self.layout.px(10), rect.y + self.layout.px(25 + linha * 19),
                    rect.w - self.layout.px(20), self.layout.px(20)), tamanho=18)
        botao = self._index_back_rect()
        surface.blit(painel_menu(botao.size, FUNDO_ORIGINAL, ACENTO_ORIGINAL,
                                 botao=True, segmentado=False), botao)
        self._legenda(surface, "ENTER / ESC  VOLTAR ÀS AÇÕES", botao, tamanho=16)

    def _draw_shop(self, surface, font, small):
        surface.blit(self._overlay(surface.get_size(), (0, 0, 0, 220)), (0, 0))
        panel = self._rect(150, 145, 600, 410)
        surface.blit(painel_menu(panel.size, (0, 0, 0), ACENTO_ORIGINAL), panel)

        def linha(rotulo: str, y: int, altura: int = 30) -> None:
            rect = self._rect(178, y, 544, altura)
            arte = texto_painel(font, rotulo, TEXTO_ORIGINAL, rect.w, rect.h)
            surface.blit(arte, arte.get_rect(center=rect.center))

        linha("OFICINA // LOJA DO LOBBY", 170, 38)
        saldo = self._formatar_moedas(self._saldo_moedas())
        linha(f"SALDO DISPONÍVEL: {saldo} MOEDAS", 218)
        melhorias = self.jogo.progresso.jogador.get("melhorias", {})
        for i, (nome, efeito, chave) in enumerate((
                ("BLINDAGEM", "+1 VIDA", "blindagem"),
                ("MOTOR", "+0.5 VELOCIDADE", "motor"))):
            y = 272 + i * 94
            rect = self._rect(174, y, 552, 82)
            surface.blit(painel_menu(rect.size, (0, 0, 0), ACENTO_ORIGINAL), rect)
            nivel = self._nivel_melhoria(melhorias, chave)
            linha(f"[{i + 1}] {nome} · NÍVEL {nivel} · {efeito}", y + 8)
            estado = ("DISPONÍVEL" if self._saldo_moedas() >= CUSTO_MELHORIA_LOBBY
                      else "SALDO INSUFICIENTE")
            linha(f"{CUSTO_MELHORIA_LOBBY} MOEDAS · {estado}", y + 43, 24)
        linha("1 / 2 COMPRAR · L FECHAR A LOJA", 486, 26)

    def _buy_upgrade(self, index: int) -> bool:
        """Compra uma melhoria sem permitir divergência entre loja e save."""
        if index not in (0, 1):
            return False
        saldo = self._saldo_moedas()
        if saldo < CUSTO_MELHORIA_LOBBY:
            return False

        jogo = self.jogo
        jog = jogo.progresso.jogador
        upgrades = jog.setdefault("melhorias", {})
        chave = "blindagem" if index == 0 else "motor"
        nivel_anterior = self._nivel_melhoria(upgrades, chave)
        saldo_anterior = jogo.loja.moedas
        upgrades[chave] = nivel_anterior + 1
        jogo.loja.moedas = saldo - CUSTO_MELHORIA_LOBBY
        jogo.progresso.sincronizar_loja(jogo.loja)
        if jogo.progresso.salvar_arquivo():
            return True

        upgrades[chave] = nivel_anterior
        jogo.loja.moedas = saldo_anterior
        jogo.progresso.sincronizar_loja(jogo.loja)
        return False
