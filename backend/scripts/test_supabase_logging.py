import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from datetime import datetime, timezone
from backend.db.supabase_client import supabase


def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_queries_insert():
    print_section("TEST 1: queries insert")

    payload = {
        "user_id": None,
        "user_question": "TEST: Can I work from home?",
        "answer": "TEST: Yes, according to the remote work policy.",
        "confidence_score": 0.91,
        "status": "answered",
        "decision_type": "answer",
        "escalation_reason": None,
        "sensitive_categories": [],
        "model_used": "test-model",
        "prompt_version": "test-v1",
    }

    result = supabase.insert("queries", payload)
    print("queries result:", result)

    if isinstance(result, list) and result:
        return result[0]["id"]

    if isinstance(result, dict):
        return result["id"]

    raise Exception("queries insert failed or returned no id")


def test_query_sources_insert(query_id):
    print_section("TEST 2: query_sources insert")

    payload = {
        "query_id": query_id,
        "document_id": "EH-2025-001",
        "chunk_id": "test-chunk-001",
        "citation_text": "TEST citation text",
        "relevance_score": 0.88,
    }

    result = supabase.insert("query_sources", payload)
    print("query_sources result:", result)


def test_audit_events_insert(query_id):
    print_section("TEST 3: audit_events insert")

    payload = {
        "query_id": query_id,
        "user_id": None,
        "event_type": "test_logging",
        "event_description": "TEST audit event insert",
    }

    result = supabase.insert("audit_events", payload)
    print("audit_events result:", result)


def test_reviews_insert(query_id):
    print_section("TEST 4: reviews insert")

    payload = {
        "query_id": query_id,
        "reviewer_id": "hr_reviewer_001",
        "reviewer_status": "approved",
        "reviewer_notes": "TEST reviewer notes",
        "final_answer": "TEST final HR answer",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }

    result = supabase.insert("reviews", payload)
    print("reviews result:", result)


def main():
    print_section("SUPABASE LOGGING TEST START")

    if supabase is None:
        print("ERROR: Supabase client is None")
        return

    print("Supabase client exists:", supabase)

    query_id = test_queries_insert()
    print("Created test query_id:", query_id)

    test_query_sources_insert(query_id)
    test_audit_events_insert(query_id)
    test_reviews_insert(query_id)

    print_section("SUPABASE LOGGING TEST COMPLETE")


if __name__ == "__main__":
    main()