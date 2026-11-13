from datetime import datetime
from modules.tts_speaker import speak
from modules.base_command import BaseCommand

class TimeCommand(BaseCommand):
    @property
    def keywords(self):
        # Frases completas: "hora" suelta chocaba con "ahora" y con "en una hora"
        return ["qué hora", "la hora", "hora es", "hora tienes"]

    def execute(self, text, actions_manager):
        ahora = datetime.now().strftime("%I:%M %p")
        frase = f"¡Claro! En mis circuitos internos son las {ahora}."
        print(f"BMO: {frase}")
        speak(frase)
