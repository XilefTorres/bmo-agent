import subprocess
import socket
from modules.tts_speaker import speak
from modules.base_command import BaseCommand

class SystemStatusCommand(BaseCommand):
    @property
    def keywords(self):
        # Palabras clave para preguntar sobre el estado del sistema
        return ["sistema", "estado", "recursos", "temperatura", "ip", "servidor", "conexión"]

    def _get_ip(self):
        """Obtiene la dirección IP local de la Raspberry Pi"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "no disponible"

    def execute(self, text, actions_manager):
        self.face.set_state("hablando")
        
        # 1. Obtener Temperatura (específico para Raspberry Pi)
        temp_text = "desconocida"
        try:
            # Comando oficial en Raspberry Pi OS
            res = subprocess.check_output(["vcgencmd", "measure_temp"]).decode("utf-8")
            temp_val = res.replace("temp=", "").replace("'C\n", "")
            temp_text = f"{temp_val} grados centígrados"
        except Exception:
            # Intento genérico para otros sistemas Linux
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    temp_text = f"{int(f.read()) / 1000.0} grados centígrados"
            except:
                pass

        # 2. Obtener IP Local
        ip_addr = self._get_ip()

        # 3. Respuesta de voz de BMO
        respuesta = (f"¡Claro que sí! Mi temperatura actual es de {temp_text}. "
                    f"Mi dirección I P es {ip_addr}. "
                    "¡Abriré el monitor de recursos para que revises mis procesos!")
        speak(respuesta)
        
        self.face.set_state("esperando")

        # 4. Lanzar la terminal con 'top'
        # Probamos diferentes emuladores comunes en Linux/RPi
        terminals = [
            ["lxterminal", "-e", "top"],      # Raspberry Pi OS
            ["gnome-terminal", "--", "top"],  # Fedora / Ubuntu
            ["xterm", "-e", "top"]            # Genérico
        ]
        
        for cmd in terminals:
            try:
                subprocess.Popen(cmd, start_new_session=True)
                break
            except FileNotFoundError:
                continue
                
        return True