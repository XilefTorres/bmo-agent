import re
import threading
import time
import pygame
from modules.tts_speaker import speak
from modules.base_command import BaseCommand
from modules.text_utils import normalize, parse_duration, format_duration

WORK_SECONDS = 25 * 60
BREAK_SECONDS = 5 * 60
LONG_BREAK_SECONDS = 15 * 60
CYCLES = 4   # pomodoros antes del descanso largo

# "para" solo cuenta como orden al inicio: "pomodoro para estudiar" NO lo detiene
STOP_RE = re.compile(
    r"(?<!\w)(?:cancela|cancelar|termina|terminar|deten|detente|quita|apaga|acaba|basta|stop)(?!\w)"
    r"|^\s*(?:para|ya para)(?!\w)"
)


class PomodoroCommand(BaseCommand):
    def __init__(self, face, bmo_brain):
        super().__init__(face, bmo_brain)
        self.is_running = False
        self.stop_event = threading.Event()
        self.phase = ""          # "Estudio" o "Descanso"
        self.phase_end = 0.0     # time.monotonic() en que termina la fase actual
        self.cycle = 0
        self._font = None

    @property
    def keywords(self):
        return ["pomodoro", "modo estudio", "modo de estudio", "sesión de estudio"]

    @property
    def threaded(self):
        return True

    def draw(self, screen):
        """Franja superior con la fase y el tiempo que falta."""
        if not self.is_running:
            return
        if self._font is None:
            self._font = pygame.font.SysFont("Arial", 22, bold=True)
        remaining = max(0, int(self.phase_end - time.monotonic()))
        strip = pygame.Surface((screen.get_width(), 36), pygame.SRCALPHA)
        strip.fill((0, 0, 0, 110))
        screen.blit(strip, (0, 0))
        label = f"{self.phase} {self.cycle}/{CYCLES}   {remaining // 60:02d}:{remaining % 60:02d}"
        screen.blit(self._font.render(label, True, (255, 255, 255)), (14, 6))

    def _wait_phase(self, name, seconds):
        """Espera una fase completa. Devuelve False si cancelaron el pomodoro."""
        self.phase = name
        self.phase_end = time.monotonic() + seconds
        return not self.stop_event.wait(seconds)

    def execute(self, text, actions_manager):
        norm = normalize(text)

        if STOP_RE.search(norm):
            if self.is_running:
                self.stop_event.set()
                speak("¡Pomodoro terminado! Estudiaste muy bien, Xilef.")
            else:
                speak("No hay ningún pomodoro corriendo, Xilef.")
            return True

        if self.is_running:
            remaining = max(0, int(self.phase_end - time.monotonic()))
            speak(f"Vas en {self.phase.lower()} {self.cycle} de {CYCLES}. Faltan {format_duration(remaining)}.")
            return True

        # "pomodoro de 50 minutos" cambia la duración del bloque de estudio
        parsed = parse_duration(text)
        work = parsed[0] if parsed else WORK_SECONDS

        self.stop_event.clear()
        self.is_running = True
        self.cycle = 1
        self.phase = "Estudio"
        self.phase_end = time.monotonic() + work
        self.face.overlays.append(self.draw)
        speak(f"¡Modo estudio activado! {format_duration(work)} de concentración. ¡Tú puedes, Xilef!")

        try:
            while True:
                if not self._wait_phase("Estudio", work):
                    break
                largo = self.cycle >= CYCLES
                descanso = LONG_BREAK_SECONDS if largo else BREAK_SECONDS
                self.face.show_expression("love", 4000)
                speak(f"¡Terminaste el pomodoro {self.cycle}! Descansa {format_duration(descanso)}.")
                if not self._wait_phase("Descanso", descanso):
                    break
                if largo:
                    self.face.show_expression("laughing", 4000)
                    speak("¡Completaste los cuatro pomodoros! Estoy muy orgulloso de ti, Xilef.")
                    break
                self.cycle += 1
                self.face.show_expression("surprised", 3000)
                speak(f"¡Se acabó el descanso! Empieza el pomodoro {self.cycle}.")
        finally:
            self.is_running = False
            if self.draw in self.face.overlays:
                self.face.overlays.remove(self.draw)
        return True
