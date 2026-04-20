import subprocess
import time
from modules.tts_speaker import speak
from modules.base_command import BaseCommand

class GameCommand(BaseCommand):
    @property
    def keywords(self):
        return ["jugar", "juego", "videojuegos", "emulador", "pegasus"]

    @property
    def threaded(self):
        return True

    def _minimize_but_bmo(self):
        try:
            subprocess.run(["wmctrl", "-k", "on"], check=False)
            time.sleep(0.5)
            subprocess.run(["wmctrl", "-a", "BMO"], check=False)
        except Exception as e:
            print(f"[!] No se pudo gestionar las ventanas: {e}")

    def execute(self, text, actions_manager):
        frase_juego = "¡Iniciando mi interfaz de juegos! ¡Diviértete mucho!"
        print(f"BMO: {frase_juego}")
        self.face.set_state("hablando")
        speak(frase_juego)
        
        actions_manager.modo_juego_activo = True
        
        if hasattr(self.bmo_brain, 'unload_model'):
            self.bmo_brain.unload_model()

        self.face.set_state("esperando")
        self._minimize_but_bmo()
        
        try:
            subprocess.run(["pegasus"], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                subprocess.run(["/home/xileftorres/PegasusApp/pegasus-fe"], check=True)
            except Exception:
                speak("¡Oh no, Xilef! Algo salió mal al intentar abrir mis juegos.")
        
        actions_manager.modo_juego_activo = False

        if hasattr(self.bmo_brain, 'reload_model'):
            self.bmo_brain.reload_model()
        
        vuelta_frase = "¡Bienvenido de vuelta! ¿Te divertiste jugando?"
        self.face.set_state("hablando")
        speak(vuelta_frase)
        self.face.set_state("esperando")