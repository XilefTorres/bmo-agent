import os
import random
import threading
import re 
from dotenv import load_dotenv
from google import genai
from google.genai import types
from modules.stt_listener import BMOListener
from modules.tts_speaker import speak
from modules.bmo_face import BMOFace

# --- CONFIGURACIÓN DE GEMINI ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("ERROR: No se encontró la GEMINI_API_KEY en el .env")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

config_bmo = types.GenerateContentConfig(
    system_instruction="Eres BMO de Hora de Aventura. Alegre, infantil, leal. Responde muy corto (máximo 50 palabras). No uses emojis.",
    temperature=0.7
)

WAKE_WORDS = ["vimos", "bmo", "vmos", "veamos", "demo"]

ACTIVATION_PHRASES = [
    "¡Hola, Xilef! Estaba esperando a que me hablaras, ¿en qué puedo ayudarte?",
    "¡BMO está presente y listo para la acción! ¿Qué tienes en mente hoy?",
    "¿Me llamaste? Justo estaba pensando en un juego nuevo, pero te escucho.",
    "¡Aquí estoy, Xilef! Mis circuitos están brillando de alegría por hablar contigo.",
    "¡Dime! Soy un robot multifuncional y estoy a tus órdenes, ¿qué necesitas?",
    "¡Oh, Xilef! Me asustaste un poquito, pero ya estoy despierto y listo."
]

def ask_gemini(prompt):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=config_bmo
        )
        return response.text
    except Exception as e:
        print(f"Error en Gemini: {e}")
        return "Mi cerebro de robot tiene un error de conexión."

# --- NUEVA FUNCIÓN: EL CEREBRO DE BMO ---
def bmo_brain_loop(face):
    """Este ciclo corre en segundo plano escuchando y pensando"""
    listener = BMOListener()
    print("\n>>> BMO ONLINE. Di 'BMO'...")

    for text in listener.listen():
        input_text = text.lower() # Convertimos todo a minúsculas por seguridad
        
        if any(word in input_text for word in WAKE_WORDS):
            face.set_state("escuchando")
            
            clean_prompt = input_text
            for word in WAKE_WORDS:
                clean_prompt = clean_prompt.replace(word, "")
            
            # --- EL FILTRO SALVA-CRÉDITOS ---
            # 1. Borramos cualquier carácter que no sea letra o número (como puntos o comas)
            clean_prompt = re.sub(r'[^\w\s]', '', clean_prompt).strip()

            user_display = clean_prompt if clean_prompt else "[Solo nombre/ruido]"
            print(f"\nXilef: {user_display}")

            # 2. Si la frase sobrante es muy corta (vacía o solo un gemido de 1 letra)
            # Entendemos que solo querías despertar a BMO. ¡No llamamos a la API!
            if len(clean_prompt) < 2:
                face.set_state("hablando")
                speak(random.choice(ACTIVATION_PHRASES))
            else:
                face.set_state("pensando")
                print("BMO: ¡Entendido!") 
                
                answer = ask_gemini(clean_prompt)
                
                face.set_state("hablando")
                speak(answer)
            
            listener.reset()
            face.set_state("esperando")
            print("\n>>> BMO listo de nuevo...")

def main():
    face = BMOFace()
    brain_thread = threading.Thread(target=bmo_brain_loop, args=(face,), daemon=True)
    brain_thread.start()
    face.update_loop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBMO se va a dormir. ¡Adiós!")