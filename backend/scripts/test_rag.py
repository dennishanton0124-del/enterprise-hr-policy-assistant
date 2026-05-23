import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from backend.services.retrieval_service import search_chunks
from backend.services.answer_question import generate_answer


QUESTIONS = [
    "What is the PTO carryover policy?",
    "Can my manager fire me for taking medical leave?",
    "What is the international relocation policy?"
]


def run_rag_test():
    for question in QUESTIONS:
        print("\n" + "=" * 80)
        print("QUESTION:", question)
        print("=" * 80)

        # Retrieve relevant chunks
        chunks = search_chunks(question)

        # Generate AI answer
        result = generate_answer(question, chunks)

        print("\nDECISION:", result["decision_type"])
        print("CONFIDENCE:", result["confidence_score"])

        print("\nANSWER:")
        print(result["answer"])

        print("\nCITATIONS:")
        for citation in result["citations"]:
            print(
                f"- {citation['document_id']} | "
                f"Section {citation['page_or_section']} | "
                f"{citation['section_title']} "
                f"(similarity: {round(citation['similarity'], 3)})"
            )


if __name__ == "__main__":
    run_rag_test()