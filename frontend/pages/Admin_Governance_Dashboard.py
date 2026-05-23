import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.observability_service import (
    get_system_metrics,
    get_decision_breakdown,
    get_confidence_trends,
    get_sensitive_category_trends,
    get_recent_queries,
    get_recent_audit_events,
)


st.set_page_config(
    page_title="Admin Governance Dashboard",
    page_icon="📊",
    layout="wide",
)

current_user = st.session_state.get("current_user")

if not current_user:
    st.error("No authenticated user.")
    st.stop()

if current_user.get("role") != "admin":
    st.error("Access denied. Admins only.")
    st.stop()


st.title("📊 Admin Governance Dashboard")
st.caption("Monitor usage, escalation trends, review activity, and audit coverage.")


metrics = get_system_metrics()

st.subheader("System Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Queries", metrics["total_queries"])
col2.metric(
    "Escalations",
    metrics["escalated_count"],
    f'{metrics["escalation_rate"]}%'
)
col3.metric(
    "Refusals",
    metrics["refused_count"],
    f'{metrics["refusal_rate"]}%'
)
col4.metric("Reviews Completed", metrics["completed_reviews"])

col5, col6 = st.columns(2)

col5.metric("Audit Events", metrics["total_audit_events"])
col6.metric("Source Citations Logged", metrics["total_sources"])

st.divider()


st.subheader("Decision Breakdown")

decision_counts = get_decision_breakdown()

if not decision_counts.empty:
    st.bar_chart(decision_counts)
else:
    st.info("No decision data available yet.")

st.divider()


st.subheader("Confidence Overview")

confidence_trends = get_confidence_trends()

st.metric("Average Confidence", metrics["average_confidence"])

if not confidence_trends.empty:
    st.line_chart(confidence_trends)
else:
    st.info("No confidence data available yet.")

st.divider()


st.subheader("Sensitive Category Trends")

category_df = get_sensitive_category_trends()

if not category_df.empty:
    st.bar_chart(category_df.set_index("category"))
else:
    st.info("No sensitive category data available yet.")

st.divider()


st.subheader("Review Queue Health")

col7, col8 = st.columns(2)

col7.metric("Pending Reviews", metrics["pending_reviews"])
col8.metric("Completed Reviews", metrics["completed_reviews"])

st.divider()


st.subheader("Recent Queries")

recent_queries = get_recent_queries()

if not recent_queries.empty:
    st.dataframe(recent_queries, use_container_width=True)
else:
    st.info("No queries logged yet.")


st.subheader("Recent Audit Events")

recent_audit_events = get_recent_audit_events()

if not recent_audit_events.empty:
    st.dataframe(recent_audit_events, use_container_width=True)
else:
    st.info("No audit events logged yet.")