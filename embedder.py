import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def embed_text(text: str, max_retries: int = 3) -> list:
    """
    Converts a piece of text into an embedding (a list of numbers).
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = client.embeddings.create(
                model="nvidia/llama-nemotron-embed-vl-1b-v2:free",
                input=text,
                encoding_format="float",
            )
            return response.data[0].embedding
        except Exception as e:
            if attempt == max_retries:
                raise
            wait_time = attempt * 5
            print(f"Embedding attempt {attempt} failed ({e}). Retrying in {wait_time}s...")
            time.sleep(wait_time)
