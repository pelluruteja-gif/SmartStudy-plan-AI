import sys
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime, timedelta

def test_full_pipeline():
    client = TestClient(app)
    
    print("1. Testing GET /api/sample-templates...")
    resp = client.get("/api/sample-templates")
    assert resp.status_code == 200
    templates = resp.json()
    assert len(templates) >= 3
    print(f"   -> Successfully retrieved {len(templates)} sample templates.")

    print("2. Testing POST /api/generate-plan with student payload...")
    today = datetime.now().strftime("%Y-%m-%d")
    two_weeks = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    sample_data = templates[0]["data"]
    sample_data["start_date"] = today
    sample_data["exam_date"] = two_weeks

    resp = client.post("/api/generate-plan", json=sample_data)
    assert resp.status_code == 200, f"Status code: {resp.status_code}, error: {resp.text}"
    plan = resp.json()
    assert "daily_schedules" in plan
    assert len(plan["daily_schedules"]) == 14
    assert len(plan["phases"]) == 4
    print(f"   -> Plan generated successfully: {plan['summary']}")
    print(f"   -> Total study hours: {plan['total_study_hours']} hrs across {plan['total_days']} days.")

    print("3. Testing POST /api/export-ics...")
    ics_resp = client.post("/api/export-ics", json=plan)
    assert ics_resp.status_code == 200
    assert "BEGIN:VCALENDAR" in ics_resp.text
    assert "END:VCALENDAR" in ics_resp.text
    print(f"   -> iCalendar (.ics) export generated ({len(ics_resp.text)} bytes).")

    print("4. Testing POST /api/export-markdown...")
    md_resp = client.post("/api/export-markdown", json=plan)
    assert md_resp.status_code == 200
    assert "# 🎯 Personalized Study Roadmap" in md_resp.text
    print(f"   -> Markdown export generated ({len(md_resp.text)} bytes).")

    print("5. Testing POST /api/chat (Copilot)...")
    chat_resp = client.post("/api/chat", json={
        "plan_summary": {
            "student_name": plan["student_name"],
            "summary": plan["summary"],
            "total_days": plan["total_days"],
            "current_day": 1
        },
        "user_message": "I missed my physics study session today, how should I reschedule it?",
        "conversation_history": []
    })
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "reply" in chat_data
    assert len(chat_data.get("suggestions", [])) > 0
    print(f"   -> Copilot replied: {chat_data['reply'][:100]}...")

    print("6. Testing GET / (Static HTML Serving)...")
    html_resp = client.get("/")
    assert html_resp.status_code == 200
    assert "SmartStudy AI" in html_resp.text or "StudyMind AI" in html_resp.text
    print("   -> Frontend HTML served cleanly with SmartStudy AI.")

    print("\n[SUCCESS] ALL SYSTEM TESTS PASSED PERFECTLY!\n")

if __name__ == "__main__":
    test_full_pipeline()
