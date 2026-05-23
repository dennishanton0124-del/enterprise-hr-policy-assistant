import os
import re
import requests
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_FOLDER = PROJECT_ROOT / "docs" / "fake_hr_policies"
ENV_PATH = PROJECT_ROOT / ".env"

# Load environment variables
load_dotenv(dotenv_path=ENV_PATH)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

DOCUMENTS = {
    "EH-2025-001": "employee_handbook.md",
    "PTO-2025-001": "pto_policy.md",
    "WFH-2025-001": "work_from_home_policy.md",
}

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}


def chunk_markdown(file_path, document_id):
    text = file_path.read_text(encoding="utf-8")

    sections = re.split(r"\n(?=### )", text)
    chunks = []

    for section in sections:
        if not section.startswith("### "):
            continue

        lines = section.split("\n", 1)
        section_title = lines[0].replace("### ", "").strip()
        chunk_text = lines[1].strip() if len(lines) > 1 else ""

        match = re.match(r"(\d+\.\d+)", section_title)
        page_or_section = match.group(1) if match else section_title

        chunks.append({
            "document_id": document_id,
            "section_title": section_title,
            "page_or_section": page_or_section,
            "chunk_text": chunk_text,
        })

    return chunks


def create_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding


def insert_chunk(chunk):
    url = f"{SUPABASE_URL}/rest/v1/chunks"

    response = requests.post(
        url,
        headers=HEADERS,
        json=chunk
    )

    return response.status_code, response.text


def ingest_documents():
    total_chunks = 0
    successful_inserts = 0
    failed_inserts = 0

    print("Starting document ingestion...")
    print("Docs folder:", DOCS_FOLDER)

    for document_id, file_name in DOCUMENTS.items():
        file_path = DOCS_FOLDER / file_name

        if not file_path.exists():
            print(f"Missing file: {file_path}")
            continue

        chunks = chunk_markdown(file_path, document_id)
        print(f"\n{file_name}")
        print(f"Chunks created: {len(chunks)}")

        for index, chunk in enumerate(chunks, start=1):
            try:
                print(f"Embedding chunk {index}/{len(chunks)}: {chunk['section_title']}")

                embedding = create_embedding(chunk["chunk_text"])
                chunk["embedding"] = embedding

                status_code, response_text = insert_chunk(chunk)

                if status_code in [200, 201, 204]:
                    successful_inserts += 1
                else:
                    failed_inserts += 1
                    print("Insert failed")
                    print("Status:", status_code)
                    print("Response:", response_text)

            except Exception as error:
                failed_inserts += 1
                print("Error processing chunk:")
                print(chunk["section_title"])
                print(error)

        total_chunks += len(chunks)

    print("\nIngestion complete.")
    print("Total chunks processed:", total_chunks)
    print("Successful inserts:", successful_inserts)
    print("Failed inserts:", failed_inserts)


if __name__ == "__main__":
    ingest_documents()