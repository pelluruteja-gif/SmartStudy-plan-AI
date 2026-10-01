"""
Comprehensive Security, Robustness, and System Integration Test Suite
Verifies:
1. Security Headers (nosniff, DENY, Referrer-Policy)
2. CORS Configuration for intended local frontend
3. Input Validation: Rejection of invalid inputs (empty name, negative hours, prep > 100%, bad date)
4. Normal Valid Input processing
5. Main study-plan creation flow
6. AI Study Coach & Chat assistant
7. Calendar & Markdown Exports with Filename Sanitization & CRLF Injection Prevention
"""

import sys
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app

def run_security_and_system_tests():
    client = TestClient(app)
    today = datetime.now().date()
    two_weeks = (today + timedelta(days=14)).strftime("%Y-%m-%d")

    print("\n" + "="*60)
    print("🔒 RUNNING SMARTSTUDY AI SECURITY & RELIABILITY VERIFICATION")
    print("="*60)

    # ---------------------------------------------------------
    # 1. SECURITY HEADERS TEST
    # ---------------------------------------------------------
    print("\n[1] Testing Security Response Headers...")
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff", "Missing X-Content-Type-Options header"
    assert resp.headers.get("X-Frame-Options") == "DENY", "Missing X-Frame-Options header"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin", "Missing Referrer-Policy header"
    print("  -> [PASS] Security headers present: nosniff, DENY, strict-origin-when-cross-origin")

    # ---------------------------------------------------------
    # 2. CORS CONFIGURATION TEST
    # ---------------------------------------------------------
    print("\n[2] Testing CORS Configuration for Intended Local Frontend...")
    # Origin 1: Allowed local origin
    cors_resp = client.options(
        "/api/smartstudy/priority",
        headers={
            "Origin": "http://127.0.0.1:8000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
    assert cors_resp.status_code == 200
    assert cors_resp.headers.get("access-control-allow-origin") == "http://127.0.0.1:8000"
    print("  -> [PASS] CORS correctly permits intended local origin: http://127.0.0.1:8000")

    # ---------------------------------------------------------
    # 3. INPUT VALIDATION TESTS (REJECTION OF MALFORMED INPUTS)
    # ---------------------------------------------------------
    print("\n[3] Testing Input Validation & Rejection of Malformed Requests...")
    
    # 3a: Empty subject name
    bad_name_resp = client.post("/api/smartstudy/priority", json=[
        {"name": "", "exam_date": two_weeks, "difficulty": "Hard", "prep_percentage": 50.0}
    ])
    assert bad_name_resp.status_code == 422, f"Expected 422 for empty name, got {bad_name_resp.status_code}"
    print("  -> [PASS] Rejected empty subject name with HTTP 422")

    # 3b: Negative preparation percentage
    neg_prep_resp = client.post("/api/smartstudy/priority", json=[
        {"name": "DSA", "exam_date": two_weeks, "difficulty": "Hard", "prep_percentage": -25.0}
    ])
    assert neg_prep_resp.status_code == 422, f"Expected 422 for negative prep %, got {neg_prep_resp.status_code}"
    print("  -> [PASS] Rejected negative preparation % with HTTP 422")

    # 3c: Preparation percentage > 100
    high_prep_resp = client.post("/api/smartstudy/priority", json=[
        {"name": "DSA", "exam_date": two_weeks, "difficulty": "Hard", "prep_percentage": 150.0}
    ])
    assert high_prep_resp.status_code == 422, f"Expected 422 for prep % > 100, got {high_prep_resp.status_code}"
    print("  -> [PASS] Rejected preparation % > 100 with HTTP 422")

    # 3d: Malformed exam date
    bad_date_resp = client.post("/api/smartstudy/priority", json=[
        {"name": "DSA", "exam_date": "not-a-date-123", "difficulty": "Hard", "prep_percentage": 50.0}
    ])
    assert bad_date_resp.status_code == 422, f"Expected 422 for invalid date, got {bad_date_resp.status_code}"
    print("  -> [PASS] Rejected malformed exam date string with HTTP 422")

    # 3e: Negative / Zero study hours in plan request
    zero_hrs_resp = client.post("/api/smartstudy/plan", json={
        "available_hours": 0.0,
        "subjects": [{"name": "DSA", "exam_date": two_weeks, "difficulty": "Hard", "prep_percentage": 50.0}]
    })
    assert zero_hrs_resp.status_code == 422, f"Expected 422 for 0.0 hours, got {zero_hrs_resp.status_code}"
    print("  -> [PASS] Rejected zero available study hours with HTTP 422")

    # 3f: Excessive study hours (> 24)
    huge_hrs_resp = client.post("/api/smartstudy/plan", json={
        "available_hours": 30.0,
        "subjects": [{"name": "DSA", "exam_date": two_weeks, "difficulty": "Hard", "prep_percentage": 50.0}]
    })
    assert huge_hrs_resp.status_code == 422, f"Expected 422 for >24 hours, got {huge_hrs_resp.status_code}"
    print("  -> [PASS] Rejected available study hours > 24 with HTTP 422")

    # ---------------------------------------------------------
    # 4. NORMAL VALID INPUTS & PLAN CREATION FLOW
    # ---------------------------------------------------------
    print("\n[4] Testing Normal Valid Input & Plan Creation Flow...")
    valid_payload = {
        "available_hours": 4.5,
        "subjects": [
            {"id": "os", "name": "Operating Systems", "exam_date": (today + timedelta(days=3)).strftime("%Y-%m-%d"), "difficulty": "Hard", "prep_percentage": 25.0},
            {"id": "dsa", "name": "Algorithms", "exam_date": (today + timedelta(days=6)).strftime("%Y-%m-%d"), "difficulty": "Hard", "prep_percentage": 45.0},
            {"id": "dbms", "name": "Databases", "exam_date": (today + timedelta(days=10)).strftime("%Y-%m-%d"), "difficulty": "Medium", "prep_percentage": 60.0}
        ]
    }
    plan_resp = client.post("/api/smartstudy/plan", json=valid_payload)
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()
    assert plan_data["daily_hours"] == 4.5
    assert len(plan_data["tasks"]) >= 3
    assert plan_data["highest_priority_subject"] == "Operating Systems"
    print(f"  -> [PASS] Study plan created successfully with {len(plan_data['tasks'])} sessions.")

    # ---------------------------------------------------------
    # 5. AI STUDY COACH & COPILOT CHAT TEST
    # ---------------------------------------------------------
    print("\n[5] Testing AI Study Coach / Copilot...")
    chat_resp = client.post("/api/chat", json={
        "plan_summary": {"student_name": "Test Student", "summary": "Finals", "total_days": 10},
        "user_message": "How do I balance Operating Systems and Algorithms today?",
        "conversation_history": []
    })
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "reply" in chat_data
    assert len(chat_data.get("suggestions", [])) > 0
    print(f"  -> [PASS] AI Coach responded cleanly: '{chat_data['reply'][:65]}...'")

    # ---------------------------------------------------------
    # 6. CALENDAR & MARKDOWN EXPORT + HEADER INJECTION PREVENTION
    # ---------------------------------------------------------
    print("\n[6] Testing Export Functionality & Filename Injection Prevention...")
    
    # Retrieve a sample plan template
    tpl_resp = client.get("/api/sample-templates")
    assert tpl_resp.status_code == 200
    sample_plan = tpl_resp.json()[0]["data"]
    gen_resp = client.post("/api/generate-plan", json=sample_plan)
    assert gen_resp.status_code == 200
    full_plan = gen_resp.json()

    # Inject malicious student name containing CRLF and directory traversal characters
    full_plan["student_name"] = "Alice\r\nEvil-Header: injected\r\n../../etc/passwd"

    # Test ICS export
    ics_resp = client.post("/api/export-ics", json=full_plan)
    assert ics_resp.status_code == 200
    cd_header = ics_resp.headers.get("content-disposition", "")
    assert "\r" not in cd_header and "\n" not in cd_header, "CRLF detected in Content-Disposition!"
    assert ".." not in cd_header, "Directory traversal detected in Content-Disposition!"
    assert "BEGIN:VCALENDAR" in ics_resp.text
    print(f"  -> [PASS] Calendar (.ics) export safe and sanitized: {cd_header}")

    # Test Markdown export
    md_resp = client.post("/api/export-markdown", json=full_plan)
    assert md_resp.status_code == 200
    cd_md_header = md_resp.headers.get("content-disposition", "")
    assert "\r" not in cd_md_header and "\n" not in cd_md_header, "CRLF detected in Content-Disposition!"
    assert ".." not in cd_md_header, "Directory traversal detected in Content-Disposition!"
    assert "# 🎯 Personalized Study Roadmap" in md_resp.text
    print(f"  -> [PASS] Markdown (.md) export safe and sanitized: {cd_md_header}")

    print("\n" + "="*60)
    print(">>> ALL SECURITY & SYSTEM INTEGRATION TESTS PASSED (6/6) <<<")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_security_and_system_tests()
