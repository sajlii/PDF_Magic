import os
import google.generativeai as genai

# Load your API key from .env or replace with the actual key
from dotenv import load_dotenv
load_dotenv()  

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))  # Or replace with your actual key string

# List and print all available models
print("Available Models:")
for m in genai.list_models():
    print(f" - {m.name}")