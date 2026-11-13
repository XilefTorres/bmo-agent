"""Salida de audio única de BMO.

Todo lo que suena (voz, pitidos de alarma, tics del metrónomo) pasa por un solo OutputStream
que mezcla los sonidos activos. Así un tic del metrónomo ya no corta la voz, como pasaba
cuando cada módulo llamaba a sd.play (que solo admite un sonido global a la vez).
"""
import threading
import numpy as np
import sounddevice as sd
from modules import settings

SAMPLE_RATE = 44100  # frecuencia del mezclador; lo que llegue a otra frecuencia se remuestrea


class Sound:
    """Un sonido en reproducción. wait() bloquea hasta que termina (o lo detienen)."""

    def __init__(self, data, channel):
        self.data = data
        self.pos = 0
        self.channel = channel
        self.done = threading.Event()

    @property
    def duration(self):
        return len(self.data) / SAMPLE_RATE

    def wait(self):
        # Con margen: si el stream muriera, no dejamos el hilo colgado para siempre
        self.done.wait(self.duration + 3.0)
        self.done.set()


_sounds = []                          # sonidos activos (los lee el callback de audio)
_sounds_lock = threading.Lock()
_stream = None
_stream_lock = threading.Lock()
try:
    _volume = max(0.0, min(1.0, float(settings.get("volume", 1.0))))   # se recuerda entre reinicios
except (TypeError, ValueError):
    _volume = 1.0


def mix_into(out, sounds):
    """Suma en `out` (1D float32) el siguiente tramo de cada sonido. Devuelve los que ya terminaron."""
    frames = len(out)
    finished = []
    for sound in sounds:
        chunk = sound.data[sound.pos:sound.pos + frames]
        out[:len(chunk)] += chunk
        sound.pos += len(chunk)
        if sound.pos >= len(sound.data):
            finished.append(sound)
    np.clip(out, -1.0, 1.0, out=out)
    return finished


def _callback(outdata, frames, time_info, status):
    out = np.zeros(frames, dtype=np.float32)
    with _sounds_lock:
        for sound in mix_into(out, _sounds):
            _sounds.remove(sound)
            sound.done.set()
    outdata[:, 0] = out * _volume


def get_volume():
    return _volume


def set_volume(volume):
    """Volumen general de BMO, de 0.0 a 1.0 (afecta voz, alarmas y metrónomo)."""
    global _volume
    _volume = max(0.0, min(1.0, float(volume)))


def _ensure_stream():
    global _stream
    with _stream_lock:
        if _stream is None or not _stream.active:
            if _stream is not None:
                _stream.close()
            _stream = sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                                      latency="low", callback=_callback)
            _stream.start()


def resample(audio, sample_rate):
    """Lleva el audio a mono float32 a la frecuencia del mezclador (interpolación lineal)."""
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    if sample_rate == SAMPLE_RATE or len(audio) < 2:
        return audio
    n = int(round(len(audio) * SAMPLE_RATE / sample_rate))
    positions = np.linspace(0, len(audio) - 1, n)
    return np.interp(positions, np.arange(len(audio)), audio).astype(np.float32)


def play(audio, sample_rate=SAMPLE_RATE, channel="fx"):
    """Empieza a reproducir sin bloquear, mezclado con lo que ya suene. Devuelve un Sound."""
    sound = Sound(resample(audio, sample_rate), channel)
    if len(sound.data) == 0:
        sound.done.set()
        return sound
    try:
        _ensure_stream()
    except Exception:
        sound.done.set()
        raise
    with _sounds_lock:
        _sounds.append(sound)
    return sound


def stop(channel=None):
    """Detiene los sonidos de un canal ('voice', 'fx', 'metronome') o todos si channel es None."""
    with _sounds_lock:
        for sound in [s for s in _sounds if channel is None or s.channel == channel]:
            _sounds.remove(sound)
            sound.done.set()


def output_latency():
    """Segundos entre que se entrega el audio y que suena (para sincronizar la boca)."""
    stream = _stream
    try:
        return float(stream.latency) if stream is not None else 0.0
    except Exception:
        return 0.0


def release():
    """Cierra el dispositivo de audio (p. ej. para dejárselo a los juegos). Se reabre solo al sonar algo."""
    global _stream
    stop()
    with _stream_lock:
        if _stream is not None:
            try:
                _stream.close()
            finally:
                _stream = None
