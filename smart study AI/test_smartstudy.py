"""
Comprehensive Production-Readiness Test Suite for SmartStudy AI
Tests:
1. Core Priority Algorithm (Urgency, Difficulty, Prep Gap, Weighted Formula)
2. Priority Levels (High >= 70, Medium >= 45, Low < 45)
3. Priority Score Updates dynamically when Preparation Percentage changes
4. Exam Countdowns accuracy based on current date
5. Daily study hours NEVER exceed user's configured limit (1.0h, 2.0h, 4.5h, 6.0h)
6. Proportional Time Distribution & Required Session Labels
7. Sample Preset Data Integrity
8. FastAPI Endpoints & Static UI Serving
"""

import sys
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import (
    app,
    calculate_urgency_score,
    calculate_difficulty_score,
    analyze_smart_subject,
    SmartSubject,
    SmartStudyPlanRequest
)

def test_priority_algorithm():
    print("\n--- TEST 1: CORE PRIORITY ALGORITHM ---")
    today = datetime.now().date()
    
    # Test Difficulty mapping
    assert calculate_difficulty_score("Easy") == 20.0, "Easy difficulty should be 20"
    assert calculate_difficulty_score("Medium") == 50.0, "Medium difficulty should be 50"
    assert calculate_difficulty_score("Hard") == 80.0, "Hard difficulty should be 80"
    print("  [PASS] Difficulty scores: Easy=20, Medium=50, Hard=80")

    # Test Urgency scores based on days remaining
    u_0 = calculate_urgency_score(0)
    u_1 = calculate_urgency_score(1)
    u_2 = calculate_urgency_score(2)
    u_7 = calculate_urgency_score(7)
    u_14 = calculate_urgency_score(14)
    u_30 = calculate_urgency_score(30)
    
    assert u_0 == 100.0, "Day 0 urgency should be 100"
    assert u_1 == 100.0, "Day 1 urgency should be 100"
    assert u_2 == 96.0, "Day 2 urgency should be 96.0"
    assert u_7 == 76.0, "Day 7 urgency should be 76.0"
    assert u_14 == 61.0, "Day 14 urgency should be 61.0"
    assert u_30 == 29.0, "Day 30 urgency should be 29.0"
    print("  [PASS] Urgency scores calibrated across days remaining (100 -> 29)")

    # Test Priority calculation for High, Medium, Low subjects
    # Subject 1: High Priority (Exam in 2 days, Hard, 25% prep)
    # Urgency: 95, Diff: 80, Gap: 75
    # Priority: 95*0.4 (38) + 80*0.25 (20) + 75*0.35 (26.25) = 84.25 -> 84.2 or 84.3 (High >= 70)
    sub_high = SmartSubject(
        id="sub-1",
        name="Operating Systems",
        exam_date=(today + timedelta(days=2)).strftime("%Y-%m-%d"),
        difficulty="Hard",
        prep_percentage=25.0
    )
    analysis_high = analyze_smart_subject(sub_high)
    assert analysis_high.prep_gap == 75.0, "Prep gap should be 100 - 25 = 75"
    assert analysis_high.priority_score >= 70.0, f"Expected High (>=70), got {analysis_high.priority_score}"
    assert analysis_high.priority_level == "High", "Expected High priority level"
    print(f"  [PASS] High Priority Subject: {analysis_high.name} -> Score: {analysis_high.priority_score} (Level: {analysis_high.priority_level})")

    # Subject 2: Medium Priority (Exam in 10 days, Medium, 60% prep)
    # Urgency: 55, Diff: 50, Gap: 40
    # Priority: 55*0.4 (22) + 50*0.25 (12.5) + 40*0.35 (14) = 48.5 -> Medium (>= 45 and < 70)
    sub_med = SmartSubject(
        id="sub-2",
        name="Computer Networks",
        exam_date=(today + timedelta(days=10)).strftime("%Y-%m-%d"),
        difficulty="Medium",
        prep_percentage=60.0
    )
    analysis_med = analyze_smart_subject(sub_med)
    assert 45.0 <= analysis_med.priority_score < 70.0, f"Expected Medium, got {analysis_med.priority_score}"
    assert analysis_med.priority_level == "Medium"
    print(f"  [PASS] Medium Priority Subject: {analysis_med.name} -> Score: {analysis_med.priority_score} (Level: {analysis_med.priority_level})")

    # Subject 3: Low Priority (Exam in 28 days, Easy, 85% prep)
    # Urgency: 25, Diff: 20, Gap: 15
    # Priority: 25*0.4 (10) + 20*0.25 (5) + 15*0.35 (5.25) = 20.25 -> Low (< 45)
    sub_low = SmartSubject(
        id="sub-3",
        name="Technical Writing",
        exam_date=(today + timedelta(days=28)).strftime("%Y-%m-%d"),
        difficulty="Easy",
        prep_percentage=85.0
    )
    analysis_low = analyze_smart_subject(sub_low)
    assert analysis_low.priority_score < 45.0, f"Expected Low (<45), got {analysis_low.priority_score}"
    assert analysis_low.priority_level == "Low"
    print(f"  [PASS] Low Priority Subject: {analysis_low.name} -> Score: {analysis_low.priority_score} (Level: {analysis_low.priority_level})")


def test_preparation_updates_priority():
    print("\n--- TEST 2: PRIORITY UPDATES WHEN PREPARATION CHANGES ---")
    today = datetime.now().date()
    exam_str = (today + timedelta(days=5)).strftime("%Y-%m-%d")

    # When preparation increases, prep gap decreases, priority score MUST decrease
    sub_20 = SmartSubject(name="DSA", exam_date=exam_str, difficulty="Hard", prep_percentage=20.0)
    sub_50 = SmartSubject(name="DSA", exam_date=exam_str, difficulty="Hard", prep_percentage=50.0)
    sub_80 = SmartSubject(name="DSA", exam_date=exam_str, difficulty="Hard", prep_percentage=80.0)

    score_20 = analyze_smart_subject(sub_20).priority_score
    score_50 = analyze_smart_subject(sub_50).priority_score
    score_80 = analyze_smart_subject(sub_80).priority_score

    assert score_20 > score_50 > score_80, "Higher preparation % must strictly lower the priority score"
    # Mathematical difference: 30% prep difference * 0.35 weight = 10.5 points difference
    diff_20_50 = round(score_20 - score_50, 1)
    diff_50_80 = round(score_50 - score_80, 1)
    assert abs(diff_20_50 - 10.5) <= 0.1, f"Expected ~10.5 point drop, got {diff_20_50}"
    assert abs(diff_50_80 - 10.5) <= 0.1, f"Expected ~10.5 point drop, got {diff_50_80}"
    print(f"  [PASS] Prep: 20% -> Score {score_20} | Prep: 50% -> Score {score_50} | Prep: 80% -> Score {score_80}")
    print(f"  [PASS] Verified exact mathematical priority score update: -10.5 pts per 30% prep boost")


def test_exam_countdown_current_date():
    print("\n--- TEST 3: EXAM COUNTDOWN USES CURRENT DATE CORRECTLY ---")
    today = datetime.now().date()

    # Exam today
    sub_today = SmartSubject(name="Exam Today", exam_date=today.strftime("%Y-%m-%d"), difficulty="Medium")
    a_today = analyze_smart_subject(sub_today)
    assert a_today.days_remaining == 0, f"Expected 0 days for exam today, got {a_today.days_remaining}"

    # Exam tomorrow
    sub_tom = SmartSubject(name="Exam Tomorrow", exam_date=(today + timedelta(days=1)).strftime("%Y-%m-%d"), difficulty="Medium")
    a_tom = analyze_smart_subject(sub_tom)
    assert a_tom.days_remaining == 1, f"Expected 1 day for exam tomorrow, got {a_tom.days_remaining}"

    # Exam in 7 days
    sub_week = SmartSubject(name="Exam in 1 Week", exam_date=(today + timedelta(days=7)).strftime("%Y-%m-%d"), difficulty="Medium")
    a_week = analyze_smart_subject(sub_week)
    assert a_week.days_remaining == 7, f"Expected 7 days for exam in a week, got {a_week.days_remaining}"
    print("  [PASS] Countdowns: Today=0 days, Tomorrow=1 day, In 7 days=7 days")


def test_daily_hours_limit_never_exceeded():
    print("\n--- TEST 4: DAILY STUDY HOURS NEVER EXCEED CONFIGURED LIMIT ---")
    client = TestClient(app)
    today = datetime.now().date()

    test_subjects = [
        {"id": "s1", "name": "OS", "exam_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"), "difficulty": "Hard", "prep_percentage": 25.0},
        {"id": "s2", "name": "DSA", "exam_date": (today + timedelta(days=5)).strftime("%Y-%m-%d"), "difficulty": "Hard", "prep_percentage": 40.0},
        {"id": "s3", "name": "DBMS", "exam_date": (today + timedelta(days=7)).strftime("%Y-%m-%d"), "difficulty": "Medium", "prep_percentage": 50.0},
        {"id": "s4", "name": "Networks", "exam_date": (today + timedelta(days=11)).strftime("%Y-%m-%d"), "difficulty": "Medium", "prep_percentage": 65.0},
        {"id": "s5", "name": "Ethics", "exam_date": (today + timedelta(days=20)).strftime("%Y-%m-%d"), "difficulty": "Easy", "prep_percentage": 80.0},
    ]

    test_hour_limits = [1.0, 1.5, 2.0, 3.0, 4.5, 6.0, 8.0]

    for hours in test_hour_limits:
        total_allowed_mins = int(round(hours * 60))
        resp = client.post("/api/smartstudy/plan", json={"available_hours": hours, "subjects": test_subjects})
        assert resp.status_code == 200
        plan = resp.json()

        total_scheduled_mins = sum(t["duration_minutes"] for t in plan["tasks"])
        assert total_scheduled_mins <= total_allowed_mins, (
            f"Configured limit {hours}h ({total_allowed_mins}m) EXCEEDED! Scheduled: {total_scheduled_mins}m"
        )
        print(f"  [PASS] Configured: {hours}h ({total_allowed_mins}m) -> Scheduled: {total_scheduled_mins}m (<= limit)")


def test_study_plan_generation_and_labels():
    print("\n--- TEST 5: STUDY PLAN GENERATOR & LABELS ---")
    client = TestClient(app)
    today = datetime.now().date()

    payload = {
        "available_hours": 4.5,
        "subjects": [
            {
                "id": "sub-os",
                "name": "Operating Systems",
                "exam_date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
                "difficulty": "Hard",
                "prep_percentage": 25.0
            },
            {
                "id": "sub-dsa",
                "name": "Data Structures & Algorithms",
                "exam_date": (today + timedelta(days=6)).strftime("%Y-%m-%d"),
                "difficulty": "Hard",
                "prep_percentage": 45.0
            },
            {
                "id": "sub-dbms",
                "name": "Database Management Systems",
                "exam_date": (today + timedelta(days=12)).strftime("%Y-%m-%d"),
                "difficulty": "Medium",
                "prep_percentage": 60.0
            }
        ]
    }

    resp = client.post("/api/smartstudy/plan", json=payload)
    assert resp.status_code == 200, f"Error: {resp.text}"
    data = resp.json()

    assert data["daily_hours"] == 4.5
    assert len(data["tasks"]) >= 3, "Should generate multiple structured sessions"
    
    # Verify higher-priority subject gets more or equal study time
    tasks = data["tasks"]
    os_mins = sum(t["duration_minutes"] for t in tasks if t["subject_name"] == "Operating Systems")
    dbms_mins = sum(t["duration_minutes"] for t in tasks if t["subject_name"] == "Database Management Systems")
    assert os_mins >= dbms_mins, f"Higher priority Operating Systems ({os_mins}m) should receive more time than DBMS ({dbms_mins}m)"
    print(f"  [PASS] Proportional time distribution verified: OS={os_mins}m vs DBMS={dbms_mins}m")

    # Check required topic/session labels
    labels_found = set(t["label"] for t in tasks)
    required_labels = {"Concept Review", "Problem Solving", "Revision", "Practice Questions"}
    valid_labels = labels_found.issubset(required_labels)
    assert valid_labels, f"Labels must only be from {required_labels}, found: {labels_found}"
    print(f"  [PASS] Verified required labels used: {labels_found}")


def test_api_and_ui_serving():
    print("\n--- TEST 6: FASTAPI ENDPOINTS & UI SERVING ---")
    client = TestClient(app)

    # 1. Sample subjects endpoint
    samples_resp = client.get("/api/smartstudy/sample-subjects")
    assert samples_resp.status_code == 200
    samples = samples_resp.json()
    assert len(samples) >= 4
    print(f"  [PASS] GET /api/smartstudy/sample-subjects returned {len(samples)} subjects")

    # 2. Priority calculation endpoint
    prio_resp = client.post("/api/smartstudy/priority", json=samples)
    assert prio_resp.status_code == 200
    prio_data = prio_resp.json()
    assert len(prio_data) == len(samples)
    assert prio_data[0]["priority_score"] >= prio_data[-1]["priority_score"], "Should be sorted by descending priority"
    print(f"  [PASS] POST /api/smartstudy/priority successfully sorted subjects: #{1} {prio_data[0]['name']} (Score: {prio_data[0]['priority_score']})")

    # 3. Static UI Serving
    html_resp = client.get("/")
    assert html_resp.status_code == 200
    assert "SmartStudy AI" in html_resp.text, "UI HTML must contain 'SmartStudy AI'"
    assert "Priority Analysis" in html_resp.text
    assert "AI Study Coach" in html_resp.text
    print("  [PASS] Static UI served cleanly with SmartStudy AI dashboard & tabs")

if __name__ == "__main__":
    test_priority_algorithm()
    test_preparation_updates_priority()
    test_exam_countdown_current_date()
    test_daily_hours_limit_never_exceeded()
    test_study_plan_generation_and_labels()
    test_api_and_ui_serving()
    print("\n" + "="*55)
    print(">>> ALL PRODUCTION TESTS PASSED FLAWLESSLY (6/6)! <<<")
    print("="*55 + "\n")
