import os
from llama_cpp import Llama

class LocalBMO:
    def __init__(self, model_filename="Llama-3.2-1B-Instruct-Q6_K.gguf"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(base_dir)
        # Ajustamos a la carpeta 'models' (asegúrate que se llame así o 'model')
        self.model_path = os.path.join(project_root, "model", model_filename)
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"No se encontró el modelo en: {self.model_path}")

        # Subimos el contexto a 2048 para que recuerde más, 
        # pero mantenemos 4 hilos para la Raspberry Pi 4.
        self.llm = Llama(
            model_path=self.model_path, 
            n_ctx=4096, 
            n_threads=4,
            verbose=False 
        )

    def ask(self, prompt):
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
            max_tokens=80,        # Bajamos de 150 a 80 para obligarlo a ser corto
            stop=["<|eot_id|>", "<|start_header_id|>", "\n\n"], 
            echo=False,
            temperature=0.7,      
            repeat_penalty=1.2,    # Subimos un poco para que no use muletillas
            top_p=0.5              # Bajamos el top_p para que sea más preciso y menos "soñador"
        )
        
        return output["choices"][0]["text"].strip()