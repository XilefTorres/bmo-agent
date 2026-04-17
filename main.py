import os
import random
import threading
import re
from modules.stt_listener import BMOListener
from modules.tts_speaker import speak
from modules.bmo_face import BMOFace
from modules.local_llm import LocalBMO 

WAKE_WORDS = ["vimos", "bmo", "vmos", "veamos", "demo"]

ACTIVATION_PHRASES = [
    "¡Hola, Xilef! Estaba esperando a que me hablaras, ¿en qué puedo ayudarte?",
    "¡BMO está presente y listo para la acción! ¿Qué tienes en mente hoy?",
    "¿Me llamaste? Justo estaba pensando en un juego nuevo, pero te escucho.",
    "¡Aquí estoy, Xilef! Mis circuitos están brillando de alegría por hablar contigo.",
    "¡Dime! Soy un robot multifuncional y estoy a tus órdenes, ¿qué necesitas?",
    "¡Oh, Xilef! Me asustaste un poquito, pero ya estoy despierto y listo."
]

print(">>> Iniciando sistemas de BMO...")
print(">>> Cargando redes neuronales locales... (Llama 3.2 1B)")
bmo_brain = LocalBMO() 

def bmo_brain_loop(face):
    listener = BMOListener()
    print("\n>>> BMO ONLINE. Di 'BMO' para despertar mis circuitos...")

    for text in listener.listen():
        input_text = text.lower() 
        
        if any(word in input_text for word in WAKE_WORDS):
            face.set_state("escuchando")
            
            clean_prompt = input_text
            for word in WAKE_WORDS:
                clean_prompt = clean_prompt.replace(word, "")
            
            clean_prompt = re.sub(r'[^\w\s]', '', clean_prompt).strip()
            user_display = clean_prompt if clean_prompt else "[Solo despertar]"
            print(f"\nXilef: {user_display}")

            if len(clean_prompt) < 2:
                face.set_state("hablando")
                speak(random.choice(ACTIVATION_PHRASES))
            else:
                face.set_state("pensando")
                print("BMO está procesando internamente...") 
                
                # Respuesta del modelo local sin restricciones de la nube
                answer = bmo_brain.ask(clean_prompt)
                
                print(f"BMO: {answer}")
                face.set_state("hablando")
                speak(answer)
            
            listener.reset()
            face.set_state("esperando")
            print("\n>>> BMO listo y atento...")

def main():
    face = BMOFace()
    brain_thread = threading.Thread(target=bmo_brain_loop, args=(face,), daemon=True)
    brain_thread.start()
    face.update_loop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] BMO está cerrando sus procesos. ¡Hasta luego, Xilef!")