from collections import Counter
import pandas as pd

from backend.db.supabase_client import supabase


def load_table(table_name):
    try:
        response = supabase.select(table_name, "select=*")

        print(f"{table_name} rows:", len(response or []))

        return response or []

    except Exception as e:
        print(f"ERROR loading {table_name}: {e}")
        return []


def get_system_metrics():
    queries = load_table("queries")
    reviews = load_table("reviews")
    audit_events = load_table("audit_events")
    query_sources = load_table("query_sources")

    queries_df = pd.DataFrame(queries)
    reviews_df = pd.DataFrame(reviews)

    total_queries = len(queries)
    total_reviews = len(reviews)
    total_audit_events = len(audit_events)
    total_sources = len(query_sources)

    answered_count = 0
    escalated_count = 0
    refused_count = 0

    if not queries_df.empty and "decision_type" in queries_df.columns:
        answered_count = len(queries_df[queries_df["decision_type"] == "answer"])
        escalated_count = len(queries_df[queries_df["decision_type"] == "escalate"])
        refused_count = len(queries_df[queries_df["decision_type"] == "refuse"])

    escalation_rate = round((escalated_count / total_queries) * 100, 1) if total_queries else 0
    refusal_rate = round((refused_count / total_queries) * 100, 1) if total_queries else 0

    completed_reviews = 0
    pending_reviews = 0

    if not reviews_df.empty and "reviewer_status" in reviews_df.columns:
        completed_reviews = len(reviews_df[reviews_df["reviewer_status"] == "completed"])
        pending_reviews = len(reviews_df[reviews_df["reviewer_status"] == "pending"])
    else:
        completed_reviews = total_reviews

    avg_confidence = 0

    if not queries_df.empty and "confidence_score" in queries_df.columns:
        queries_df["confidence_score"] = pd.to_numeric(
            queries_df["confidence_score"],
            errors="coerce"
        )
        avg_confidence = round(queries_df["confidence_score"].mean(), 2)

    return {
        "total_queries": total_queries,
        "answered_count": answered_count,
        "escalated_count": escalated_count,
        "refused_count": refused_count,
        "escalation_rate": escalation_rate,
        "refusal_rate": refusal_rate,
        "completed_reviews": completed_reviews,
        "pending_reviews": pending_reviews,
        "total_audit_events": total_audit_events,
        "total_sources": total_sources,
        "average_confidence": avg_confidence,
    }


def get_decision_breakdown():
    queries = load_table("queries")
    queries_df = pd.DataFrame(queries)

    if queries_df.empty or "decision_type" not in queries_df.columns:
        return pd.Series(dtype="int64")

    return queries_df["decision_type"].value_counts()


def get_confidence_trends():
    queries = load_table("queries")
    queries_df = pd.DataFrame(queries)

    if queries_df.empty or "confidence_score" not in queries_df.columns:
        return pd.Series(dtype="float64")

    queries_df["confidence_score"] = pd.to_numeric(
        queries_df["confidence_score"],
        errors="coerce"
    )

    return queries_df["confidence_score"].dropna()


def get_sensitive_category_trends():
    queries = load_table("queries")
    queries_df = pd.DataFrame(queries)

    category_counter = Counter()

    if queries_df.empty:
        return pd.DataFrame(columns=["category", "count"])

    category_column = None

    if "sensitive_categories" in queries_df.columns:
        category_column = "sensitive_categories"
    elif "sensitive_category" in queries_df.columns:
        category_column = "sensitive_category"

    if not category_column:
        return pd.DataFrame(columns=["category", "count"])

    for value in queries_df[category_column].dropna():
        if isinstance(value, list):
            category_counter.update(value)
        elif isinstance(value, str):
            cleaned = value.strip("{}[]").replace('"', "")
            if cleaned:
                category_counter.update(
                    item.strip()
                    for item in cleaned.split(",")
                    if item.strip()
                )

    if not category_counter:
        return pd.DataFrame(columns=["category", "count"])

    return pd.DataFrame(
        category_counter.items(),
        columns=["category", "count"]
    ).sort_values("count", ascending=False)


def get_recent_queries(limit=10):
    queries = load_table("queries")
    queries_df = pd.DataFrame(queries)

    if queries_df.empty:
        return pd.DataFrame()

    display_columns = [
        col for col in [
            "created_at",
            "user_question",
            "decision_type",
            "status",
            "review_status",
            "confidence_score",
            "escalation_reason",
        ]
        if col in queries_df.columns
    ]

    if "created_at" in queries_df.columns:
        queries_df = queries_df.sort_values("created_at", ascending=False)

    return queries_df[display_columns].head(limit)


def get_recent_audit_events(limit=10):
    audit_events = load_table("audit_events")
    audit_df = pd.DataFrame(audit_events)

    if audit_df.empty:
        return pd.DataFrame()

    display_columns = [
        col for col in [
            "created_at",
            "event_type",
            "event_description",
            "query_id",
            "user_id",
        ]
        if col in audit_df.columns
    ]

    if "created_at" in audit_df.columns:
        audit_df = audit_df.sort_values("created_at", ascending=False)

    return audit_df[display_columns].head(limit)