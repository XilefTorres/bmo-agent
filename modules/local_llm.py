import os
import gc
from llama_cpp import Llama

class LocalBMO:
    def __init__(self, model_filename="Llama-3.2-1B-Instruct-Q6_K.gguf"):
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
        # Si el modelo está descargado (porque estás jugando), lo recargamos
        if self.llm is None:
            self.reload_model()

        system_content = (
            "Eres BMO de Hora de Aventura. Eres alegre, infantil y servicial. "
            "REGLA CRÍTICA: Tus respuestas deben ser MUY BREVES, máximo 2 o 3 oraciones. "
            "No te enrolles. Ve al grano pero con estilo entusiasta de robot niño. "
            "Hablas en español latino y respondes de forma útil y rápida."
        )
        
        full_prompt = (
            f"<|start_header_id|>system<|end_header_id|>\n\n{system_content}<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n\n"
        )
        
        output = self.llm(
            full_prompt, 
            max_tokens=80,
            stop=["<|eot_id|>", "<|start_header_id|>", "\n\n"], 
            echo=False,
            temperature=0.7,      
            repeat_penalty=1.2,
            top_p=0.5
        )
        
        return output["choices"][0]["text"].strip()