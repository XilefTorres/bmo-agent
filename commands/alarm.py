import json
import os
import re
import threading
import time
from datetime import datetime
import numpy as np
from modules.tts_speaker import speak, play_sound
from modules.base_command import BaseCommand
from modules.text_utils import normalize, parse_duration, format_duration, parse_clock_time, format_clock

# Las alarmas pendientes se guardan aquí para sobrevivir a un reinicio de BMO
ALARMS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "alarms.json")


def extract_reminder(text, start, end):
    """Saca el recordatorio de 'recuérdame sacar la basura en 5 minutos' -> 'sacar la basura'."""
    norm = normalize(text)
    trigger = re.search(r"(?<!\w)recuerdame\s+(?:que\s+)?", norm)
    if not trigger:
        return ""
    # Quitamos la duración y el "en" / "dentro de" que la introduce
    intro = re.search(r"(?:(?<!\w)(?:en|dentro de)\s+)$", norm[:start])
    cut_start = intro.start() if intro else start
    if cut_start < trigger.end():
        reminder = text[end:]            # "recuérdame en 5 minutos sacar la basura"
    else:
        reminder = text[trigger.end():cut_start] + " " + text[end:]
    return re.sub(r"\s+", " ", reminder).strip(" ,.")


class AlarmCommand(BaseCommand):
    def __init__(self, face, bmo_brain):
        super().__init__(face, bmo_brain)
        self._lock = threading.Lock()
        self._alarms = []   # [{"due": epoch, "label": "5 minutos", "reminder": "sacar la basura"}]
        self._restore()

    @property
    def keywords(self):
        return ["alarma", "alarmas", "despiértame", "recuérdame", "avísame",
                "temporizador", "temporizadores", "recordatorios"]

    # ---------- persistencia ----------
    def _save(self):
        try:
            with open(ALARMS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._alarms, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"[!] No se pudieron guardar las alarmas: {e}")

    def _restore(self):
        try:
            with open(ALARMS_FILE, encoding="utf-8") as f:
                saved = json.load(f)
        except (OSError, ValueError):
            return
        for alarm in saved:
            if isinstance(alarm, dict) and "due" in alarm:
                self._alarms.append(alarm)
                self._start_timer(alarm, min_delay=5)
        if self._alarms:
            print(f">>> Se recuperaron {len(self._alarms)} alarmas pendientes.")

    # ---------- alarma ----------
    def _play_beep(self):
        """Genera un tono cuadrado estilo retro de 8 bits"""
        fs = 44100
        duration = 0.15
        t = np.linspace(0, duration, int(fs * duration), False)
        # Usamos sign(sin) para crear una onda cuadrada (sonido de consola vieja)
        beep = (0.2 * np.sign(np.sin(2 * np.pi * 1000 * t))).astype(np.float32)
        play_sound(beep, fs)

    def _start_timer(self, alarm, min_delay=0):
        def alarm_timer():
            # Las que vencieron con BMO apagado suenan poco después de arrancar
            time.sleep(max(alarm["due"] - time.time(), min_delay))
            with self._lock:
                if not any(a is alarm for a in self._alarms):
                    return   # la cancelaron mientras esperaba
            for _ in range(3):
                self._play_beep()
                time.sleep(0.1)

            if alarm.get("reminder"):
                speak(f"¡Xilef! Me pediste que te recordara: {alarm['reminder']}.")
            elif alarm.get("kind") == "clock":
                speak(f"¡Xilef! ¡Ya son {alarm['label']}! ¡Despierta!")
            else:
                speak(f"¡Xilef! ¡Ya pasó el tiempo de {alarm['label']}! ¡Despierta!")
            print(f">>> ALARMA: {alarm['label']} ({alarm.get('reminder') or 'sin recordatorio'}).")

            with self._lock:
                if alarm in self._alarms:
                    self._alarms.remove(alarm)
                self._save()

        threading.Thread(target=alarm_timer, daemon=True).start()

    def _cancel_all(self):
        with self._lock:
            cantidad = len(self._alarms)
            self._alarms.clear()   # los hilos en espera ven que su alarma ya no está y no suenan
            self._save()
        if cantidad == 0:
            speak("No tengo ninguna alarma pendiente, Xilef.")
        elif cantidad == 1:
            speak("¡Listo! Cancelé tu alarma.")
        else:
            speak(f"¡Listo! Cancelé tus {cantidad} alarmas.")
        return True

    def _list(self):
        with self._lock:
            pendientes = sorted(self._alarms, key=lambda a: a["due"])
        if not pendientes:
            speak("No tengo ninguna alarma pendiente, Xilef.")
            return True
        partes = []
        for alarm in pendientes:
            if alarm.get("kind") == "clock":
                cuando = f"a {alarm['label']}"
            else:
                falta = max(alarm["due"] - time.time(), 1)
                # Los segundos solo importan en alarmas cortas
                cuando = "en " + format_duration(round(falta / 60) * 60 if falta >= 60 else falta)
            partes.append(cuando +(f", para {alarm['reminder']}" if alarm.get("reminder") else ""))
        cuantas = "una alarma" if len(partes) == 1 else f"{len(partes)} alarmas"
        speak(f"Tienes {cuantas}: " + "; ".join(partes) + ".")
        return True

    def _set_clock_alarm(self, text, due, start, end):
        """Alarma a una hora del día: 'alarma a las 9 de la mañana', 'despiértame a las 11'."""
        label = format_clock(due)
        reminder = extract_reminder(text, start, end)
        alarm = {"due": due.timestamp(), "label": label, "reminder": reminder, "kind": "clock"}
        with self._lock:
            self._alarms.append(alarm)
            self._save()
        self._start_timer(alarm)

        falta = max(due.timestamp() - time.time(), 60)
        falta = format_duration(round(falta / 60) * 60)
        cuando = "mañana a " if due.date() != datetime.now().date() else "a "
        if reminder:
            speak(f"¡Entendido! {cuando.capitalize()}{label} te recuerdo {reminder}. Faltan {falta}.")
        else:
            speak(f"¡Entendido! Pondré la alarma {cuando}{label}. Faltan {falta}.")
        return True

    def execute(self, text, actions_manager):
        norm = normalize(text)
        if re.search(r"(?<!\w)(?:cancela|cancelar|borra|borrar|quita|quitar|elimina|eliminar|apaga)(?!\w)", norm):
            return self._cancel_all()

        parsed = parse_duration(text)
        clock = None if parsed else parse_clock_time(text, datetime.now())
        if clock:
            return self._set_clock_alarm(text, *clock)

        if not parsed and re.search(r"(?<!\w)(?:que|cuales|cuantas|cuantos|lista|dime|tengo|hay|pendientes)(?!\w)", norm):
            return self._list()

        if not parsed:
            speak("¿Para cuándo quieres la alarma? No entendí bien el tiempo, Xilef.")
            return False

        segundos, start, end = parsed
        label = format_duration(segundos)
        reminder = extract_reminder(text, start, end)

        alarm = {"due": time.time() + segundos, "label": label, "reminder": reminder}
        with self._lock:
            self._alarms.append(alarm)
            self._save()
        self._start_timer(alarm)

        if reminder:
            speak(f"¡Entendido! En {label} te recuerdo {reminder}.")
        else:
            speak(f"¡Entendido! Pondré mi reloj interno en {label}. ¡Te avisaré!")
        return True
