import google.generativeai as genai
import os
from dotenv import load_dotenv

# Carrega a sua chave de API
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("Buscando modelos disponíveis para a sua chave...")
print("-" * 30)

# Itera sobre todos os modelos e verifica quais suportam o método 'generateContent'
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ Nome do Modelo: {model.name}")
        print(f"   Descrição: {model.description}\n")

print("-" * 30)
print("Use um dos nomes de modelo listados acima no seu arquivo app.py")