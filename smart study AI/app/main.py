import os
import re
import logging
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from dotenv import load_dotenv

from app.models import (
    StudyPlanRequest, StudyPlanResponse, ChatRequest, ChatResponse,
    SmartSubject, SmartSubjectAnalysis, SmartStudyPlanRequest, SmartStudyPlanResponse, SmartStudyTask
)
from app.gemini_engine import generate_gemini_plan, chat_with_copilot
from app.planner_engine import generate_algorithmic_plan
from app.exporter import generate_ics_calendar, generate_markdown_plan

load_dotenv()
logger = logging.getLogger("smartstudy")

app = FastAPI(
    title="SmartStudy AI - Intelligent Study Planner",
    description="Adaptive exam preparation & priority engine for college students.",
    version="1.0.0"
)

# 1. Defensive HTTP Security Headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# 2. Production-Safe CORS Configuration
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
render_external_url = os.getenv("RENDER_EXTERNAL_URL")

allowed_origins = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

if render_external_url:
    clean_render_url = render_external_url.strip()
    if clean_render_url and clean_render_url not in allowed_origins:
        allowed_origins.append(clean_render_url)

if allowed_origins_env:
    for o in allowed_origins_env.split(","):
        clean_o = o.strip()
        if clean_o and clean_o not in allowed_origins:
            allowed_origins.append(clean_o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.post("/api/generate-plan", response_model=StudyPlanResponse)
async def create_study_plan(request: StudyPlanRequest):
    try:
        # Default start date if not provided
        if not request.start_date:
            request.start_date = datetime.now().strftime("%Y-%m-%d")

        # Validation: exam date must be in future
        start_d = datetime.strptime(request.start_date, "%Y-%m-%d")
        exam_d = datetime.strptime(request.exam_date, "%Y-%m-%d")
        if exam_d <= start_d:
            raise HTTPException(
                status_code=400,
                detail="Exam / Target Date must be after the Start Date."
            )

        # If user explicitly has an API key or env key, use Gemini engine (with fallback), otherwise algorithmic
        plan = generate_gemini_plan(request)
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating plan: {e}", exc_info=True)
        # Always return reliable algorithmic plan on unexpected failure
        return generate_algorithmic_plan(request)

@app.post("/api/chat", response_model=ChatResponse)
async def chat_assistant(request: ChatRequest):
    try:
        return chat_with_copilot(request)
    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        return ChatResponse(
            reply="I ran into a temporary hiccup, but remember: break hard problems down and protect your rest time!",
            suggestions=["How do I catch up if I fell behind?", "Give me active recall tips"]
        )

def sanitize_filename_slug(name: str) -> str:
    """Sanitizes student name to a safe alphanumeric filename slug."""
    clean = re.sub(r'[^a-zA-Z0-9_-]', '', name.replace(' ', '_').strip())
    return clean[:50] or "student"

@app.post("/api/export-ics")
async def export_calendar(plan: StudyPlanResponse):
    try:
        ics_content = generate_ics_calendar(plan)
        safe_slug = sanitize_filename_slug(plan.student_name)
        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={
                "Content-Disposition": f'attachment; filename="study_plan_{safe_slug}.ics"'
            }
        )
    except Exception as e:
        logger.error(f"Failed to export calendar: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export calendar. Please try again.")

@app.post("/api/export-markdown")
async def export_markdown(plan: StudyPlanResponse):
    try:
        md_content = generate_markdown_plan(plan)
        safe_slug = sanitize_filename_slug(plan.student_name)
        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="study_plan_{safe_slug}.md"'
            }
        )
    except Exception as e:
        logger.error(f"Failed to export markdown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export markdown. Please try again.")

@app.get("/api/sample-templates")
async def get_sample_templates():
    today = datetime.now()
    two_weeks_later = (today + timedelta(days=14)).strftime("%Y-%m-%d")
    one_month_later = (today + timedelta(days=30)).strftime("%Y-%m-%d")
    
    return [
        {
            "id": "cs-finals",
            "name": "💻 Computer Science & Software Engineering Finals",
            "description": "Balanced plan covering Data Structures, Operating Systems, and Database Systems with high-intensity coding drills.",
            "data": {
                "student_name": "Alex Chen",
                "academic_level": "Undergraduate",
                "target_goal": "Score 95%+ / Grade A+",
                "exam_date": two_weeks_later,
                "start_date": today.strftime("%Y-%m-%d"),
                "weekday_hours": 4.5,
                "weekend_hours": 6.5,
                "preferred_time": "morning",
                "break_technique": "pomodoro",
                "learning_style": "practice_heavy",
                "rest_days": ["Sunday"],
                "custom_notes": "Struggling with Dynamic Programming and Virtual Memory concepts.",
                "subjects": [
                    {
                        "name": "Data Structures & Algorithms",
                        "priority": "high",
                        "topics": [
                            {"name": "Dynamic Programming & Memoization", "difficulty": "hard"},
                            {"name": "Graph Traversal (Dijkstra, BFS/DFS)", "difficulty": "hard"},
                            {"name": "Trees & Binary Search Trees", "difficulty": "medium"},
                            {"name": "Sorting & Array Manipulations", "difficulty": "easy"}
                        ]
                    },
                    {
                        "name": "Operating Systems",
                        "priority": "high",
                        "topics": [
                            {"name": "Virtual Memory & Paging Algorithms", "difficulty": "hard"},
                            {"name": "Process Synchronization & Semaphores", "difficulty": "medium"},
                            {"name": "CPU Scheduling Algorithms", "difficulty": "easy"}
                        ]
                    },
                    {
                        "name": "Database Management Systems",
                        "priority": "medium",
                        "topics": [
                            {"name": "SQL Queries & Indexing Optimizations", "difficulty": "medium"},
                            {"name": "ACID Properties & Transactions", "difficulty": "medium"},
                            {"name": "Relational Normalization (1NF to BCNF)", "difficulty": "easy"}
                        ]
                    }
                ]
            }
        },
        {
            "id": "medical-prep",
            "name": "🩺 Pre-Med / Biology & Organic Chemistry Mastery",
            "description": "High active recall focus for Anatomy, Organic Synthesis, and Cell Physiology with daily spaced repetition.",
            "data": {
                "student_name": "Maya Patel",
                "academic_level": "Competitive Exam / Pre-Med",
                "target_goal": "Score 99th Percentile",
                "exam_date": one_month_later,
                "start_date": today.strftime("%Y-%m-%d"),
                "weekday_hours": 5.0,
                "weekend_hours": 7.5,
                "preferred_time": "morning",
                "break_technique": "long_focus",
                "learning_style": "active_recall",
                "rest_days": ["Saturday"],
                "custom_notes": "Need to memorize organic reaction mechanisms and metabolic pathways.",
                "subjects": [
                    {
                        "name": "Organic Chemistry",
                        "priority": "high",
                        "topics": [
                            {"name": "Electrophilic Addition & Substitution", "difficulty": "hard"},
                            {"name": "Stereochemistry & Chirality", "difficulty": "medium"},
                            {"name": "Carbonyl Reactions & Aldol Condensations", "difficulty": "hard"}
                        ]
                    },
                    {
                        "name": "Human Physiology",
                        "priority": "high",
                        "topics": [
                            {"name": "Renal System & Countercurrent Multiplier", "difficulty": "hard"},
                            {"name": "Cardiovascular Pressure-Volume Loops", "difficulty": "medium"},
                            {"name": "Endocrine Feedback Hormones", "difficulty": "easy"}
                        ]
                    },
                    {
                        "name": "Biochemistry",
                        "priority": "medium",
                        "topics": [
                            {"name": "Krebs Cycle & Oxidative Phosphorylation", "difficulty": "medium"},
                            {"name": "Enzyme Kinetics (Michaelis-Menten)", "difficulty": "hard"},
                            {"name": "Amino Acid Structures & pKa Values", "difficulty": "easy"}
                        ]
                    }
                ]
            }
        },
        {
            "id": "high-school-stem",
            "name": "🚀 High School STEM / AP Calculus & Physics",
            "description": "Tailored for high school students preparing for AP / Board exams in Calculus, Mechanics, and Chemistry.",
            "data": {
                "student_name": "Ethan Wright",
                "academic_level": "High School",
                "target_goal": "AP Score 5 / Top Rank",
                "exam_date": two_weeks_later,
                "start_date": today.strftime("%Y-%m-%d"),
                "weekday_hours": 3.0,
                "weekend_hours": 5.0,
                "preferred_time": "evening",
                "break_technique": "pomodoro",
                "learning_style": "visual",
                "rest_days": ["Sunday"],
                "custom_notes": "Focus on calculus word problems and rotational motion in physics.",
                "subjects": [
                    {
                        "name": "AP Calculus BC",
                        "priority": "high",
                        "topics": [
                            {"name": "Integration by Parts & Partial Fractions", "difficulty": "medium"},
                            {"name": "Taylor & Maclaurin Series Convergence", "difficulty": "hard"},
                            {"name": "Differential Equations & Slope Fields", "difficulty": "easy"}
                        ]
                    },
                    {
                        "name": "AP Physics C: Mechanics",
                        "priority": "high",
                        "topics": [
                            {"name": "Rotational Inertia & Angular Momentum", "difficulty": "hard"},
                            {"name": "Simple Harmonic Motion & Pendulums", "difficulty": "medium"},
                            {"name": "Conservation of Energy & Work", "difficulty": "easy"}
                        ]
                    }
                ]
            }
        }
    ]

from app.priority_engine import (
    calculate_urgency_score, calculate_difficulty_score, 
    calculate_preparation_gap, calculate_priority_score, 
    get_priority_level, analyze_smart_subject, rank_subjects_by_priority
)

@app.post("/api/smartstudy/priority", response_model=list[SmartSubjectAnalysis])
@app.post("/api/calculate-priority", response_model=list[SmartSubjectAnalysis])
async def calculate_priorities(subjects: list[SmartSubject]):
    return rank_subjects_by_priority(subjects)

@app.post("/api/smartstudy/plan", response_model=SmartStudyPlanResponse)
async def generate_smartstudy_plan(request: SmartStudyPlanRequest):
    analyzed = [analyze_smart_subject(s) for s in request.subjects]
    analyzed.sort(key=lambda x: x.priority_score, reverse=True)
    
    total_minutes = max(30, int(round(request.available_hours * 60)))
    eligible = [s for s in analyzed if s.days_remaining >= 0 and s.prep_percentage < 100]
    if not eligible:
        eligible = analyzed[:3]
        
    # Strictly respect available hours limit by limiting active pool to what can fit
    max_subjects = max(1, min(4, total_minutes // 25, len(eligible)))
    active_pool = eligible[:max_subjects]
    sum_priority = sum(s.priority_score for s in active_pool) or 1.0
    
    # Proportionally distribute total_minutes strictly
    allocated = []
    for s in active_pool:
        w = s.priority_score / sum_priority
        m = max(25, (int(round(w * total_minutes)) // 5) * 5)
        allocated.append(m)
        
    while sum(allocated) > total_minutes and len(allocated) > 0:
        diff = sum(allocated) - total_minutes
        reduced = False
        for i in range(len(allocated) - 1, -1, -1):
            if allocated[i] > 25:
                step = min(diff, min(5, allocated[i] - 25))
                allocated[i] -= step
                diff -= step
                reduced = True
                if sum(allocated) <= total_minutes:
                    break
        if not reduced:
            if len(allocated) > 1:
                allocated.pop()
                active_pool.pop()
            else:
                allocated[0] = total_minutes
                break
                
    if sum(allocated) < total_minutes and allocated:
        allocated[0] += (total_minutes - sum(allocated))
        
    tasks = []
    session_num = 1
    current_start_min = 9 * 60  # Start at 09:00 AM
    
    for s, sub_mins in zip(active_pool, allocated):
        if sub_mins > 75:
            c1 = (sub_mins * 55) // 100
            c2 = sub_mins - c1
            
            l1 = "Concept Review" if s.prep_percentage < 50 else "Problem Solving"
            t1 = f"Deep Concept Exploration & Core Theory" if l1 == "Concept Review" else f"Analytical Problem Solving Drills"
            
            l2 = "Revision" if s.days_remaining <= 3 else "Practice Questions"
            t2 = f"Urgent Mock Practice Questions" if l2 == "Practice Questions" else f"Comprehensive Formula Revision"
            
            t1_end = current_start_min + c1
            t1_slot = f"{current_start_min // 60:02d}:{current_start_min % 60:02d} - {t1_end // 60:02d}:{t1_end % 60:02d}"
            current_start_min = t1_end + 10  # 10 min break
            
            tasks.append(SmartStudyTask(
                id=f"task_{s.id}_{session_num}",
                subject_id=s.id,
                subject_name=s.name,
                label=l1,
                title=f"{l1}: {t1}",
                duration_minutes=c1,
                time_slot=t1_slot,
                completed=False
            ))
            session_num += 1
            
            t2_end = current_start_min + c2
            t2_slot = f"{current_start_min // 60:02d}:{current_start_min % 60:02d} - {t2_end // 60:02d}:{t2_end % 60:02d}"
            current_start_min = t2_end + 15  # 15 min break
            
            tasks.append(SmartStudyTask(
                id=f"task_{s.id}_{session_num}",
                subject_id=s.id,
                subject_name=s.name,
                label=l2,
                title=f"{l2}: {t2}",
                duration_minutes=c2,
                time_slot=t2_slot,
                completed=False
            ))
            session_num += 1
        else:
            if s.days_remaining <= 3:
                lbl = "Practice Questions"
                tit = "Exam High-Yield Mock Questions"
            elif s.difficulty_score == 80.0 and s.prep_percentage >= 35:
                lbl = "Problem Solving"
                tit = "Complex Problem Formulation & Solving"
            elif s.prep_percentage >= 65:
                lbl = "Revision"
                tit = "Rapid Spaced Retrieval & Formula Check"
            else:
                lbl = "Concept Review"
                tit = "Foundational Concepts & Principles"
                
            t_end = current_start_min + sub_mins
            t_slot = f"{current_start_min // 60:02d}:{current_start_min % 60:02d} - {t_end // 60:02d}:{t_end % 60:02d}"
            current_start_min = t_end + 15
            
            tasks.append(SmartStudyTask(
                id=f"task_{s.id}_{session_num}",
                subject_id=s.id,
                subject_name=s.name,
                label=lbl,
                title=f"{lbl}: {tit}",
                duration_minutes=sub_mins,
                time_slot=t_slot,
                completed=False
            ))
            session_num += 1
            
    highest_sub = analyzed[0].name if analyzed else None
    overall_prep = round(sum(s.prep_percentage for s in analyzed) / len(analyzed), 1) if analyzed else 0.0
    
    return SmartStudyPlanResponse(
        daily_hours=request.available_hours,
        subjects=analyzed,
        tasks=tasks,
        highest_priority_subject=highest_sub,
        overall_preparation=overall_prep
    )

@app.get("/api/smartstudy/sample-subjects", response_model=list[SmartSubject])
async def get_smartstudy_sample_subjects():
    today = datetime.now().date()
    return [
        SmartSubject(id="sub-1", name="Operating Systems", exam_date=(today + timedelta(days=3)).strftime("%Y-%m-%d"), difficulty="Hard", prep_percentage=25.0),
        SmartSubject(id="sub-2", name="Data Structures & Algorithms", exam_date=(today + timedelta(days=5)).strftime("%Y-%m-%d"), difficulty="Hard", prep_percentage=40.0),
        SmartSubject(id="sub-3", name="Database Management Systems", exam_date=(today + timedelta(days=7)).strftime("%Y-%m-%d"), difficulty="Medium", prep_percentage=50.0),
        SmartSubject(id="sub-4", name="Computer Networks", exam_date=(today + timedelta(days=11)).strftime("%Y-%m-%d"), difficulty="Medium", prep_percentage=65.0),
        SmartSubject(id="sub-5", name="Software Engineering & Ethics", exam_date=(today + timedelta(days=20)).strftime("%Y-%m-%d"), difficulty="Easy", prep_percentage=80.0),
    ]

# Mount static folder
app.mount("/", StaticFiles(directory="static", html=True), name="static")

