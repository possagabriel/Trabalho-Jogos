"""Liga eventos de encontros ao avanço visual do cenário."""

from __future__ import annotations

import math
import weakref
from typing import Any

from src.core.event_bus import EventBus, GameEvent, GameEventType
from src.core.settings import VELOCIDADES_AVANCO_PADRAO
from src.runtime.domain.world.scroll import ModeloAvanco


def _ler(config: Any, chave: str, padrao: Any) -> Any:
    try:
        return config[chave]
    except (KeyError, TypeError):
        return padrao


def _numero(valor: Any, padrao: float, minimo: float, maximo: float) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return padrao
    return max(minimo, min(maximo, numero)) if math.isfinite(numero) else padrao


class ControladorAvanco:
    """Escuta eventos genéricos e controla somente a velocidade do fundo."""

    def __init__(self, jogo: Any) -> None:
        self._jogo = weakref.ref(jogo)
        self.config = jogo.config
        self.direcao = self._direcao()
        self.modelo = self._novo_modelo(1)
        self._retomada_pendente = False
        self._bus = EventBus()
        referencia = weakref.ref(self)
        bus = self._bus
        tipos = (GameEventType.BOSS_SPAWNED, GameEventType.BOSS_DEFEATED,
                 GameEventType.MINIBOSS_SPAWNED, GameEventType.MINIBOSS_DEFEATED,
                 GameEventType.MINIBOSS_REMOVED)

        def escutar(evento: GameEvent) -> None:
            controlador = referencia()
            if controlador is None:
                for tipo in tipos:
                    bus.unsubscribe(tipo, escutar)
            else:
                controlador._ao_evento(evento)

        self._escutar = escutar
        for tipo in tipos:
            self._bus.subscribe(tipo, escutar)

    def _direcao(self) -> tuple[float, float]:
        valor = _ler(self.config, "avanco_direcao", [0, 1])
        try:
            dx, dy = float(valor[0]), float(valor[1])
            if math.isfinite(dx) and math.isfinite(dy) and (dx or dy):
                return dx, dy
        except (IndexError, KeyError, TypeError, ValueError):
            pass
        return 0.0, 1.0

    def _velocidade(self, cenario_id: int) -> float:
        velocidades = _ler(self.config, "avanco_velocidades", {})
        padrao = VELOCIDADES_AVANCO_PADRAO[str(cenario_id)]
        valor = velocidades.get(str(cenario_id), padrao) if isinstance(velocidades, dict) \
            else padrao
        intensidade = _numero(_ler(self.config, "avanco_intensidade", 1), 1, 0, 2)
        return _numero(valor, padrao, 0, 500) * intensidade

    def _novo_modelo(self, cenario_id: int) -> ModeloAvanco:
        pico_ativo = bool(_ler(self.config, "avanco_pico", True))
        return ModeloAvanco(
            self._velocidade(cenario_id),
            freada=_numero(_ler(self.config, "avanco_freada_s", 1.5), 1.5, 0.1, 5),
            aceleracao=_numero(_ler(self.config, "avanco_aceleracao_s", 1.2), 1.2, 0.1, 5),
            pico=_numero(_ler(self.config, "avanco_pico_s", 0.3), 0.3, 0, 2)
            if pico_ativo else 0,
            intensidade_pico=_numero(
                _ler(self.config, "avanco_pico_intensidade", 0.25), 0.25, 0, 1),
        )

    def _configurar_cenario(self, cenario: Any) -> None:
        cenario.configurar_avanco(
            str(_ler(self.config, "avanco_qualidade", "MEDIA")),
            self.direcao, bool(_ler(self.config, "avanco_linhas", True)),
            bool(_ler(self.config, "avanco_camadas", True)),
        )

    def reiniciar(self, cenario: Any) -> None:
        """Recomeça na velocidade normal da primeira dimensão."""
        self.direcao = self._direcao()
        self.modelo = self._novo_modelo(cenario.id)
        self._retomada_pendente = False
        self._configurar_cenario(cenario)

    def trocar_dimensao(self, cenario: Any) -> None:
        """Conserva a aceleração vigente e aplica o impulso do salto."""
        self._configurar_cenario(cenario)
        self.modelo.trocar_dimensao(
            self._velocidade(cenario.id),
            duracao_salto=_numero(_ler(self.config, "avanco_salto_s", 1), 1, 0, 3),
            pico_salto=_numero(
                _ler(self.config, "avanco_salto_intensidade", 0.5), 0.5, 0, 2)
            if bool(_ler(self.config, "avanco_pico", True)) else 0.0,
        )

    def _ao_evento(self, evento: GameEvent) -> None:
        if evento.data.get("sessao") is not self._jogo():
            return
        tipo = evento.type
        if tipo is GameEventType.BOSS_SPAWNED:
            if bool(_ler(self.config, "avanco_parada_boss", True)):
                self.modelo.boss_entrou()
        elif tipo is GameEventType.BOSS_DEFEATED:
            jogo = self._jogo()
            narrativa = getattr(jogo, "cutscene_controller", None)
            if narrativa is not None and narrativa.tem_pos_boss(evento.data.get("cenario_id", 0)):
                self._retomada_pendente = True
            else:
                self.modelo.boss_derrotado()
        elif tipo is GameEventType.MINIBOSS_SPAWNED:
            mapa = _ler(self.config, "avanco_miniboss_tipos", {})
            chave = evento.data.get("chave", "")
            valor = mapa.get(chave) if isinstance(mapa, dict) else None
            padrao = _numero(_ler(self.config, "avanco_miniboss_percentual", 0.5),
                             0.5, 0, 1)
            self.modelo.miniboss_entrou(_numero(valor, padrao, 0, 1))
        elif tipo in (GameEventType.MINIBOSS_DEFEATED, GameEventType.MINIBOSS_REMOVED):
            self.modelo.miniboss_derrotado()

    def liberar_retomada(self) -> None:
        """Acelera após a última cena ligada à derrota do boss."""
        if self._retomada_pendente:
            self._retomada_pendente = False
            self.modelo.boss_derrotado()

    def atualizar(self, cenario: Any, dt: float) -> None:
        """Avança uma etapa fixa e aplica a velocidade ao cenário visível."""
        if self._retomada_pendente:
            narrativa = getattr(self._jogo(), "cutscene_controller", None)
            if narrativa is None or (not narrativa.ativo and not narrativa.fila):
                self.liberar_retomada()
        self.modelo.atualizar(dt)
        fundo = getattr(cenario, "parallax", None)
        if fundo is not None:
            fundo.atualizar(
                self.modelo.velocidade, self.modelo.velocidade_base, dt,
                self.modelo.estado,
                _numero(_ler(self.config, "avanco_desvio_parado", 0.04),
                        0.04, 0, 0.1),
                _numero(_ler(self.config, "avanco_linhas_intensidade", 1), 1, 0, 2),
            )
