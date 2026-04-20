from datetime import datetime
from modules.tts_speaker import speak
from modules.base_command import BaseCommand

class TimeCommand(BaseCommand):
    @property
    def keywords(self):
        return ["hora", "qué hora es", "momento"]

    def execute(self, text, actions_manager):
        ahora = datetime.now().strftime("%I:%M %p")
        frase = f"¡Claro! En mis circuitos internos son las {ahora}."
        print(f"BMO: {frase}")
        self.face.set_state("hablando")
        speak(frase)
        self.face.set_state("esperando")