import re
import threading
import time
from modules.tts_speaker import speak
from modules.base_command import BaseCommand

class AlarmCommand(BaseCommand):
    @property
    def keywords(self):
        return ["alarma", "despiértame", "recuérdame", "tiempo", "segundos", "minutos"]

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
            self.face.set_state("hablando")
            speak(f"¡BEEP BEEP! ¡Xilef! ¡Ya pasaron los {cantidad} {unidad}s! ¡Despierta!")
            print(f">>> ALARMA: Han pasado {cantidad} {unidad}s.")
            self.face.set_state("esperando")

        threading.Thread(target=alarm_timer, daemon=True).start()
        return True