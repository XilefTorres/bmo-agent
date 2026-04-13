import os
import random  # Para que las frases de activación varíen
from dotenv import load_dotenv
from google import genai
from google.genai import types
from modules.stt_listener import BMOListener
from modules.tts_speaker import speak

# --- CONFIGURACIÓN DE GEMINI ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("ERROR: No se encontró la GEMINI_API_KEY en el .env")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

config_bmo = types.GenerateContentConfig(
    system_instruction="Eres BMO de Hora de Aventura. Alegre, infantil, leal. Responde muy corto (máximo 30 palabras). No uses emojis.",
    temperature=0.7
)

WAKE_WORDS = ["vimos", "bmo", "vmos", "veamos", "demo"]

# Frases rápidas para cuando BMO escucha su nombre
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
            model="gemini-2.0-flash-lite",
            contents=prompt,
            config=config_bmo
        )
        return response.text
    except Exception as e:
        print(f"Error en Gemini: {e}")
        return "Mi cerebro de robot tiene un error de conexión."

def main():
    listener = BMOListener()
    print("\n>>> BMO ONLINE. Di 'BMO'...")

    for text in listener.listen():
        if any(word in text for word in WAKE_WORDS):
            # 1. Limpiar el prompt
            clean_prompt = text
            for word in WAKE_WORDS:
                clean_prompt = clean_prompt.replace(word, "")
            clean_prompt = clean_prompt.strip()

            user_display = clean_prompt if clean_prompt else "[Solo nombre]"
            print(f"\nXilef: {user_display}")

            # 2. Lógica de habla inmediata
            if not clean_prompt:
                # Si solo dijo "BMO", responde algo de la lista
                speak(random.choice(ACTIVATION_PHRASES))
            else:
                # Si dijo "BMO" + una pregunta, da una señal de que escuchó antes de ir a Gemini
                # Esto reduce la sensación de latencia
                print("BMO: ¡Entendido!") 
                # Opcional: speak("¡Oh!") o algo muy corto para confirmar
                
                answer = ask_gemini(clean_prompt)
                speak(answer)
            
            listener.reset()
            print("\n>>> BMO listo de nuevo...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBMO se va a dormir. ¡Adiós!")