import os
import random
import threading
import re
import time
import schedule
from modules.stt_listener import BMOListener
from modules.tts_speaker import speak
from modules.bmo_face import BMOFace
from modules.local_llm import LocalBMO 
from modules.actions import BMOActions
from commands.wiki_search import WikipediaCommand

WAKE_WORDS = ["beemo", "vimos", "vmos", "primo", "vivo"]

print(">>> Iniciando sistemas de BMO...")
print(">>> Cargando redes neuronales locales... (Llama 3.2 1B)")
bmo_brain = LocalBMO() 

def start_daily_fact(wiki_cmd):
    def run_scheduler():
        # Mañana
        schedule.every().day.at("12:00").do(wiki_cmd.learn_something_new)
        
        # Noche
        schedule.every().day.at("22:30").do(wiki_cmd.learn_something_new)
        
        print(">>> [HORARIOS] Rutinas de aprendizaje programadas: 09:00 y 22:30")
        
        while True:
            schedule.run_pending()
            time.sleep(60) # Revisa cada minuto para no saturar el CPU

    # Ejecutar en un hilo separado para no trabar el loop principal
    threading.Thread(target=run_scheduler, daemon=True).start()

def bmo_brain_loop(face):
    actions = BMOActions(face, bmo_brain)
    face.key_callback = actions.handle_key

    # Buscamos el comando de wikipedia en la lista de acciones
    wiki_cmd = next((c for c in actions.commands if isinstance(c, WikipediaCommand)), None)
    
    if wiki_cmd:
        print(">>> Iniciando rutina de aprendizaje diario de BMO...")
        start_daily_fact(wiki_cmd)

    listener = BMOListener()
    is_active = False # BMO empieza en espera
    print("\n>>> BMO ONLINE. Di 'BMO' para despertar mis circuitos...")

    for text in listener.listen():
        input_text = text.lower() 
        
        # 1. Lógica de Activación: Despertar a BMO
        if not is_active:
            if any(word in input_text for word in WAKE_WORDS):
                is_active = True
                print("\n>>> [MODO CONSULTA ACTIVADO]")
                
                # Limpiamos el texto por si incluyó una orden junto al nombre (ej: "BMO qué hora es")
                clean_prompt = input_text
                for word in WAKE_WORDS:
                    clean_prompt = clean_prompt.replace(word, "")
                clean_prompt = re.sub(r'[^\w\s]', '', clean_prompt).strip()
                
                if not clean_prompt:
                    face.set_state("hablando")
                    speak(random.choice(actions.activation_phrases))
                    face.set_state("esperando")
                    continue # Esperar a la siguiente frase
                else:
                    # Si ya traía una orden, la procesamos directamente
                    input_text = clean_prompt
            else:
                continue # Ignorar si no escucha la palabra de activación

        # 2. Lógica de Desactivación: Regresar al estado de espera
        if any(stop_word in input_text for stop_word in ["adiós", "descansa", "duérmete", "silencio", "apagate"]):
            is_active = False
            face.set_state("hablando")
            speak("¡De acuerdo! Me iré a descansar un poco. ¡Llámame cuando quieras hablar!")
            face.set_state("esperando")
            print("\n>>> [MODO CONSULTA FINALIZADO]")
            continue

        # 3. Procesamiento de la Consulta (BMO ya está despierto)
        if actions.modo_juego_activo:
            face.set_state("hablando")
            speak("¡Sigo aquí! Pero estoy concentrado en tus juegos ahora mismo.")
            face.set_state("esperando")
            continue
            
        face.set_state("esperando")
        # Limpiamos posibles menciones redundantes de BMO por costumbre del usuario
        clean_prompt = input_text
        for word in WAKE_WORDS:
            clean_prompt = clean_prompt.replace(word, "")
        clean_prompt = re.sub(r'[^\w\s]', '', clean_prompt).strip()
            
        user_display = clean_prompt if clean_prompt else "[Escuchando...]"
        print(f"\nXilef: {user_display}")

        if len(clean_prompt) < 2:
            continue
            
        if actions.dispatch(clean_prompt):
            pass 
        else:
            face.set_state("pensando")
            print("BMO está procesando internamente...") 
            answer = bmo_brain.ask(clean_prompt)
            print(f"BMO: {answer}")
            face.set_state("hablando")
            speak(answer)
            face.set_state("esperando")
        
        listener.reset()
        print("\n>>> BMO sigue atento (di 'descansa' para dormirlo)...")

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