import threading
from commands.game_mode import GameCommand
from commands.alarm import AlarmCommand
from commands.time import TimeCommand
from commands.metronome import MetronomeCommand
from commands.system_status import SystemStatusCommand

class BMOActions:
    def __init__(self, face, bmo_brain):
        self.face = face
        self.bmo_brain = bmo_brain
        self.modo_juego_activo = False
        self.activation_phrases = [
            "¡Hola, Xilef! ¿En qué puedo ayudarte?",
            "¡BMO presente! ¿Qué tienes en mente?",
            "¡Aquí estoy, Xilef! Mis circuitos están listos."
        ]
        
        # Instanciamos los comandos registrados
        self.commands = [
            GameCommand(face, bmo_brain),
            AlarmCommand(face, bmo_brain),
            TimeCommand(face, bmo_brain),
            MetronomeCommand(face, bmo_brain),
            SystemStatusCommand(face, bmo_brain)
        ]

    def dispatch(self, text):
        """Busca y ejecuta una acción basada en el texto"""
        text_lower = text.lower()
        for cmd in self.commands:
            if any(k in text_lower for k in cmd.keywords):
                if cmd.threaded:
                    threading.Thread(target=cmd.execute, args=(text, self), daemon=True).start()
                else:
                    cmd.execute(text, self)
                return True
        return False

    def handle_key(self, key):
        """Propaga el evento de teclado a todos los comandos"""
        for cmd in self.commands:
            cmd.handle_key(key)