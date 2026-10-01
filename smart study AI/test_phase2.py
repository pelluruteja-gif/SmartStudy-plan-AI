from datetime import datetime, date, timedelta
from app.models import SmartSubject, SmartSubjectAnalysis
from app.priority_engine import (
    calculate_days_remaining,
    calculate_urgency_score,
    calculate_difficulty_score,
    calculate_preparation_gap,
    calculate_priority_score,
    get_priority_level,
    analyze_smart_subject,
    rank_subjects_by_priority
)
from fastapi.testclient import TestClient
from app.main import app

def test_phase2_priority_engine():
    print("=" * 60)
    print("TESTING PHASE 2: INTELLIGENT EXAM PRIORITY ENGINE")
    print("=" * 60)
    
    today = date(2026, 10, 1)

    # 1. Test Days Remaining Calculation
    print("\n1. Testing Days Remaining Calculation...")
    assert calculate_days_remaining("2026-10-01", today) == 0, "Today should be 0 days"
    assert calculate_days_remaining("2026-10-02", today) == 1, "Tomorrow should be 1 day"
    assert calculate_days_remaining("2026-10-08", today) == 7, "+7 days should be 7"
    assert calculate_days_remaining("2026-10-31", today) == 30, "+30 days should be 30"
    print("   [PASS] Days remaining calculated correctly.")

    # 2. Test Urgency Score Monotonicity (Increases as exam gets closer)
    print("\n2. Testing Urgency Score Curve...")
    days_to_test = [60, 45, 30, 20, 14, 10, 7, 5, 3, 2, 1, 0]
    urgency_scores = [calculate_urgency_score(d) for d in days_to_test]
    
    print(f"   Days:    {days_to_test}")
    print(f"   Scores:  {urgency_scores}")

    for i in range(len(urgency_scores) - 1):
        d_curr, d_next = days_to_test[i], days_to_test[i+1]
        s_curr, s_next = urgency_scores[i], urgency_scores[i+1]
        assert s_next >= s_curr, f"Urgency failed to increase as exam gets closer: day {d_next} score {s_next} < day {d_curr} score {s_curr}"
        if d_next > 1 and d_curr > d_next:
            assert s_next > s_curr, f"Urgency should strictly increase from day {d_curr} ({s_curr}) to day {d_next} ({s_next})"

    print("   [PASS] Urgency score strictly increases as exam approaches.")

    # 3. Test Difficulty Scores
    print("\n3. Testing Difficulty Scores (Easy=20, Medium=50, Hard=80)...")
    assert calculate_difficulty_score("Easy") == 20.0, "Easy should be 20.0"
    assert calculate_difficulty_score("easy") == 20.0, "easy should be 20.0"
    assert calculate_difficulty_score("Medium") == 50.0, "Medium should be 50.0"
    assert calculate_difficulty_score("medium") == 50.0, "medium should be 50.0"
    assert calculate_difficulty_score("Hard") == 80.0, "Hard should be 80.0"
    assert calculate_difficulty_score("hard") == 80.0, "hard should be 80.0"
    print("   [PASS] Difficulty scores correspond accurately to 20, 50, and 80.")

    # 4. Test Preparation Gap (100 - preparation percentage)
    print("\n4. Testing Preparation Gap (100 - prep %)...")
    assert calculate_preparation_gap(0.0) == 100.0
    assert calculate_preparation_gap(25.0) == 75.0
    assert calculate_preparation_gap(50.0) == 50.0
    assert calculate_preparation_gap(80.0) == 20.0
    assert calculate_preparation_gap(100.0) == 0.0
    print("   [PASS] Preparation gap = 100 - prep% verified.")

    # 5. Test Priority Formula: (urgency * 0.40) + (difficulty * 0.25) + (prepGap * 0.35)
    print("\n5. Testing Final Priority Score Calculation...")
    # Example A: urgency = 96.0, difficulty = 80.0 (Hard), prepGap = 75.0 (25% prep)
    # Expected: (96.0 * 0.40) + (80.0 * 0.25) + (75.0 * 0.35)
    #           = 38.4 + 20.0 + 26.25 = 84.65 -> 84.7
    score_a = calculate_priority_score(96.0, 80.0, 75.0)
    assert score_a == 84.6 or score_a == 84.7, f"Expected ~84.7, got {score_a}"
    assert get_priority_level(score_a) == "High", f"Expected High, got {get_priority_level(score_a)}"

    # Example B: urgency = 61.0, difficulty = 50.0 (Medium), prepGap = 50.0 (50% prep)
    # Expected: (61.0 * 0.40) + (50.0 * 0.25) + (50.0 * 0.35)
    #           = 24.4 + 12.5 + 17.5 = 54.4
    score_b = calculate_priority_score(61.0, 50.0, 50.0)
    assert score_b == 54.4, f"Expected 54.4, got {score_b}"
    assert get_priority_level(score_b) == "Medium", f"Expected Medium, got {get_priority_level(score_b)}"

    # Example C: urgency = 16.2, difficulty = 20.0 (Easy), prepGap = 20.0 (80% prep)
    # Expected: (16.2 * 0.40) + (20.0 * 0.25) + (20.0 * 0.35)
    #           = 6.48 + 5.0 + 7.0 = 18.48 -> 18.5
    score_c = calculate_priority_score(16.2, 20.0, 20.0)
    assert score_c == 18.5, f"Expected 18.5, got {score_c}"
    assert get_priority_level(score_c) == "Low", f"Expected Low, got {get_priority_level(score_c)}"

    print("   [PASS] Priority score mathematical formulation and rounding verified.")

    # 6. Test Priority Levels Classification
    print("\n6. Testing Priority Level Classification (High >= 70, Medium 45-69, Low < 45)...")
    assert get_priority_level(85.0) == "High"
    assert get_priority_level(70.0) == "High"
    assert get_priority_level(69.9) == "Medium"
    assert get_priority_level(50.0) == "Medium"
    assert get_priority_level(45.0) == "Medium"
    assert get_priority_level(44.9) == "Low"
    assert get_priority_level(20.0) == "Low"
    print("   [PASS] Priority level thresholds (>=70: High, 45-69: Medium, <45: Low) verified.")

    # 7. Test Ranking of Sample Subjects (Highest Priority First)
    print("\n7. Testing Ranking with Sample Subjects...")
    sample_subjects = [
        SmartSubject(id="sub-1", name="Operating Systems", exam_date="2026-10-03", difficulty="Hard", prep_percentage=25.0), # in 2 days, Hard, 25% prep
        SmartSubject(id="sub-2", name="Software Engineering & Ethics", exam_date="2026-10-21", difficulty="Easy", prep_percentage=80.0), # in 20 days, Easy, 80% prep
        SmartSubject(id="sub-3", name="Database Systems", exam_date="2026-10-08", difficulty="Medium", prep_percentage=50.0), # in 7 days, Medium, 50% prep
    ]

    ranked = rank_subjects_by_priority(sample_subjects, today)
    print(f"   Rank 1: {ranked[0].name} - Score: {ranked[0].priority_score} ({ranked[0].priority_level})")
    print(f"   Rank 2: {ranked[1].name} - Score: {ranked[1].priority_score} ({ranked[1].priority_level})")
    print(f"   Rank 3: {ranked[2].name} - Score: {ranked[2].priority_score} ({ranked[2].priority_level})")

    assert ranked[0].name == "Operating Systems", "Operating Systems should be Rank 1"
    assert ranked[0].priority_level == "High", "Operating Systems should be High priority"
    assert ranked[1].name == "Database Systems", "Database Systems should be Rank 2"
    assert ranked[1].priority_level == "Medium", "Database Systems should be Medium priority"
    assert ranked[2].name == "Software Engineering & Ethics", "Software Engineering should be Rank 3"
    assert ranked[2].priority_level == "Low", "Software Engineering should be Low priority"
    
    assert ranked[0].priority_score >= ranked[1].priority_score >= ranked[2].priority_score, "Subjects must be sorted highest priority first"
    print("   [PASS] Subjects correctly ranked by highest priority first.")

    # 8. Test HTTP API Endpoints
    print("\n8. Testing HTTP API Endpoints via TestClient...")
    client = TestClient(app)
    
    # Endpoint A: /api/calculate-priority
    resp = client.post("/api/calculate-priority", json=[s.model_dump() for s in sample_subjects])
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    api_ranked = resp.json()
    assert len(api_ranked) == 3
    assert api_ranked[0]["name"] == "Operating Systems"
    assert "urgency_score" in api_ranked[0]
    assert "difficulty_score" in api_ranked[0]
    assert "prep_gap" in api_ranked[0]
    assert "priority_score" in api_ranked[0]
    assert "priority_level" in api_ranked[0]
    print("   [PASS] POST /api/calculate-priority returned valid ranked analysis.")

    # Endpoint B: /api/smartstudy/priority
    resp2 = client.post("/api/smartstudy/priority", json=[s.model_dump() for s in sample_subjects])
    assert resp2.status_code == 200
    print("   [PASS] POST /api/smartstudy/priority returned 200 OK.")

    # Endpoint C: /api/smartstudy/sample-subjects
    resp3 = client.get("/api/smartstudy/sample-subjects")
    assert resp3.status_code == 200
    assert len(resp3.json()) >= 4
    print("   [PASS] GET /api/smartstudy/sample-subjects returned sample subjects.")

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL PHASE 2 ENGINE REQUIREMENTS VERIFIED!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    test_phase2_priority_engine()
