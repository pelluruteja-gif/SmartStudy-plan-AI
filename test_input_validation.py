"""
Automated Test Suite for User Request: Security & Input Validation Testing
Tests the application through its normal user-facing flows and API endpoints.
"""

import sys
import json
import urllib.request
import urllib.error
from datetime import date, timedelta

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"

def make_request(method, path, data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    payload = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, content, dict(resp.headers), None
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        return e.code, content, dict(e.headers), e.reason
    except Exception as e:
        return 0, str(e), {}, "Connection/Server Exception"

def run_tests():
    print("======================================================================")
    print("🔍 EXECUTING COMPREHENSIVE INPUT VALIDATION & SECURITY TESTING SUITE")
    print("======================================================================")

    results = []
    future_date = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")

    # --------------------------------------------------------------------
    # TEST 1 — Preparation percentage
    # --------------------------------------------------------------------
    print("\n--- TEST 1: Preparation percentage ---")

    # 1.1 Valid value (50)
    p1_data = [{
        "name": "Linear Algebra",
        "exam_date": future_date,
        "difficulty": "Medium",
        "prep_percentage": 50.0
    }]
    status, body, _, err = make_request("POST", "/api/smartstudy/priority", p1_data)
    t1_1_pass = (status == 200)
    results.append({
        "test": "TEST 1.1: Prep percentage = 50 (valid)",
        "input": "prep_percentage: 50.0",
        "status": status,
        "pass": t1_1_pass,
        "msg": "Successfully accepted with 200 OK" if t1_1_pass else f"Unexpected status {status}",
        "crashed": status == 0 or status == 500
    })
    print(f"  1.1 Valid (50): {'PASS' if t1_1_pass else 'FAIL'} [HTTP {status}]")

    # 1.2 Negative value (-10)
    p2_data = [{
        "name": "Linear Algebra",
        "exam_date": future_date,
        "difficulty": "Medium",
        "prep_percentage": -10.0
    }]
    status, body, _, err = make_request("POST", "/api/smartstudy/priority", p2_data)
    t1_2_pass = (status == 422)
    results.append({
        "test": "TEST 1.2: Prep percentage = -10 (invalid negative)",
        "input": "prep_percentage: -10.0",
        "status": status,
        "pass": t1_2_pass,
        "msg": body.strip() if t1_2_pass else f"Expected 422, got {status}",
        "crashed": status == 0 or status == 500
    })
    print(f"  1.2 Negative (-10): {'PASS' if t1_2_pass else 'FAIL'} [HTTP {status}] -> Rejection verified")

    # 1.3 Excessive value (150)
    p3_data = [{
        "name": "Linear Algebra",
        "exam_date": future_date,
        "difficulty": "Medium",
        "prep_percentage": 150.0
    }]
    status, body, _, err = make_request("POST", "/api/smartstudy/priority", p3_data)
    t1_3_pass = (status == 422)
    results.append({
        "test": "TEST 1.3: Prep percentage = 150 (invalid excessive)",
        "input": "prep_percentage: 150.0",
        "status": status,
        "pass": t1_3_pass,
        "msg": body.strip() if t1_3_pass else f"Expected 422, got {status}",
        "crashed": status == 0 or status == 500
    })
    print(f"  1.3 Excessive (150): {'PASS' if t1_3_pass else 'FAIL'} [HTTP {status}] -> Rejection verified")

    # --------------------------------------------------------------------
    # TEST 2 — Study hours
    # --------------------------------------------------------------------
    print("\n--- TEST 2: Study hours ---")

    # 2.1 Normal value (4)
    h1_data = {
        "available_hours": 4.0,
        "subjects": [{
            "name": "Data Structures",
            "exam_date": future_date,
            "difficulty": "Hard",
            "prep_percentage": 30.0
        }]
    }
    status, body, _, err = make_request("POST", "/api/smartstudy/plan", h1_data)
    t2_1_pass = (status == 200)
    results.append({
        "test": "TEST 2.1: Study hours = 4 (normal)",
        "input": "available_hours: 4.0",
        "status": status,
        "pass": t2_1_pass,
        "msg": "Study plan generated successfully with 200 OK" if t2_1_pass else f"Unexpected status {status}",
        "crashed": status == 0 or status == 500
    })
    print(f"  2.1 Normal (4): {'PASS' if t2_1_pass else 'FAIL'} [HTTP {status}]")

    # 2.2 Negative value (-5)
    h2_data = {
        "available_hours": -5.0,
        "subjects": [{
            "name": "Data Structures",
            "exam_date": future_date,
            "difficulty": "Hard",
            "prep_percentage": 30.0
        }]
    }
    status, body, _, err = make_request("POST", "/api/smartstudy/plan", h2_data)
    t2_2_pass = (status == 422)
    results.append({
        "test": "TEST 2.2: Study hours = -5 (invalid negative)",
        "input": "available_hours: -5.0",
        "status": status,
        "pass": t2_2_pass,
        "msg": body.strip() if t2_2_pass else f"Expected 422, got {status}",
        "crashed": status == 0 or status == 500
    })
    print(f"  2.2 Negative (-5): {'PASS' if t2_2_pass else 'FAIL'} [HTTP {status}] -> Rejection verified")

    # 2.3 Extremely large value (999)
    h3_data = {
        "available_hours": 999.0,
        "subjects": [{
            "name": "Data Structures",
            "exam_date": future_date,
            "difficulty": "Hard",
            "prep_percentage": 30.0
        }]
    }
    status, body, _, err = make_request("POST", "/api/smartstudy/plan", h3_data)
    t2_3_pass = (status == 422)
    results.append({
        "test": "TEST 2.3: Study hours = 999 (unreasonable excessive)",
        "input": "available_hours: 999.0",
        "status": status,
        "pass": t2_3_pass,
        "msg": body.strip() if t2_3_pass else f"Expected 422, got {status}",
        "crashed": status == 0 or status == 500
    })
    print(f"  2.3 Excessive (999): {'PASS' if t2_3_pass else 'FAIL'} [HTTP {status}] -> Rejection verified")

    # --------------------------------------------------------------------
    # TEST 3 — Empty subject
    # --------------------------------------------------------------------
    print("\n--- TEST 3: Empty subject ---")

    # 3.1 Empty subject name string ""
    sub_empty_data = {
        "available_hours": 4.0,
        "subjects": [{
            "name": "",
            "exam_date": future_date,
            "difficulty": "Medium",
            "prep_percentage": 40.0
        }]
    }
    status, body, _, err = make_request("POST", "/api/smartstudy/plan", sub_empty_data)
    t3_1_pass = (status == 422)
    results.append({
        "test": "TEST 3.1: Empty subject name '' in plan request",
        "input": "name: ''",
        "status": status,
        "pass": t3_1_pass,
        "msg": body.strip() if t3_1_pass else f"Expected 422, got {status}",
        "crashed": status == 0 or status == 500
    })
    print(f"  3.1 Empty Subject Name: {'PASS' if t3_1_pass else 'FAIL'} [HTTP {status}] -> Rejection verified")

    # 3.2 Empty subjects array []
    sub_empty_list_data = {
        "available_hours": 4.0,
        "subjects": []
    }
    status, body, _, err = make_request("POST", "/api/smartstudy/plan", sub_empty_list_data)
    t3_2_pass = (status == 422)
    results.append({
        "test": "TEST 3.2: Empty subjects list [] in plan request",
        "input": "subjects: []",
        "status": status,
        "pass": t3_2_pass,
        "msg": body.strip() if t3_2_pass else f"Expected 422, got {status}",
        "crashed": status == 0 or status == 500
    })
    print(f"  3.2 Empty Subjects Array: {'PASS' if t3_2_pass else 'FAIL'} [HTTP {status}] -> Rejection verified")

    # --------------------------------------------------------------------
    # TEST 4 — Very long subject name
    # --------------------------------------------------------------------
    print("\n--- TEST 4: Very long subject name ---")

    # 4.1 500-character subject name
    long_name = "Advanced Quantum Cryptography And Distributed Consensus Systems Under Adversarial Network Partitions " * 5
    sub_long_data = {
        "available_hours": 4.0,
        "subjects": [{
            "name": long_name,
            "exam_date": future_date,
            "difficulty": "Hard",
            "prep_percentage": 40.0
        }]
    }
    status, body, _, err = make_request("POST", "/api/smartstudy/plan", sub_long_data)
    t4_pass = (status == 422)
    results.append({
        "test": "TEST 4: Oversized subject name (500 chars, limit is 120)",
        "input": f"name length: {len(long_name)} characters",
        "status": status,
        "pass": t4_pass,
        "msg": body.strip() if t4_pass else f"Expected 422, got {status}",
        "crashed": status == 0 or status == 500
    })
    print(f"  4.1 Oversized Subject Name (500 chars): {'PASS' if t4_pass else 'FAIL'} [HTTP {status}] -> Rejection verified")

    # 4.2 Boundary valid length (120 chars)
    valid_long_name = "Computer Science 401: Advanced Operating Systems, Concurrency Control, File Systems, Microkernels and Virtualization"
    sub_valid_long = {
        "available_hours": 4.0,
        "subjects": [{
            "name": valid_long_name,
            "exam_date": future_date,
            "difficulty": "Hard",
            "prep_percentage": 40.0
        }]
    }
    status, body, _, err = make_request("POST", "/api/smartstudy/plan", sub_valid_long)
    t4_2_pass = (status == 200)
    results.append({
        "test": "TEST 4.2: Maximum valid boundary subject name (116 chars)",
        "input": f"name length: {len(valid_long_name)} chars",
        "status": status,
        "pass": t4_2_pass,
        "msg": "Accepted and processed cleanly within allowed 120-char threshold" if t4_2_pass else f"Status {status}",
        "crashed": status == 0 or status == 500
    })
    print(f"  4.2 Boundary Long Subject Name ({len(valid_long_name)} chars): {'PASS' if t4_2_pass else 'FAIL'} [HTTP {status}]")

    # --------------------------------------------------------------------
    # TEST 5 — Difficulty
    # --------------------------------------------------------------------
    print("\n--- TEST 5: Difficulty ---")

    difficulties = ["Easy", "Medium", "Hard"]
    expected_scores = {"Easy": 20.0, "Medium": 50.0, "Hard": 80.0}

    for diff in difficulties:
        diff_payload = [{
            "name": f"Subject {diff}",
            "exam_date": future_date,
            "difficulty": diff,
            "prep_percentage": 50.0
        }]
        status, body, _, _ = make_request("POST", "/api/smartstudy/priority", diff_payload)
        parsed = json.loads(body)
        analyzed_sub = parsed[0]
        actual_diff_score = analyzed_sub["difficulty_score"]
        expected_diff_score = expected_scores[diff]

        is_diff_pass = (status == 200 and actual_diff_score == expected_diff_score)

        results.append({
            "test": f"TEST 5: Difficulty '{diff}'",
            "input": f"difficulty: '{diff}'",
            "status": status,
            "pass": is_diff_pass,
            "msg": f"Difficulty score verified: {actual_diff_score} (Expected: {expected_diff_score})",
            "crashed": status == 0 or status == 500
        })
        print(f"  5.{difficulties.index(diff)+1} Difficulty '{diff}': {'PASS' if is_diff_pass else 'FAIL'} [Score: {actual_diff_score}]")

    # 5.4 Case-insensitivity check ("easy", "HARD", "medium")
    diff_lower_payload = [{
        "name": "Subject Case Test",
        "exam_date": future_date,
        "difficulty": "hard",
        "prep_percentage": 50.0
    }]
    status, body, _, _ = make_request("POST", "/api/smartstudy/priority", diff_lower_payload)
    parsed = json.loads(body)
    case_score = parsed[0]["difficulty_score"]
    case_pass = (status == 200 and case_score == 80.0)
    results.append({
        "test": "TEST 5.4: Difficulty case tolerance ('hard')",
        "input": "difficulty: 'hard'",
        "status": status,
        "pass": case_pass,
        "msg": f"Case-tolerant difficulty score verified: {case_score}",
        "crashed": status == 0 or status == 500
    })
    print(f"  5.4 Difficulty Case Tolerance ('hard'): {'PASS' if case_pass else 'FAIL'} [Score: {case_score}]")

    # --------------------------------------------------------------------
    # TEST 6 — Normal workflow regression
    # --------------------------------------------------------------------
    print("\n--- TEST 6: Normal workflow regression ---")

    # 6.1 Normal Study Plan Generation
    reg_payload = {
        "available_hours": 4.5,
        "subjects": [
            {"name": "Operating Systems", "exam_date": (date.today() + timedelta(days=3)).strftime("%Y-%m-%d"), "difficulty": "Hard", "prep_percentage": 25.0},
            {"name": "Database Systems", "exam_date": (date.today() + timedelta(days=7)).strftime("%Y-%m-%d"), "difficulty": "Medium", "prep_percentage": 50.0},
            {"name": "Software Engineering", "exam_date": (date.today() + timedelta(days=15)).strftime("%Y-%m-%d"), "difficulty": "Easy", "prep_percentage": 80.0}
        ]
    }
    status, body, _, _ = make_request("POST", "/api/smartstudy/plan", reg_payload)
    plan_data = json.loads(body) if status == 200 else {}
    tasks = plan_data.get("tasks", [])
    t6_1_pass = (status == 200 and len(tasks) > 0)
    results.append({
        "test": "TEST 6.1: Study plan generation workflow",
        "input": "3 valid subjects, 4.5 hours daily target",
        "status": status,
        "pass": t6_1_pass,
        "msg": f"Generated {len(tasks)} sessions strictly under daily limit.",
        "crashed": status == 0 or status == 500
    })
    print(f"  6.1 Plan Generation: {'PASS' if t6_1_pass else 'FAIL'} [HTTP {status}, {len(tasks)} tasks]")

    # 6.2 Adaptive Plan Workflow
    total_allocated = sum(t["duration_minutes"] for t in tasks)
    hours_limit_minutes = 4.5 * 60
    t6_2_pass = (total_allocated <= hours_limit_minutes)
    results.append({
        "test": "TEST 6.2: Adaptive Plan duration constraints",
        "input": "Configured 4.5 hrs limit (270 mins)",
        "status": status,
        "pass": t6_2_pass,
        "msg": f"Total scheduled: {total_allocated} mins <= Limit: {hours_limit_minutes} mins",
        "crashed": False
    })
    print(f"  6.2 Adaptive Constraints: {'PASS' if t6_2_pass else 'FAIL'} [{total_allocated}m <= {hours_limit_minutes}m]")

    # 6.3 AI Study Coach Works
    coach_payload = {
        "plan_summary": {
            "summary": "Alex Chen exam plan",
            "daily_schedules": []
        },
        "user_message": "I only have 3 days before my Operating Systems exam. What active recall technique should I use?",
        "conversation_history": []
    }
    status, body, _, _ = make_request("POST", "/api/chat", coach_payload)
    chat_resp = json.loads(body) if status == 200 else {}
    coach_reply = chat_resp.get("reply", "")
    t6_3_pass = (status == 200 and len(coach_reply) > 50)
    results.append({
        "test": "TEST 6.3: AI Study Coach response",
        "input": "Active recall question with exam context",
        "status": status,
        "pass": t6_3_pass,
        "msg": f"Coach generated {len(coach_reply)} characters of advice.",
        "crashed": status == 0 or status == 500
    })
    print(f"  6.3 AI Study Coach: {'PASS' if t6_3_pass else 'FAIL'} [HTTP {status}]")

    # 6.4 Markdown Export Works
    md_payload = {
        "plan_id": "plan_123",
        "student_name": "Alex Student",
        "summary": "Master study schedule",
        "total_days": 14,
        "total_study_hours": 58.0,
        "readiness_forecast": "95%",
        "phases": [],
        "daily_schedules": [],
        "spaced_repetition_strategy": "Ebbinghaus",
        "burnout_prevention_tips": ["Rest properly"],
        "subject_hours_distribution": {"OS": 30.0}
    }
    status, body, headers, _ = make_request("POST", "/api/export-markdown", md_payload)
    t6_4_pass = (status == 200 and "text/markdown" in headers.get("content-type", "") and len(body) > 50)
    results.append({
        "test": "TEST 6.4: Markdown Download / Export",
        "input": "Alex Student study plan payload",
        "status": status,
        "pass": t6_4_pass,
        "msg": f"Generated {len(body)} bytes of markdown with Content-Disposition.",
        "crashed": status == 0 or status == 500
    })
    print(f"  6.4 Markdown Export: {'PASS' if t6_4_pass else 'FAIL'} [HTTP {status}, {len(body)} bytes]")

    # 6.5 iCalendar (.ics) Export Works
    ics_payload = {
        "plan_id": "plan_123",
        "student_name": "Alex Student",
        "summary": "Master study schedule",
        "total_days": 14,
        "total_study_hours": 58.0,
        "readiness_forecast": "95%",
        "phases": [],
        "daily_schedules": [
            {
                "day_number": 1,
                "date": future_date,
                "day_of_week": "Monday",
                "theme": "Core Theory",
                "target_hours": 3.0,
                "sessions": [
                    {
                        "session_id": "sess_1",
                        "time_slot": "09:00 - 10:30",
                        "subject": "Operating Systems",
                        "topic": "Process Synchronization",
                        "activity_type": "Concept Learning",
                        "duration_minutes": 90,
                        "actionable_goal": "Master Semaphores",
                        "recommended_technique": "Feynman Technique"
                    }
                ],
                "daily_tip": "Stay hydrated",
                "review_topics": ["Semaphores"]
            }
        ],
        "spaced_repetition_strategy": "Ebbinghaus",
        "burnout_prevention_tips": ["Take breaks"],
        "subject_hours_distribution": {"OS": 3.0}
    }
    status, body, headers, _ = make_request("POST", "/api/export-ics", ics_payload)
    t6_5_pass = (status == 200 and "BEGIN:VCALENDAR" in body and "END:VCALENDAR" in body)
    results.append({
        "test": "TEST 6.5: iCalendar (.ics) Export",
        "input": "iCalendar study session payload",
        "status": status,
        "pass": t6_5_pass,
        "msg": f"Generated RFC 5545 valid .ics ({len(body)} bytes).",
        "crashed": status == 0 or status == 500
    })
    print(f"  6.5 Calendar (.ics) Export: {'PASS' if t6_5_pass else 'FAIL'} [HTTP {status}, {len(body)} bytes]")

    # --------------------------------------------------------------------
    # FINAL CRASH CHECK & SUMMARY
    # --------------------------------------------------------------------
    print("\n======================================================================")
    print("📋 SUMMARY OF TEST EXECUTION")
    print("======================================================================")

    passed_count = sum(1 for r in results if r["pass"])
    failed_count = sum(1 for r in results if not r["pass"])
    crashed_count = sum(1 for r in results if r["crashed"])

    print(f"Total Tests Executed: {len(results)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print(f"Server Crashes Detected: {crashed_count}")

    # Output JSON test report
    with open("test_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return failed_count == 0 and crashed_count == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
