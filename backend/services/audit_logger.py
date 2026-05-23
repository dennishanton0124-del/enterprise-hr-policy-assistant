from backend.db.supabase_client import supabase
from backend.services.notification_service import send_escalation_notification


def log_interaction(
    *,
    user_question: str,
    answer: str | None,
    confidence_score: float | None,
    status: str,
    decision_type: str,
    escalation_reason: str | None = None,
    sensitive_categories: list[str] | None = None,
    model_used: str | None = None,
    prompt_version: str = "v1",
    citations: list[dict] | None = None,
    user_id: str | None = None,
) -> dict:
    """
    Logs one complete HR assistant interaction:
    - query record
    - source citations
    - audit event
    - n8n escalation notification when escalated
    """

    print("[log_interaction] Starting interaction log...")

    if supabase is None:
        print("[log_interaction] ERROR: Supabase client is None; cannot log interaction")
        return {}

    review_status = (
        "pending"
        if decision_type == "escalate"
        else "not_required"
    )

    query_payload = {
        "user_id": user_id,
        "user_question": user_question,
        "answer": answer,
        "confidence_score": confidence_score,
        "status": status,
        "decision_type": decision_type,
        "escalation_reason": escalation_reason,
        "sensitive_categories": sensitive_categories or [],
        "model_used": model_used,
        "prompt_version": prompt_version,
        "review_status": review_status,
    }

    print(
        "[log_interaction] Inserting query: "
        f"status={status}, decision_type={decision_type}, review_status={review_status}"
    )

    try:
        query_results = supabase.insert("queries", query_payload)
        print("[log_interaction] Query inserted successfully")
        print(f"[log_interaction] Query response: {query_results}")

        if isinstance(query_results, list) and query_results:
            query_record = query_results[0]
        elif isinstance(query_results, dict):
            query_record = query_results
        else:
            print("[log_interaction] ERROR: Query insert returned no usable record")
            return {}

        query_id = query_record.get("id")

        if not query_id:
            print("[log_interaction] ERROR: Query record has no id")
            return {}

        print(f"[log_interaction] Query ID: {query_id}")

    except Exception as e:
        print(f"[log_interaction] ERROR inserting query: {e}")
        return {}

    # Send escalation notification to n8n after query_id exists
    if decision_type == "escalate":
        print("[log_interaction] Escalation detected. Sending n8n notification...")

        send_escalation_notification(
            query_id=query_id,
            user_question=user_question,
            answer=answer,
            confidence_score=confidence_score,
            escalation_reason=escalation_reason,
            sensitive_categories=sensitive_categories or [],
        )

    print("[log_interaction] Raw citations received:", citations)

    if citations:
        print(f"[log_interaction] Processing {len(citations)} citations...")

        for citation in citations:
            source_row = {
                "query_id": query_id,
                "document_id": (
                    str(citation.get("document_id"))
                    if citation.get("document_id")
                    else None
                ),
                "chunk_id": str(
                    citation.get("chunk_id")
                    or citation.get("id")
                    or citation.get("chunk_uuid")
                    or ""
                ),
                "citation_text": (
                    citation.get("citation_text")
                    or f"{citation.get('section_title', '')} {citation.get('page_or_section', '')}".strip()
                    or "Source citation"
                ),
                "relevance_score": (
                    citation.get("relevance_score")
                    or citation.get("similarity")
                    or citation.get("score")
                ),
            }

            print(f"[log_interaction] Source row: {source_row}")

            try:
                source_results = supabase.insert("query_sources", source_row)
                print("[log_interaction] Citation inserted successfully")
                print(f"[log_interaction] Source response: {source_results}")

            except Exception as e:
                print(f"[log_interaction] WARNING: Error inserting citation: {e}")
    else:
        print("[log_interaction] No citations provided; skipping query_sources insert")

    audit_payload = {
        "query_id": query_id,
        "user_id": user_id,
        "event_type": "interaction_logged",
        "event_description": f"Decision: {decision_type}, Status: {status}",
    }

    print("[log_interaction] Inserting audit event...")

    try:
        audit_results = supabase.insert("audit_events", audit_payload)
        print("[log_interaction] Audit event inserted successfully")
        print(f"[log_interaction] Audit response: {audit_results}")

    except Exception as e:
        print(f"[log_interaction] WARNING: Error inserting audit event: {e}")

    print("[log_interaction] Interaction log complete")

    return query_record