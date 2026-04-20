import re
import threading
import time
import numpy as np
import sounddevice as sd
from modules.tts_speaker import speak
from modules.base_command import BaseCommand

class AlarmCommand(BaseCommand):
    @property
    def keywords(self):
        return ["alarma", "despiértame", "recuérdame", "tiempo", "segundos", "minutos"]

    def _play_beep(self):
        """Genera un tono cuadrado estilo retro de 8 bits"""
        fs = 44100
        duration = 0.15
        t = np.linspace(0, duration, int(fs * duration), False)
        # Usamos sign(sin) para crear una onda cuadrada (sonido de consola vieja)
        beep = 0.2 * np.sign(np.sin(2 * np.pi * 1000 * t))
        sd.play(beep, fs)
        sd.wait()

    def execute(self, text, actions_manager):
        match = re.search(r"(\d+)\s*(segundo|minuto|hora)", text.lower())
        
        if not match:
            self.face.set_state("hablando")
            speak("¿Para cuándo quieres la alarma? No entendí bien el tiempo, Xilef.")
            return False

        cantidad = int(match.group(1))
        unidad = match.group(2)
        
        segundos = cantidad
        if "minuto" in unidad:
            segundos *= 60
        elif "hora" in unidad:
            segundos *= 3600
        
        self.face.set_state("hablando")
        speak(f"¡Entendido! Pondré mi reloj interno en {cantidad} {unidad}s. ¡Te avisaré!")
        self.face.set_state("esperando")

        def alarm_timer():
            time.sleep(segundos)
            # Alerta visual y sonora
            self.face.set_state("hablando")
            for _ in range(3):
                self._play_beep()
                time.sleep(0.1)
            
            speak(f"¡Xilef! ¡Ya pasaron los {cantidad} {unidad}s! ¡Despierta!")
            print(f">>> ALARMA: Han pasado {cantidad} {unidad}s.")
            self.face.set_state("esperando")

        threading.Thread(target=alarm_timer, daemon=True).start()
        return True