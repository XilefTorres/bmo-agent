import speech_recognition as sr

class BMOListener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Configuraciones para mejorar la escucha
        self.recognizer.pause_threshold = 1.2  # Tiempo de silencio para considerar que terminaste de hablar
        self.recognizer.dynamic_energy_threshold = True # Se adapta al ruido de tu cuarto
        
        print(">>> Calibrando micrófono para el ruido ambiental...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def listen(self):
        """Escucha y devuelve el texto usando Google Speech Recognition (Gratis)"""
        while True:
            with self.microphone as source:
                try:
                    # Escuchamos el audio
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=10)
                    
                    # Convertimos audio a texto (Motor de Google gratuito)
                    text = self.recognizer.recognize_google(audio, language="es-MX")
                    
                    if text:
                        print(f"\nXilef: {text}")
                        yield text.lower()
                        
                except sr.UnknownValueError:
                    # Si no entendió nada (ruido), sigue escuchando en silencio
                    continue
                except sr.RequestError:
                    print("\n[!] Error de conexión con el servicio de voz.")
                    continue
                except Exception as e:
                    print(f"\n[!] Error inesperado: {e}")
                    continue

    def reset(self):
        """Con esta tecnología no es necesario resetear manualmente los buffers."""
        pass