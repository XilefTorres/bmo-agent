import re
import threading
import time
import numpy as np
import sounddevice as sd
import pygame
from modules.tts_speaker import speak
from modules.base_command import BaseCommand

class MetronomeCommand(BaseCommand):
    def __init__(self, face, bmo_brain):
        super().__init__(face, bmo_brain)
        self.is_running = False
        self.stop_event = threading.Event()
        self.bpm = 120
        self.beats_per_bar = 4
        self.current_beat = 0

    @property
    def keywords(self):
        return ["metrónomo", "ritmo", "compás", "para el metrónomo", "detén el metrónomo", "detente metrónomo", "metronomo"]

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

        # Fuente básica de Pygame
        font = pygame.font.SysFont("Arial", 24, bold=True)
        
        # Dibujar fondo semitransparente para el texto
        overlay = pygame.Surface((480, 60), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 260))

        # Texto de info
        info_text = font.render(f"BPM: {self.bpm}  |  Compás: {self.beats_per_bar}/4", True, (255, 255, 255))
        screen.blit(info_text, (20, 275))

        # Dibujar los puntos del compás
        margin = 20
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

    def _play_tick(self, is_accent=False):
        """Genera un sonido de click percusivo estilo metrónomo usando numpy"""
        fs = 44100
        duration = 0.05
        # Tono más agudo para marcar el primer tiempo (acento) del compás
        freq = 1000 if is_accent else 600
        t = np.linspace(0, duration, int(fs * duration), False)
        # Aplicamos una envolvente exponencial para que el sonido sea 'seco' y percusivo
        tick = 0.5 * np.sin(2 * np.pi * freq * t) * np.exp(-40 * t)
        sd.play(tick, fs)

    def execute(self, text, actions_manager):
        text_lower = text.lower()
        
        # Lógica para detener el metrónomo
        if any(word in text_lower for word in ["para", "detén", "detente", "stop"]):
            if self.is_running:
                self.stop_event.set()
                self.face.set_state("hablando")
                speak("¡Metrónomo detenido! Espero que hayas tenido una gran sesión de práctica.")
                self.face.set_state("esperando")
                return True
            return False

        # Si ya hay uno corriendo, lo frenamos antes de configurar el nuevo
        if self.is_running:
            self.stop_event.set()
            time.sleep(0.1)

        # Extraer BPM (ej: 'metrónomo a 100')
        bpm_match = re.search(r"(\d+)", text_lower)
        self.bpm = int(bpm_match.group(1)) if bpm_match else 120
        self.bpm = max(40, min(self.bpm, 250)) # Rango musical estándar

        # Extraer tipo de compás (ej: 3/4, 4/4, 2/4)
        sig_match = re.search(r"(\d)/4", text_lower)
        self.beats_per_bar = int(sig_match.group(1)) if sig_match else 4

        self.face.set_state("hablando")
        speak(f"¡Claro! Metrónomo a {self.bpm} pulsaciones. ¡Uno, dos, tres, va!")
        self.face.set_state("esperando")
        
        # Activar el dibujo en la cara
        self.face.overlay_callback = self.draw

        self.stop_event.clear()
        self.is_running = True
        self.current_beat = 0

        try:
            while not self.stop_event.is_set():
                interval = 60.0 / self.bpm
                is_accent = (self.current_beat == 0)
                self._play_tick(is_accent)
                
                time.sleep(interval)
                self.current_beat = (self.current_beat + 1) % self.beats_per_bar
        finally:
            self.is_running = False
            self.face.overlay_callback = None
        
        return True