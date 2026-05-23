import os
import requests
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def create_embedding(text: str):
    print("[create_embedding] Creating embedding...")

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )

    print("[create_embedding] Embedding created")

    return response.data[0].embedding


def search_chunks(question: str, match_count: int = 5):
    print("\n" + "=" * 80)
    print("[search_chunks] START")
    print(f"[search_chunks] Question: {question}")
    print(f"[search_chunks] Match count: {match_count}")

    if not SUPABASE_URL:
        print("[search_chunks] ERROR: SUPABASE_URL is missing")
        return []

    if not SUPABASE_KEY:
        print("[search_chunks] ERROR: SUPABASE key is missing")
        return []

    try:
        question_embedding = create_embedding(question)
        print("[search_chunks] Question embedding generated")
    except Exception as e:
        print(f"[search_chunks] ERROR creating embedding: {e}")
        return []

    url = f"{SUPABASE_URL}/rest/v1/rpc/match_chunks"

    payload = {
        "query_embedding": question_embedding,
        "match_count": match_count,
    }

    print("[search_chunks] Calling Supabase RPC match_chunks...")
    print(f"[search_chunks] RPC URL: {url}")

    try:
        response = requests.post(
            url,
            headers=HEADERS,
            json=payload,
            timeout=20,
        )

        print(f"[search_chunks] Status code: {response.status_code}")

        if response.status_code != 200:
            print("[search_chunks] ERROR response from Supabase")
            print("[search_chunks] Response text:", response.text)
            return []

        results = response.json()

        print(f"[search_chunks] Retrieved chunks: {len(results)}")

        for index, chunk in enumerate(results, start=1):
            print("-" * 60)
            print(f"[search_chunks] Chunk #{index}")
            print("document_id:", chunk.get("document_id"))
            print("chunk_id:", chunk.get("id") or chunk.get("chunk_id"))
            print("section_title:", chunk.get("section_title"))
            print("page_or_section:", chunk.get("page_or_section"))
            print("similarity:", chunk.get("similarity"))
            preview = chunk.get("chunk_text", "")
            print("text preview:", preview[:250])

        print("[search_chunks] END")
        print("=" * 80 + "\n")

        return results

    except Exception as e:
        print(f"[search_chunks] ERROR calling match_chunks: {e}")
        return []


def retrieve_relevant_chunks(question: str, match_count: int = 5):
    """
    Wrapper for search_chunks to provide backward compatibility.
    """
    return search_chunks(question, match_count)