from datetime import datetime, date
from typing import List, Optional
from app.models import SmartSubject, SmartSubjectAnalysis

def calculate_days_remaining(exam_date_str: str, reference_date: Optional[date] = None) -> int:
    """Calculates calendar days remaining between reference_date (defaults to today) and exam_date."""
    ref = reference_date or datetime.now().date()
    try:
        exam_d = datetime.strptime(exam_date_str.strip(), "%Y-%m-%d").date()
        return (exam_d - ref).days
    except Exception:
        return 7

def calculate_urgency_score(days: int) -> float:
    """
    Calculates the Exam Urgency score from 5.0 to 100.0.
    The score strictly increases as the exam date draws closer (days remaining decreases).
    """
    if days <= 0:
        return 100.0
    elif days == 1:
        return 100.0
    elif days <= 7:
        # Day 2 -> 96.0 down to Day 7 -> 76.0 (drops 4.0 points per day)
        return round(104.0 - (days * 4.0), 1)
    elif days <= 30:
        # Day 8 -> 73.0 down to Day 30 -> 29.0 (drops 2.0 points per day)
        return round(89.0 - (days * 2.0), 1)
    else:
        # Days 31+ smoothly tapers towards minimum floor 5.0
        return max(5.0, round(100.0 / (1.0 + (days / 6.0)), 1))

def calculate_difficulty_score(difficulty: str) -> float:
    """
    Difficulty score mappings:
    Easy = 20
    Medium = 50
    Hard = 80
    """
    d = (difficulty or "").strip().lower()
    if d == "easy":
        return 20.0
    elif d == "medium":
        return 50.0
    elif d == "hard":
        return 80.0
    return 50.0

def calculate_preparation_gap(prep_percentage: float) -> float:
    """
    Preparation gap formula:
    100 - preparation percentage (clamped to [0.0, 100.0])
    """
    prep = max(0.0, min(100.0, float(prep_percentage)))
    return round(100.0 - prep, 1)

def calculate_priority_score(urgency: float, difficulty: float, prep_gap: float) -> float:
    """
    Final Priority score formula:
    priority = (urgency × 0.40) + (difficulty × 0.25) + (preparationGap × 0.35)
    """
    raw = (urgency * 0.40) + (difficulty * 0.25) + (prep_gap * 0.35)
    return round(raw, 1)

def get_priority_level(score: float) -> str:
    """
    Priority levels:
    High = 70 or above
    Medium = 45–69
    Low = below 45
    """
    if score >= 70.0:
        return "High"
    elif score >= 45.0:
        return "Medium"
    else:
        return "Low"

def analyze_smart_subject(sub: SmartSubject, reference_date: Optional[date] = None) -> SmartSubjectAnalysis:
    """Computes all 5 exam priority metrics for a given subject."""
    days_rem = calculate_days_remaining(sub.exam_date, reference_date)
    urgency = calculate_urgency_score(days_rem)
    diff_score = calculate_difficulty_score(sub.difficulty)
    prep_gap = calculate_preparation_gap(sub.prep_percentage)
    
    priority = calculate_priority_score(urgency, diff_score, prep_gap)
    level = get_priority_level(priority)
    
    return SmartSubjectAnalysis(
        id=sub.id or f"sub_{int(datetime.now().timestamp()*1000)}",
        name=sub.name,
        exam_date=sub.exam_date,
        days_remaining=days_rem,
        urgency_score=urgency,
        difficulty_score=diff_score,
        prep_percentage=round(float(sub.prep_percentage), 1),
        prep_gap=prep_gap,
        priority_score=priority,
        priority_level=level
    )

def rank_subjects_by_priority(subjects: List[SmartSubject], reference_date: Optional[date] = None) -> List[SmartSubjectAnalysis]:
    """Calculates priorities and sorts subjects by highest priority first."""
    analyzed = [analyze_smart_subject(s, reference_date) for s in subjects]
    analyzed.sort(key=lambda x: x.priority_score, reverse=True)
    return analyzed
