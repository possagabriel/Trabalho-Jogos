"""Procedural sound generation and management (no external audio files).

All sound effects and background music are synthesised at runtime using
basic waveforms and noise, then converted to ``pygame.mixer.Sound`` objects.
The background music loops indefinitely.

Migrated from game/sounds.py -- the full ``Sons`` class with all procedural
generation logic.
"""

import io
import math
import random
import struct
from typing import Dict, Optional

import pygame

SAMPLE_RATE = 22050


# ---------------------------------------------------------------------------
# Low-level waveform generators
# ---------------------------------------------------------------------------

def _wav_bytes(samples) -> bytes:
    """Convert a list of float samples to raw WAV bytes."""
    n = len(samples)
    out = bytearray(b"RIFF")
    out += struct.pack("<I", 36 + n * 2)
    out += b"WAVEfmt "
    out += struct.pack("<IHHIIHH", 16, 1, 1, SAMPLE_RATE, SAMPLE_RATE * 2, 2, 16)
    out += b"data"
    out += struct.pack("<I", n * 2)
    for s in samples:
        out += struct.pack("<h", int(max(-32768, min(32767, s))))
    return bytes(out)


def _sweep(f_inicial: float, f_final: float, duracao: float,
           vol: float, onda: str = "quadrada") -> list:
    """Frequency sweep (glissando) with envelope decay."""
    n = int(SAMPLE_RATE * duracao)
    fase = 0.0
    samples: list = []
    for i in range(n):
        f = f_inicial + (f_final - f_inicial) * i / n
        fase += 2 * math.pi * f / SAMPLE_RATE
        if onda == "seno":
            v = math.sin(fase)
        elif onda == "serra":
            v = (fase / math.tau) % 1 * 2 - 1
        else:
            v = 1.0 if math.sin(fase) >= 0 else -1.0
        samples.append(v * vol * (1 - i / n))
    return samples


def _tone(frequencia: float, duracao: float, vol: float,
          onda: str = "seno") -> list:
    """Simple tone with envelope decay."""
    n = int(SAMPLE_RATE * duracao)
    return [_onda_val(frequencia, i, onda) * vol * (1 - i / n)
            for i in range(n)]


def _onda_val(freq: float, i: int, onda: str) -> float:
    """Sample a waveform at sample index *i*."""
    if onda == "seno":
        return math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
    if onda == "serra":
        return (freq * i / SAMPLE_RATE) % 1 * 2 - 1
    return 1.0 if math.sin(2 * math.pi * freq * i / SAMPLE_RATE) >= 0 else -1.0


def _ruido(duracao: float, vol: float) -> list:
    """White noise with envelope decay."""
    n = int(SAMPLE_RATE * duracao)
    return [random.uniform(-1, 1) * vol * (1 - i / n) for i in range(n)]


# ---------------------------------------------------------------------------
# Sound manager
# ---------------------------------------------------------------------------

class SoundManager:
    """Manages procedural sound effects and background music.

    Initialises the mixer and pre-generates all sound effects at startup.
    If the mixer cannot be initialised (e.g. no audio device), all ``tocar``
    calls become safe no-ops.
    """

    def __init__(self):
        self.habilitado: bool = True
        self._sons: Dict[str, Optional[pygame.mixer.Sound]] = {}
        try:
            pygame.mixer.init(SAMPLE_RATE, -16, 1, 512)
        except pygame.error:
            self.habilitado = False
            return
        self._criar_sons()
        self._criar_musica()

    def _novo_som(self, samples) -> Optional[pygame.mixer.Sound]:
        try:
            return pygame.mixer.Sound(buffer=_wav_bytes(samples))
        except pygame.error:
            return None

    # ------------------------------------------------------------------
    # Procedural sound effects
    # ------------------------------------------------------------------

    def _criar_sons(self) -> None:
        self._sons["tiro"] = self._novo_som(_sweep(950, 400, 0.09, 0.15))
        self._sons["explosao"] = self._novo_som(_ruido(0.3, 0.45))
        self._sons["dano"] = self._novo_som(_sweep(200, 70, 0.25, 0.45))
        self._sons["coleta"] = self._novo_som(
            _sweep(400, 950, 0.16, 0.3, "seno"))
        self._sons["boss"] = self._novo_som(_sweep(120, 60, 0.9, 0.4, "serra"))
        self._sons["nivel"] = self._novo_som(
            _tone(520, 0.12, 0.3) + _tone(780, 0.16, 0.3))
        self._sons["navegar"] = self._novo_som(_tone(600, 0.06, 0.2))
        self._sons["comprar"] = self._novo_som(
            _tone(660, 0.08, 0.3) + _tone(990, 0.14, 0.3))
        self._sons["equipar"] = self._novo_som(
            _tone(440, 0.06, 0.25) + _tone(660, 0.1, 0.25))
        self._sons["erro"] = self._novo_som(_sweep(220, 120, 0.2, 0.3))
        self._sons["carga"] = self._novo_som(_tone(1200, 0.05, 0.2))
        self._sons["transicao"] = self._novo_som(
            _sweep(300, 1400, 0.7, 0.3, "seno"))
        self._sons["gameover"] = self._novo_som(
            _sweep(400, 70, 1.0, 0.5, "seno"))
        self._sons["acerto"] = self._novo_som(_tone(2100, 0.05, 0.22))
        self._sons["escudo"] = self._novo_som(
            _sweep(900, 220, 0.3, 0.4, "seno"))
        self._sons["arma"] = self._novo_som(
            _tone(520, 0.1, 0.3) + _tone(780, 0.16, 0.3) +
            _tone(1040, 0.2, 0.3))
        self._sons["nova"] = self._novo_som(
            _ruido(0.35, 0.5) + _sweep(1400, 300, 0.3, 0.35))
        self._sons["especial"] = self._novo_som(
            _sweep(180, 900, 0.5, 0.4, "serra") + _tone(1400, 0.4, 0.25))

    # ------------------------------------------------------------------
    # Procedural background music
    # ------------------------------------------------------------------

    def _criar_musica(self) -> None:
        try:
            pygame.mixer.music.load(io.BytesIO(_wav_bytes(self._gerar_musica())))
            pygame.mixer.music.set_volume(0.22)
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    def _gerar_musica(self):
        """Generate a procedural chiptune-style loop (16 bars at 120 BPM)."""
        bpm = 120
        batida = 60 / bpm
        bloco = int(batida * SAMPLE_RATE)
        total = bloco * 16
        dados = [0.0] * total
        baixo = [110, 110, 130.8, 110, 87.3, 87.3, 98, 110,
                 110, 110, 130.8, 110, 98, 98, 87.3, 110]
        melodia = [220, 261.6, 329.6, 392, 329.6, 261.6, 220, 174.6,
                   220, 261.6, 329.6, 392, 440, 392, 329.6, 261.6]
        for b in range(16):
            for i in range(bloco):
                v_baixo = _onda_val(baixo[b], i, "quadrada") * 0.18
                v_mel = _onda_val(melodia[b], i, "seno") * 0.10
                dados[b * bloco + i] = v_baixo + v_mel
        pico = max(abs(x) for x in dados) or 1.0
        return [x / pico * 0.7 for x in dados]

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def tocar(self, nome: str) -> None:
        """Play a named sound effect (safe no-op if mixer unavailable)."""
        if not self.habilitado:
            return
        som = self._sons.get(nome)
        if som:
            try:
                som.play()
            except pygame.error:
                pass

    def set_volume_musica(self, volume: float) -> None:
        """Adjust background music volume (0.0 to 1.0)."""
        if not self.habilitado:
            return
        try:
            pygame.mixer.music.set_volume(0.22 * max(0.0, min(1.0, volume)))
        except pygame.error:
            pass

    def set_volume_efeitos(self, volume: float) -> None:
        """Adjust all sound effects volume (0.0 to 1.0)."""
        if not self.habilitado:
            return
        volume = max(0.0, min(1.0, volume))
        for som in self._sons.values():
            if som:
                try:
                    som.set_volume(volume)
                except pygame.error:
                    pass

    def parar_musica(self) -> None:
        """Stop the background music."""
        if not self.habilitado:
            return
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass

    def pausar_musica(self) -> None:
        """Pause the background music."""
        if not self.habilitado:
            return
        try:
            pygame.mixer.music.pause()
        except pygame.error:
            pass

    def retomar_musica(self) -> None:
        """Resume the background music."""
        if not self.habilitado:
            return
        try:
            pygame.mixer.music.unpause()
        except pygame.error:
            pass
