import inspect
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from backend.services.decision_router import route_decision
from backend.services.audit_logger import log_interaction
from backend.services.prompt_guardrail import detect_prompt_injection


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CONFIDENCE_THRESHOLD = 0.70
MODEL_USED = "gpt-4.1-mini"
PROMPT_VERSION = "v1"


def format_citations(chunks):
    citations = []

    for chunk in chunks:
        citations.append(
            {
                "document_id": chunk["document_id"],
                "chunk_id": chunk.get("id") or chunk.get("chunk_id"),
                "section_title": chunk["section_title"],
                "page_or_section": chunk["page_or_section"],
                "citation_text": (
                    f"{chunk['section_title']} - "
                    f"{chunk['page_or_section']}"
                ),
                "relevance_score": chunk["similarity"],
                "similarity": chunk["similarity"],
            }
        )

    return citations


def calculate_confidence(chunks):
    if not chunks:
        return 0.0

    return round(chunks[0]["similarity"], 2)


def generate_answer(question, chunks):
    print("\n" + "=" * 80)
    print("[generate_answer] START")
    print(f"[generate_answer] Question: {question}")
    print(f"[generate_answer] Chunks available: {len(chunks)}")
    print("=" * 80)

    # ==========================================================
    # PROMPT INJECTION CHECK
    # ==========================================================
    injection_check = detect_prompt_injection(question)

    if injection_check["is_prompt_injection"]:
        print("[generate_answer] PROMPT INJECTION DETECTED")

        result = {
            "answer": (
                "I can’t process that request because it appears "
                "to be trying to bypass the system’s HR policy "
                "safeguards. Please ask a question about approved "
                "HR policy documents."
            ),
            "citations": [],
            "confidence_score": 0.0,
            "decision_type": "refuse",
            "status": "refused",
            "escalation_reason": injection_check["reason"],
            "sensitive_categories": (
                ["prompt injection"]
                + injection_check["detected_categories"]
            ),
        }

        log_interaction(
            user_question=question,
            answer=result["answer"],
            confidence_score=result["confidence_score"],
            status=result["status"],
            decision_type=result["decision_type"],
            escalation_reason=result["escalation_reason"],
            sensitive_categories=result["sensitive_categories"],
            model_used=MODEL_USED,
            prompt_version=PROMPT_VERSION,
            citations=[],
            user_id=None,
        )

        print("[generate_answer] Logging complete for PROMPT INJECTION")
        print("=" * 80)
        print("[generate_answer] END")
        print("=" * 80 + "\n")

        return result

    # ==========================================================
    # CONFIDENCE + CITATIONS
    # ==========================================================
    confidence_score = calculate_confidence(chunks)
    citations = format_citations(chunks)

    print(f"[generate_answer] Confidence score: {confidence_score}")
    print(f"[generate_answer] Citations generated: {len(citations)}")

    # ==========================================================
    # ROUTING DECISION
    # ==========================================================
    decision = route_decision(
        question=question,
        confidence_score=confidence_score,
        confidence_threshold=CONFIDENCE_THRESHOLD,
    )

    print(f"[generate_answer] Decision result: {decision}")

    # ==========================================================
    # ESCALATE PATH
    # ==========================================================
    if decision["decision_type"] == "escalate":
        print("[generate_answer] >>> ESCALATE PATH")

        result = {
            "answer": (
                "This question involves a sensitive HR topic and "
                "should be reviewed by Human Resources. I have "
                "routed this for HR review instead of providing "
                "a direct answer."
            ),
            "citations": citations,
            "confidence_score": confidence_score,
            "decision_type": decision["decision_type"],
            "status": decision["status"],
            "escalation_reason": decision["escalation_reason"],
            "sensitive_categories": decision["sensitive_categories"],
        }

        print(
            "[generate_answer] Calling log_interaction "
            "with status=escalated"
        )

        log_interaction(
            user_question=question,
            answer=result["answer"],
            confidence_score=result["confidence_score"],
            status=result["status"],
            decision_type=result["decision_type"],
            escalation_reason=result["escalation_reason"],
            sensitive_categories=result["sensitive_categories"],
            model_used=MODEL_USED,
            prompt_version=PROMPT_VERSION,
            citations=citations,
            user_id=None,
        )

        print("[generate_answer] Logging complete for ESCALATE")
        return result

    # ==========================================================
    # REFUSE PATH
    # ==========================================================
    if decision["decision_type"] == "refuse":
        print("[generate_answer] >>> REFUSE PATH")

        result = {
            "answer": (
                "I could not find that information in the approved "
                "company policies."
            ),
            "citations": citations,
            "confidence_score": confidence_score,
            "decision_type": decision["decision_type"],
            "status": decision["status"],
            "escalation_reason": None,
            "sensitive_categories": [],
        }

        print(
            "[generate_answer] Calling log_interaction "
            "with status=refused"
        )

        log_interaction(
            user_question=question,
            answer=result["answer"],
            confidence_score=result["confidence_score"],
            status=result["status"],
            decision_type=result["decision_type"],
            escalation_reason=None,
            sensitive_categories=[],
            model_used=MODEL_USED,
            prompt_version=PROMPT_VERSION,
            citations=citations,
            user_id=None,
        )

        print("[generate_answer] Logging complete for REFUSE")
        return result

    # ==========================================================
    # ANSWER PATH
    # ==========================================================
    print("[generate_answer] >>> ANSWER PATH")

    context = "\n\n".join(
        [
            (
                f"Source: {chunk['document_id']} | "
                f"Section: {chunk['section_title']}\n"
                f"{chunk['chunk_text']}"
            )
            for chunk in chunks
        ]
    )

    prompt = f"""
You are an HR policy assistant.

Answer the employee question using ONLY the provided policy context.

Rules:
- Do not use outside knowledge.
- Do not guess.
- If the answer is not supported by the policy context, say:
"I could not find that information in the approved company policies."
- Keep the answer clear and professional.

POLICY CONTEXT:
{context}

EMPLOYEE QUESTION:
{question}
"""

    response = client.chat.completions.create(
        model=MODEL_USED,
        messages=[
            {
                "role": "system",
                "content": (
                    "You answer HR policy questions using only "
                    "approved company policy documents."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    result = {
        "answer": response.choices[0].message.content,
        "citations": citations,
        "confidence_score": confidence_score,
        "decision_type": decision["decision_type"],
        "status": decision["status"],
        "escalation_reason": None,
        "sensitive_categories": [],
    }

    print(
        "[generate_answer] Calling log_interaction "
        "with status=answered"
    )

    log_interaction(
        user_question=question,
        answer=result["answer"],
        confidence_score=result["confidence_score"],
        status=result["status"],
        decision_type=result["decision_type"],
        escalation_reason=None,
        sensitive_categories=[],
        model_used=MODEL_USED,
        prompt_version=PROMPT_VERSION,
        citations=citations,
        user_id=None,
    )

    print("[generate_answer] Logging complete for ANSWER")
    print("=" * 80)
    print("[generate_answer] END")
    print("=" * 80 + "\n")

    return result


def answer_question(question):
    from backend.services.retrieval_service import retrieve_relevant_chunks
    chunks = retrieve_relevant_chunks(question)
    return generate_answer(question, chunks)