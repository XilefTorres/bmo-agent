import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice
from pedalboard import Chorus, Clipping, Distortion, LadderFilter, LowpassFilter, Pedalboard, Bitcrush, HighpassFilter, Gain, PitchShift, Resample
import os
import threading
import time

# Rutas relativas para portabilidad total
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "piper", "es_MX-claude-high.onnx")

voice = None
_is_speaking = False
_speaking_count = 0

def is_speaking():
    """Indica si BMO está reproduciendo audio en este momento."""
    return _is_speaking

def get_speaking_count():
    """Devuelve un contador que aumenta cada vez que BMO empieza a hablar."""
    return _speaking_count

def load_voice():
    """Carga el modelo de Piper solo si no ha sido cargado antes."""
    global voice
    if voice is None:
        if os.path.exists(MODEL_PATH):
            voice = PiperVoice.load(MODEL_PATH)
        else:
            print(f"ERROR: No se encontró el modelo en: {MODEL_PATH}")

def speak(text):
    global _is_speaking, _speaking_count
    load_voice()
    if not text or voice is None:
        return

    try:
        _is_speaking = True
        _speaking_count += 1
        # 1. Configuración de frecuencia (Aceleramos un 30% para tono agudo)
        BMO_SAMPLE_RATE = voice.config.sample_rate
        
        all_audio_data = [chunk.audio_int16_bytes for chunk in voice.synthesize(text)]
        if not all_audio_data: return

        full_audio = b"".join(all_audio_data)
        
        # 2. Convertir a float32 entre -1.0 y 1.0 (Requerido para Pedalboard)
        audio_array = np.frombuffer(full_audio, dtype=np.int16).astype(np.float32) / 32768.0

        # 3. CADENA DE EFECTOS (EL MODULADOR)
        # Highpass: Quita bajos (sonido pequeño)
        # Lowpass: Quita agudos cristalinos (sonido viejo/opaco)
        # LadderFilter: Da esa resonancia de radio o juguete
        # Bitcrush: El "grano" rasposo que buscabas
        # Distortion: Simula que la bocina está "al límite"
        # Gain: Aumenta el volumen
        board = Pedalboard([
            PitchShift(semitones=5),
            HighpassFilter(cutoff_frequency_hz=5080),
            Bitcrush(bit_depth=20),
            Distortion(drive_db=10),
            LadderFilter(cutoff_hz=3500, resonance=0.6, drive=1.0),
            LowpassFilter(cutoff_frequency_hz=5000),
            Gain(gain_db=1.5)
        ])

        # Aplicamos efectos
        effected_audio = board(audio_array, BMO_SAMPLE_RATE)

        # 3. Vibrato Robótico mejorado
        t = np.arange(len(effected_audio)) / BMO_SAMPLE_RATE
        # Una oscilación un poco más errática suena más a "aparato viejo"
        vibrato = 1 + 0.07 * np.sin(2 * np.pi * 50 * t) 
        effected_audio *= vibrato

        # 4. Normalización para evitar que truene feo en Fedora
        if np.max(np.abs(effected_audio)) > 1.0:
            effected_audio = effected_audio / np.max(np.abs(effected_audio))
        # 5. Reproducción (con la boca de BMO sincronizada al volumen del audio)
        levels = _mouth_levels(effected_audio, BMO_SAMPLE_RATE)
        with _speak_lock:
            sd.play(effected_audio, samplerate=BMO_SAMPLE_RATE)
            _drive_mouth(levels)
            sd.wait()

    except Exception as e:
        print(f"Error en la salida de audio de BMO: {e}")
    finally:
<<<<<<< Updated upstream
        _is_speaking = False
=======
        _notify_mouth(None)


# ---------- Sincronización de la boca ----------
ENV_HOP = 0.04  # segundos por muestra de la envolvente (25 por segundo)
_speak_lock = threading.Lock()  # evita que dos frases suenen encima una de otra
_mouth_callback = None


def set_mouth_callback(callback):
    """La cara registra aquí su función: callback(nivel 0-3) mientras suena, callback(None) al terminar."""
    global _mouth_callback
    _mouth_callback = callback


def _notify_mouth(level):
    if _mouth_callback is not None:
        try:
            _mouth_callback(level)
        except Exception as e:
            print(f"Error actualizando la boca de BMO: {e}")


def _mouth_levels(audio, sample_rate):
    """Convierte el audio en una lista de niveles de apertura (0 cerrada ... 3 muy abierta)."""
    audio = np.asarray(audio).reshape(-1)
    hop = int(sample_rate * ENV_HOP)
    n = len(audio) // hop
    if n == 0:
        return []
    rms = np.sqrt((audio[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    loud = rms[rms > 0.1 * rms.max()]
    if loud.size == 0:
        return [0] * n
    ratio = rms / np.percentile(loud, 90)
    return np.digitize(ratio, [0.15, 0.45, 0.8]).tolist()


def _drive_mouth(levels):
    """Mientras suena el audio, avisa a la cara del nivel que toca en cada instante."""
    if not levels or _mouth_callback is None:
        return
    try:
        latency = float(sd.get_stream().latency)
    except Exception:
        latency = 0.0
    start = time.perf_counter()
    while True:
        i = int((time.perf_counter() - start - latency) / ENV_HOP)
        if i >= len(levels):
            break
        _notify_mouth(levels[max(i, 0)])
        time.sleep(0.01)
>>>>>>> Stashed changes
