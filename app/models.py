from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TopicItem(BaseModel):
    name: str
    difficulty: str = "medium"  # "easy", "medium", "hard"
    subtopics: Optional[List[str]] = Field(default_factory=list)
    estimated_hours: Optional[float] = None

class SubjectItem(BaseModel):
    name: str
    priority: str = "medium"  # "high", "medium", "low"
    topics: List[TopicItem] = Field(default_factory=list)

class StudyPlanRequest(BaseModel):
    student_name: str = "Student"
    academic_level: str = "Undergraduate"  # High School, Undergraduate, Graduate, Competitive Exam, Self-Paced
    target_goal: str = "Score 90%+ / High Distinction"
    exam_date: str  # YYYY-MM-DD
    start_date: Optional[str] = None  # YYYY-MM-DD (defaults to today)
    weekday_hours: float = 4.0
    weekend_hours: float = 6.0
    preferred_time: str = "morning"  # morning, afternoon, evening, night
    break_technique: str = "pomodoro"  # pomodoro (25/5), long_focus (50/10), ultradian (90/20)
    learning_style: str = "active_recall"  # active_recall, visual, practice_heavy, reading_summarizing
    rest_days: List[str] = Field(default_factory=lambda: ["Sunday"])
    subjects: List[SubjectItem] = Field(default_factory=list)
    custom_notes: Optional[str] = None
    api_key: Optional[str] = None

class StudySessionBlock(BaseModel):
    session_id: str
    time_slot: str
    subject: str
    topic: str
    activity_type: str  # Concept Learning, Problem Solving, Active Recall, Quick Review, Mock Test
    duration_minutes: int
    actionable_goal: str
    recommended_technique: str
    completed: bool = False

class DailySchedule(BaseModel):
    day_number: int
    date: str  # YYYY-MM-DD
    day_of_week: str
    theme: str
    target_hours: float
    sessions: List[StudySessionBlock] = Field(default_factory=list)
    daily_tip: str = ""
    review_topics: List[str] = Field(default_factory=list)

class PhaseRoadmap(BaseModel):
    phase_name: str
    duration_days: str
    focus: str
    key_milestones: List[str] = Field(default_factory=list)

class StudyPlanResponse(BaseModel):
    plan_id: str
    student_name: str
    summary: str
    total_days: int
    total_study_hours: float
    readiness_forecast: str
    phases: List[PhaseRoadmap] = Field(default_factory=list)
    daily_schedules: List[DailySchedule] = Field(default_factory=list)
    spaced_repetition_strategy: str
    burnout_prevention_tips: List[str] = Field(default_factory=list)
    subject_hours_distribution: Dict[str, float] = Field(default_factory=dict)
    source: str = "smart-algorithmic-engine"

class ChatMessage(BaseModel):
    role: str  # user or model
    content: str

class ChatRequest(BaseModel):
    plan_summary: Dict[str, Any]
    user_message: str
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    api_key: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    suggestions: List[str] = Field(default_factory=list)

# SmartStudy AI Models
class SmartSubject(BaseModel):
    id: Optional[str] = None
    name: str = Field(min_length=1, max_length=120)
    exam_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    difficulty: str = Field(default="Medium", max_length=20)  # Easy, Medium, Hard
    prep_percentage: float = Field(default=0.0, ge=0.0, le=100.0)

class SmartSubjectAnalysis(BaseModel):
    id: str
    name: str
    exam_date: str
    days_remaining: int
    urgency_score: float
    difficulty_score: float
    prep_percentage: float
    prep_gap: float
    priority_score: float
    priority_level: str

class SmartStudyPlanRequest(BaseModel):
    available_hours: float = Field(default=4.5, gt=0.0, le=24.0)
    subjects: List[SmartSubject] = Field(min_length=1)

class SmartStudyTask(BaseModel):
    id: str
    subject_id: str
    subject_name: str
    label: str  # Concept Review, Problem Solving, Revision, Practice Questions
    title: str
    duration_minutes: int
    time_slot: str
    completed: bool = False
    missed: bool = False

class SmartStudyPlanResponse(BaseModel):
    daily_hours: float
    subjects: List[SmartSubjectAnalysis]
    tasks: List[SmartStudyTask]
    highest_priority_subject: Optional[str] = None
    overall_preparation: float = 0.0

