import wikipediaapi
import re
import random
from modules.tts_speaker import speak
from modules.base_command import BaseCommand

class WikipediaCommand(BaseCommand):
    def __init__(self, face, bmo_brain):
        super().__init__(face, bmo_brain)
        # Importante: Wikipedia pide un User-Agent descriptivo
        self.wiki = wikipediaapi.Wikipedia(
            user_agent="BMO_Agent_Xilef/0.8 (xilefjacobotorres@gmail.com)",
            language='es'
        )

    @property
    def keywords(self):
        return ["busca en wikipedia", "investiga sobre", "cuéntame de"]

    @property
    def threaded(self):
        return True # Recomendado para peticiones de red en la Raspberry Pi

    def execute(self, text, actions_manager):
        self.face.set_state("pensando")
        
        # Extraemos lo que queremos buscar
        query = self._extract_query(text.lower())
        print(f">>> BMO consultando archivos de Wikipedia: {query}")

        page = self.wiki.page(query)

        if page.exists():
            # Obtenemos un resumen manejable (primeros 2 o 3 párrafos)
            wiki_context = page.summary[:700]
            
            # Le pedimos al cerebro de BMO que procese la info con su personalidad
            prompt = (
                f"Contexto de Wikipedia: {wiki_context}\n\n"
                f"Pregunta del usuario: {text}\n"
                "Instrucción: Responde de forma breve, útil y con la personalidad de BMO."
            )
            respuesta = self.bmo_brain.ask(prompt)
        else:
            respuesta = f"¡Oh, rayos! Mis sensores no encontraron nada sobre {query} en Wikipedia."

        print(f"BMO (Wiki): {respuesta}")
        self.face.set_state("hablando")
        speak(respuesta)
        self.face.set_state("esperando")

    def _extract_query(self, text):
        """Limpia las keywords para obtener el término de búsqueda puro"""
        clean_text = text
        for word in self.keywords:
            clean_text = clean_text.replace(word, "")
        
        # Limpieza extra de símbolos y espacios
        clean_text = re.sub(r'[^\w\s]', '', clean_text).strip()
        return clean_text

    def learn_something_new(self):
        """BMO busca algo basado en tus gustos y te lo cuenta"""
        mis_gustos = ["Programación", "Videojuegos", "Electrónica", "Sinaloa", "Historia", "Arte", "Dinosaurios", "Manga"]
        tema_elegido = random.choice(mis_gustos)
        
        # Usamos la búsqueda de Wikipedia para obtener una página relacionada
        # Tip: 'search' de la API de wikipedia puede darte títulos exactos
        self.face.set_state("pensando")
        page = self.wiki.page(tema_elegido)
        
        if page.exists():
            context = page.summary[:800]
            prompt = (
                f"Es tiempo de un nuevo dato curioso. Encontré información sobre {tema_elegido} en mis archivos.\n"
                f"Info: {context}\n"
                "Instrucción: Despierta a Xilef con entusiasmo y cuéntale este dato curioso con tu personalidad de BMO."
            )
            respuesta = self.bmo_brain.ask(prompt)
            
            self.face.set_state("hablando")
            speak(respuesta)
            self.face.set_state("esperando")