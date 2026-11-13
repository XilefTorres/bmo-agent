import numpy as np
from modules import audio
from piper.voice import PiperVoice
from pedalboard import Chorus, Clipping, Distortion, LadderFilter, LowpassFilter, Pedalboard, Bitcrush, HighpassFilter, Gain, PitchShift, Resample
import os
import queue
import threading
import time

# Rutas relativas para portabilidad total
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "piper", "es_MX-claude-high.onnx")

voice = None
_active_speakers = 0   # frases sonando o esperando turno (puede haber varias en cola)
_speaking_count = 0
_last_spoke_at = 0.0
_state_lock = threading.Lock()
_speak_lock = threading.Lock()  # evita que dos frases suenen encima una de otra
_interrupt_gen = 0   # sube cada vez que alguien calla a BMO

def is_speaking():
    """Indica si BMO está reproduciendo audio (o tiene audio en cola) en este momento."""
    return _active_speakers > 0

def last_spoke_at():
    """time.monotonic() de la última vez que BMO terminó de hablar."""
    return _last_spoke_at

def _begin_audio():
    global _active_speakers, _speaking_count
    with _state_lock:
        _active_speakers += 1
        _speaking_count += 1

def _end_audio():
    global _active_speakers, _last_spoke_at
    with _state_lock:
        _active_speakers -= 1
        _last_spoke_at = time.monotonic()

def stop_speaking():
    """Calla a BMO: corta la frase que suena y descarta las que estaban en cola."""
    global _interrupt_gen
    _interrupt_gen += 1
    audio.stop("voice")

def play_sound(sound, sample_rate):
    """Reproduce un efecto (pitidos de alarma...) respetando el turno de la voz, sin cortarla."""
    _begin_audio()
    try:
        with _speak_lock:
            audio.play(sound, sample_rate, channel="fx").wait()
    except Exception as e:
        print(f"Error reproduciendo sonido: {e}")
    finally:
        _end_audio()

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

def _synthesize(text):
    """Texto -> (audio con la voz de BMO, frecuencia, niveles de boca). No reproduce nada."""
    BMO_SAMPLE_RATE = voice.config.sample_rate

    all_audio_data = [chunk.audio_int16_bytes for chunk in voice.synthesize(text)]
    if not all_audio_data:
        return None

    full_audio = b"".join(all_audio_data)

    # Convertir a float32 entre -1.0 y 1.0 (Requerido para Pedalboard)
    audio_array = np.frombuffer(full_audio, dtype=np.int16).astype(np.float32) / 32768.0

    # CADENA DE EFECTOS (EL MODULADOR)
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

    # Vibrato Robótico mejorado
    t = np.arange(len(effected_audio)) / BMO_SAMPLE_RATE
    # Una oscilación un poco más errática suena más a "aparato viejo"
    vibrato = 1 + 0.07 * np.sin(2 * np.pi * 50 * t)
    effected_audio *= vibrato

    # Normalización para evitar que truene feo en Fedora
    if np.max(np.abs(effected_audio)) > 1.0:
        effected_audio = effected_audio / np.max(np.abs(effected_audio))

    return effected_audio, BMO_SAMPLE_RATE, _mouth_levels(effected_audio, BMO_SAMPLE_RATE)


def _play_clip(clip):
    """Reproduce un clip ya sintetizado moviendo la boca de BMO al volumen del audio."""
    effected_audio, sample_rate, levels = clip
    playing = audio.play(effected_audio, sample_rate, channel="voice")
    _drive_mouth(levels, playing)
    playing.wait()


def speak(text):
    """Dice una frase completa (bloquea hasta que termina de sonar)."""
    return speak_stream([text])


def speak_stream(sentences):
    """Dice las oraciones conforme van llegando (p. ej. de bmo_brain.ask_stream).

    Un hilo sintetiza la siguiente oración mientras suena la actual, así BMO empieza a hablar
    en cuanto tiene la primera en vez de esperar la respuesta completa. Devuelve el texto dicho.
    """
    load_voice()
    if voice is None:
        return ""

    gen = _interrupt_gen
    clips = queue.Queue(maxsize=2)   # no adelantamos trabajo de más por si callan a BMO
    spoken = []

    def interrupted():
        return gen != _interrupt_gen

    def producer():
        try:
            for sentence in sentences:
                if interrupted():
                    break
                sentence = (sentence or "").strip()
                if not sentence:
                    continue
                clip = _synthesize(sentence)
                if clip is None:
                    continue
                while not interrupted():
                    try:
                        clips.put((sentence, clip), timeout=0.2)
                        break
                    except queue.Full:
                        pass
        except Exception as e:
            print(f"Error preparando la voz de BMO: {e}")
        finally:
            # Cerrar el generador libera el candado del LLM si lo callaron a media respuesta
            if hasattr(sentences, "close"):
                sentences.close()
            while True:
                try:
                    clips.put(None, timeout=0.2)   # fin de la respuesta
                    break
                except queue.Full:
                    if interrupted():
                        try:
                            clips.get_nowait()
                        except queue.Empty:
                            pass

    _begin_audio()
    worker = threading.Thread(target=producer, daemon=True)
    worker.start()
    try:
        # El turno se toma una vez para toda la respuesta: nadie se cuela entre oraciones
        with _speak_lock:
            while True:
                item = clips.get()
                if item is None:
                    break
                if interrupted():
                    continue   # callaron a BMO: vaciamos lo que quede sin reproducirlo
                sentence, clip = item
                spoken.append(sentence)
                _play_clip(clip)
                _notify_mouth(0)   # boca cerrada mientras llega la siguiente oración
    except Exception as e:
        print(f"Error en la salida de audio de BMO: {e}")
    finally:
        _end_audio()
        _notify_mouth(None)
    return " ".join(spoken)


# ---------- Sincronización de la boca ----------
ENV_HOP = 0.04  # segundos por muestra de la envolvente (25 por segundo)
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


def _drive_mouth(levels, playing):
    """Mientras suena el audio, avisa a la cara del nivel que toca en cada instante."""
    if not levels or _mouth_callback is None:
        return
    latency = audio.output_latency()
    start = time.perf_counter()
    while True:
        i = int((time.perf_counter() - start - latency) / ENV_HOP)
        if i >= len(levels) or playing.done.is_set():
            break
        _notify_mouth(levels[max(i, 0)])
        time.sleep(0.01)
