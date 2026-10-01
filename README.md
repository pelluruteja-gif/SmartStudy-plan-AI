# 🎓 SmartStudy AI — Adaptive Multi-Exam Study Planner

**SmartStudy AI** is an intelligent, responsive web application designed specifically for college students preparing for multiple exams simultaneously. It analyzes exam deadlines, subject difficulties, preparation gaps, and available study hours to calculate dynamic priority scores and generate an adaptive, personalized daily study roadmap.

---

## 🌟 Core Priority Algorithm

SmartStudy AI uses a multi-factor priority algorithm to determine exactly which subjects need the most attention each day:

1. **Exam Urgency Score ($0 - 100$)**:
   Calculated dynamically based on days remaining until the exam date:
   * $\le 1$ day remaining: $100$
   * $2$ days remaining: $95$
   * $\le 4$ days remaining: $85$
   * $\le 7$ days remaining: $75$
   * $\le 14$ days remaining: $55$
   * $\le 21$ days remaining: $40$
   * $\le 30$ days remaining: $25$
   * $> 30$ days: Continuous decay function

2. **Difficulty Score**:
   * **Easy**: $20$
   * **Medium**: $50$
   * **Hard**: $80$

3. **Preparation Gap**:
   $$\text{Preparation Gap} = 100 - \text{Current Preparation Percentage}$$

### Final Priority Formula:
$$\text{Priority} = (\text{Urgency} \times 0.40) + (\text{Difficulty} \times 0.25) + (\text{Preparation Gap} \times 0.35)$$

Higher score means higher study priority.

### Priority Levels:
* 🔴 **High Priority**: Score $\ge 70$
* 🟡 **Medium Priority**: Score $\ge 45$ and $< 70$
* 🟢 **Low Priority**: Score $< 45$

---

## 🚀 Key Features

### 1. Modern Student Dashboard
* **Total Subjects Counter**: Real-time count of active college exams.
* **Highest-Priority Subject**: Instant badge highlighting the most critical exam.
* **Overall Preparation Percentage**: Visual progress bar averaging preparedness across all subjects.
* **Available Daily Study Hours**: Dynamic stepper (`+` / `-`) and slider adjuster ($1.0 - 12.0$ hrs/day).
* **Upcoming Exams Countdown**: Cards sorted chronologically with days-remaining countdowns.
* **Today's Generated Plan**: Interactive checklist of prioritized study blocks.

### 2. Add & Manage Subjects
* Enter **Subject Name**, **Exam Date**, **Difficulty** (Easy, Medium, Hard), and **Current Preparation %** ($0-100\%$).
* Supports adding multiple subjects, editing existing subjects, or removing completed exams.
* **1-Click College Presets**: Pre-loaded templates for Computer Science, Engineering, and Business majors.

### 3. Priority Analysis Matrix
* Comprehensive analytical matrix showing:
  * Days remaining countdown
  * Difficulty score ($20 / 50 / 80$)
  * Current preparation percentage
  * Preparation gap ($100 - \text{prep}\%$)
  * Exact calculated priority score
  * Priority level badge (High / Medium / Low)
  * Breakdown of the three mathematical components

### 4. Proportional Study Plan Generator
* Distributes student's available daily hours proportionally according to priority scores.
* Higher-priority subjects receive longer, focused study blocks.
* Automatically generates structured study sessions labeled with:
  * 📘 **Concept Review**: Core principles and definition drills for low-prep or hard subjects.
  * 💻 **Problem Solving**: Deep analytical exercise solving.
  * 🔁 **Revision**: Spaced retrieval and formula flashcard reviews.
  * ❓ **Practice Questions**: Exam-style timed mock questions and past papers.

### 5. Progress Tracking & Dynamic Priority Recalculation
* Interactive checkboxes for every study task.
* When marked **Completed**:
  * Visual completion animation and progress bar update.
  * **Adaptive Feedback**: Automatically increases that subject's preparation percentage.
  * Dynamically lowers the subject's preparation gap, automatically recalculating and updating the priority score in real time!
* Unchecking reverts the preparation boost.

### 6. Adaptive Planning
* **Missed Session Handling**: Students can mark a session as missed without guilt. The engine automatically adapts the remaining schedule, shifting into high-yield drills.
* **Dynamic Hour Rebalancing**: Changing available daily study hours instantly adapts and recalculates the schedule.
* **1-Click "Adapt Plan"**: Recomputes optimal distribution anytime.

### 7. AI Study Coach
* Built-in intelligent recommendation engine that analyzes upcoming exams, difficulty, preparation gaps, and remaining time.
* **Critical Priority Triage**: Identifies urgent exams requiring emergency study shifts.
* **Cognitive Interleaving & Rhythm**: Recommends alternating between high-load and low-load subjects to prevent mental plateau and burnout.
* **Subject-by-Subject Action Plan**: Specific, actionable study tactics for each subject.
* **Interactive "Ask Coach" Q&A**: Answers queries on triage tactics, cramming avoidance, and active recall methods.

### 8. Focus Pomodoro Engine
* Integrated 25-minute, 45-minute, and 5-minute Pomodoro timers directly launchable from any generated study task.

---

## 💻 Tech Stack & Architecture

* **Frontend**: Pure HTML5, modern CSS3 (with Tailwind CSS and glassmorphism styling), Vanilla JavaScript (ES6+).
* **Storage**: Browser `localStorage` for offline persistence (no external database or authentication required).
* **Backend (Optional / API)**: FastAPI + Uvicorn server providing REST endpoints for programmatic plan generation.

---

## 🏃 Getting Started

### Option A: Open Directly in Browser (No Python Required)
Simply double-click or open `index.html` in any modern web browser (Chrome, Edge, Firefox, Safari).

### Option B: Run via Python Server
Open terminal in the project directory and run:

```bash
python run.py
```

The web server will start at `http://127.0.0.1:8000` and automatically launch your default browser.

### Run Tests:
```bash
python test_smartstudy.py
```
Verifies the priority algorithm, time distribution weighting, required labels, and API routes.
