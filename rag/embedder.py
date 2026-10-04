import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
)

def embed_text(text: str, max_retries: int = 3) -> list:
    """
    Converts a piece of text into an embedding (a list of numbers).
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = gemini_client.models.embed_content(
                model="gemini-embedding-2-preview",
                contents=text,
            )
            return response.embeddings[0].values
        except Exception as e:
            if attempt == max_retries:
                raise
            wait_time = attempt * 5
            print(f"Embedding attempt {attempt} failed ({e}). Retrying in {wait_time}s...")
            time.sleep(wait_time)