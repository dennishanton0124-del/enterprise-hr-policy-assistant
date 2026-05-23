import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from backend.db.supabase_client import supabase


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)

N8N_ESCALATION_WEBHOOK_URL = os.getenv("N8N_ESCALATION_WEBHOOK_URL")


def send_escalation_notification(
    *,
    query_id: str,
    user_question: str,
    answer: str,
    confidence_score: float,
    escalation_reason: str | None,
    sensitive_categories: list[str],
):
    print("[notification_service] Preparing escalation notification...")

    if not N8N_ESCALATION_WEBHOOK_URL:
        print("[notification_service] No N8N webhook URL configured.")
        return None

    payload = {
        "event_type": "hr_escalation_created",
        "query_id": query_id,
        "user_question": user_question,
        "answer": answer,
        "confidence_score": confidence_score,
        "escalation_reason": escalation_reason,
        "sensitive_categories": sensitive_categories,
        "review_queue": "Open the HR Review Queue in Streamlit.",
    }

    try:
        response = requests.post(
            N8N_ESCALATION_WEBHOOK_URL,
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

        print("[notification_service] n8n notification sent successfully.")
        print("[notification_service] Response:", response.text)

        if supabase is not None:
            supabase.insert(
                "audit_events",
                {
                    "query_id": query_id,
                    "user_id": None,
                    "event_type": "escalation_notification_sent",
                    "event_description": "Escalation notification sent to n8n workflow.",
                },
            )

        return payload

    except Exception as e:
        print("[notification_service] ERROR sending n8n notification:", e)

        if supabase is not None:
            supabase.insert(
                "audit_events",
                {
                    "query_id": query_id,
                    "user_id": None,
                    "event_type": "escalation_notification_failed",
                    "event_description": str(e),
                },
            )

        return None