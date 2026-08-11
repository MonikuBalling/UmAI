import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
g_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
genai.configure(api_key=g_key)

try:
    print("=== Available Gemini Models ===")
    models = genai.list_models()
    for m in models:
        if "generateContent" in m.supported_generation_methods:
            print("MODEL:", m.name)
except Exception as e:
    print("Error listing models:", e)
