import os
import random
import threading
import re
import subprocess
import time
from modules.stt_listener import BMOListener
from modules.tts_speaker import speak
from modules.bmo_face import BMOFace
from modules.local_llm import LocalBMO 

WAKE_WORDS = ["vimos", "bmo", "vmos", "veamos", "demo"]
MODO_JUEGO_ACTIVO = False

ACTIVATION_PHRASES = [
    "¡Hola, Xilef! ¿En qué puedo ayudarte?",
    "¡BMO presente! ¿Qué tienes en mente?",
    "¡Aquí estoy, Xilef! Mis circuitos están listos."
]

print(">>> Iniciando sistemas de BMO...")
print(">>> Cargando redes neuronales locales... (Llama 3.2 1B)")
bmo_brain = LocalBMO() 

def minimizar_todo_excepto_bmo():
    """Limpia el escritorio para darle foco a BMO"""
    try:
        subprocess.run(["wmctrl", "-k", "on"], check=False)
        # Nota: Si wmctrl no está instalado, corre: sudo dnf install wmctrl
    except Exception as e:
        print(f"[!] No se pudo minimizar las ventanas: {e}")

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

    face.set_state("esperando")
    
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

def bmo_brain_loop(face):
    listener = BMOListener()
    print("\n>>> BMO ONLINE. Di 'BMO' para despertar mis circuitos...")

    for text in listener.listen():
        input_text = text.lower() 
        
        if any(word in input_text for word in WAKE_WORDS):
            minimizar_todo_excepto_bmo()
            # Si estamos jugando, BMO solo da una respuesta corta sin usar el LLM
            if MODO_JUEGO_ACTIVO:
                face.set_state("hablando")
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