import re
from modules import audio, settings
from modules.tts_speaker import speak
from modules.base_command import BaseCommand
from modules.text_utils import normalize, NUMBER_WORDS

STEP = 0.2
MIN_VOLUME = 0.05   # nunca en cero: BMO no podría avisar que ya lo subiste


def parse_volume(text, current):
    """Devuelve el volumen pedido (0.0 a 1.0) o None si solo preguntaron cuál es."""
    norm = normalize(text)
    digits = re.search(r"(\d{1,3})", norm)
    if digits:
        return int(digits.group(1)) / 100
    if re.search(r"(?<!\w)(?:maximo|tope|todo)(?!\w)", norm):
        return 1.0
    if re.search(r"(?<!\w)(?:minimo|bajito|quedito)(?!\w)", norm):
        return 0.2
    if re.search(r"(?<!\w)(?:mitad|medio)(?!\w)", norm):
        return 0.5
    # "volumen al cincuenta"
    for word in sorted(NUMBER_WORDS, key=len, reverse=True):
        if NUMBER_WORDS[word] >= 1 and re.search(rf"(?<!\w)(?:a|al|en)\s+(?:el\s+)?{word}(?!\w)", norm):
            return NUMBER_WORDS[word] / 100
    if re.search(r"(?<!\w)(?:sube|subele|subir|aumenta|mas alto|mas fuerte|mas volumen)(?!\w)", norm):
        return current + STEP
    if re.search(r"(?<!\w)(?:baja|bajale|bajar|disminuye|mas bajo|menos volumen)(?!\w)", norm):
        return current - STEP
    return None


class VolumeCommand(BaseCommand):
    @property
    def keywords(self):
        return ["volumen"]

    def execute(self, text, actions_manager):
        current = audio.get_volume()
        target = parse_volume(text, current)
        if target is None:
            speak(f"Mi volumen está al {round(current * 100)} por ciento.")
            return True

        target = max(MIN_VOLUME, min(1.0, target))
        audio.set_volume(target)
        settings.set("volume", target)
        speak(f"¡Listo! Volumen al {round(target * 100)} por ciento.")
        return True
