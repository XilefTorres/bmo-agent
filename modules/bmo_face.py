import pygame
import os
import random
import threading

from modules.tts_speaker import speak, set_mouth_callback

SCREEN_SIZE = (480, 320)

# Estado -> nombre de imagen (faces/bmo_<nombre>.png|jpg)
STATE_IMAGE = {
    "esperando": "happy",
    "escuchando": "listening",
    "pensando": "thinking",
    "hablando": "mouth_0",
    "jugando": "game",
}

# Bocas por nivel de apertura (0 = cerrada ... 3 = muy abierta).
# En el nivel 2 se van alternando variantes para que no se vea mecanico.
MOUTH_MID = ["mouth_2", "mouth_o", "mouth_e"]


class BMOFace:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("BMO")
        self.key_callback = None
        self.overlay_callback = None
        self.state = "esperando"
        self.running = True
        self.BG_COLOR = (128, 230, 209)

        # Boca sincronizada con el audio (la actualiza tts_speaker desde su hilo)
        self.mouth_level = None      # None = BMO no esta hablando
        self._shown_level = 0
        self._mid_variant = 0

<<<<<<< Updated upstream
        # Imágenes estáticas para estados
        self.faces = {}
        image_files = {
            "esperando": "bmo_happy.jpg",
            "escuchando": "bmo_listening.jpg",
            "pensando": "bmo_thinking.jpg",
            "hablando_base": "bmo_talking.jpg" 
        }

        # --- CONFIGURACIÓN DE ANIMACIÓN DE HABLA ---
        self.talking_frames = []
        talking_frame_files = [
            "bmo_talk1.jpg", # boca muy abierta (Índice 0)
            "bmo_talk2.jpg", # boca medio abierta (Índice 1)
            "bmo_talk3.jpg", # boca poco abierta (Índice 2)
            "bmo_talk4.jpg"  # boca cerrada (Índice 3)
        ]
        
        # Secuencia para un movimiento de boca más natural (abrir y cerrar)
        self.animation_sequence = [0, 1, 2, 3, 2, 1]
        self.talking_frame_index = 0 
        self.last_talking_frame_time = pygame.time.get_ticks()
        self.talking_animation_interval = 120 # Milisegundos entre frames
        # -------------------------------------------

        # Cargar imágenes
        try:
            # Caras estáticas
            for state, filename in image_files.items():
                img_path = os.path.join(faces_dir, filename)
                if os.path.exists(img_path):
                    raw_img = pygame.image.load(img_path).convert()
                    self.faces[state] = pygame.transform.scale(raw_img, (480, 320))
            
            # Fotogramas de animación
            for filename in talking_frame_files:
                img_path = os.path.join(faces_dir, filename)
                if os.path.exists(img_path):
                    raw_img = pygame.image.load(img_path).convert()
                    scaled_img = pygame.transform.scale(raw_img, (480, 320))
                    self.talking_frames.append(scaled_img)

            # Ajuste de nombre para estado hablando
            if "hablando_base" in self.faces:
                self.faces["hablando"] = self.faces.pop("hablando_base")

            print(f">>> Éxito: {len(self.faces) + len(self.talking_frames)} imágenes cargadas.")
        except Exception as e:
            print(f"!!! Error cargando imágenes: {e}")
=======
        # Expresion temporal (risa, amor...) que tiene prioridad sobre todo lo demas
        self.expression = None
        self.expression_until = 0

        # Parpadeo aleatorio cuando esta en reposo
        now = pygame.time.get_ticks()
        self.next_blink = now + 3000
        self.blink_until = 0

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.images = self._load_images(os.path.join(project_root, "faces"))

        set_mouth_callback(self.set_mouth_level)

    # ---------- carga de imagenes ----------
    def _load_images(self, faces_dir):
        """Carga todas las faces/bmo_*.png|jpg. La clave es el nombre sin 'bmo_' ni extension."""
        images = {}
        if not os.path.isdir(faces_dir):
            print(f"!!! Error: No existe la carpeta de caras: {faces_dir}")
            return images
        for filename in sorted(os.listdir(faces_dir)):
            stem, ext = os.path.splitext(filename)
            if not stem.startswith("bmo_") or ext.lower() not in (".png", ".jpg", ".jpeg"):
                continue
            try:
                images[stem[4:]] = self._fit(pygame.image.load(os.path.join(faces_dir, filename)).convert())
            except Exception as e:
                print(f"!!! Error cargando {filename}: {e}")
        print(f">>> Se cargaron {len(images)} caras desde {faces_dir}")
        return images
>>>>>>> Stashed changes

    @staticmethod
    def _fit(img):
        """Escala sin deformar y rellena los bordes con el color de fondo de la propia imagen."""
        w, h = img.get_size()
        scale = min(SCREEN_SIZE[0] / w, SCREEN_SIZE[1] / h)
        new_size = (round(w * scale), round(h * scale))
        scaled = pygame.transform.smoothscale(img, new_size)
        surface = pygame.Surface(SCREEN_SIZE)
        surface.fill(img.get_at((0, 0)))
        surface.blit(scaled, ((SCREEN_SIZE[0] - new_size[0]) // 2, (SCREEN_SIZE[1] - new_size[1]) // 2))
        return surface

    # ---------- API para otros hilos ----------
    def set_state(self, new_state):
        self.state = new_state

    def set_mouth_level(self, level):
        """Lo llama tts_speaker: 0-3 mientras suena el audio, None cuando termina."""
        self.mouth_level = level
        if level is None:
            self._shown_level = 0

    def show_expression(self, name, duration_ms):
        """Muestra una cara especial (laughing, love, surprised, sad...) por un tiempo."""
        if name in self.images:
            self.expression = name
            self.expression_until = pygame.time.get_ticks() + duration_ms

    # ---------- seleccion de la cara ----------
    def _mouth_image_name(self):
        target = self.mouth_level
        # Abre de golpe, cierra de a un nivel por fotograma (se ve mas natural)
        if target > self._shown_level:
            new = target
        elif target < self._shown_level:
            new = self._shown_level - 1
        else:
            new = target
        if new == 2 and self._shown_level != 2:
            self._mid_variant = (self._mid_variant + 1) % len(MOUTH_MID)
        self._shown_level = new
        return MOUTH_MID[self._mid_variant] if new == 2 else f"mouth_{new}"

    def _current_image(self, now):
        if self.expression and now < self.expression_until:
            return self.images.get(self.expression)

        level = self.mouth_level
        if level is not None:
            return self.images.get(self._mouth_image_name())

        if self.state == "esperando":
            if now >= self.next_blink:
                self.blink_until = now + 140
                self.next_blink = now + random.randint(2500, 6000)
            if now < self.blink_until:
                return self.images.get("blink")

        return self.images.get(STATE_IMAGE.get(self.state))

    # ---------- bucle principal ----------
    def update_loop(self):
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
<<<<<<< Updated upstream

=======
>>>>>>> Stashed changes
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    self.handle_touch(x, y)

                if event.type == pygame.KEYDOWN:
                    if self.key_callback:
                        self.key_callback(event.key)

            self.screen.fill(self.BG_COLOR)
<<<<<<< Updated upstream
            face_img = None
            
            # LÓGICA DE ANIMACIÓN
            if self.state == "hablando" and self.talking_frames:
                current_time = pygame.time.get_ticks()
                
                if current_time - self.last_talking_frame_time > self.talking_animation_interval:
                    # Avanzar en la secuencia personalizada
                    self.talking_frame_index = (self.talking_frame_index + 1) % len(self.animation_sequence)
                    self.last_talking_frame_time = current_time
                
                # Mapear el índice de la secuencia al frame real
                seq_idx = self.animation_sequence[self.talking_frame_index]
                face_img = self.talking_frames[seq_idx]
            else:
                face_img = self.faces.get(self.state)
            
            if face_img:
                self.screen.blit(face_img, (0, 0))
            
            # Capa superior (Overlays como el metrónomo)
            if self.overlay_callback:
                self.overlay_callback(self.screen)

            pygame.display.flip()
            clock.tick(15) # 30 FPS es ideal para Fedora/Raspberry
            
        pygame.quit()

    def handle_touch(self, x, y):
        """Interacción táctil de BMO"""
        if y < 150: # Parte superior
            self.set_state("pensando")
            from modules.tts_speaker import speak
            respuestas = ["¡Eso me da cosquillas!", "¡Jajaja! Detente Xilef.", "¡Mis circuitos!"]
            threading.Thread(target=speak, args=(random.choice(respuestas),), daemon=True).start()
        else: # Parte inferior
            self.set_state("esperando")
            from modules.tts_speaker import speak
            threading.Thread(target=speak, args=("¿Me quieres, Xilef?",), daemon=True).start()

    def set_state(self, new_state):
        if self.state != new_state:
            # Reiniciar animación si entramos o salimos de 'hablando'
            if self.state == "hablando" or new_state == "hablando":
                self.talking_frame_index = 0
                self.last_talking_frame_time = pygame.time.get_ticks()
            self.state = new_state
=======
            face_img = self._current_image(pygame.time.get_ticks())

            if face_img:
                self.screen.blit(face_img, (0, 0))
            else:
                # Placeholder si faltan imagenes
                pygame.draw.circle(self.screen, (0, 0, 0), (140, 140), 40)
                pygame.draw.circle(self.screen, (0, 0, 0), (340, 140), 40)
                pygame.draw.arc(self.screen, (0, 0, 0), (190, 200, 100, 60), 3.14, 0, 10)

            pygame.display.flip()
            clock.tick(30)

        pygame.quit()

    def handle_touch(self, x, y):
        """Define qué hace BMO según dónde lo toques"""
        if y < 150:
            self.show_expression("laughing", 2500)
            phrase = random.choice([
                "¡Eso me da cosquillas!",
                "¡Mis circuitos hacen cosquillas!",
                "¡Jajaja! Detente Xilef.",
            ])
        else:
            self.show_expression("love", 3000)
            phrase = "¿Me quieres, Xilef?"
        threading.Thread(target=speak, args=(phrase,), daemon=True).start()
>>>>>>> Stashed changes
