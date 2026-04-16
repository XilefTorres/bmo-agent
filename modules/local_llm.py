# /modules/local_llm.py
import os
from llama_cpp import Llama

class LocalBMO:
    def __init__(self, model_filename="SmolLM2-360M-Instruct-Q6_K_L.gguf"):
        # Construimos la ruta dinámica basada en la carpeta /models
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(base_dir)
        self.model_path = os.path.join(project_root, "models", model_filename)
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"No se encontró el modelo en: {self.model_path}")

        # Configuración optimizada para RPi 4 (4GB RAM)
        # n_ctx=512 es suficiente para respuestas cortas
        # n_threads=4 aprovecha los 4 núcleos de la Pi
        self.llm = Llama(
            model_path=self.model_path, 
            n_ctx=512, 
            n_threads=4,
            verbose=False # Esto evita que la terminal se llene de logs técnicos
        )

    def ask(self, prompt):
        # Formato de prompt específico para modelos instruct
        full_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        output = self.llm(
            full_prompt, 
            max_tokens=64, 
            stop=["<|im_end|>", "\n"], 
            echo=False
        )
        return output["choices"][0]["text"].strip()