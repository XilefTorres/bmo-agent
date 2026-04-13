import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice
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
    """Convierte texto a voz con efecto infantil de BMO."""
    load_voice()
    if not text or voice is None:
        return

    print(f"BMO: {text}")

    try:
        # Hack de frecuencia para voz aguda (infantil)
        BMO_SAMPLE_RATE = int(voice.config.sample_rate * 1.25)
        
        # Generar audio y extraer los bytes específicos detectados
        all_audio_data = [chunk.audio_int16_bytes for chunk in voice.synthesize(text)]
        
        if not all_audio_data:
            return

        # Unir fragmentos y convertir a array de NumPy
        full_audio = b"".join(all_audio_data)
        audio_array = np.frombuffer(full_audio, dtype=np.int16)

        # Reproducción y bloqueo (para no interrumpirse a sí mismo)
        sd.play(audio_array, samplerate=BMO_SAMPLE_RATE)
        sd.wait() 
        
    except Exception as e:
        print(f"Error en la salida de audio de BMO: {e}")