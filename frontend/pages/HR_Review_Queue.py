import streamlit as st

current_user = st.session_state.get("current_user")

if not current_user:
    st.error("No authenticated user.")
    st.stop()

if current_user["role"] not in ["hr_reviewer", "admin"]:
    st.error("Access denied. HR reviewers only.")
    st.stop()

from backend.services.review_service import (
    get_escalated_queries,
    get_query_sources,
    submit_review,
)

st.set_page_config(
    page_title="HR Review Queue",
    page_icon="🧑‍⚖️",
    layout="wide",
)

st.title("🧑‍⚖️ HR Review Queue")
st.caption("Review escalated HR policy questions that require human oversight.")

reviewer_id = st.text_input(
    "Reviewer ID",
    value="hr_reviewer_001",
    help="Temporary reviewer ID for demo purposes."
)

st.divider()

queries = get_escalated_queries()

if not queries:
    st.success("No escalated questions waiting for review.")
    st.stop()

st.subheader(f"Pending escalations: {len(queries)}")

for query in queries:
    query_id = query["id"]

    with st.expander(
        f"Escalated Question | Confidence: {query.get('confidence_score')} | Created: {query.get('created_at')}",
        expanded=False,
    ):
        st.markdown("### Employee Question")
        st.write(query.get("user_question"))

        st.markdown("### AI Response")
        st.write(query.get("answer"))

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Decision", query.get("decision_type"))

        with col2:
            st.metric("Status", query.get("status"))

        with col3:
            st.metric("Confidence", query.get("confidence_score"))

        st.markdown("### Escalation Details")
        st.write(f"**Reason:** {query.get('escalation_reason')}")

        sensitive_categories = query.get("sensitive_categories") or []
        if sensitive_categories:
            st.write("**Sensitive Categories:**")
            for category in sensitive_categories:
                st.write(f"- {category}")
        else:
            st.write("**Sensitive Categories:** None")

        st.markdown("### Sources Used")
        sources = get_query_sources(query_id)

        if sources:
            for source in sources:
                st.write(f"**Document ID:** {source.get('document_id')}")
                st.write(f"**Chunk ID:** {source.get('chunk_id')}")
                st.write(f"**Citation:** {source.get('citation_text')}")
                st.write(f"**Relevance Score:** {source.get('relevance_score')}")
                st.divider()
        else:
            st.info("No sources logged for this query.")

        st.markdown("### HR Review")

        reviewer_status = st.selectbox(
            "Review Status",
            options=["pending", "approved", "rejected", "resolved"],
            key=f"status_{query_id}",
        )

        reviewer_notes = st.text_area(
            "Reviewer Notes",
            key=f"notes_{query_id}",
            placeholder="Add HR review notes here...",
        )

        final_answer = st.text_area(
            "Final HR-Approved Answer",
            key=f"final_answer_{query_id}",
            placeholder="Optional final response approved by HR...",
        )

        if st.button("Submit Review", key=f"submit_{query_id}"):
            submit_review(
                query_id=query_id,
                reviewer_id=reviewer_id,
                reviewer_status=reviewer_status,
                reviewer_notes=reviewer_notes,
                final_answer=final_answer,
            )

            st.success("Review submitted successfully.")
            st.rerun()