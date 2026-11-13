import os
import subprocess
import time
from modules import audio
from modules.tts_speaker import speak
from modules.base_command import BaseCommand

# Se prueban en orden. BMO_PEGASUS_PATH permite fijar la ruta sin tocar el código.
PEGASUS_CANDIDATES = [
    os.environ.get("BMO_PEGASUS_PATH"),
    "pegasus",
    "pegasus-fe",
    os.path.expanduser("~/PegasusApp/pegasus-fe"),
]

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

    def _run_pegasus(self):
        """Abre Pegasus y espera a que se cierre. Devuelve False si no se pudo abrir."""
        for path in PEGASUS_CANDIDATES:
            if not path:
                continue
            try:
                result = subprocess.run([path])
            except (FileNotFoundError, PermissionError):
                continue
            if result.returncode != 0:
                print(f"[!] Pegasus terminó con código {result.returncode}")
            return True
        return False

    def execute(self, text, actions_manager):
        frase_juego = "¡Iniciando mi interfaz de juegos! ¡Diviértete mucho!"
        print(f"BMO: {frase_juego}")
        speak(frase_juego)

        actions_manager.modo_juego_activo = True
        abierto = False
        try:
            if hasattr(self.bmo_brain, 'unload_model'):
                self.bmo_brain.unload_model()

            # Soltamos el dispositivo de audio para los juegos (se reabre solo cuando BMO hable)
            audio.release()

            self.face.set_state("jugando")
            self._minimize_but_bmo()
            abierto = self._run_pegasus()
        finally:
            # Pase lo que pase, BMO vuelve a escuchar y a pensar
            actions_manager.modo_juego_activo = False
            self.face.set_state("esperando")
            if hasattr(self.bmo_brain, 'reload_model'):
                self.bmo_brain.reload_model()

        if abierto:
            speak("¡Bienvenido de vuelta! ¿Te divertiste jugando?")
        else:
            self.face.show_expression("sad", 4000)
            speak("¡Oh no, Xilef! Algo salió mal al intentar abrir mis juegos.")
