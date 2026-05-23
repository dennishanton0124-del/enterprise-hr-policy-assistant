import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from backend.services.retrieval_service import search_chunks


TEST_QUESTIONS = [
    "What is the PTO carryover policy?",
    "What internet speed do I need to work from home?",
    "When am I eligible for 401k?",
]


def run_tests():
    for question in TEST_QUESTIONS:
        print("\n" + "=" * 80)
        print("QUESTION:", question)
        print("=" * 80)

        results = search_chunks(question)

        for index, result in enumerate(results, start=1):
            print(f"\nResult {index}")
            print("Document:", result["document_id"])
            print("Section:", result["section_title"])
            print("Page/Section:", result["page_or_section"])
            print("Similarity:", round(result["similarity"], 4))
            print("Preview:", result["chunk_text"][:300], "...")


if __name__ == "__main__":
    run_tests()