SENSITIVE_TOPICS = {
    "medical leave": [
        "medical leave",
        "fmla",
        "sick leave",
        "health condition",
        "disability",
        "medical",
    ],

    "pregnancy or parental leave": [
        "pregnant",
        "pregnancy",
        "maternity leave",
        "parental leave",
        "paternity leave",
        "promotion chances",
        "hurt my promotion",
        "protected leave",
    ],

    "termination": [
        "fire",
        "fired",
        "terminate",
        "termination",
        "laid off",
        "dismissed",
    ],

    "legal risk": [
        "sue",
        "lawsuit",
        "legal",
        "lawyer",
        "rights",
        "liable",
        "is that allowed",
    ],

    "retaliation": [
        "retaliation",
        "retaliate",
        "punished",
        "punish",
    ],

    "harassment": [
        "harassment",
        "harassed",
    ],

    "discrimination": [
        "discrimination",
        "discriminated",
        "religion",
        "race",
        "age",
        "gender",
        "sex",
        "pregnant",
        "pregnancy",
    ],

    "compensation disputes": [
        "pay dispute",
        "wage",
        "salary dispute",
        "unpaid",
    ],

    "benefits disputes": [
        "benefits dispute",
        "insurance dispute",
        "claim denied",
    ],
}


def detect_sensitive_categories(question: str) -> list[str]:
    question_lower = question.lower()
    detected_categories = []

    for category, keywords in SENSITIVE_TOPICS.items():
        for keyword in keywords:
            if keyword in question_lower:
                detected_categories.append(category)
                break

    return detected_categories


def route_decision(
    question: str,
    confidence_score: float,
    confidence_threshold: float = 0.70,
) -> dict:
    print("=" * 80)
    print("USING UPDATED DECISION ROUTER")
    print("QUESTION:", question)

    sensitive_categories = detect_sensitive_categories(question)

    print("SENSITIVE CATEGORIES:", sensitive_categories)
    print("CONFIDENCE SCORE:", confidence_score)
    print("=" * 80)

    # Rule 1: Sensitive HR topics always escalate first
    if sensitive_categories:
        print("[decision_router] ESCALATE triggered")

        return {
            "decision_type": "escalate",
            "status": "escalated",
            "escalation_reason": "Sensitive HR topic detected",
            "sensitive_categories": sensitive_categories,
        }

    # Rule 2: If confidence is below threshold, refuse
    if confidence_score < confidence_threshold:
        print("[decision_router] REFUSE triggered")

        return {
            "decision_type": "refuse",
            "status": "refused",
            "escalation_reason": None,
            "sensitive_categories": [],
        }

    # Rule 3: Safe + enough source support = answer
    print("[decision_router] ANSWER triggered")

    return {
        "decision_type": "answer",
        "status": "answered",
        "escalation_reason": None,
        "sensitive_categories": [],
    }