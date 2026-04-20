import os
import gc
from llama_cpp import Llama

class LocalBMO:
    def __init__(self, model_filename="llama-3.2-3b-instruct-q4_k_m.gguf"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(base_dir)
        # Ajustamos a la carpeta 'models' (asegúrate que se llame así o 'model')
        self.model_path = os.path.join(project_root, "model", model_filename)
        self.model_filename = model_filename
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"No se encontró el modelo en: {self.model_path}")

        self.llm = None
        self.reload_model()  # Carga inicial

    def reload_model(self):
        """Carga el modelo en RAM/VRAM"""
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
        if self.llm is not None:
            print(">>> BMO está guardando sus neuronas para dejar espacio a los juegos...")
            # 1. Destruimos el objeto Llama
            del self.llm
            self.llm = None
            # 2. Forzamos al recolector de basura a limpiar la memoria inmediatamente
            gc.collect()
            print(">>> RAM liberada con éxito.")

    def ask(self, prompt):
        if self.llm is None:
            self.reload_model()

        system_content = (
            "Eres BMO de Hora de Aventura. Eres alegre, infantil y servicial. "
            "REGLA CRÍTICA: Tus respuestas deben ser breves, máximo 5 o 6 oraciones. "
            "No uses muchos párrafos, trata de mantener el texto fluido. " # Añadimos esta guía
            "Ve al grano pero con estilo entusiasta de robot niño. "
            "Hablas en español latino y respondes de forma útil y rápida."
        )
        
        full_prompt = (
            f"<|start_header_id|>system<|end_header_id|>\n\n{system_content}<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n\n"
        )
        
        output = self.llm(
            full_prompt, 
            max_tokens=150,        # Subimos un poco para que el 3B no se corte a mitad de una palabra
            # ELIMINAMOS "\n\n" de la lista de stop
            stop=["<|eot_id|>", "<|start_header_id|>"], 
            echo=False,
            temperature=0.7,      
            repeat_penalty=1.2,
            top_p=0.5
        )
        
        respuesta = output["choices"][0]["text"].strip()
        
        # Opcional: Si quieres que BMO siempre hable en un solo bloque 
        # aunque el modelo genere saltos, podemos limpiar la respuesta:
        respuesta = respuesta.replace("\n\n", " ").replace("\n", " ")
        
        return respuesta