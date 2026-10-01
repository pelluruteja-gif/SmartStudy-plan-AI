import json
import re
import os
import uuid
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from app.models import (
    StudyPlanRequest, StudyPlanResponse, DailySchedule, 
    StudySessionBlock, PhaseRoadmap, ChatRequest, ChatResponse
)
from app.planner_engine import generate_algorithmic_plan

def clean_json_string(raw_text: str) -> str:
    """Removes markdown code blocks and trims whitespace."""
    text = raw_text.strip()
    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text

def get_gemini_client(api_key: Optional[str] = None) -> Optional[genai.Client]:
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key or key.strip() == "":
        return None
    try:
        return genai.Client(api_key=key.strip())
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")
        return None

def generate_gemini_plan(req: StudyPlanRequest) -> StudyPlanResponse:
    client = get_gemini_client(req.api_key)
    if not client:
        # Fallback to algorithmic planner immediately
        plan = generate_algorithmic_plan(req)
        plan.source = "smart-algorithmic-engine (No API key provided)"
        return plan

    # Build prompt with full student context and explicit JSON schema requirement
    subjects_summary = []
    for s in req.subjects:
        topics_str = ", ".join([f"{t.name} ({t.difficulty})" for t in s.topics])
        subjects_summary.append(f"- {s.name} (Priority: {s.priority}): {topics_str}")

    prompt = f"""You are Nova, an elite cognitive science and pedagogical study planning AI.
Create a hyper-personalized, realistic, and science-backed study plan for this student:

[STUDENT CONTEXT]
- Name: {req.student_name}
- Academic Level: {req.academic_level}
- Target Goal: {req.target_goal}
- Exam Date: {req.exam_date}
- Start Date: {req.start_date or 'Today'}
- Weekday Available Study Hours: {req.weekday_hours} hours/day
- Weekend Available Study Hours: {req.weekend_hours} hours/day
- Peak Energy Study Time: {req.preferred_time}
- Preferred Study Technique: {req.break_technique}
- Preferred Learning Style: {req.learning_style}
- Rest Days: {', '.join(req.rest_days) if req.rest_days else 'None'}
- Custom Notes / Constraints: {req.custom_notes or 'None'}

[SUBJECTS & TOPICS]
{chr(10).join(subjects_summary)}

[SCIENTIFIC PRINCIPLES TO ENFORCE]
1. Spaced Repetition (Ebbinghaus curve): Schedule systematic reviews of prior topics at 1-day, 3-day, and 7-day intervals.
2. Subject Interleaving: Alternate between subjects rather than cramming one subject all day to avoid fatigue.
3. Active Retrieval Practice: Emphasize blind recall, past paper problems, Feynman technique, and practice drills rather than passive reading.
4. Cognitive Load Management: Front-load 'hard' topics in the student's peak time slot ({req.preferred_time}).
5. Structured Phases:
   - Phase 1: Foundation & Difficult Concept Domination
   - Phase 2: Deep Problem Solving & Cross-Subject Interleaving
   - Phase 3: High-Fidelity Mock Exams & Error Remediation
   - Phase 4: Final Taper, Formula Retention & Mental Peak

Return ONLY valid JSON matching this exact structure:
{{
  "summary": "Concise 2-3 sentence overview of this study roadmap",
  "readiness_forecast": "e.g., 94% - High Distinction Trajectory",
  "phases": [
    {{
      "phase_name": "Phase 1: ...",
      "duration_days": "Day 1 - Day X",
      "focus": "...",
      "key_milestones": ["milestone 1", "milestone 2"]
    }}
  ],
  "daily_schedules": [
    {{
      "day_number": 1,
      "date": "YYYY-MM-DD",
      "day_of_week": "Monday",
      "theme": "Core Topic Domination",
      "target_hours": 4.0,
      "daily_tip": "...",
      "review_topics": ["Topic name"],
      "sessions": [
        {{
          "session_id": "s1",
          "time_slot": "09:00 - 10:30",
          "subject": "...",
          "topic": "...",
          "activity_type": "Concept Learning | Problem Solving | Active Recall | Mock Test",
          "duration_minutes": 60,
          "actionable_goal": "Specific concrete task to achieve in this session",
          "recommended_technique": "e.g., Feynman Technique, Blurting, Leitner Box",
          "completed": false
        }}
      ]
    }}
  ],
  "spaced_repetition_strategy": "Explanation of the review intervals implemented",
  "burnout_prevention_tips": ["tip 1", "tip 2", "tip 3"]
}}
"""

    models_to_try = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-3.5-flash-lite"]
    response_text = None
    
    for model_name in models_to_try:
        try:
            # First try client.interactions.create (gemini-api-dev standard)
            try:
                interaction = client.interactions.create(
                    model=model_name,
                    input=prompt
                )
                if interaction and interaction.output_text:
                    response_text = interaction.output_text
                    break
            except Exception as e_int:
                # If interactions not enabled for model, fallback to client.models.generate_content
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if resp and resp.text:
                    response_text = resp.text
                    break
        except Exception as e:
            print(f"Error calling Gemini with model {model_name}: {e}")
            continue

    if not response_text:
        # Fallback to algorithmic generator
        plan = generate_algorithmic_plan(req)
        plan.source = "smart-algorithmic-engine (Gemini connection could not be established)"
        return plan

    try:
        clean_json = clean_json_string(response_text)
        data = json.loads(clean_json)

        # Parse daily schedules
        daily_schedules = []
        subject_hours = {s.name: 0.0 for s in req.subjects}
        total_hours = 0.0

        for d in data.get("daily_schedules", []):
            sessions = []
            for s in d.get("sessions", []):
                sess = StudySessionBlock(
                    session_id=s.get("session_id") or str(uuid.uuid4())[:8],
                    time_slot=s.get("time_slot", "09:00"),
                    subject=s.get("subject", "General"),
                    topic=s.get("topic", "Topic"),
                    activity_type=s.get("activity_type", "Concept Learning"),
                    duration_minutes=int(s.get("duration_minutes", 60)),
                    actionable_goal=s.get("actionable_goal", "Study topic"),
                    recommended_technique=s.get("recommended_technique", "Active Recall"),
                    completed=bool(s.get("completed", False))
                )
                sessions.append(sess)
                subj_name = sess.subject
                dur_hrs = sess.duration_minutes / 60.0
                subject_hours[subj_name] = round(subject_hours.get(subj_name, 0.0) + dur_hrs, 1)
                total_hours += dur_hrs

            daily_schedules.append(DailySchedule(
                day_number=int(d.get("day_number", 1)),
                date=d.get("date", ""),
                day_of_week=d.get("day_of_week", ""),
                theme=d.get("theme", "Focused Study"),
                target_hours=float(d.get("target_hours", 4.0)),
                sessions=sessions,
                daily_tip=d.get("daily_tip", ""),
                review_topics=d.get("review_topics", [])
            ))

        phases = []
        for p in data.get("phases", []):
            phases.append(PhaseRoadmap(
                phase_name=p.get("phase_name", "Phase"),
                duration_days=p.get("duration_days", ""),
                focus=p.get("focus", ""),
                key_milestones=p.get("key_milestones", [])
            ))

        total_days = len(daily_schedules) if daily_schedules else 7

        return StudyPlanResponse(
            plan_id=str(uuid.uuid4()),
            student_name=req.student_name,
            summary=data.get("summary", f"AI-optimized study plan for {req.student_name}"),
            total_days=total_days,
            total_study_hours=round(total_hours, 1),
            readiness_forecast=data.get("readiness_forecast", "90% - High Mastery Trajectory"),
            phases=phases,
            daily_schedules=daily_schedules,
            spaced_repetition_strategy=data.get("spaced_repetition_strategy", "Automated spaced recall intervals"),
            burnout_prevention_tips=data.get("burnout_prevention_tips", [
                "Take regular 5-10 minute screen-free breaks.",
                "Prioritize 7-8 hours of sleep.",
                "Review weak areas early in the day."
            ]),
            subject_hours_distribution=subject_hours,
            source="gemini-ai"
        )
    except Exception as e:
        print(f"Error parsing Gemini response: {e}. Falling back to algorithmic plan.")
        fallback = generate_algorithmic_plan(req)
        fallback.source = "smart-algorithmic-engine (fallback after parsing error)"
        return fallback

def chat_with_copilot(req: ChatRequest) -> ChatResponse:
    client = get_gemini_client(req.api_key)
    
    if not client:
        # High quality algorithmic copilot response
        msg_lower = req.user_message.lower()
        if "miss" in msg_lower or "sick" in msg_lower or "behind" in msg_lower or "reschedule" in msg_lower:
            reply = (
                "Don't worry! Falling behind happens to everyone. Here is how to handle it strategically:\n\n"
                "1. **Never double your hours tomorrow**: Cramming 8 hours after missing 4 leads to cognitive overload and burnout.\n"
                "2. **Triage topics**: Move the missed 'High Difficulty' or 'High Priority' topics into your next review buffer slot.\n"
                "3. **Compress lower-priority sessions**: Turn 60-minute deep reading sessions for easier topics into 20-minute active recall/flashcard sessions.\n"
                "4. **Protect your rest days**: Keep at least a half-day off so your brain consolidates what you learned."
            )
            suggestions = [
                "How do I compress easy topics into flashcards?",
                "Which topics in my plan are highest priority?",
                "Give me a 30-minute catch-up routine"
            ]
        elif "flashcard" in msg_lower or "question" in msg_lower or "test" in msg_lower or "quiz" in msg_lower:
            reply = (
                "Here is an active retrieval exercise you can perform right now:\n\n"
                "**The Feynman 4-Step Blurting Drill**:\n"
                "1. Take a blank sheet of paper.\n"
                "2. Write down the topic name at the top.\n"
                "3. Set a timer for 5 minutes and write/draw every definition, formula, and mechanism you remember without looking at your book.\n"
                "4. Open your notes in red ink: mark what you missed or got wrong. Those red marks are your *only* study priority today!"
            )
            suggestions = [
                "How do I use Leitner Box spaced repetition?",
                "What should I do if I get stuck on a hard problem?",
                "How to simulate a timed exam at home?"
            ]
        elif "tired" in msg_lower or "burnout" in msg_lower or "stress" in msg_lower or "overwhelmed" in msg_lower:
            reply = (
                "Take a deep breath. Cognitive fatigue is a physical signal that your working memory buffer is full:\n\n"
                "• **Immediate Action**: Stop staring at the screen. Step outside for 10 minutes, drink a glass of cold water, and stretch.\n"
                "• **Switch to Low-Friction Mode**: If you have 2 hours left, don't tackle complex proofs. Instead, do 15 minutes of audio revision or organize your flashcards.\n"
                "• **Remember the 80/20 Rule**: 80% of your exam score comes from mastering 20% of core high-frequency concepts. Focus on the core!"
            )
            suggestions = [
                "Help me identify the top 20% core topics",
                "Show me a 15-minute low-friction study technique",
                "How does sleep affect memory consolidation?"
            ]
        else:
            reply = (
                f"I am your AI Study Copilot! I have reviewed your plan targeting {req.plan_summary.get('student_name', 'Student')}'s goals. "
                "You can ask me to reschedule sessions, generate active recall questions for any topic, explain complex concepts simply, "
                "or adjust your workload if your schedule changes."
            )
            suggestions = [
                "I missed a study session today, help me reschedule",
                "Give me an active recall test on my hardest topic",
                "How should I prepare 2 days before the exam?"
            ]
        return ChatResponse(reply=reply, suggestions=suggestions)

    # Use Gemini for Chat
    prompt = f"""You are Nova, an empathetic and highly knowledgeable AI Study Coach and Academic Mentor.
The student has this study plan context:
{json.dumps(req.plan_summary, indent=2)}

Conversation History:
{json.dumps([m.dict() for m in req.conversation_history[-6:]], indent=2)}

Student's Latest Message:
"{req.user_message}"

Provide a warm, inspiring, science-backed, and immediately actionable response. If they are stressed or missed a day, give them exact steps to recover without burnout. Include 3 short follow-up questions/prompts they can click next.

Return JSON in this format:
{{
  "reply": "Your markdown-formatted response here...",
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}}
"""
    try:
        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt
        )
        resp_text = interaction.output_text if interaction else None
        if not resp_text:
            resp = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )
            resp_text = resp.text

        clean = clean_json_string(resp_text)
        data = json.loads(clean)
        return ChatResponse(
            reply=data.get("reply", "Here is your customized study guidance."),
            suggestions=data.get("suggestions", [
                "How do I balance revisions?",
                "What is the best way to tackle mock exams?",
                "Help me stay focused"
            ])
        )
    except Exception as e:
        print(f"Gemini chat error: {e}")
        return ChatResponse(
            reply="I'm here to support your study journey! Remember to take regular breaks, test yourself actively, and celebrate your daily milestones.",
            suggestions=["Help me reschedule missed sessions", "Give me active recall tips", "How to manage exam anxiety"]
        )
