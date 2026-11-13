import re
import requests
from modules import settings
from modules.tts_speaker import speak
from modules.base_command import BaseCommand
from modules.text_utils import normalize

# Códigos de tiempo de la OMM que devuelve Open-Meteo
WEATHER_CODES = {
    0: "cielo despejado", 1: "cielo mayormente despejado", 2: "cielo parcialmente nublado", 3: "cielo nublado",
    45: "niebla", 48: "niebla con escarcha",
    51: "llovizna ligera", 53: "llovizna", 55: "llovizna intensa",
    56: "llovizna helada", 57: "llovizna helada intensa",
    61: "lluvia ligera", 63: "lluvia", 65: "lluvia fuerte",
    66: "lluvia helada", 67: "lluvia helada fuerte",
    71: "nevada ligera", 73: "nevada", 75: "nevada fuerte", 77: "granizo fino",
    80: "chubascos ligeros", 81: "chubascos", 82: "chubascos fuertes",
    85: "chubascos de nieve", 86: "chubascos de nieve fuertes",
    95: "tormenta eléctrica", 96: "tormenta con granizo", 99: "tormenta fuerte con granizo",
}

# "clima en Culiacán", "va a llover en la Ciudad de México mañana"
_CITY_RE = re.compile(r"(?<!\w)en\s+(.+?)(?:\s+(?:hoy|ahora|ahorita|manana|por favor))*\s*$")


def extract_city(text):
    """Saca la ciudad de la frase (con sus acentos originales), o '' si no se mencionó."""
    match = _CITY_RE.search(normalize(text))
    if not match:
        return ""
    # "va a llover en la tarde" habla de un momento, no de una ciudad
    if re.match(r"(?:la|el|esta|este|estos|unos?|unas?)\s", match.group(1)) and \
            re.search(r"(?:tarde|noche|manana|dia|dias|rato|semana|horas?|minutos?)$", match.group(1)):
        return ""
    return re.sub(r"[^\w\s]", "", text[match.start(1):match.end(1)]).strip()


class WeatherCommand(BaseCommand):
    @property
    def keywords(self):
        return ["clima", "pronóstico", "va a llover", "lloverá", "qué tiempo hace", "tiempo hará",
                "hace frío", "hace calor"]

    @property
    def threaded(self):
        return True

    def _geocode(self, city):
        res = requests.get("https://geocoding-api.open-meteo.com/v1/search",
                           params={"name": city, "count": 1, "language": "es"}, timeout=8)
        res.raise_for_status()
        results = res.json().get("results") or []
        if not results:
            return None
        place = results[0]
        return {"name": place["name"], "lat": place["latitude"], "lon": place["longitude"]}

    def _forecast(self, place):
        res = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": place["lat"], "longitude": place["lon"],
            "current": "temperature_2m,apparent_temperature,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto", "forecast_days": 1,
        }, timeout=8)
        res.raise_for_status()
        return res.json()

    def execute(self, text, actions_manager):
        city = extract_city(text)
        place = None if city else settings.get("weather_place")

        if not city and not place:
            speak("Todavía no sé dónde vives, Xilef. Dime por ejemplo: clima en Guadalajara, y lo recordaré.")
            return False

        with self.face.estado("pensando"):
            try:
                if city:
                    place = self._geocode(city)
                    if place is None:
                        speak(f"No encontré ninguna ciudad llamada {city} en mis mapas.")
                        return False
                    # La primera ciudad que preguntes queda como tu ciudad por defecto
                    if not settings.get("weather_place"):
                        settings.set("weather_place", place)
                data = self._forecast(place)
            except (requests.RequestException, ValueError, KeyError) as e:
                print(f"[!] Error consultando el clima: {e}")
                self.face.show_expression("offline", 3000)
                speak("¡Rayos! No pude conectarme con el satélite del clima.")
                return False

        current, daily = data["current"], data["daily"]
        descripcion = WEATHER_CODES.get(current["weather_code"], "un clima raro")
        frase = (f"En {place['name']} hay {descripcion} y {round(current['temperature_2m'])} grados, "
                 f"con sensación de {round(current['apparent_temperature'])}. "
                 f"Hoy la máxima es de {round(daily['temperature_2m_max'][0])} "
                 f"y la mínima de {round(daily['temperature_2m_min'][0])}.")
        lluvia = daily["precipitation_probability_max"][0]
        if lluvia is not None:
            frase += f" La probabilidad de lluvia es del {round(lluvia)} por ciento."
            if lluvia >= 60:
                frase += " ¡Llévate un paraguas!"
        print(f"BMO (Clima): {frase}")
        speak(frase)
        return True
