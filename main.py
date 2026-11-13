import random
import threading
import re
import time
import traceback
import schedule
from datetime import datetime, time as dtime
from modules.stt_listener import BMOListener
from modules.tts_speaker import speak, speak_stream, is_speaking, last_spoke_at
from modules.bmo_face import BMOFace
from modules.local_llm import LocalBMO
from modules.actions import BMOActions
from modules.text_utils import contains_phrase, remove_phrases, in_time_range
from commands.wiki_search import WikipediaCommand

# Formas en que Google suele transcribir "BMO". Se buscan como palabra completa.
WAKE_WORDS = ["bmo", "beemo", "bimo", "vimo", "vimos", "vmos", "primo"]
STOP_WORDS = ["adiós", "descansa", "duérmete", "silencio", "apágate"]
# Segundos sin hablarle (ni hablar él) antes de que BMO vuelva a pedir su nombre
ACTIVE_TIMEOUT = 30
# Horario silencioso: BMO no habla por iniciativa propia (datos curiosos) entre estas horas
QUIET_START = dtime(22, 0)
QUIET_END = dtime(8, 0)

print(">>> Iniciando sistemas de BMO...")
print(">>> Cargando redes neuronales locales... (Llama 3.2 3B)")
bmo_brain = LocalBMO()

def start_daily_fact(wiki_cmd, actions):
    def daily_fact():
        # Si Xilef está jugando no recargamos el modelo ni hablamos encima del juego
        if actions.modo_juego_activo:
            print(">>> [HORARIOS] Dato curioso omitido: modo juego activo.")
            return
        # Las alarmas sí suenan en horario silencioso; lo que BMO dice por iniciativa propia, no
        if in_time_range(datetime.now().time(), QUIET_START, QUIET_END):
            print(">>> [HORARIOS] Dato curioso omitido: horario silencioso.")
            return
        try:
            wiki_cmd.learn_something_new()
        except Exception:
            print("[!] Error en el dato curioso diario:")
            traceback.print_exc()

    def run_scheduler():
        # Mañana
        schedule.every().day.at("12:00").do(daily_fact)

        # Noche
        schedule.every().day.at("20:30").do(daily_fact)

        print(">>> [HORARIOS] Rutinas de aprendizaje programadas: 12:00 y 20:30")

        while True:
            schedule.run_pending()
            time.sleep(60) # Revisa cada minuto para no saturar el CPU

    # Ejecutar en un hilo separado para no trabar el loop principal
    threading.Thread(target=run_scheduler, daemon=True).start()

def clean_text(text):
    """Quita el nombre de BMO y la puntuación de la frase."""
    text = remove_phrases(text, WAKE_WORDS)
    return re.sub(r'[^\w\s]', '', text).strip()

def bmo_brain_loop(face):
    actions = BMOActions(face, bmo_brain)
    face.key_callback = actions.handle_key

    # Buscamos el comando de wikipedia en la lista de acciones
    wiki_cmd = next((c for c in actions.commands if isinstance(c, WikipediaCommand)), None)

    if wiki_cmd:
        print(">>> Iniciando rutina de aprendizaje diario de BMO...")
        start_daily_fact(wiki_cmd, actions)

    listener = BMOListener()
    is_active = False # BMO empieza en espera
    last_interaction = 0.0
    print("\n>>> BMO ONLINE. Di 'BMO' para despertar mis circuitos...")

    for text in listener.listen():
        # Un error procesando una frase no debe matar el hilo: se registra y se sigue escuchando
        try:
            input_text = text.lower()

            # 0. Si lleva un rato sin que nadie le hable, BMO vuelve a esperar su nombre
            if is_active and not is_speaking():
                idle = time.monotonic() - max(last_interaction, last_spoke_at())
                if idle > ACTIVE_TIMEOUT:
                    is_active = False
                    bmo_brain.forget()   # plática nueva, memoria nueva
                    print("\n>>> [MODO CONSULTA FINALIZADO POR INACTIVIDAD]")

            # 1. Lógica de Activación: Despertar a BMO
            if not is_active:
                if not contains_phrase(input_text, WAKE_WORDS):
                    continue # Ignorar si no escucha la palabra de activación

                is_active = True
                last_interaction = time.monotonic()
                print("\n>>> [MODO CONSULTA ACTIVADO]")

                # Si solo dijo el nombre, saludamos y esperamos la siguiente frase
                if not clean_text(input_text):
                    speak(random.choice(actions.activation_phrases))
                    continue

            # 2. Lógica de Desactivación: Regresar al estado de espera
            if contains_phrase(input_text, STOP_WORDS):
                is_active = False
                bmo_brain.forget()
                speak("¡De acuerdo! Me iré a descansar un poco. ¡Llámame cuando quieras hablar!")
                print("\n>>> [MODO CONSULTA FINALIZADO]")
                continue

            # 3. Procesamiento de la Consulta (BMO ya está despierto)
            last_interaction = time.monotonic()
            if actions.modo_juego_activo:
                # La boca se mueve sola con el audio; al terminar vuelve la cara de juego
                speak("¡Sigo aquí! Pero estoy concentrado en tus juegos ahora mismo.")
                continue

            # Limpiamos posibles menciones redundantes de BMO por costumbre del usuario
            clean_prompt = clean_text(input_text)

            user_display = clean_prompt if clean_prompt else "[Escuchando...]"
            print(f"\nXilef: {user_display}")

            if len(clean_prompt) < 2:
                continue

            if not actions.dispatch(clean_prompt):
                print("BMO está procesando internamente...")
                # BMO empieza a hablar en cuanto tiene la primera oración; la cara de pensar
                # se ve hasta que la boca empieza a moverse
                with face.estado("pensando"):
                    answer = speak_stream(bmo_brain.ask_stream(clean_prompt, remember=True))
                print(f"BMO: {answer}")

            last_interaction = time.monotonic()
            listener.reset()
            print("\n>>> BMO sigue atento (di 'descansa' para dormirlo)...")
        except Exception:
            print("\n[!] Error en el cerebro de BMO:")
            traceback.print_exc()
            if not actions.modo_juego_activo:
                face.set_state("esperando")
            face.show_expression("error", 3000)

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
