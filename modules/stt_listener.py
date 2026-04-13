import os
import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# Cargar el modelo que descargaste y renombraste a 'model'
if not os.path.exists("model"):
    print("Error: No se encuentra la carpeta 'model'. Descárgala de Vosk y ponla aquí.")
    exit(1)

model = Model("model")
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

def listen_locally():
    # Configuramos la entrada de audio (Fedora usa PipeWire/PulseAudio)
    device_info = sd.query_devices(None, 'input')
    samplerate = int(device_info['default_samplerate'])

    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        
        recognizer = KaldiRecognizer(model, samplerate)
        print(">>> BMO está escuchando (Vosk activo)...")

        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                if text:
                    return text