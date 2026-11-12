"""Sons e musica gerados proceduralmente (sem arquivos externos)."""

import io
import math
import random
import struct
from functools import lru_cache

import pygame

SAMPLE_RATE = 22050


def _wav_bytes(samples):
    n = len(samples)
    out = bytearray(b"RIFF")
    out += struct.pack("<I", 36 + n * 2)
    out += b"WAVEfmt "
    out += struct.pack("<IHHIIHH", 16, 1, 1, SAMPLE_RATE, SAMPLE_RATE * 2, 2, 16)
    out += b"data"
    out += struct.pack("<I", n * 2)
    for s in samples:
        out += struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767))
    return bytes(out)


def _sweep(f_inicial, f_final, duracao, vol, onda="quadrada"):
    n = int(SAMPLE_RATE * duracao)
    fase = 0.0
    samples = []
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


def _tone(frequencia, duracao, vol, onda="seno"):
    n = int(SAMPLE_RATE * duracao)
    return [_onda_val(frequencia, i, onda) * vol * (1 - i / n)
            for i in range(n)]


def _onda_val(freq, i, onda):
    if onda == "seno":
        return math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
    if onda == "serra":
        return (freq * i / SAMPLE_RATE) % 1 * 2 - 1
    return 1.0 if math.sin(2 * math.pi * freq * i / SAMPLE_RATE) >= 0 else -1.0


def _ruido(duracao, vol):
    n = int(SAMPLE_RATE * duracao)
    return [random.uniform(-1, 1) * vol * (1 - i / n) for i in range(n)]


# Frequências, duração, modulação FM e número de pulsos: identidade de cada emissor.
_PERFIS_TIRO = {
    "padrao": (820, 260, 0.12, 1.4, 1),
    "laser": (2100, 650, 0.16, 0.4, 1),
    "duplo": (900, 380, 0.22, 1.8, 2),
    "plasma": (280, 65, 0.36, 4.5, 1),
    "metralhadora": (680, 140, 0.055, 3.0, 1),
    "espiral": (480, 1250, 0.32, 2.6, 3),
    "ion": (110, 720, 0.52, 5.0, 1),
    "gauss": (3200, 90, 0.20, 0.8, 1),
    "nova": (190, 35, 0.60, 6.0, 1),
}


@lru_cache(maxsize=9)
def _amostras_tiro(tipo: str) -> tuple[float, ...]:
    """Sintetiza emissores FM uma vez; pulsos múltiplos pertencem ao mesmo disparo."""
    inicio, fim, duracao, modulacao, pulsos = _PERFIS_TIRO[tipo]
    total = int(SAMPLE_RATE * duracao)
    fase = 0.0
    dados = []
    for i in range(total):
        progresso = i / total
        local = (progresso * pulsos) % 1
        ataque = min(1.0, local * duracao / pulsos / 0.005)
        envelope = ataque * (1 - local) ** 2
        frequencia = inicio * (fim / inicio) ** progresso
        fase += math.tau * frequencia / SAMPLE_RATE
        modulador = math.sin(fase * 1.97) * modulacao * 0.55 * (1 - local)
        sinal = 0.6 * math.sin(fase) + 0.4 * math.sin(fase + modulador)
        grave = math.sin(fase * 0.5) * 0.15
        dados.append((sinal + grave) * envelope * 0.11)
    return tuple(dados)


@lru_cache(maxsize=1)
def _amostras_impacto() -> tuple[float, ...]:
    """Impacto eletrônico abafado, com ataque suave e cauda curta."""
    total = int(SAMPLE_RATE * 0.11)
    dados = []
    fase = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        progresso = i / total
        fase += math.tau * (180 + 380 * math.exp(-t * 60)) / SAMPLE_RATE
        envelope = min(1.0, t / 0.003) * (1 - progresso) ** 3
        corpo = math.sin(fase) * 0.8
        textura = math.sin(fase * 2.41) * 0.2 * math.exp(-t * 40)
        dados.append((corpo + textura) * envelope * 0.12)
    return tuple(dados)


class Sons:
    """Gerencia emissores futuristas e música synthwave procedural."""

    def __init__(self):
        self.habilitado = True
        self._sons = {}
        try:
            pygame.mixer.init(SAMPLE_RATE, -16, 1, 512)
        except pygame.error:
            self.habilitado = False
            return
        self._criar_sons()
        self._criar_musica()

    def _novo_som(self, samples):
        try:
            return pygame.mixer.Sound(file=io.BytesIO(_wav_bytes(samples)))
        except pygame.error:
            return None

    def _criar_sons(self):
        for tipo in _PERFIS_TIRO:
            self._sons[f"tiro_{tipo}"] = self._novo_som(_amostras_tiro(tipo))
        self._sons["tiro"] = self._sons["tiro_padrao"]
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
        self._sons["acerto"] = self._novo_som(_amostras_impacto())
        self._sons["escudo"] = self._novo_som(
            _sweep(900, 220, 0.3, 0.4, "seno"))
        self._sons["arma"] = self._novo_som(
            _tone(520, 0.1, 0.3) + _tone(780, 0.16, 0.3) +
            _tone(1040, 0.2, 0.3))
        self._sons["nova"] = self._novo_som(
            _ruido(0.35, 0.5) + _sweep(1400, 300, 0.3, 0.35))
        self._sons["especial"] = self._novo_som(
            _sweep(180, 900, 0.5, 0.4, "serra") + _tone(1400, 0.4, 0.25))

    def _criar_musica(self):
        try:
            pygame.mixer.music.load(io.BytesIO(_wav_bytes(self._gerar_musica())))
            pygame.mixer.music.set_volume(0.22)
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    @staticmethod
    @lru_cache(maxsize=1)
    def _gerar_musica() -> tuple[float, ...]:
        """Loop synthwave: baixo pulsante, arpejos FM, pads e bateria eletrônica."""
        batida = 60 / 112
        total = int(32 * batida * SAMPLE_RATE)
        dados = []
        acordes = ((55, 65.406, 82.407), (43.654, 55, 65.406),
                   (65.406, 82.407, 98), (48.999, 61.735, 73.416))
        for i in range(total):
            t = i / SAMPLE_RATE
            pulso = t / batida
            acorde = acordes[int(pulso // 8) % 4]
            passo = int(pulso * 2)
            local = (pulso * 2) % 1
            nota = acorde[passo % 3] * (4 if passo % 4 else 8)
            arp = math.sin(math.tau * nota * t + 1.1 * math.sin(math.tau * nota * 2 * t))
            arp *= math.exp(-local * 6) * min(1, local * 90) * 0.10
            baixo = math.sin(math.tau * acorde[0] * t) * 0.15
            baixo *= (0.3 + 0.7 * math.sin(math.pi * (pulso % 1)) ** 2)
            pad = sum(math.sin(math.tau * f * 2 * t) for f in acorde) * 0.025
            tempo_kick = (pulso % 1) * batida
            kick = math.sin(math.tau * (45 * tempo_kick + 1.5 *
                                        (1 - math.exp(-tempo_kick * 45))))
            kick *= math.exp(-tempo_kick * 23) * 0.18
            # Ruído determinístico local, sem consumir o RNG da jogabilidade.
            ruido = math.sin(i * 12.9898) * 43758.5453
            ruido = (ruido % 1) * 2 - 1
            hat = ruido * math.exp(-local * 45) * min(1, local * 150) * 0.035
            snare = ruido * math.exp(-tempo_kick * 32) * 0.06 if int(pulso) % 2 else 0
            fade = min(1.0, t / 0.02, (total / SAMPLE_RATE - t) / 0.02)
            dados.append((baixo + pad + arp + kick + hat + snare) * fade)
        return tuple(dados)

    def tocar(self, nome):
        if not self.habilitado:
            return
        som = self._sons.get(nome)
        if som:
            try:
                som.play()
            except pygame.error:
                pass

    def set_volume_musica(self, volume):
        """Ajusta o volume da musica de fundo (0.0 a 1.0)."""
        if not self.habilitado:
            return
        try:
            pygame.mixer.music.set_volume(0.22 * max(0.0, min(1.0, volume)))
        except pygame.error:
            pass

    def set_volume_efeitos(self, volume):
        """Ajusta o volume de todos os efeitos sonoros (0.0 a 1.0)."""
        if not self.habilitado:
            return
        volume = max(0.0, min(1.0, volume))
        for som in self._sons.values():
            if som:
                try:
                    som.set_volume(volume)
                except pygame.error:
                    pass
    def pausar_musica(self) -> None:
        """Suspende a trilha durante uma cena."""
        if self.habilitado:
            try:
                pygame.mixer.music.pause()
            except pygame.error:
                pass

    def retomar_musica(self) -> None:
        """Retoma a trilha já carregada."""
        if self.habilitado:
            try:
                pygame.mixer.music.unpause()
            except pygame.error:
                pass
