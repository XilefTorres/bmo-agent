import speech_recognition as sr
import time
from modules.tts_speaker import is_speaking, get_speaking_count

class BMOListener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Configuraciones para mejorar la escucha
        self.recognizer.pause_threshold = 1.2  # Tiempo de silencio para considerar que terminaste de hablar
        self.recognizer.dynamic_energy_threshold = True 
        self.recognizer.energy_threshold = 300 # Umbral inicial
        
        print(">>> Calibrando micrófono... (No hables por 1 segundo)")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print(f">>> Calibración lista. Umbral de energía: {self.recognizer.energy_threshold}")

    def listen(self):
        """Escucha y devuelve el texto usando Google Speech Recognition (Gratis)"""
        while True:
            # Si BMO está hablando (por ejemplo desde una alarma o respuesta previa), esperamos
            if is_speaking():
                time.sleep(0.5)
                continue

            # Registramos el estado del contador antes de abrir el micrófono
            start_count = get_speaking_count()

            text = None
            try:
                # El micrófono solo queda abierto mientras se graba la frase
                with self.microphone as source:
                    print("\n[Escuchando...]")
                    # Escuchamos con un timeout para re-evaluar si BMO empezó a hablar periódicamente
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)

                # Si BMO empezó a hablar o terminó de hablar mientras el micrófono estaba abierto, descartamos el audio
                if get_speaking_count() != start_count or is_speaking():
                    continue

                # Convertimos audio a texto (Motor de Google gratuito)
                text = self.recognizer.recognize_google(audio, language="es-MX")
            except sr.WaitTimeoutError:
                continue # Reintenta el ciclo si no hubo sonido detectado
            except sr.UnknownValueError:
                continue # Hubo sonido pero no se entendió ninguna palabra
            except sr.RequestError:
                print("\n[!] Error de conexión con el servicio de voz.")
                time.sleep(2)
                continue
            except Exception as e:
                print(f"\n[!] Error inesperado: {e}")
                continue

            # El yield va fuera del 'with': el micrófono ya está cerrado mientras BMO procesa
            if text:
                print(f">>> BMO captó: \"{text}\"")
                yield text.lower()

    def reset(self):
        """Con esta tecnología no es necesario resetear manualmente los buffers."""
        pass