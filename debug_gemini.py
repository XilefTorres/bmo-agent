import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("--- LISTADO DE MODELOS DISPONIBLES ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Nombre: {m.name} | Versión: {m.version if hasattr(m, 'version') else 'N/A'}")
except Exception as e:
    print(f"Error al listar: {e}")