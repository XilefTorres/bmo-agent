import pygame
import time
import os
import random
import threading

class BMOFace:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((480, 320))
        pygame.display.set_caption("BMO")
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
            # Imagen base si falla la animación
            "hablando_base": "bmo_talking.jpg" 
        }

        # --- NUEVO: Configuración para la animación de hablar ---
        self.talking_frames = []
        # Lista con los nombres de archivo para la animación
        # Asumimos .jpg por consistencia. bmo_talk4 es la boca cerrada.
        talking_frame_files = [
            "bmo_talk1.jpg", # boca muy abierta
            "bmo_talk2.jpg", # boca medio abierta
            "bmo_talk3.jpg", # boca poco abierta
            "bmo_talk4.jpg"  # boca cerrada
        ]
        
        # Variables de estado para la animación
        self.talking_frame_index = 0 # fotograma actual
        self.last_talking_frame_time = pygame.time.get_ticks() # tiempo del último cambio
        # Intervalo de tiempo entre fotogramas en milisegundos (ajusta para velocidad)
        self.talking_animation_interval = 150 
        # --------------------------------------------------------

        # Bloque para cargar y escalar todas las imágenes
        try:
            # Cargar caras estáticas
            for state, filename in image_files.items():
                img_path = os.path.join(faces_dir, filename)
                if os.path.exists(img_path):
                    raw_img = pygame.image.load(img_path).convert()
                    self.faces[state] = pygame.transform.scale(raw_img, (480, 320))
                else:
                    print(f"!!! Error: No se encuentra el archivo: {img_path}")
            
            # --- NUEVO: Cargar fotogramas de la animación ---
            for filename in talking_frame_files:
                img_path = os.path.join(faces_dir, filename)
                if os.path.exists(img_path):
                    raw_img = pygame.image.load(img_path).convert()
                    scaled_img = pygame.transform.scale(raw_img, (480, 320))
                    self.talking_frames.append(scaled_img)
                else:
                    print(f"!!! Error: No se encuentra el archivo: {img_path}")
            # ------------------------------------------------

            # Re-indexar la cara base de hablar
            if "hablando_base" in self.faces:
                self.faces["hablando"] = self.faces.pop("hablando_base")

            if self.faces or self.talking_frames:
                print(f">>> Éxito: Se cargaron {len(self.faces) + len(self.talking_frames)} imágenes desde {faces_dir}")
        except Exception as e:
            print(f"!!! Error crítico cargando imágenes: {e}")

    def update_loop(self):
        clock = pygame.time.Clock()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                # --- DETECCIÓN TÁCTIL ---
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    self.handle_touch(x, y)

            self.screen.fill(self.BG_COLOR)
            
            # --- NUEVO: Lógica para dibujar la cara ---
            face_img = None
            
            # Si está hablando y hay fotogramas cargados, animar
            if self.state == "hablando" and self.talking_frames:
                current_time = pygame.time.get_ticks()
                
                # Verificar si ha pasado suficiente tiempo para cambiar de fotograma
                if current_time - self.last_talking_frame_time > self.talking_animation_interval:
                    # Incrementar índice y hacer loop
                    self.talking_frame_index = (self.talking_frame_index + 1) % len(self.talking_frames)
                    self.last_talking_frame_time = current_time
                
                face_img = self.talking_frames[self.talking_frame_index]
            else:
                # Usar imágenes estáticas para los demás estados
                face_img = self.faces.get(self.state)
            
            if face_img:
                self.screen.blit(face_img, (0, 0))
            else:
                # Dibujos de placeholder mejorados para cada estado si no hay imágenes
                # Ojos negros
                pygame.draw.circle(self.screen, (0,0,0), (140, 140), 40)
                pygame.draw.circle(self.screen, (0,0,0), (340, 140), 40)
                
                # Boca según el estado
                if self.state == "esperando":
                    # Sonrisa
                    pygame.draw.arc(self.screen, (0,0,0), (190, 200, 100, 60), 3.14, 0, 10)
                elif self.state == "escuchando":
                    # Línea recta
                    pygame.draw.rect(self.screen, (0,0,0), (190, 240, 100, 20))
                elif self.state == "pensando":
                    # Círculo pequeño descentrado
                    pygame.draw.ellipse(self.screen, (0,0,0), (210, 220, 60, 60), 5)
                elif self.state == "hablando":
                    # Óvalo grande (boca abierta)
                     pygame.draw.ellipse(self.screen, (0,0,0), (190, 220, 100, 60))
            # -------------------------------------------

            pygame.display.flip()
            # Mantener a 30 fotogramas por segundo
            clock.tick(30)
            
        # Limpieza cuando se cierra la ventana
        pygame.quit()

    def handle_touch(self, x, y):
        """Define qué hace BMO según dónde lo toques"""
        
        # Ejemplo: Si tocas la parte de arriba (frente/ojos)
        if y < 150:
            self.set_state("pensando") # O un nuevo estado "risa"
            # Importamos speak aquí o lo manejas con un evento
            from modules.tts_speaker import speak
            respuestas = [
                "¡Eso me da cosquillas!", 
                "¡Mis circuitos hacen cosquillas!", 
                "¡Jajaja! Detente Xilef."
            ]
            threading.Thread(target=speak, args=(random.choice(respuestas),), daemon=True).start()
        
        # Ejemplo: Si tocas la parte de abajo (boca/mejillas)
        else:
            self.set_state("esperando")
            from modules.tts_speaker import speak
            threading.Thread(target=speak, args=("¿Me quieres, Xilef?",), daemon=True).start()

    def set_state(self, new_state):
        # Actualizamos el estado solo si es diferente para evitar spam en consola
        if self.state != new_state:
            # --- Reiniciar índices de animación al cambiar de estado ---
            if self.state == "hablando" or new_state == "hablando":
                self.talking_frame_index = 0
                self.last_talking_frame_time = pygame.time.get_ticks()
            # ------------------------------------------------------------------
            self.state = new_state
    