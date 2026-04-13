import os
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

# Inicializamos el nuevo cliente
client = genai.Client(api_key=GEMINI_API_KEY)

# Configuración del sistema (Instrucciones de BMO)
config_bmo = types.GenerateContentConfig(
    system_instruction="Eres BMO de Hora de Aventura. Alegre, infantil, leal. Responde muy corto (máximo 15 palabras). No uses emojis.",
    temperature=0.7
)

WAKE_WORDS = ["vimos", "bmo", "vemos", "veamos", "demo"]

def ask_gemini(prompt):
    try:
        # Usamos el modelo 3 Flash que te salió en el debug
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=prompt,
            config=config_bmo
        )
        return response.text
    except Exception as e:
        print(f"Error en Gemini: {e}")
        return "Mi cerebro de robot tiene un error de conexión."

def main():
    listener = BMOListener()
    print("\n>>> BMO ONLINE (Gemini 3). Di 'BMO'...")

    for text in listener.listen():
        if any(word in text for word in WAKE_WORDS):
            clean_prompt = text
            for word in WAKE_WORDS:
                clean_prompt = clean_prompt.replace(word, "")
            clean_prompt = clean_prompt.strip()

            user_display = clean_prompt if clean_prompt else "[Activación]"
            print(f"\nXilef: {user_display}")

            if not clean_prompt:
                speak("¿Dime, Xilef? ¿Quieres jugar?")
            else:
                answer = ask_gemini(clean_prompt)
                speak(answer)
            
            listener.reset()
            print("\n>>> BMO listo de nuevo...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBMO se va a dormir. ¡Adiós!")