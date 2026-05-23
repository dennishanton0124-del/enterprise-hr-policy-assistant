from datetime import datetime, timezone
import traceback

from backend.db.supabase_client import supabase


def get_escalated_queries():
    print("[get_escalated_queries] Fetching pending escalated queries...")

    if supabase is None:
        print("[get_escalated_queries] ERROR: Supabase client is None")
        return []

    try:
        results = supabase.select(
            "queries",
            "status=eq.escalated&review_status=eq.pending&order=created_at.desc"
        )

        print(f"[get_escalated_queries] Found {len(results)} pending escalated queries")
        return results

    except Exception as e:
        print(f"[get_escalated_queries] ERROR: {e}")
        traceback.print_exc()
        return []


def get_query_sources(query_id: str):
    print(f"[get_query_sources] Fetching sources for query {query_id}")

    if supabase is None:
        print("[get_query_sources] ERROR: Supabase client is None")
        return []

    try:
        results = supabase.select(
            "query_sources",
            f"query_id=eq.{query_id}"
        )

        print(f"[get_query_sources] Found {len(results)} sources")
        return results

    except Exception as e:
        print(f"[get_query_sources] ERROR: {e}")
        traceback.print_exc()
        return []


def submit_review(
    *,
    query_id: str,
    reviewer_id: str,
    reviewer_status: str,
    reviewer_notes: str,
    final_answer: str,
):
    print("\n" + "=" * 80)
    print("[submit_review] START")
    print(f"[submit_review] query_id={query_id}")
    print(f"[submit_review] reviewer_id={reviewer_id}")
    print(f"[submit_review] reviewer_status={reviewer_status}")
    print("=" * 80)

    if supabase is None:
        print("[submit_review] ERROR: Supabase client is None")
        return None

    reviewed_at = datetime.now(timezone.utc).isoformat()

    review_payload = {
        "query_id": query_id,
        "reviewer_id": reviewer_id,
        "reviewer_status": reviewer_status,
        "reviewer_notes": reviewer_notes,
        "final_answer": final_answer,
        "reviewed_at": reviewed_at,
    }

    print(f"[submit_review] Review payload ready: {review_payload}")

    try:
        print("[submit_review] Calling supabase.insert('reviews', ...)")
        review_results = supabase.insert("reviews", review_payload)

        print("[submit_review] Review inserted successfully")
        print(f"[submit_review] Review response: {review_results}")

        if isinstance(review_results, list) and review_results:
            review_record = review_results[0]
        else:
            review_record = review_results

    except Exception as e:
        print(f"[submit_review] ERROR inserting review: {e}")
        traceback.print_exc()
        return None

    query_update_payload = {
        "review_status": "completed",
        "reviewed_at": reviewed_at,
        "reviewer_id": reviewer_id,
        "final_answer": final_answer,
    }

    try:
        print("[submit_review] Updating original query lifecycle fields...")
        print(f"[submit_review] Query update payload: {query_update_payload}")

        update_results = supabase.update(
            "queries",
            query_update_payload,
            f"id=eq.{query_id}"
        )

        print("[submit_review] Query lifecycle updated successfully")
        print(f"[submit_review] Update response: {update_results}")

    except Exception as e:
        print(f"[submit_review] WARNING updating query lifecycle failed: {e}")
        traceback.print_exc()

    audit_payload = {
        "query_id": query_id,
        "user_id": reviewer_id,
        "event_type": "human_review_completed",
        "event_description": f"HR reviewer marked query as {reviewer_status}",
    }

    print(f"[submit_review] Audit payload ready: {audit_payload}")

    try:
        print("[submit_review] Calling supabase.insert('audit_events', ...)")
        audit_results = supabase.insert("audit_events", audit_payload)

        print("[submit_review] Audit event inserted successfully")
        print(f"[submit_review] Audit response: {audit_results}")

    except Exception as e:
        print(f"[submit_review] WARNING inserting audit event failed: {e}")
        traceback.print_exc()

    print("[submit_review] Review submission complete")
    print("=" * 80 + "\n")

    return review_record