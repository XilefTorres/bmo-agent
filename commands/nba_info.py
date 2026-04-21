import requests
from modules.tts_speaker import speak
from modules.base_command import BaseCommand

class NBAInfoCommand(BaseCommand):
    @property
    def keywords(self):
        # Palabras clave para activar la búsqueda de la NBA
        return ["nba", "basquetbol", "básquetbol", "partidos de hoy", "marcador"]

    @property
    def threaded(self):
        return True

    def execute(self, text, actions_manager):
        self.face.set_state("pensando")
        speak("¡Oí N B A! Dame un segundo para sintonizar mis antenas deportivas.")

        try:
            # Usamos el endpoint público de ESPN que es muy ligero para la Raspberry Pi
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                eventos = data.get('events', [])
                
                if not eventos:
                    self.face.set_state("hablando")
                    speak("¡Oh! Parece que no hay partidos programados para hoy en mis circuitos.")
                    self.face.set_state("esperando")
                    return True

                # Construimos un resumen crudo para el LLM
                resumen_crudo = []
                for event in eventos:
                    estado = event.get('status', {}).get('type', {}).get('description')
                    equipos = event.get('name')
                    # Marcadores
                    score_list = []
                    for comp in event.get('competitions', [{}])[0].get('competitors', []):
                        team_name = comp.get('team', {}).get('abbreviation')
                        score = comp.get('score')
                        score_list.append(f"{team_name}: {score}")
                    
                    resumen_crudo.append(f"Partido: {equipos} | Estado: {estado} | Marcador: {' vs '.join(score_list)}")

                texto_para_llm = " | ".join(resumen_crudo)

                # 2. Le pedimos al LLM que analice y resuma como BMO
                prompt = (f"Actúa como BMO. Aquí tienes los datos de la NBA de hoy: {texto_para_llm}. "
                          "Haz un resumen muy breve, alegre y entusiasta de los partidos más importantes o resultados actuales.")
                
                respuesta_bmo = self.bmo_brain.ask(prompt)
                self.face.set_state("hablando")
                speak(respuesta_bmo)
            else:
                speak("¡Rayos! No pude conectarme con el satélite de la liga. ¿Habrá interferencia?")
        except Exception as e:
            print(f"Error en NBAInfo: {e}")
            speak("¡Mis circuitos deportivos hicieron cortocircuito! No pude obtener la información.")

        self.face.set_state("esperando")
        return True