"""Utilidades de texto sin dependencias de hardware (se pueden probar sin micrófono ni pantalla)."""
import re
import unicodedata


def normalize(text):
    """Minúsculas y sin acentos. Conserva la longitud: cada carácter sigue en su misma posición."""
    text = unicodedata.normalize("NFC", text).lower()
    out = []
    for ch in text:
        base = unicodedata.normalize("NFD", ch)[0]
        out.append(base if len(base) == 1 else ch)
    return "".join(out)


def _phrase_regex(phrases):
    alternation = "|".join(re.escape(normalize(p)) for p in sorted(phrases, key=len, reverse=True))
    # Límites de palabra: "ip" no coincide con "tipo", ni "hora" con "ahora"
    return re.compile(rf"(?<!\w)(?:{alternation})(?!\w)")


def contains_phrase(text, phrases):
    """True si alguna frase aparece como palabra(s) completa(s), ignorando acentos y mayúsculas."""
    if not phrases:
        return False
    return _phrase_regex(phrases).search(normalize(text)) is not None


def remove_phrases(text, phrases):
    """Quita las frases (palabras completas) del texto original, conservando sus acentos."""
    if not phrases:
        return text
    text = unicodedata.normalize("NFC", text)
    result, last = [], 0
    for m in _phrase_regex(phrases).finditer(normalize(text)):
        result.append(text[last:m.start()])
        last = m.end()
    result.append(text[last:])
    return re.sub(r"\s+", " ", "".join(result)).strip()


# ---------- Duraciones habladas ("cinco minutos", "hora y media", "1 hora y 30 minutos") ----------
_UNITS = ["cero", "un", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
          "once", "doce", "trece", "catorce", "quince", "dieciseis", "diecisiete", "dieciocho",
          "diecinueve", "veinte", "veintiun", "veintidos", "veintitres", "veinticuatro", "veinticinco",
          "veintiseis", "veintisiete", "veintiocho", "veintinueve"]
_TENS = {"treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70,
         "ochenta": 80, "noventa": 90}

NUMBER_WORDS = {word: i for i, word in enumerate(_UNITS)}
NUMBER_WORDS.update({"una": 1, "uno": 1, "veintiuna": 21, "veintiuno": 21, "media": 0.5, "medio": 0.5})
for _ten, _value in _TENS.items():
    NUMBER_WORDS[_ten] = _value
    for _i in range(1, 10):
        NUMBER_WORDS[f"{_ten} y {_UNITS[_i]}"] = _value + _i
    NUMBER_WORDS[f"{_ten} y una"] = _value + 1
    NUMBER_WORDS[f"{_ten} y uno"] = _value + 1

_UNIT_SECONDS = {"segundo": 1, "minuto": 60, "hora": 3600}
_NUMBER_ALT = "|".join(sorted(NUMBER_WORDS, key=len, reverse=True))
_DURATION_RE = re.compile(
    rf"(?<!\w)(\d+(?:[.,]\d+)?|{_NUMBER_ALT})\s+(segundo|minuto|hora)s?(?!\w)(\s+y\s+medi[ao](?!\w))?"
)


def parse_duration(text):
    """Devuelve (segundos, inicio, fin) de la duración mencionada en el texto, o None si no hay.

    inicio/fin son posiciones sobre el texto original, para poder recortar la duración de la frase.
    """
    norm = normalize(text)
    total, start, end = 0.0, None, None
    for m in _DURATION_RE.finditer(norm):
        raw = m.group(1)
        amount = NUMBER_WORDS[raw] if raw in NUMBER_WORDS else float(raw.replace(",", "."))
        if m.group(3):
            amount += 0.5
        total += amount * _UNIT_SECONDS[m.group(2)]
        start = m.start() if start is None else start
        end = m.end()
    if start is None or total <= 0:
        return None
    return int(round(total)), start, end


def format_duration(seconds):
    """'1 minuto', '2 horas y 30 minutos'... con singular y plural correctos."""
    seconds = int(seconds)
    parts = []
    for name, size in (("hora", 3600), ("minuto", 60), ("segundo", 1)):
        amount, seconds = divmod(seconds, size)
        if amount:
            parts.append(f"{amount} {name}" + ("" if amount == 1 else "s"))
    if not parts:
        return "0 segundos"
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " y " + parts[-1]


# ---------- Hora del día ("a las 9 de la mañana", "a las 11", "a las 7 y media de la tarde") ----------
_INT_WORDS = {w: v for w, v in NUMBER_WORDS.items() if isinstance(v, int) and 1 <= v <= 59}
_INT_ALT = "|".join(sorted(_INT_WORDS, key=len, reverse=True))
_CLOCK_RE = re.compile(
    rf"(?<!\w)a\s+las?\s+(\d{{1,2}}|{_INT_ALT})(?!\w)"
    rf"(?:\s*[:.]\s*(\d{{2}})(?!\d)|\s+(?:y|con)\s+(media|cuarto|\d{{1,2}}|{_INT_ALT})(?!\w))?"
    r"(?:\s+(?:de|por)\s+la\s+(manana|tarde|noche|madrugada)(?!\w)|\s*([ap])\.?\s?m\b\.?)?"
)
_NOON_RE = re.compile(r"(?<!\w)al?\s+(medio\s?dia|media\s?noche)(?!\w)")
_TOMORROW_RE = re.compile(r"(?<!la\s)(?<!\w)manana(?!\w)")


def _to_int(raw):
    return int(raw) if raw.isdigit() else _INT_WORDS[raw]


def parse_clock_time(text, now):
    """Devuelve (datetime en que debe sonar, inicio, fin) para una hora dicha en el texto, o None.

    Sin "de la mañana/tarde" se elige la próxima vez que el reloj marque esa hora:
    "a las 11" dicho a las 3 de la tarde es las 11 de la noche.
    """
    from datetime import timedelta

    norm = normalize(text)
    m = _CLOCK_RE.search(norm)
    if m:
        hour = _to_int(m.group(1))
        if m.group(2):
            minute = int(m.group(2))
        elif m.group(3):
            minute = {"media": 30, "cuarto": 15}.get(m.group(3)) or _to_int(m.group(3))
        else:
            minute = 0
        period = m.group(4) or {"a": "manana", "p": "tarde"}.get(m.group(5))
    else:
        m = _NOON_RE.search(norm)
        if not m:
            return None
        hour, minute, period = (12, 0, "tarde") if "dia" in m.group(1) else (12, 0, "noche")

    if hour > 23 or minute > 59:
        return None

    # "mañana a las 9" (el día siguiente), distinto de "a las 9 de la mañana"
    rest = norm[:m.start()] + " " + norm[m.end():]
    tomorrow = _TOMORROW_RE.search(rest) is not None

    if period in ("manana", "madrugada"):
        candidates = [hour % 12 if hour <= 12 else hour]
    elif period == "tarde":
        candidates = [hour if hour >= 12 else hour + 12]
    elif period == "noche":
        candidates = [0 if hour == 12 else (hour if hour > 12 else hour + 12)]
    elif hour == 0 or hour > 12 or tomorrow:
        candidates = [hour]                      # formato de 24 horas, o "mañana a las 9"
    else:
        candidates = [hour % 12, hour % 12 + 12]  # ambiguo: la que llegue primero

    base = now.replace(second=0, microsecond=0)
    options = []
    for h in candidates:
        due = base.replace(hour=h, minute=minute)
        if tomorrow:
            due += timedelta(days=1)
        elif due <= now:
            due += timedelta(days=1)
        options.append(due)
    return min(options), m.start(), m.end()


def format_clock(moment):
    """datetime -> 'las 9 de la mañana', 'la 1 y 30 de la tarde' (para que BMO lo diga)."""
    hour12 = moment.hour % 12 or 12
    article = "la" if hour12 == 1 else "las"
    minutes = f" y {moment.minute}" if moment.minute else ""
    if moment.hour < 12:
        period = "de la mañana"
    elif moment.hour < 19:
        period = "de la tarde"
    else:
        period = "de la noche"
    return f"{article} {hour12}{minutes} {period}"


def in_time_range(now, start, end):
    """¿La hora `now` cae entre start y end? Acepta rangos que cruzan la medianoche (22:00 a 08:00)."""
    if start <= end:
        return start <= now < end
    return now >= start or now < end


def parse_price(raw):
    """'$1,299.50' -> 1299.5. Devuelve None si no hay número."""
    cleaned = re.sub(r"[^\d.]", "", str(raw).replace(",", ""))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def trim_to_sentence(text):
    """Si el texto quedó cortado a medias, lo recorta al final de la última oración completa."""
    text = text.strip()
    if not text or text[-1] in ".!?…":
        return text
    cut = max(text.rfind(c) for c in ".!?…")
    return text[: cut + 1] if cut > 0 else text


_SENTENCE_END_RE = re.compile(r"[.!?…]+[\"'»)]*\s+")


def pop_sentences(buffer, min_chars=25):
    """Separa del buffer las oraciones ya completas. Devuelve (oraciones, resto sin terminar).

    Las oraciones muy cortas ("¡Hola!") se juntan con la siguiente para no sintetizar trocitos.
    """
    sentences, start = [], 0
    for m in _SENTENCE_END_RE.finditer(buffer):
        if m.end() - start >= min_chars:
            sentences.append(buffer[start:m.end()].strip())
            start = m.end()
    return sentences, buffer[start:]
