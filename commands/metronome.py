import re
import threading
import time
import numpy as np
import pygame
from modules import audio
from modules.tts_speaker import speak
from modules.base_command import BaseCommand
from modules.text_utils import normalize

TICK_FS = audio.SAMPLE_RATE

# Órdenes de parar. "para" solo cuenta como orden al inicio de la frase o seguido del metrónomo:
# "pon un metrónomo para practicar a 100" NO es una orden de parar.
STOP_RE = re.compile(
    r"(?<!\w)(?:deten|detente|stop|apaga|quita|basta)(?!\w)"
    r"|^\s*(?:para|parale|ya para)(?!\w)"
    r"|(?<!\w)parar?\s+(?:ya\s+)?(?:el|ese|tu|con el)\s+(?:metronomo|ritmo|compas)"
)


def is_stop_request(text):
    return STOP_RE.search(normalize(text)) is not None


class MetronomeCommand(BaseCommand):
    def __init__(self, face, bmo_brain):
        super().__init__(face, bmo_brain)
        self.is_running = False
        self.stop_event = threading.Event()
        self.bpm = 120
        self.beats_per_bar = 4
        self.current_beat = 0
        self._font = None

    @property
    def keywords(self):
        return ["metrónomo", "ritmo", "compás"]

    @property
    def threaded(self):
        return True

    def handle_key(self, key):
        """Ajusta el BPM en tiempo real con el teclado"""
        if not self.is_running:
            return

        if key in [pygame.K_UP, pygame.K_w]:
            self.bpm = min(self.bpm + 5, 250)
            print(f">>> BPM ajustado: {self.bpm}")
        elif key in [pygame.K_DOWN, pygame.K_s]:
            self.bpm = max(self.bpm - 5, 40)
            print(f">>> BPM ajustado: {self.bpm}")
        elif key in [pygame.K_RIGHT, pygame.K_d]:
            self.beats_per_bar = min(self.beats_per_bar + 1, 8)
            print(f">>> Compás: {self.beats_per_bar}/4")
        elif key in [pygame.K_LEFT, pygame.K_a]:
            self.beats_per_bar = max(self.beats_per_bar - 1, 1)
            print(f">>> Compás: {self.beats_per_bar}/4")

    def draw(self, screen):
        """Dibuja la interfaz visual del metrónomo sobre la cara de BMO"""
        if not self.is_running:
            return

        # La fuente se crea una sola vez (antes se creaba en cada fotograma)
        if self._font is None:
            self._font = pygame.font.SysFont("Arial", 24, bold=True)
        font = self._font

        # Dibujar fondo semitransparente para el texto
        overlay = pygame.Surface((480, 60), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 260))

        # Texto de info
        info_text = font.render(f"BPM: {self.bpm}  |  Compás: {self.beats_per_bar}/4", True, (255, 255, 255))
        screen.blit(info_text, (20, 275))

        # Dibujar los puntos del compás
        start_x = 320
        for i in range(self.beats_per_bar):
            color = (255, 255, 255) # Blanco por defecto
            radius = 8

            # Si es el beat actual, resaltarlo
            if i == self.current_beat:
                color = (255, 200, 0) if i == 0 else (0, 255, 100) # Amarillo el acento, verde el resto
                radius = 12

            pygame.draw.circle(screen, color, (start_x + (i * 25), 290), radius)
            pygame.draw.circle(screen, (0, 0, 0), (start_x + (i * 25), 290), radius, 2)

    @staticmethod
    def _make_tick(is_accent=False):
        """Genera un sonido de click percusivo estilo metrónomo usando numpy"""
        duration = 0.05
        # Tono más agudo para marcar el primer tiempo (acento) del compás
        freq = 1000 if is_accent else 600
        t = np.linspace(0, duration, int(TICK_FS * duration), False)
        # Aplicamos una envolvente exponencial para que el sonido sea 'seco' y percusivo
        tick = 0.5 * np.sin(2 * np.pi * freq * t) * np.exp(-40 * t)
        return tick.astype(np.float32)

    def execute(self, text, actions_manager):
        text_lower = normalize(text)

        # Lógica para detener el metrónomo
        if is_stop_request(text):
            if self.is_running:
                self.stop_event.set()
                speak("¡Metrónomo detenido! Espero que hayas tenido una gran sesión de práctica.")
                return True
            return False

        # Si ya hay uno corriendo, lo frenamos y esperamos a que termine antes de configurar el nuevo
        if self.is_running:
            self.stop_event.set()
            deadline = time.monotonic() + 2
            while self.is_running and time.monotonic() < deadline:
                time.sleep(0.02)

        # Extraer tipo de compás (ej: 3/4, 4/4, 2/4)
        sig_match = re.search(r"(\d)\s*/\s*4", text_lower)
        self.beats_per_bar = max(1, int(sig_match.group(1))) if sig_match else 4
        if sig_match:
            text_lower = text_lower.replace(sig_match.group(0), " ")

        # Extraer BPM (ej: 'metrónomo a 100')
        bpm_match = re.search(r"(\d+)", text_lower)
        self.bpm = int(bpm_match.group(1)) if bpm_match else 120
        self.bpm = max(40, min(self.bpm, 250)) # Rango musical estándar

        speak(f"¡Claro! Metrónomo a {self.bpm} pulsaciones. ¡Uno, dos, tres, va!")

        ticks = {True: self._make_tick(True), False: self._make_tick(False)}

        self.stop_event.clear()
        self.is_running = True
        self.current_beat = 0
        # Activar el dibujo en la cara
        self.face.overlay_callback = self.draw

        try:
            next_tick = time.monotonic()
            while not self.stop_event.is_set():
                # El mezclador suma el tic a la voz de BMO en vez de cortarla
                audio.play(ticks[self.current_beat == 0], TICK_FS, channel="metronome")

                # Reloj absoluto: no acumula deriva
                next_tick += 60.0 / self.bpm
                if self.stop_event.wait(max(0.0, next_tick - time.monotonic())):
                    break
                self.current_beat = (self.current_beat + 1) % self.beats_per_bar
        finally:
            self.is_running = False
            self.face.overlay_callback = None

        return True
