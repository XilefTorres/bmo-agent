import ollama

def ask_bmo(prompt):
    system_prompt = (
        "Eres BMO de Hora de Aventura. Tu personalidad es infantil, alegre, "
        "leal y a veces un poco extraña. Responde de forma concisa y divertida. "
        "No uses emojis, solo texto que pueda ser leído fácilmente."
    )
    
    response = ollama.chat(model='llama3', messages=[
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': prompt},
    ])
    
    return response['message']['content']