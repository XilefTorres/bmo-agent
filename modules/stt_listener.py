import speech_recognition as sr

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
            with self.microphone as source:
                try:
                    print("\n[Escuchando...]")
                    # Escuchamos el audio
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=10)
                    
                    # Convertimos audio a texto (Motor de Google gratuito)
                    text = self.recognizer.recognize_google(audio, language="es-MX")
                    
                    if text:
                        print(f">>> BMO captó: \"{text}\"")
                        yield text.lower()
                        
                except sr.RequestError:
                    print("\n[!] Error de conexión con el servicio de voz.")
                    continue
                except Exception as e:
                    print(f"\n[!] Error inesperado: {e}")
                    continue

    def reset(self):
        """Con esta tecnología no es necesario resetear manualmente los buffers."""
        pass