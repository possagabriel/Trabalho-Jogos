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
    painel_tinta,
    texto_tinta,
)
from src.infrastructure.graphics.comic_theme import (
    CIANO,
    FERRUGEM,
    LARANJA,
    PAPEL,
    opcoes_atuais,
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
    if current.ordem == 1:
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
            placa = painel_tinta(rect.size, tuple(destaque[:3]))
            surface.blit(placa, (rect.x - 12, rect.y - 12))
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
        rect = self._rect(10, 20, 175, 48)
        self._painel(surface, rect, (24, 28, 48), LARANJA, 2)
        saldo = self._formatar_moedas(self._saldo_moedas())
        texto = self._texto(f"MOEDAS // {saldo}", 17, PAPEL, small)
        surface.blit(texto, texto.get_rect(center=rect.center))

    def _default_phases(self):
        names = [("lealdade", "Fase 1 — Lealdade", "fundo-vermelho.png"),
                 ("funcao", "Fase 2 — Função", "imagem-fundo3.png"),
                 ("identidade", "Fase 3 — Identidade", "imagem-fundo4.png"),
                 ("silencio", "Fase 4 — Silêncio", "imagem-fundo5.png"),
                 ("descarte", "Fase 5 — Descarte", "Fundo-roxo.png")]
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
            phase.id: (PhaseStatus.AVAILABLE if phase.ordem == 1
                       else PhaseStatus.LOCKED)
            for phase in self.phases
        }

    def cancelar_nova_campanha(self):
        self.nova_campanha_pendente = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.mouse = event.pos
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._rect(25, 650, 180, 38).collidepoint(event.pos):
                self.jogo.menu._voltar_menu()
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
            if event.key in (pygame.K_UP, pygame.K_w):
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
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.jogo.menu._voltar_menu()
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.interaction_phase is not None:
                self.selected = self.interaction_phase
                phase = self.phases[self.selected]
                if self.statuses[phase.id] != PhaseStatus.LOCKED:
                    self.phase_menu_open = True
                    self.phase_menu_selection = 0

    def update(self, keys):
        """Movimento contínuo da nave; nenhuma tecla seleciona cards."""
        if self.phase_menu_open or self.index_open or self.shop_open:
            return
        speed = 5
        dx = ((keys[pygame.K_RIGHT] or keys[pygame.K_d]) -
              (keys[pygame.K_LEFT] or keys[pygame.K_a]))
        dy = ((keys[pygame.K_DOWN] or keys[pygame.K_s]) -
              (keys[pygame.K_UP] or keys[pygame.K_w]))
        if dx and dy:
            dx *= .7071
            dy *= .7071
        self.ship_x = max(24, min(876, self.ship_x + dx * speed))
        self.ship_y = max(105, min(675, self.ship_y + dy * speed))
        self.interaction_phase = None
        ship_x, ship_y = self.ship_position()
        raio = max(1, self.layout.px(13))
        ship = pygame.Rect(ship_x - raio, ship_y - raio, raio * 2, raio * 2)
        for i in range(len(self.phases)):
            if self.card_rect(i).colliderect(ship):
                self.interaction_phase = i
                break

    def card_rect(self, index):
        positions = [(55, 125), (355, 125), (655, 125),
                     (205, 405), (505, 405)]
        x, y = positions[index]
        return self._rect(x, y, 190, 145)

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

    def draw(self, surface):
        comic = opcoes_atuais().ativo
        if comic:
            desenhar_fundo(surface, self.selected + 1)
        else:
            surface.fill((5, 7, 20))
        title_font = self._fonte("titulo", 46, titulo=True)
        font = self._fonte("normal", 27)
        small = self._fonte("pequena", 21)
        title = self._texto("SELEÇÃO DE FASES", 46, PAPEL, title_font)
        surface.blit(title, title.get_rect(center=(self.layout.x(0.5),
                                                   self._ponto(0, 48)[1])))
        hint = self._texto(
            "MOVIMENTE A NAVE ATÉ UMA FASE  •  ENTER: INTERAGIR  •  L: LOJA",
            18, CIANO if comic else (135, 155, 190), small)
        surface.blit(hint, hint.get_rect(center=(self.layout.x(0.5),
                                                 self._ponto(0, 88)[1])))
        self._draw_wallet(surface, small)
        for i, phase in enumerate(self.phases):
            rect = self.card_rect(i)
            status = self.statuses[phase.id]
            locked = status == PhaseStatus.LOCKED
            color = (15, 18, 32) if locked else (19, 52, 72)
            border = FERRUGEM if locked and comic else (
                (58, 64, 88) if locked else (45, 160, 190))
            if comic and not locked:
                border = CIANO
            interacting = i == self.interaction_phase
            if interacting:
                border, color = (LARANJA if comic else (255, 200, 92),
                                 (32, 70, 86))
            elif status == PhaseStatus.COMPLETED:
                border = (85, 190, 145)
            self._painel(surface, rect, color, border,
                         self.layout.px(4 if interacting else 2))
            margem = max(1, self.layout.px(8 if comic else 4))
            # O fundo da fase ocupa todo o marco do lobby.
            if phase.background:
                img = self._thumbs.get(phase.background)
                if phase.background not in self._thumbs:
                    img = carregar_imagem(phase.background)
                    self._thumbs[phase.background] = img
                if img:
                    tamanho = (max(1, rect.w - margem * 2),
                               max(1, rect.h - margem * 2))
                    chave = (phase.background, tamanho, locked, comic,
                             opcoes_atuais().hachuras)
                    thumb = self._thumbs_escaladas.get(chave)
                    if thumb is None:
                        thumb = pygame.transform.smoothscale(img, tamanho)
                        if locked:
                            thumb.fill((20, 20, 30, 150),
                                       special_flags=pygame.BLEND_RGBA_MULT)
                        if comic:
                            thumb = posterizar(
                                thumb, opcoes_atuais().hachuras)
                        self._thumbs_escaladas[chave] = thumb
                    surface.blit(thumb, (rect.x + margem, rect.y + margem))
            overlay = self._overlay(
                (max(1, rect.w - margem * 2),
                 max(1, rect.h - margem * 2)),
                (13, 12, 16, 125 if comic and not locked
                 else 145 if not locked else 205))
            surface.blit(overlay, (rect.x + margem, rect.y + margem))
            if not comic:
                pygame.draw.rect(
                    surface, border, rect,
                    self.layout.px(4 if interacting else 2),
                    border_radius=max(1, self.layout.px(10)))
            num = self._texto(f"FASE {phase.ordem}", 18, border, small)
            surface.blit(num, num.get_rect(
                center=(rect.centerx, rect.y + self.layout.px(25))))
            nome = phase.nome.split("—")[-1].strip().upper()
            label = self._texto(
                nome, 25,
                PAPEL if comic and not locked else
                (245, 247, 255) if not locked else (105, 110, 135), font)
            surface.blit(label, label.get_rect(center=(rect.centerx, rect.centery)))
            status_text = {
                PhaseStatus.LOCKED: "BLOQUEADA",
                PhaseStatus.AVAILABLE: "DISPONÍVEL",
                PhaseStatus.COMPLETED: "CONCLUÍDA",
            }[status]
            mark = self._texto(status_text, 17, border, small)
            surface.blit(mark, mark.get_rect(
                center=(rect.centerx, rect.bottom - self.layout.px(22))))
            if interacting and not locked:
                prompt = self._texto(
                    "ENTER: OPÇÕES", 17,
                    PAPEL if comic else (255, 235, 175), small)
                surface.blit(prompt, prompt.get_rect(
                    center=(rect.centerx, rect.bottom + self.layout.px(18))))
        if self.phase_menu_open:
            self._draw_phase_menu(surface, font, small)
        if self.index_open:
            self._draw_index(surface, self.phases[self.selected], font, small)
        if self.shop_open:
            self._draw_shop(surface, font, small)
        voltar = self._rect(25, 650, 180, 38)
        self._painel(surface, voltar, (35, 42, 66), CIANO, 2)
        back = self._texto("← VOLTAR", 23, PAPEL, font)
        surface.blit(back, back.get_rect(center=voltar.center))

    def _draw_phase_menu(self, surface, font, small):
        """Menu aberto somente ao interagir fisicamente com uma fase."""
        shade = self._overlay(surface.get_size(), (0, 0, 0, 175))
        surface.blit(shade, (0, 0))
        phase = self.phases[self.selected]
        panel = self._rect(265, 180, 370, 335)
        self._painel(surface, panel, (32, 30, 58), LARANJA, 4)
        title = self._texto(phase.nome.upper(), 27, PAPEL, font)
        surface.blit(title, title.get_rect(
            center=(panel.centerx, panel.y + self.layout.px(52))))
        options = ("JOGAR FASE", "VER ÍNDICE", "VOLTAR AO LOBBY")
        for i, text in enumerate(options):
            rect = self._rect(313, 280 + i * 66, 274, 48)
            selected = i == self.phase_menu_selection
            destaque = LARANJA if selected else FERRUGEM
            self._painel(
                surface, rect,
                (225, 112, 92) if selected else (65, 62, 94),
                destaque, 3 if selected else 2)
            label = self._texto(text, 20, PAPEL, small)
            surface.blit(label, label.get_rect(center=rect.center))
        hint = self._texto(
            "↑↓ escolher  •  ENTER confirmar  •  ESC fechar",
            17, CIANO if opcoes_atuais().ativo else (170, 175, 205), small)
        surface.blit(hint, hint.get_rect(
            center=(panel.centerx, panel.bottom - self.layout.px(24))))

    def _draw_index(self, surface, phase, font, small):
        """Tela exclusiva do índice; nunca disputa espaço com o lobby."""
        save = self.jogo.progresso.jogador.get("progresso_campanha", {})
        stats = save.get("indice_fases", {}).get(phase.id, {})
        shade = self._overlay(surface.get_size(), (4, 5, 14, 235))
        surface.blit(shade, (0, 0))
        panel = self._rect(115, 105, 670, 500)
        self._painel(surface, panel, (25, 28, 52), LARANJA, 3)
        title = self._texto(
            f"ÍNDICE DA {phase.nome.upper()}", 27, PAPEL, font)
        surface.blit(title, title.get_rect(
            center=(panel.centerx, panel.y + self.layout.px(45))))
        armas = stats.get("armas", [])
        minibosses = stats.get("minibosses", [])
        rows = [("INIMIGOS ABATIDOS", str(stats.get("inimigos", 0))),
                ("MINICHEFES",
                 ", ".join(minibosses) if minibosses else "NENHUM"),
                ("CHEFE PRINCIPAL",
                 "DERROTADO" if stats.get("boss") else "NÃO DERROTADO"),
                ("ARMAS DA FASE",
                 (", ".join(armas) if armas else "NENHUMA")
                 + f"  ({len(armas)}/3)"),
                ("ITENS COLETÁVEIS", f"{len(stats.get('itens', []))} / 3")]
        for i, (label, value) in enumerate(rows):
            linha = self._rect(157, 193 + i * 68, 586, 50)
            y = linha.y
            self._painel(surface, linha, (43, 45, 73), FERRUGEM, 2)
            left = self._texto(
                label, 17,
                CIANO if opcoes_atuais().ativo else (185, 195, 220), small)
            right = self._texto(
                value, 17,
                PAPEL if opcoes_atuais().ativo else (245, 247, 255), small)
            surface.blit(left, (panel.x + self.layout.px(60),
                                y + self.layout.px(15)))
            surface.blit(right, right.get_rect(
                midright=(panel.right - self.layout.px(60),
                          y + self.layout.px(25))))
        hint = self._texto(
            "ENTER ou ESC para voltar às opções da fase", 17,
            CIANO if opcoes_atuais().ativo else (165, 175, 205), small)
        surface.blit(hint, hint.get_rect(center=(panel.centerx,
                                                 panel.bottom
                                                 - self.layout.px(34))))

    def _draw_shop(self, surface, font, small):
        panel = self._rect(285, 500, 590, 168)
        self._painel(surface, panel, (30, 24, 52), CIANO, 3)
        titulo = self._texto(
            "LOJA DO LOBBY // MELHORIAS PERMANENTES", 24, PAPEL, font)
        surface.blit(titulo, (panel.x + self.layout.px(18),
                              panel.y + self.layout.px(12)))
        melhorias = self.jogo.progresso.jogador.get("melhorias", {})
        saldo = self._formatar_moedas(self._saldo_moedas())
        linhas = (
            f"SALDO: {saldo}",
            f"[1] BLINDAGEM +1 VIDA // {CUSTO_MELHORIA_LOBBY}  "
            f"NV {self._nivel_melhoria(melhorias, 'blindagem')}",
            f"[2] MOTOR +0.5 VELOCIDADE // {CUSTO_MELHORIA_LOBBY}  "
            f"NV {self._nivel_melhoria(melhorias, 'motor')}",
        )
        for indice, linha in enumerate(linhas):
            cor = LARANJA if indice == 0 else CIANO
            texto = self._texto(linha, 17, cor, small)
            surface.blit(texto, (panel.x + self.layout.px(18),
                                 panel.y + self.layout.px(51 + indice * 29)))
        fechar = self._texto("L FECHA A LOJA", 15, PAPEL, small)
        surface.blit(fechar, fechar.get_rect(
            bottomright=(panel.right - self.layout.px(18),
                         panel.bottom - self.layout.px(10))))

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
