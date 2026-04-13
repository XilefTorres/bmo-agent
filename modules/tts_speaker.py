import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice
from pedalboard import Chorus, Clipping, Distortion, LadderFilter, LowpassFilter, Pedalboard, Bitcrush, HighpassFilter, Gain, PitchShift, Resample
import os

# Rutas relativas para portabilidad total
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "piper", "es_MX-claude-high.onnx")

voice = None

def load_voice():
    """Carga el modelo de Piper solo si no ha sido cargado antes."""
    global voice
    if voice is None:
        if os.path.exists(MODEL_PATH):
            voice = PiperVoice.load(MODEL_PATH)
        else:
            print(f"ERROR: No se encontró el modelo en: {MODEL_PATH}")

def speak(text):
    load_voice()
    if not text or voice is None:
        return

    print(f"\nBMO: {text}")

    try:
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
        # 5. Reproducción
        sd.play(effected_audio, samplerate=BMO_SAMPLE_RATE)
        sd.wait() 
        
    except Exception as e:
        print(f"Error en la salida de audio de BMO: {e}")