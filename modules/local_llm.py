import os
import gc
import threading
from collections import deque
from llama_cpp import Llama

MEMORY_TURNS = 5  # cuántos intercambios recientes recuerda BMO dentro de una plática
from modules.text_utils import trim_to_sentence, pop_sentences

class LocalBMO:
    def __init__(self, model_filename="llama-3.2-3b-instruct-q4_k_m.gguf"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(base_dir)
        # Ajustamos a la carpeta 'models' (asegúrate que se llame así o 'model')
        self.model_path = os.path.join(project_root, "model", model_filename)
        self.model_filename = model_filename
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"No se encontró el modelo en: {self.model_path}")

        # llama-cpp no es thread-safe: una sola llamada (o carga/descarga) a la vez
        self._lock = threading.RLock()
        # Memoria de la plática: últimos turnos (pregunta, respuesta)
        self.history = deque(maxlen=MEMORY_TURNS)
        self.llm = None
        self.reload_model()  # Carga inicial

    def reload_model(self):
        """Carga el modelo en RAM/VRAM"""
        with self._lock:
            if self.llm is None:
                print(">>> BMO está cargando sus recuerdos en la RAM...")
                self.llm = Llama(
                    model_path=self.model_path, 
                    n_ctx=4096, 
                    n_threads=4,
                    verbose=False 
                )
    
    def unload_model(self):
        """Libera los recursos del modelo para poder jugar"""
        with self._lock:
            if self.llm is not None:
                print(">>> BMO está guardando sus neuronas para dejar espacio a los juegos...")
                # 1. Destruimos el objeto Llama
                del self.llm
                self.llm = None
                # 2. Forzamos al recolector de basura a limpiar la memoria inmediatamente
                gc.collect()
                print(">>> RAM liberada con éxito.")

    def forget(self):
        """Olvida la conversación (cuando BMO se va a descansar)."""
        self.history.clear()

    def ask(self, prompt, remember=False):
        """Respuesta completa de una sola vez."""
        return " ".join(self.ask_stream(prompt, remember=remember))

    def ask_stream(self, prompt, remember=False):
        """Genera la respuesta y la va entregando oración por oración (para hablar mientras piensa).

        Con remember=True la pregunta se responde con los últimos turnos de la plática como
        contexto y queda guardada para las siguientes ("¿y cuánto medía?").
        """
        system_content = (
            "Eres BMO de Hora de Aventura. Eres alegre, infantil y servicial. "
            "REGLA CRÍTICA: Tus respuestas deben ser breves, máximo 5 o 6 oraciones. "
            "No uses muchos párrafos, trata de mantener el texto fluido. " # Añadimos esta guía
            "Ve al grano pero con estilo entusiasta de robot niño. "
            "Hablas en español latino y respondes de forma útil y rápida."
        )
        
        previous_turns = "".join(
            f"<|start_header_id|>user<|end_header_id|>\n\n{question}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n\n{answer}<|eot_id|>"
            for question, answer in (list(self.history) if remember else [])
        )

        full_prompt = (
            f"<|start_header_id|>system<|end_header_id|>\n\n{system_content}<|eot_id|>"
            f"{previous_turns}"
            f"<|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n\n"
        )
        
        # El candado se mantiene mientras dure la generación (se libera también si cierran el generador)
        with self._lock:
            if self.llm is None:
                self.reload_model()

            stream = self.llm(
                full_prompt, 
                max_tokens=150,        # Subimos un poco para que el 3B no se corte a mitad de una palabra
                # ELIMINAMOS "\n\n" de la lista de stop
                stop=["<|eot_id|>", "<|start_header_id|>"], 
                echo=False,
                temperature=0.7,      
                repeat_penalty=1.2,
                top_p=0.5,
                stream=True
            )

            buffer = ""
            finish_reason = None
            said = []
            try:
                for chunk in stream:
                    choice = chunk["choices"][0]
                    # BMO habla en un solo bloque aunque el modelo genere saltos de línea
                    buffer += choice["text"].replace("\n", " ")
                    finish_reason = choice.get("finish_reason") or finish_reason
                    sentences, buffer = pop_sentences(buffer)
                    for sentence in sentences:
                        said.append(sentence)
                        yield sentence

                resto = buffer.strip()
                # Si max_tokens cortó la respuesta a medias, descartamos la oración incompleta
                if finish_reason == "length":
                    resto = trim_to_sentence(resto)
                    if resto[-1:] not in ".!?…":
                        resto = ""
                if resto:
                    said.append(resto)
                    yield resto
            finally:
                # También si callaron a BMO a media respuesta: recuerda lo que alcanzó a decir
                if remember and said:
                    self.history.append((prompt, " ".join(said)))
