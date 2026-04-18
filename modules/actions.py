import os
import random
import threading
import re
import subprocess
import time
from datetime import datetime
from modules.tts_speaker import speak

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
        
        # REGISTRO DE COMANDOS: Aquí es donde configuras todo.
        # keywords: lista de palabras que activan la acción.
        # function: el método que se ejecuta.
        # threaded: ¿Debe correr en segundo plano para no bloquear a BMO?
        self.registry = [
            {
                "keywords": ["jugar", "juego", "videojuegos", "emulador", "pegasus"],
                "function": self.abrir_modo_juego,
                "threaded": True
            },
            {
                "keywords": ["alarma", "despiértame", "recuérdame", "tiempo", "segundos", "minutos"],
                "function": self.set_alarm,
                "threaded": False # set_alarm ya gestiona su propio hilo interno
            },
            {
                "keywords": ["hora", "qué hora es", "momento"],
                "function": self.get_current_time,
                "threaded": False
            }
        ]

    # --- UTILIDADES ---

    def _minimize_but_bmo(self):
        """Limpia el escritorio para darle foco a BMO"""
        try:
            subprocess.run(["wmctrl", "-k", "on"], check=False)
            time.sleep(0.5)
            subprocess.run(["wmctrl", "-a", "BMO"], check=False)
        except Exception as e:
            print(f"[!] No se pudo gestionar las ventanas: {e}")

    def dispatch(self, text):
        """Busca y ejecuta una acción basada en el texto"""
        for command in self.registry:
            if any(k in text.lower() for k in command["keywords"]):
                if command["threaded"]:
                    threading.Thread(target=command["function"], args=(text,), daemon=True).start()
                else:
                    command["function"](text)
                return True
        return False

    # --- ACCIONES ---

    def abrir_modo_juego(self, text=None):
        """Gestiona la transición al modo emulador liberando RAM"""
        frase_juego = "¡Iniciando mi interfaz de juegos! ¡Diviértete mucho!"
        print(f"BMO: {frase_juego}")
        self.face.set_state("hablando")
        speak(frase_juego)
        
        self.modo_juego_activo = True
        
        if hasattr(self.bmo_brain, 'unload_model'):
            self.bmo_brain.unload_model()

        self.face.set_state("esperando")
        self._minimize_but_bmo()
        
        try:
            # Intentamos ejecutar Pegasus
            subprocess.run(["pegasus"], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                subprocess.run(["/home/xileftorres/PegasusApp/pegasus-fe"], check=True)
            except Exception:
                speak("¡Oh no, Xilef! Algo salió mal al intentar abrir mis juegos.")
        
        self.modo_juego_activo = False

        if hasattr(self.bmo_brain, 'reload_model'):
            self.bmo_brain.reload_model()
        
        vuelta_frase = "¡Bienvenido de vuelta! ¿Te divertiste jugando?"
        self.face.set_state("hablando")
        speak(vuelta_frase)
        self.face.set_state("esperando")

    def set_alarm(self, text):
        """Configura una alarma temporal basada en voz"""
        # Buscamos números seguidos de segundos, minutos u horas
        match = re.search(r"(\d+)\s*(segundo|minuto|hora)", text.lower())
        
        if not match:
            self.face.set_state("hablando")
            speak("¿Para cuándo quieres la alarma? No entendí bien el tiempo, Xilef.")
            return False

        cantidad = int(match.group(1))
        unidad = match.group(2)
        
        segundos = cantidad
        if "minuto" in unidad:
            segundos *= 60
        elif "hora" in unidad:
            segundos *= 3600
        
        self.face.set_state("hablando")
        speak(f"¡Entendido! Pondré mi reloj interno en {cantidad} {unidad}s. ¡Te avisaré!")
        self.face.set_state("esperando")

        def alarm_timer():
            time.sleep(segundos)
            self.face.set_state("hablando")
            speak(f"¡BEEP BEEP! ¡Xilef! ¡Ya pasaron los {cantidad} {unidad}s! ¡Despierta!")
            print(f">>> ALARMA: Han pasado {cantidad} {unidad}s.")
            self.face.set_state("esperando")

        threading.Thread(target=alarm_timer, daemon=True).start()
        return True

    def get_current_time(self, text=None):
        """Informa la hora actual"""
        ahora = datetime.now().strftime("%I:%M %p")
        frase = f"¡Claro! En mis circuitos internos son las {ahora}."
        print(f"BMO: {frase}")
        self.face.set_state("hablando")
        speak(frase)
        self.face.set_state("esperando")