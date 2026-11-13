import os
import wikipediaapi
import re
import random
import requests
from modules.tts_speaker import speak, speak_stream
from modules.base_command import BaseCommand
from modules.text_utils import normalize, remove_phrases

# Wikipedia pide un User-Agent descriptivo con contacto. El correo va en la variable de
# entorno BMO_CONTACT_EMAIL (no en el código que se sube a git).
_CONTACT = os.environ.get("BMO_CONTACT_EMAIL", "").strip()
USER_AGENT = "BMO_Agent_Xilef/0.8" + (f" ({_CONTACT})" if _CONTACT else "")

# "cuéntame de/sobre X", pero no "cuéntame de tu día" o "cuéntame de ti" (eso es plática, no Wikipedia)
_TELL_ME_RE = re.compile(r"(?<!\w)cuentame (?:de|sobre|acerca de)\s+(?!ti\b|tu\b|tus\b|mi\b|mis\b|como\b|que\b)\w")


class WikipediaCommand(BaseCommand):
    def __init__(self, face, bmo_brain):
        super().__init__(face, bmo_brain)
        self.wiki = wikipediaapi.Wikipedia(user_agent=USER_AGENT, language='es')

    @property
    def keywords(self):
        return ["busca en wikipedia", "investiga sobre", "investiga acerca de"]

    def matches(self, text):
        return super().matches(text) or _TELL_ME_RE.search(normalize(text)) is not None

    @property
    def threaded(self):
        return True # Recomendado para peticiones de red en la Raspberry Pi

    def _resolve_title(self, query):
        """Usa el buscador de Wikipedia para pasar de 'mexico' al título real 'México'."""
        try:
            res = requests.get(
                "https://es.wikipedia.org/w/api.php",
                params={"action": "query", "list": "search", "srsearch": query,
                        "srlimit": 1, "format": "json"},
                headers={"User-Agent": USER_AGENT},
                timeout=8,
            )
            results = res.json().get("query", {}).get("search", [])
            if results:
                return results[0]["title"]
        except (requests.RequestException, ValueError) as e:
            print(f"[!] Búsqueda de Wikipedia falló: {e}")
        return query

    def execute(self, text, actions_manager):
        with self.face.estado("pensando"):
            # Extraemos lo que queremos buscar
            query = self._extract_query(text.lower())
            titulo = self._resolve_title(query)
            print(f">>> BMO consultando archivos de Wikipedia: {query} -> {titulo}")

            page = self.wiki.page(titulo)

            if page.exists():
                # Obtenemos un resumen manejable (primeros 2 o 3 párrafos)
                wiki_context = page.summary[:700]

                # Le pedimos al cerebro de BMO que procese la info con su personalidad
                prompt = (
                    f"Contexto de Wikipedia sobre {titulo}: {wiki_context}\n\n"
                    f"Pregunta del usuario: {text}\n"
                    "Instrucción: Responde de forma breve, útil y con la personalidad de BMO."
                )
                respuesta = speak_stream(self.bmo_brain.ask_stream(prompt))
            else:
                respuesta = f"¡Oh, rayos! Mis sensores no encontraron nada sobre {query} en Wikipedia."
                speak(respuesta)

        print(f"BMO (Wiki): {respuesta}")

    def _extract_query(self, text):
        """Limpia las keywords para obtener el término de búsqueda puro"""
        clean_text = remove_phrases(text, self.keywords + ["cuéntame de", "cuéntame sobre", "cuéntame acerca de"])

        # Limpieza extra de símbolos y espacios
        clean_text = re.sub(r'[^\w\s]', '', clean_text).strip()
        return clean_text

    def learn_something_new(self):
        """BMO busca algo basado en tus gustos y te lo cuenta"""
        mis_gustos = ["Programación", "Videojuegos", "Electrónica", "Sinaloa", "Historia", "Arte", "Dinosaurios", "Manga"]
        tema_elegido = random.choice(mis_gustos)

        with self.face.estado("pensando"):
            page = self.wiki.page(tema_elegido)
            if not page.exists():
                return

            context = page.summary[:800]
            prompt = (
                f"Es tiempo de un nuevo dato curioso. Encontré información sobre {tema_elegido} en mis archivos.\n"
                f"Info: {context}\n"
                "Instrucción: Despierta a Xilef con entusiasmo y cuéntale este dato curioso con tu personalidad de BMO."
            )
            speak_stream(self.bmo_brain.ask_stream(prompt))
