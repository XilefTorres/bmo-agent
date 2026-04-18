import os
import random
import threading
import re
from modules.stt_listener import BMOListener
from modules.tts_speaker import speak
from modules.bmo_face import BMOFace
from modules.local_llm import LocalBMO 
from modules.actions import BMOActions

WAKE_WORDS = ["beemo", "vimos", "vmos", "primo", "vivo"]

print(">>> Iniciando sistemas de BMO...")
print(">>> Cargando redes neuronales locales... (Llama 3.2 1B)")
bmo_brain = LocalBMO() 

def bmo_brain_loop(face):
    actions = BMOActions(face, bmo_brain)
    listener = BMOListener()
    print("\n>>> BMO ONLINE. Di 'BMO' para despertar mis circuitos...")

    for text in listener.listen():
        input_text = text.lower() 
        
        if any(word in input_text for word in WAKE_WORDS):
            if actions.modo_juego_activo:
                face.set_state("hablando")
                speak("¡Sigo aquí! Pero estoy concentrado en tus juegos ahora mismo.")
                continue
            
            face.set_state("esperando")
            clean_prompt = input_text
            for word in WAKE_WORDS:
                clean_prompt = clean_prompt.replace(word, "")
            clean_prompt = re.sub(r'[^\w\s]', '', clean_prompt).strip()
            
            user_display = clean_prompt if clean_prompt else "[Solo despertar]"
            print(f"\nXilef: {user_display}")

            if len(clean_prompt) < 2:
                face.set_state("hablando")
                speak(random.choice(actions.activation_phrases))
            
            # Intentamos despachar a través del nuevo sistema de acciones
            elif actions.dispatch(clean_prompt):
                pass # La acción ya se ejecutó o se mandó a un hilo
                
            else:
                face.set_state("pensando")
                print("BMO está procesando internamente...") 
                
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