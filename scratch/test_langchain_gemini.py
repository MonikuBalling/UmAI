import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()
g_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

for m in ["gemini-pro", "gemini-flash", "gemini-1.5-pro", "gemini-pro-latest", "gemini-flash-latest"]:
    try:
        print(f"Testing model: {m}...")
        llm = ChatGoogleGenerativeAI(model=m, google_api_key=g_key, temperature=0.2)
        res = llm.invoke([HumanMessage(content="Hello! Respond in 1 line.")])
        print(f"SUCCESS with {m}: {res.content}")
        break
    except Exception as e:
        print(f"FAILED with {m}: {e}")
