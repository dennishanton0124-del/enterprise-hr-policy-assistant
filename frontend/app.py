import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.retrieval_service import search_chunks
from backend.services.answer_question import generate_answer
from backend.services.auth_service import get_users

st.set_page_config(
    page_title="Enterprise HR Policy Assistant",
    page_icon="📘",
    layout="wide"
)

users = get_users()

if not users:
    st.error("No users found. Please add test users to the users table.")
    st.stop()

user_options = {
    f"{user['email']} ({user['role']})": user
    for user in users
}

selected_label = st.sidebar.selectbox(
    "Select Test User",
    options=list(user_options.keys())
)

selected_user = user_options[selected_label]

st.session_state["current_user"] = selected_user

st.sidebar.markdown("### Current Role")
st.sidebar.write(selected_user["role"])

st.title("📘 Enterprise HR Policy Assistant")
st.caption("Source-grounded HR policy answers with confidence scoring and citations.")

question = st.text_area(
    "Ask an HR policy question:",
    placeholder="Example: Can I carry over unused PTO?"
)

if st.button("Ask Question"):
    print("\n" + "="*80)
    print("[FRONTEND] Ask Question button CLICKED")
    print("="*80)
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Searching approved HR policies..."):
            print("[FRONTEND] Calling search_chunks...")
            chunks = search_chunks(question)
            print(f"[FRONTEND] Got {len(chunks)} chunks")
            
            print("[FRONTEND] Calling generate_answer...")
            result = generate_answer(question, chunks)
            print(f"[FRONTEND] Got result: decision_type={result.get('decision_type')}, status={result.get('status')}")

        print(f"[FRONTEND] Rendering result to UI...")
        decision = result["decision_type"]
        confidence = result["confidence_score"]

        st.subheader("Decision")

        if decision == "answer":
            st.success(f"Decision: Answer | Confidence: {confidence}")
        elif decision == "refuse":
            st.error(f"Decision: Refuse | Confidence: {confidence}")
        else:
            st.warning(f"Decision: {decision} | Confidence: {confidence}")

        st.subheader("Answer")
        st.write(result["answer"])

        st.subheader("Citations")

        if result["citations"]:
            for citation in result["citations"]:
                st.markdown(
                    f"""
                    **Document:** {citation['document_id']}  
                    **Section:** {citation['page_or_section']} — {citation['section_title']}  
                    **Similarity:** {round(citation['similarity'], 3)}
                    """
                )
                st.divider()
        else:
            st.info("No citations available.")
        
        print("[FRONTEND] Rendering complete")
        print("="*80 + "\n")