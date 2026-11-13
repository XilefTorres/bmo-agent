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

<<<<<<< Updated upstream
    # Ejecutar en un hilo separado para no trabar el loop principal
    threading.Thread(target=run_scheduler, daemon=True).start()
=======
def abrir_modo_juego(face):
    """Función para gestionar la transición al modo emulador"""
    global MODO_JUEGO_ACTIVO
    frase_juego = "¡Iniciando mi interfaz de juegos!"
    print(f"BMO: {frase_juego}")
    
    face.set_state("hablando")
    speak(frase_juego)
    
    # Activamos el seguro para no usar el LLM
    MODO_JUEGO_ACTIVO = True
    
    # Intentar liberar memoria si el objeto bmo_brain tiene esa función
    if hasattr(bmo_brain, 'unload_model'):
        bmo_brain.unload_model()

    face.set_state("jugando")

    try:
        # Nota: Aquí el hilo se detiene hasta que Pegasus se cierra
        subprocess.run(["pegasus"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error al ejecutar Pegasus: {e}")
        speak("¡Oh no, Xilef! Algo salió mal al intentar abrir mis juegos.")
    except FileNotFoundError:
        print(">>> Comando 'pegasus' no encontrado, intentando ruta directa...")
        subprocess.run(["/home/xileftorres/PegasusApp/pegasus-fe"])
    
    # Al cerrar Pegasus, desactivamos el seguro
    MODO_JUEGO_ACTIVO = False

    if hasattr(bmo_brain, 'reload_model'):
        bmo_brain.reload_model()
    
    vuelta_frase = "¡Bienvenido de vuelta! ¿Te divertiste jugando?"
    print(f"BMO: {vuelta_frase}")
    face.set_state("hablando")
    speak(vuelta_frase)
    face.set_state("esperando")
>>>>>>> Stashed changes

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
        
<<<<<<< Updated upstream
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
=======
        if any(word in input_text for word in WAKE_WORDS):
            minimizar_todo_excepto_bmo()
            # Si estamos jugando, BMO solo da una respuesta corta sin usar el LLM
            if MODO_JUEGO_ACTIVO:
                # Sin cambiar el estado: la cara de juego vuelve sola cuando termine de hablar
                speak("¡Sigo aquí! Pero estoy concentrado en tus juegos ahora mismo.")
                continue

            face.set_state("escuchando")
            
            clean_prompt = input_text
            for word in WAKE_WORDS:
                clean_prompt = clean_prompt.replace(word, "")
            
            clean_prompt = re.sub(r'[^\w\s]', '', clean_prompt).strip()
            user_display = clean_prompt if clean_prompt else "[Solo despertar]"
            print(f"\nXilef: {user_display}")

            palabras_juego = ["juguemos", "jugar", "videojuegos", "emulador"]
            
            if len(clean_prompt) < 2:
                face.set_state("hablando")
                speak(random.choice(ACTIVATION_PHRASES))
            
            elif any(p in clean_prompt for p in palabras_juego):
                # Lanzar el modo juego en un hilo separado para no bloquear el listener
                game_thread = threading.Thread(target=abrir_modo_juego, args=(face,))
                game_thread.start()
                continue  # el hilo del juego maneja la cara; no la pisamos con "esperando"
            
>>>>>>> Stashed changes
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