import pygame
import time
import os
import random
import threading

class BMOFace:
    def __init__(self):
        try:
            pygame.mixer.pre_init(44100, -16, 2, 4096)
        except Exception as e:
            print(f"Advertencia: No se pudo pre-inicializar el mixer: {e}")

        pygame.init()
        self.screen = pygame.display.set_mode((480, 320))
        pygame.display.set_caption("BMO")
        self.key_callback = None
        self.overlay_callback = None
        self.state = "esperando"
        self.running = True
        # Color verde BMO de fondo
        self.BG_COLOR = (155, 188, 15)

        # Configuración de rutas
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        faces_dir = os.path.join(project_root, "faces")

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

    def update_loop(self):
        clock = pygame.time.Clock()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    self.handle_touch(x, y)

                if event.type == pygame.KEYDOWN:
                    if self.key_callback:
                        self.key_callback(event.key)

            self.screen.fill(self.BG_COLOR)
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
            clock.tick(30) # 30 FPS es ideal para Fedora/Raspberry
            
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