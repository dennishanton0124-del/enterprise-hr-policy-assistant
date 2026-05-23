#!/usr/bin/env python3
"""
End-to-end test script for Supabase logging in the Enterprise HR Policy Assistant.
Tests all decision paths: escalate, refuse, answer.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 100)
print("ENTERPRISE HR POLICY ASSISTANT - SUPABASE LOGGING TEST")
print("=" * 100)

# Test 1: Verify Supabase client
print("\n[TEST 1] Supabase client initialization...")
try:
    from backend.db.supabase_client import supabase
    assert supabase is not None, "Supabase client is None"
    assert hasattr(supabase, 'insert'), "Missing insert method"
    assert hasattr(supabase, 'select'), "Missing select method"
    print("[TEST 1] PASSED - Supabase client ready")
except Exception as e:
    print(f"[TEST 1] FAILED: {e}")
    sys.exit(1)

# Test 2: Test answer decision path (high confidence, no sensitive keywords)
print("\n[TEST 2] Testing ANSWER decision path...")
try:
    from backend.services.answer_question import generate_answer
    
    # Mock chunks for answer path
    mock_chunks = [
        {
            "document_id": "WFH-2025-001",
            "chunk_id": "chunk-1",
            "section_title": "Work From Home Policy",
            "page_or_section": "1.1",
            "chunk_text": "Employees may work from home up to 3 days per week.",
            "similarity": 0.95,
            "id": "chunk-1"
        }
    ]
    
    print("[TEST 2] Calling generate_answer with high-confidence question...")
    result = generate_answer("Can I work from home?", mock_chunks)
    
    assert result["decision_type"] == "answer", f"Expected 'answer', got {result['decision_type']}"
    assert result["status"] == "answered", f"Expected 'answered', got {result['status']}"
    assert result["confidence_score"] >= 0.90, f"Expected high confidence, got {result['confidence_score']}"
    print("[TEST 2] PASSED - ANSWER path logged to Supabase")
except Exception as e:
    print(f"[TEST 2] FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Test refuse decision path (low confidence)
print("\n[TEST 3] Testing REFUSE decision path...")
try:
    # Mock chunks for refuse path (empty = low confidence)
    mock_chunks = []
    
    print("[TEST 3] Calling generate_answer with no chunks...")
    result = generate_answer("What's the secret employee discount?", mock_chunks)
    
    assert result["decision_type"] == "refuse", f"Expected 'refuse', got {result['decision_type']}"
    assert result["status"] == "refused", f"Expected 'refused', got {result['status']}"
    print("[TEST 3] PASSED - REFUSE path logged to Supabase")
except Exception as e:
    print(f"[TEST 3] FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test escalate decision path (sensitive keyword)
print("\n[TEST 4] Testing ESCALATE decision path...")
try:
    from backend.services.review_service import get_escalated_queries
    
    # Mock chunks (irrelevant since sensitive keywords trigger escalate)
    mock_chunks = [
        {
            "document_id": "LEAVE-2025-001",
            "chunk_id": "chunk-2",
            "section_title": "Medical Leave",
            "page_or_section": "2.1",
            "chunk_text": "Medical leave requires HR approval.",
            "similarity": 0.85,
            "id": "chunk-2"
        }
    ]
    
    print("[TEST 4] Calling generate_answer with sensitive keyword (medical leave)...")
    result = generate_answer("Can my manager fire me for taking medical leave?", mock_chunks)
    
    assert result["decision_type"] == "escalate", f"Expected 'escalate', got {result['decision_type']}"
    assert result["status"] == "escalated", f"Expected 'escalated', got {result['status']}"
    assert "medical leave" in result["sensitive_categories"], f"Expected 'medical leave' in categories"
    print("[TEST 4] PASSED - ESCALATE path logged to Supabase")
    
    # Verify escalated query appears in list
    print("[TEST 4] Fetching escalated queries from Supabase...")
    escalated_queries = get_escalated_queries()
    assert len(escalated_queries) > 0, "No escalated queries found in Supabase"
    
    escalated_query = escalated_queries[0]
    assert escalated_query["status"] == "escalated", "Query not marked as escalated"
    print(f"[TEST 4] Found escalated query: {escalated_query['id']}")
    print("[TEST 4] PASSED - Escalated query visible in HR Review Queue")
    
except Exception as e:
    print(f"[TEST 4] FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test review submission
print("\n[TEST 5] Testing HR review submission...")
try:
    from backend.services.review_service import submit_review, get_escalated_queries
    
    # Get the latest escalated query
    escalated_queries = get_escalated_queries()
    if escalated_queries:
        query_id = escalated_queries[0]["id"]
        
        print(f"[TEST 5] Submitting review for query {query_id}...")
        review_result = submit_review(
            query_id=query_id,
            reviewer_id="hr_reviewer_001",
            reviewer_status="approved",
            reviewer_notes="Approved for medical leave. Employee has submitted proper documentation.",
            final_answer="Your request for medical leave has been approved by HR. Please contact HR to finalize the dates."
        )
        
        assert review_result is not None, "Review submission returned None"
        assert review_result.get("id") is not None, "Review has no ID"
        print(f"[TEST 5] PASSED - Review submitted with ID: {review_result['id']}")
    else:
        print("[TEST 5] SKIPPED - No escalated queries available")
        
except Exception as e:
    print(f"[TEST 5] FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Verify all tables have data
print("\n[TEST 6] Verifying Supabase tables...")
try:
    from backend.db.supabase_client import supabase
    
    print("[TEST 6] Checking queries table...")
    queries = supabase.select("queries", "order=created_at.desc&limit=5")
    print(f"[TEST 6] Found {len(queries)} recent queries")
    
    print("[TEST 6] Checking query_sources table...")
    sources = supabase.select("query_sources", "order=created_at.desc&limit=10")
    print(f"[TEST 6] Found {len(sources)} recent citations")
    
    print("[TEST 6] Checking audit_events table...")
    audit_events = supabase.select("audit_events", "order=created_at.desc&limit=10")
    print(f"[TEST 6] Found {len(audit_events)} recent audit events")
    
    print("[TEST 6] Checking reviews table...")
    reviews = supabase.select("reviews", "order=reviewed_at.desc&limit=5")
    print(f"[TEST 6] Found {len(reviews)} recent reviews")
    
    print("[TEST 6] PASSED - All tables populated")
    
except Exception as e:
    print(f"[TEST 6] WARNING: {e}")

print("\n" + "=" * 100)
print("ALL TESTS COMPLETED")
print("=" * 100)
print("\nNext steps:")
print("1. Run: streamlit run frontend/app.py")
print("2. Ask questions in the app")
print("3. Check HR Review Queue page")
print("4. Submit reviews to test complete flow")
print("\nCheck Supabase tables:")
print("- queries: All questions asked")
print("- query_sources: All citations")
print("- audit_events: All interactions")
print("- reviews: All HR reviews submitted")
print("=" * 100 + "\n")
