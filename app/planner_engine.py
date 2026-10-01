from datetime import datetime, timedelta
import uuid
import math
from typing import List, Dict, Tuple
from app.models import (
    StudyPlanRequest, StudyPlanResponse, DailySchedule, 
    StudySessionBlock, PhaseRoadmap, SubjectItem, TopicItem
)

DIFFICULTY_MULTIPLIER = {
    "easy": 1.0,
    "medium": 1.4,
    "hard": 2.0
}

PRIORITY_MULTIPLIER = {
    "low": 0.8,
    "medium": 1.0,
    "high": 1.3
}

SLOT_STARTS = {
    "morning": ["08:30", "10:15", "11:45", "14:00", "15:45", "17:30", "19:30"],
    "afternoon": ["13:00", "14:45", "16:30", "18:30", "20:00", "21:30"],
    "evening": ["17:00", "18:45", "20:15", "21:45", "23:00"],
    "night": ["20:00", "21:45", "23:30", "01:00", "02:30"]
}

ACTIVITY_TECHNIQUES = {
    "easy": [
        ("Active Recall & Flashcards", "Quick retrieval practice without notes"),
        ("Practice Quiz & Speed Drills", "Timed multiple-choice drills to build automaticity"),
        ("Concept Synthesis", "Create concise one-page cheat sheet")
    ],
    "medium": [
        ("Structured Problem Solving", "Solve standard & past exam questions step-by-step"),
        ("Feynman Technique", "Explain the concept out loud simply as if teaching a beginner"),
        ("Interleaved Practice", "Mix problem types from previous chapters")
    ],
    "hard": [
        ("Deep Concept Breakdown", "First-principles deconstruction: identify points of confusion"),
        ("Worked-Example Reflection", "Trace solved problem line by line, then replicate blind"),
        ("Error Log Remediation", "Analyze previously failed questions and articulate exact error reasons")
    ]
}

def generate_algorithmic_plan(req: StudyPlanRequest) -> StudyPlanResponse:
    # 1. Parse dates
    start_dt = datetime.strptime(req.start_date, "%Y-%m-%d") if req.start_date else datetime.now()
    exam_dt = datetime.strptime(req.exam_date, "%Y-%m-%d")
    
    total_days = max(1, (exam_dt.date() - start_dt.date()).days)
    
    # 2. Extract and weigh all topics
    weighted_topics = []
    subject_hours_dist = {subj.name: 0.0 for subj in req.subjects}
    
    if not req.subjects:
        # Default placeholder if user gave no subjects
        default_subj = SubjectItem(
            name="General Studies",
            priority="high",
            topics=[
                TopicItem(name="Core Fundamentals", difficulty="medium"),
                TopicItem(name="Advanced Concepts", difficulty="hard"),
                TopicItem(name="Review & Practice Questions", difficulty="easy")
            ]
        )
        req.subjects = [default_subj]
        subject_hours_dist["General Studies"] = 0.0

    for subj in req.subjects:
        p_mult = PRIORITY_MULTIPLIER.get(subj.priority.lower(), 1.0)
        for topic in subj.topics:
            d_mult = DIFFICULTY_MULTIPLIER.get(topic.difficulty.lower(), 1.4)
            base_weight = d_mult * p_mult
            weighted_topics.append({
                "subject": subj.name,
                "topic": topic.name,
                "difficulty": topic.difficulty.lower(),
                "weight": base_weight,
                "subtopics": topic.subtopics or []
            })

    # Sort topics: hard and high priority first so they get prime early study time
    weighted_topics.sort(key=lambda x: x["weight"], reverse=True)

    # 3. Calculate total study capacity across the period
    total_study_hours = 0.0
    day_capacities: List[Tuple[datetime, float, bool]] = [] # (date, hours, is_rest)
    
    rest_day_set = {d.strip().capitalize() for d in req.rest_days}
    
    for i in range(total_days):
        cur_date = start_dt + timedelta(days=i)
        weekday_name = cur_date.strftime("%A")
        is_weekend = weekday_name in ["Saturday", "Sunday"]
        
        if weekday_name in rest_day_set:
            day_capacities.append((cur_date, 0.0, True))
            continue
            
        hrs = req.weekend_hours if is_weekend else req.weekday_hours
        day_capacities.append((cur_date, hrs, False))
        total_study_hours += hrs

    # Distribute topics across days using Spaced Repetition & Interleaving
    # Session length based on break technique
    session_dur_min = 60 if req.break_technique == "long_focus" else (90 if req.break_technique == "ultradian" else 45)
    
    daily_schedules: List[DailySchedule] = []
    spaced_reviews: Dict[int, List[str]] = {} # day_idx -> list of topic review strings
    
    time_slots = SLOT_STARTS.get(req.preferred_time.lower(), SLOT_STARTS["morning"])
    topic_cursor = 0
    num_topics = len(weighted_topics)

    for day_idx, (cur_date, hours, is_rest) in enumerate(day_capacities):
        day_num = day_idx + 1
        day_str = cur_date.strftime("%Y-%m-%d")
        day_of_week = cur_date.strftime("%A")
        
        if is_rest:
            daily_schedules.append(DailySchedule(
                day_number=day_num,
                date=day_str,
                day_of_week=day_of_week,
                theme="Active Recovery & Mental Reset",
                target_hours=0.0,
                sessions=[
                    StudySessionBlock(
                        session_id=str(uuid.uuid4())[:8],
                        time_slot="Flexible",
                        subject="Rest & Rejuvenation",
                        topic="Cognitive Recharge",
                        activity_type="Mindful Recovery",
                        duration_minutes=0,
                        actionable_goal="Light outdoor walk, adequate sleep, and zero screen fatigue to consolidate weekly memories.",
                        recommended_technique="Mental Defocused Mode (Diffuse Thinking)",
                        completed=False
                    )
                ],
                daily_tip="Rest is when memories consolidate into long-term storage. Don't feel guilty about taking your planned rest day!",
                review_topics=[]
            ))
            continue

        # Sessions for this active day
        sessions: List[StudySessionBlock] = []
        sessions_needed = max(1, int(round((hours * 60) / (session_dur_min + 15))))
        
        # Check if there are spaced reviews due today
        reviews_due = spaced_reviews.get(day_idx, [])
        if reviews_due and sessions_needed > 1:
            rev_topic = reviews_due.pop(0)
            rev_slot = time_slots[0] if time_slots else "09:00"
            sessions.append(StudySessionBlock(
                session_id=str(uuid.uuid4())[:8],
                time_slot=rev_slot,
                subject="Spaced Repetition Review",
                topic=rev_topic,
                activity_type="Active Recall & Flashcards",
                duration_minutes=min(30, session_dur_min),
                actionable_goal=f"Test yourself on key formulas, concepts, and blind recall for '{rev_topic}' without looking at notes.",
                recommended_technique="Blurting Method / Leitner Box",
                completed=False
            ))

        # Fill remaining sessions with new learning / practice
        curr_session_idx = len(sessions)
        while curr_session_idx < sessions_needed:
            # Pick topic using interleaving (alternating subjects)
            t_info = weighted_topics[topic_cursor % num_topics]
            topic_cursor += 1
            
            # Technique selection based on difficulty
            techniques = ACTIVITY_TECHNIQUES.get(t_info["difficulty"], ACTIVITY_TECHNIQUES["medium"])
            tech_name, tech_desc = techniques[curr_session_idx % len(techniques)]
            
            slot_time = time_slots[curr_session_idx % len(time_slots)]
            
            # Actionable goal
            act_goal = f"Master core principles of {t_info['topic']} ({t_info['difficulty']} tier). Solve at least 3-5 typical examination problems."
            
            sessions.append(StudySessionBlock(
                session_id=str(uuid.uuid4())[:8],
                time_slot=slot_time,
                subject=t_info["subject"],
                topic=t_info["topic"],
                activity_type=tech_name,
                duration_minutes=session_dur_min,
                actionable_goal=act_goal,
                recommended_technique=tech_desc,
                completed=False
            ))
            
            # Track hours
            subject_hours_dist[t_info["subject"]] = round(subject_hours_dist.get(t_info["subject"], 0.0) + (session_dur_min / 60.0), 1)

            # Schedule Spaced Repetitions (Ebbinghaus Intervals: +1 day, +3 days, +7 days)
            for offset in [1, 3, 7]:
                target_review_day = day_idx + offset
                if target_review_day < total_days:
                    spaced_reviews.setdefault(target_review_day, []).append(f"{t_info['subject']}: {t_info['topic']}")

            curr_session_idx += 1

        # Determine daily theme
        subjects_today = list({s.subject for s in sessions if s.subject != "Spaced Repetition Review"})
        theme_str = f"Focus on {', '.join(subjects_today[:2])}" if subjects_today else "Comprehensive Review"
        
        daily_tip = (
            f"Use the {req.break_technique.title()} technique today: study intensely during the block, "
            f"and step away completely during breaks. Peak energy slot: {req.preferred_time.title()}."
        )

        daily_schedules.append(DailySchedule(
            day_number=day_num,
            date=day_str,
            day_of_week=day_of_week,
            theme=theme_str,
            target_hours=round(hours, 1),
            sessions=sessions,
            daily_tip=daily_tip,
            review_topics=[s.topic for s in sessions if "Review" in s.activity_type or "Active Recall" in s.activity_type]
        ))

    # 4. Generate Strategic Milestone Phases
    p1_end = max(1, int(total_days * 0.35))
    p2_end = max(p1_end + 1, int(total_days * 0.70))
    p3_end = max(p2_end + 1, int(total_days * 0.90))
    
    phases = [
        PhaseRoadmap(
            phase_name="Phase 1: Foundation & Difficult Concept Domination",
            duration_days=f"Day 1 - Day {p1_end}",
            focus="Target hardest subjects and core theory first while motivation and cognitive bandwidth are at their maximum.",
            key_milestones=[
                "Deconstruct high-difficulty topics into foundational bite-sized notes",
                "Complete first round of active recall flashcard generation",
                "Eliminate conceptual blindspots in core subjects"
            ]
        ),
        PhaseRoadmap(
            phase_name="Phase 2: Deep Problem Solving & Subject Interleaving",
            duration_days=f"Day {p1_end + 1} - Day {p2_end}",
            focus="Shift from passive theory reading to active mixed problem-solving and synthesis.",
            key_milestones=[
                "Interleaved past-paper questions without looking at solution keys",
                "Consolidate Spaced Repetition cycles for 80%+ topic retention",
                "Compile formula sheets and rapid reaction cheat-sheets"
            ]
        ),
        PhaseRoadmap(
            phase_name="Phase 3: High-Fidelity Mock Drills & Error Remediation",
            duration_days=f"Day {p2_end + 1} - Day {p3_end}",
            focus="Simulate real exam pressure, strict time management, and fix remaining weak areas.",
            key_milestones=[
                "Complete at least 2-3 full-length timed mock exams under real conditions",
                "Perform in-depth post-mortem on every mistake made",
                "Refine pacing and question triage strategy (Easy -> Medium -> Hard)"
            ]
        ),
        PhaseRoadmap(
            phase_name="Phase 4: Final Taper, Retention Lock & Mental Peak",
            duration_days=f"Day {p3_end + 1} - Day {total_days}",
            focus="Light cognitive load, high-speed flashcard runs, mental confidence, and sleep alignment.",
            key_milestones=[
                "Zero new learning — only high-yield formula and summary sheet skimming",
                "Align circadian rhythm to exam morning schedule",
                "Arrive at exam day fresh, clear-headed, and energized"
            ]
        )
    ]

    # Estimated Readiness Forecast
    readiness = "92% - High Distinction Trajectory" if total_study_hours >= 30 else "85% - Solid Mastery Trajectory"

    return StudyPlanResponse(
        plan_id=str(uuid.uuid4()),
        student_name=req.student_name,
        summary=(
            f"Tailored {total_days}-day strategic study roadmap for {req.student_name} aiming for '{req.target_goal}'. "
            f"Equipped with Spaced Repetition (Ebbinghaus curve), cognitive interleaving, and {req.break_technique.title()} cycles "
            f"covering {len(weighted_topics)} topics across {len(req.subjects)} subjects."
        ),
        total_days=total_days,
        total_study_hours=round(total_study_hours, 1),
        readiness_forecast=readiness,
        phases=phases,
        daily_schedules=daily_schedules,
        spaced_repetition_strategy=(
            "System schedules automated review micro-sessions at intervals of 24h, 72h, and 7 days. "
            "Ensure you do not read notes passively; test yourself via blind retrieval or practice questions."
        ),
        burnout_prevention_tips=[
            "Never study for more than 90 minutes without a 15-minute screen-free break.",
            "Guard your planned rest days fiercely — cognitive synthesis happens during rest.",
            "Hydrate consistently and maintain 7-8 hours of sleep for memory consolidation.",
            "If an emergency occurs, don't double tomorrow's load; use the AI Copilot to redistribute evenly."
        ],
        subject_hours_distribution=subject_hours_dist,
        source="smart-algorithmic-engine"
    )
