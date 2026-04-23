import subprocess
import socket
import shutil
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
        
        # 1. Obtener Temperatura
        temp_val = None
        # Intento A: Raspberry Pi
        try:
            res = subprocess.check_output(["vcgencmd", "measure_temp"]).decode("utf-8")
            temp_val = res.replace("temp=", "").replace("'C\n", "").strip()
        except Exception:
            # Intento B: Genérico Linux/Fedora (probamos las primeras 5 zonas térmicas)
            for i in range(5):
                try:
                    with open(f"/sys/class/thermal/thermal_zone{i}/temp", "r") as f:
                        raw_temp = int(f.read().strip())
                        if raw_temp > 0:
                            temp_val = round(raw_temp / 1000.0, 1)
                            break
                except: continue

        temp_text = f"{temp_val} grados" if temp_val else "desconocida"

        # 2. Obtener IP Local
        ip_addr = self._get_ip()
        # Forzamos a que lo lea bloque por bloque diciendo "punto"
        ip_speech = ip_addr.replace(".", " punto ")

        # 3. Respuesta de voz de BMO
        respuesta = (f"¡Claro que sí! Mi temperatura actual es de {temp_text}. "
                    f"Mi dirección I P es {ip_speech}. "
                    "¡Abriré el monitor de recursos para que revises mis procesos!")
        speak(respuesta)
        
        self.face.set_state("esperando")

        # Verificamos si htop existe, si no usamos top
        monitor_cmd = "btop" if shutil.which("btop") else "top"

        # 4. Lanzar la terminal con 'top'
        # Probamos diferentes emuladores comunes en Linux/Fedora/RPi
        terminals = [
            ["gnome-terminal", "--", monitor_cmd], # Fedora estándar
            ["kgx", "--", monitor_cmd],             # Fedora GNOME Console (Nueva)
            ["ptyxis", "--", monitor_cmd],          # Fedora Atomic / Silverblue
            ["lxterminal", "-e", monitor_cmd],      # Raspberry Pi OS
            ["xterm", "-e", monitor_cmd]            # Genérico
        ]
        
        for cmd in terminals:
            try:
                subprocess.Popen(cmd, start_new_session=True)
                break
            except FileNotFoundError:
                continue
                
        return True