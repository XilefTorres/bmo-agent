import os
import json
import queue
import sys
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import ollama
from modules.tts_speaker import speak

# --- CONFIGURACIÓN INICIAL ---
MODEL_PATH = "model"
VOSK_SAMPLE_RATE = 16000
WAKE_WORDS = ["vimos", "bmo", "vemos", "veamos", "demo"]

# Inicializar Oídos (Vosk)
if not os.path.exists(MODEL_PATH):
    print(f"Error: No se encuentra la carpeta '{MODEL_PATH}'.")
    sys.exit(1)

vosk_model = Model(MODEL_PATH)
audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))

def ask_ollama(prompt):
    try:
        response = ollama.chat(model='llama3:8b', messages=[
            {
                'role': 'system', 
                'content': 'Eres BMO de Hora de Aventura. Eres alegre, infantil, leal. Responde corto. No uses emojis.'
            },
            {'role': 'user', 'content': prompt},
        ])
        return response['message']['content']
    except Exception:
        return "Mi cerebro de robot tiene un error."

def main():
    with sd.RawInputStream(samplerate=VOSK_SAMPLE_RATE, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        
        recognizer = KaldiRecognizer(vosk_model, VOSK_SAMPLE_RATE)
        print("\n>>> BMO ACTIVADO. Di 'BMO'...")

        while True:
            data = audio_queue.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()

                # Solo actuamos si detectamos una palabra de activación
                if text and any(word in text for word in WAKE_WORDS):
                    
                    # Limpiar el prompt de palabras clave para el print y para Ollama
                    clean_prompt = text
                    for word in WAKE_WORDS:
                        clean_prompt = clean_prompt.replace(word, "")
                    clean_prompt = clean_prompt.strip()
                    
                    # --- NUEVO FORMATO DE PRINT ---
                    # Mostramos lo que tú dijiste (o solo tu nombre si fue solo el wake word)
                    user_display = clean_prompt if clean_prompt else "[Activación]"
                    print(f"\nXilef: {user_display}")
                    
                    if not clean_prompt:
                        speak("¿Dime, Xilef?")
                    else:
                        answer = ask_ollama(clean_prompt)
                        speak(answer)
                    
                    # Limpieza para la siguiente escucha
                    while not audio_queue.empty():
                        audio_queue.get()
                    
                    recognizer.Reset()
                    print("\n>>> BMO listo de nuevo...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBMO se va a dormir. ¡Adiós!")