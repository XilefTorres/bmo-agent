import threading
import traceback
from commands.game_mode import GameCommand
from commands.alarm import AlarmCommand
from commands.time import TimeCommand
from commands.metronome import MetronomeCommand
from commands.system_status import SystemStatusCommand
from commands.nba_info import NBAInfoCommand
from commands.wiki_search import WikipediaCommand
from commands.price_search import PriceSearchCommand
from commands.weather import WeatherCommand
from commands.volume import VolumeCommand
from commands.pomodoro import PomodoroCommand

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
        
        # Comandos registrados, de más específico a más genérico:
        # el primero que coincide atiende la frase.
        self.commands = [
            PomodoroCommand(face, bmo_brain),
            MetronomeCommand(face, bmo_brain),
            VolumeCommand(face, bmo_brain),
            WeatherCommand(face, bmo_brain),
            PriceSearchCommand(face, bmo_brain),
            WikipediaCommand(face, bmo_brain),
            NBAInfoCommand(face, bmo_brain),
            AlarmCommand(face, bmo_brain),
            GameCommand(face, bmo_brain),
            TimeCommand(face, bmo_brain),
            SystemStatusCommand(face, bmo_brain)
        ]

    def _run(self, cmd, text):
        """Ejecuta un comando sin dejar que una excepción mate el hilo ni deje la cara atascada."""
        try:
            cmd.execute(text, self)
        except Exception:
            print(f"[!] Error en el comando {type(cmd).__name__}:")
            traceback.print_exc()
            if not self.modo_juego_activo:
                self.face.set_state("esperando")
            self.face.show_expression("error", 3000)

    def dispatch(self, text):
        """Busca y ejecuta una acción basada en el texto"""
        for cmd in self.commands:
            if cmd.matches(text):
                if cmd.threaded:
                    threading.Thread(target=self._run, args=(cmd, text), daemon=True).start()
                else:
                    self._run(cmd, text)
                return True
        return False

    def handle_key(self, key):
        """Propaga el evento de teclado a todos los comandos"""
        for cmd in self.commands:
            cmd.handle_key(key)
