import requests
from modules.tts_speaker import speak, speak_stream
from modules.base_command import BaseCommand

class NBAInfoCommand(BaseCommand):
    @property
    def keywords(self):
        # Palabras clave para activar la búsqueda de la NBA
        return ["nba", "basquetbol", "básquetbol", "partidos de hoy", "marcador"]

    @property
    def threaded(self):
        return True

    def _fetch_summary(self):
        """Devuelve el resumen crudo de los partidos de hoy ('' si no hay partidos)."""
        # Usamos el endpoint público de ESPN que es muy ligero para la Raspberry Pi
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()

        resumen_crudo = []
        for event in response.json().get('events', []):
            estado = event.get('status', {}).get('type', {}).get('description')
            equipos = event.get('name')
            # Marcadores
            score_list = []
            for comp in event.get('competitions', [{}])[0].get('competitors', []):
                team_name = comp.get('team', {}).get('abbreviation')
                score = comp.get('score')
                score_list.append(f"{team_name}: {score}")

            resumen_crudo.append(f"Partido: {equipos} | Estado: {estado} | Marcador: {' vs '.join(score_list)}")
        return " | ".join(resumen_crudo)

    def execute(self, text, actions_manager):
        speak("¡Oí N B A! Dame un segundo para sintonizar mis antenas deportivas.")

        # El 'with' regresa la cara a su estado anterior aunque algo falle
        with self.face.estado("pensando"):
            try:
                texto_para_llm = self._fetch_summary()
                if not texto_para_llm:
                    respuesta = "¡Oh! Parece que no hay partidos programados para hoy en mis circuitos."
                else:
                    # Le pedimos al LLM que analice y resuma como BMO
                    prompt = (f"Actúa como BMO. Aquí tienes los datos de la NBA de hoy: {texto_para_llm}. "
                              "Haz un resumen muy breve, alegre y entusiasta de los partidos más importantes o resultados actuales.")
                    speak_stream(self.bmo_brain.ask_stream(prompt))
                    return True
            except requests.RequestException as e:
                print(f"Error de red en NBAInfo: {e}")
                respuesta = "¡Rayos! No pude conectarme con el satélite de la liga. ¿Habrá interferencia?"
            except Exception as e:
                print(f"Error en NBAInfo: {e}")
                respuesta = "¡Mis circuitos deportivos hicieron cortocircuito! No pude obtener la información."

        speak(respuesta)
        return True
