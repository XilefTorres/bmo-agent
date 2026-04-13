import os
import json
import queue
import sys
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# Configuraciones base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "model")
SAMPLE_RATE = 16000

audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))

class BMOListener:
    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            print(f"ERROR: No se encuentra la carpeta de modelo en {MODEL_PATH}")
            sys.exit(1)
        
        self.model = Model(MODEL_PATH)
        # Opcional: Podríamos añadir gramática aquí para mejorar la precisión
        self.recognizer = KaldiRecognizer(self.model, SAMPLE_RATE)

    def listen(self):
        """Generador que escucha y devuelve el texto procesado."""
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype='int16',
                               channels=1, callback=audio_callback):
            while True:
                data = audio_queue.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").lower()
                    if text:
                        yield text

    def reset(self):
        """Limpia la cola y el reconocedor."""
        while not audio_queue.empty():
            audio_queue.get()
        self.recognizer.Reset()