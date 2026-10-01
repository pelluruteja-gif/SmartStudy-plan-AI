/**
 * SmartStudy AI — Adaptive Exam Preparation & Priority Engine
 * Production-Grade Core Controller
 */

// ==========================================
// 1. STATE MANAGEMENT & LOCAL STORAGE
// ==========================================
const STORAGE_KEY = "smartstudy_data_v2";

let state = {
  dailyHours: 4.5,
  subjects: [],
  todayTasks: [],
  lastPlanDate: null,
};

// Pomodoro Timer State
let timerInterval = null;
let timerSeconds = 25 * 60;
let timerRunning = false;

// ==========================================
// 2. DATE UTILITIES (Local Timezone Safe)
// ==========================================

function formatLocalDate(d) {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getTodayDateStr() {
  return formatLocalDate(new Date());
}

function calculateDaysRemaining(examDateStr) {
  if (!examDateStr) return 0;
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const parts = String(examDateStr).split("-").map(Number);
  if (parts.length !== 3 || isNaN(parts[0]) || isNaN(parts[1]) || isNaN(parts[2])) {
    return 0;
  }
  const exam = new Date(parts[0], parts[1] - 1, parts[2], 0, 0, 0, 0);
  const diffTime = exam.getTime() - today.getTime();
  return Math.round(diffTime / (1000 * 60 * 60 * 24));
}

// ==========================================
// 3. DEFAULT SAMPLE PRESETS
// ==========================================

function getSampleSubjects(presetKey = "cs-college") {
  const today = new Date();
  
  function futureDateStr(daysAhead) {
    const d = new Date();
    d.setDate(today.getDate() + daysAhead);
    return formatLocalDate(d);
  }

  if (presetKey === "eng-finals") {
    return [
      { id: "eng-1", name: "Signals & Systems", examDate: futureDateStr(3), difficulty: "Hard", prepPercentage: 35, color: "#ef4444" },
      { id: "eng-2", name: "Microprocessor Architecture", examDate: futureDateStr(6), difficulty: "Hard", prepPercentage: 45, color: "#f97316" },
      { id: "eng-3", name: "Engineering Electromagnetics", examDate: futureDateStr(10), difficulty: "Medium", prepPercentage: 55, color: "#3b82f6" },
      { id: "eng-4", name: "Probability & Stochastic Processes", examDate: futureDateStr(15), difficulty: "Easy", prepPercentage: 80, color: "#10b981" }
    ];
  } else if (presetKey === "business-finals") {
    return [
      { id: "bus-1", name: "Corporate Financial Accounting", examDate: futureDateStr(3), difficulty: "Hard", prepPercentage: 30, color: "#ef4444" },
      { id: "bus-2", name: "Managerial Microeconomics", examDate: futureDateStr(5), difficulty: "Medium", prepPercentage: 50, color: "#f97316" },
      { id: "bus-3", name: "Business Statistics & Analytics", examDate: futureDateStr(9), difficulty: "Hard", prepPercentage: 60, color: "#3b82f6" },
      { id: "bus-4", name: "Organizational Behavior", examDate: futureDateStr(18), difficulty: "Easy", prepPercentage: 85, color: "#10b981" }
    ];
  }

  // Default: Computer Science College Finals
  return [
    { id: "sub-1", name: "Operating Systems", examDate: futureDateStr(3), difficulty: "Hard", prepPercentage: 25, color: "#ef4444" },
    { id: "sub-2", name: "Data Structures & Algorithms", examDate: futureDateStr(5), difficulty: "Hard", prepPercentage: 40, color: "#f97316" },
    { id: "sub-3", name: "Database Management Systems", examDate: futureDateStr(7), difficulty: "Medium", prepPercentage: 50, color: "#3b82f6" },
    { id: "sub-4", name: "Computer Networks", examDate: futureDateStr(11), difficulty: "Medium", prepPercentage: 65, color: "#8b5cf6" },
    { id: "sub-5", name: "Software Engineering & Ethics", examDate: futureDateStr(20), difficulty: "Easy", prepPercentage: 80, color: "#10b981" }
  ];
}

// Load State from LocalStorage or initialize
function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      state.dailyHours = typeof parsed.dailyHours === "number" ? parsed.dailyHours : 4.5;
      state.subjects = Array.isArray(parsed.subjects) ? parsed.subjects : [];
      state.todayTasks = Array.isArray(parsed.todayTasks) ? parsed.todayTasks : [];
      state.lastPlanDate = parsed.lastPlanDate || null;
    }
  } catch (err) {
    console.error("Failed to parse localStorage", err);
  }

  // If no subjects found, load default sample
  if (!state.subjects || state.subjects.length === 0) {
    state.subjects = getSampleSubjects("cs-college");
    saveState();
  }

  // Check if we need to generate today's plan
  const todayStr = getTodayDateStr();
  if (!state.todayTasks || state.todayTasks.length === 0 || state.lastPlanDate !== todayStr) {
    generateStudyPlan(false);
  }
}

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (err) {
    console.error("Failed to save state to localStorage", err);
  }
}

// ==========================================
// 4. CORE PRIORITY ALGORITHM
// ==========================================

/**
 * 1. Exam Urgency score based on days remaining:
 * Continuous well-calibrated curve from 100 (due today/tomorrow) down to 5 (due in months)
 */
function calculateUrgency(daysRemaining) {
  if (daysRemaining <= 0) return 100.0;
  if (daysRemaining === 1) return 100.0;
  if (daysRemaining === 2) return 95.0;
  if (daysRemaining <= 4) return 85.0;
  if (daysRemaining <= 7) return 75.0;
  if (daysRemaining <= 14) return 55.0;
  if (daysRemaining <= 21) return 40.0;
  if (daysRemaining <= 30) return 25.0;
  return Math.max(5.0, Math.round((100.0 / (1.0 + (daysRemaining / 6.0))) * 10) / 10);
}

/**
 * 2. Difficulty score:
 * Easy = 20, Medium = 50, Hard = 80
 */
function getDifficultyScore(difficulty) {
  const d = (difficulty || "").toLowerCase().trim();
  if (d === "easy") return 20.0;
  if (d === "medium") return 50.0;
  if (d === "hard") return 80.0;
  return 50.0;
}

/**
 * 3. Preparation Gap:
 * 100 - Current Preparation Percentage
 */
function getPreparationGap(prepPercentage) {
  const prep = Number(prepPercentage) || 0;
  return Math.max(0.0, 100.0 - prep);
}

/**
 * Final Priority Formula:
 * priority = (urgency * 0.40) + (difficulty * 0.25) + (preparationGap * 0.35)
 * 
 * Levels:
 * High: score >= 70
 * Medium: score >= 45
 * Low: below 45
 */
function analyzeSubject(subject) {
  const daysRemaining = calculateDaysRemaining(subject.examDate);
  const urgency = calculateUrgency(daysRemaining);
  const difficultyScore = getDifficultyScore(subject.difficulty);
  const prepGap = getPreparationGap(subject.prepPercentage);

  const rawPriority = (urgency * 0.40) + (difficultyScore * 0.25) + (prepGap * 0.35);
  const priorityScore = Math.round(rawPriority * 10) / 10;

  let priorityLevel = "Low";
  let badgeClass = "badge-low";
  if (priorityScore >= 70.0) {
    priorityLevel = "High";
    badgeClass = "badge-high";
  } else if (priorityScore >= 45.0) {
    priorityLevel = "Medium";
    badgeClass = "badge-medium";
  }

  return {
    ...subject,
    daysRemaining,
    urgency,
    difficultyScore,
    prepGap,
    priorityScore,
    priorityLevel,
    badgeClass,
  };
}

function getAnalyzedSubjects() {
  return state.subjects.map(analyzeSubject).sort((a, b) => b.priorityScore - a.priorityScore);
}

// ==========================================
// 5. STUDY PLAN GENERATOR & ADAPTIVE SCHEDULING
// ==========================================

/**
 * Generates personalized daily study sessions strictly respecting available daily hours.
 * Enforces sum(task.duration) <= totalMinutes at all times.
 * Session labels strictly include:
 * - Concept Review
 * - Problem Solving
 * - Revision
 * - Practice Questions
 */
function generateStudyPlan(preserveCompleted = true) {
  const analyzed = getAnalyzedSubjects();
  if (analyzed.length === 0) {
    state.todayTasks = [];
    state.lastPlanDate = getTodayDateStr();
    saveState();
    return;
  }

  // Preserve existing completed tasks if requested
  const existingCompletedTasks = [];
  if (preserveCompleted && Array.isArray(state.todayTasks)) {
    state.todayTasks.forEach(t => {
      if (t.completed) {
        existingCompletedTasks.push(t);
      }
    });
  }

  const totalMinutes = Math.max(30, Math.round(state.dailyHours * 60));
  
  // Calculate completed minutes already logged
  const completedMins = existingCompletedTasks.reduce((sum, t) => sum + (t.duration || 0), 0);
  let availableForNewTasks = Math.max(0, totalMinutes - completedMins);

  // If already at or above limit with completed tasks, preserve completed only
  if (availableForNewTasks < 25 && existingCompletedTasks.length > 0) {
    state.todayTasks = existingCompletedTasks;
    state.lastPlanDate = getTodayDateStr();
    saveState();
    return;
  }

  // If regenerating clean or remaining time exists:
  const targetMinutesToAllocate = existingCompletedTasks.length > 0 ? availableForNewTasks : totalMinutes;

  // Active pool: candidate subjects (exclude 100% prepared or passed exams)
  let eligibleSubjects = analyzed.filter(s => s.daysRemaining >= 0 && s.prepPercentage < 100);
  if (eligibleSubjects.length === 0) {
    eligibleSubjects = analyzed.slice(0, 3);
  }

  // How many subjects can realistically fit without violating limits? (min 25 min each)
  const maxSubjects = Math.max(1, Math.min(4, Math.floor(targetMinutesToAllocate / 25), eligibleSubjects.length));
  const activePool = eligibleSubjects.slice(0, maxSubjects);
  const sumPriority = activePool.reduce((acc, s) => acc + s.priorityScore, 0) || 1;

  // Proportionally distribute targetMinutesToAllocate strictly in 5-minute increments
  let allocated = activePool.map(s => {
    const w = s.priorityScore / sumPriority;
    return Math.max(25, Math.floor((w * targetMinutesToAllocate) / 5) * 5);
  });

  // Guarantee sum(allocated) <= targetMinutesToAllocate
  let totalAllocated = allocated.reduce((a, b) => a + b, 0);
  while (totalAllocated > targetMinutesToAllocate && allocated.length > 0) {
    const diff = totalAllocated - targetMinutesToAllocate;
    let reduced = false;
    for (let i = allocated.length - 1; i >= 0; i--) {
      if (allocated[i] > 25) {
        const step = Math.min(diff, Math.min(5, allocated[i] - 25));
        allocated[i] -= step;
        totalAllocated -= step;
        reduced = true;
        if (totalAllocated <= targetMinutesToAllocate) break;
      }
    }
    if (!reduced) {
      if (allocated.length > 1) {
        allocated.pop();
        activePool.pop();
        totalAllocated = allocated.reduce((a, b) => a + b, 0);
      } else {
        allocated[0] = targetMinutesToAllocate;
        totalAllocated = targetMinutesToAllocate;
        break;
      }
    }
  }

  // If there is leftover unallocated time, grant to highest priority
  if (totalAllocated < targetMinutesToAllocate && allocated.length > 0) {
    allocated[0] += (targetMinutesToAllocate - totalAllocated);
  }

  // Generate new task objects
  const newTasks = [];
  let currentStartMin = 9 * 60; // 09:00 AM base start
  let sessionIndex = existingCompletedTasks.length + 1;

  activePool.forEach((sub, idx) => {
    const subMins = allocated[idx];
    if (subMins <= 0) return;

    if (subMins > 75) {
      const c1 = Math.floor((subMins * 55) / 100);
      const c2 = subMins - c1;

      let l1 = "Concept Review";
      let t1 = "Deep Concept Breakdown & High-Yield Notes";
      if (sub.prepPercentage >= 50) {
        l1 = "Problem Solving";
        t1 = "Analytical Problem Solving & Scenario Drills";
      }

      let l2 = sub.daysRemaining <= 3 ? "Revision" : "Practice Questions";
      let t2 = l2 === "Revision" ? "High-Speed Formula & Key Fact Revision" : "Timed Exam Practice Questions & Past Papers";

      const t1Slot = formatTimeSlot(currentStartMin, c1);
      currentStartMin += c1 + 10;
      newTasks.push(createTaskObj(sub, l1, t1, c1, sessionIndex++, t1Slot));

      const t2Slot = formatTimeSlot(currentStartMin, c2);
      currentStartMin += c2 + 15;
      newTasks.push(createTaskObj(sub, l2, t2, c2, sessionIndex++, t2Slot));
    } else {
      let label = "Concept Review";
      let title = "Fundamental Topic Review & Core Theorems";

      if (sub.daysRemaining <= 3) {
        label = "Practice Questions";
        title = "Urgent Exam Mock Questions & High-Frequency Patterns";
      } else if (sub.difficultyScore === 80.0 && sub.prepPercentage >= 35) {
        label = "Problem Solving";
        title = "Complex Exercise Solving & Algorithmic Drills";
      } else if (sub.prepPercentage >= 65) {
        label = "Revision";
        title = "Spaced Retrieval & Flashcard Formula Revision";
      }

      const tSlot = formatTimeSlot(currentStartMin, subMins);
      currentStartMin += subMins + 15;
      newTasks.push(createTaskObj(sub, label, title, subMins, sessionIndex++, tSlot));
    }
  });

  // Combine completed tasks and newly generated tasks
  state.todayTasks = [...existingCompletedTasks, ...newTasks];

  // Final sanity check: ensure absolute total never exceeds configured daily limit
  const finalSum = state.todayTasks.reduce((s, t) => s + (t.duration || 0), 0);
  if (finalSum > totalMinutes) {
    const excess = finalSum - totalMinutes;
    // Trim excess from the last uncompleted task
    for (let i = state.todayTasks.length - 1; i >= 0; i--) {
      if (!state.todayTasks[i].completed && state.todayTasks[i].duration > 25) {
        state.todayTasks[i].duration = Math.max(25, state.todayTasks[i].duration - excess);
        break;
      }
    }
  }

  state.lastPlanDate = getTodayDateStr();
  saveState();
}

function formatTimeSlot(startMins, durationMins) {
  const endMins = startMins + durationMins;
  const sH = Math.floor(startMins / 60);
  const sM = startMins % 60;
  const eH = Math.floor(endMins / 60);
  const eM = endMins % 60;
  return `${String(sH).padStart(2, "0")}:${String(sM).padStart(2, "0")} - ${String(eH).padStart(2, "0")}:${String(eM).padStart(2, "0")}`;
}

function createTaskObj(sub, label, title, durationMinutes, sessionIndex, timeSlot) {
  return {
    id: `task_${sub.id}_${label}_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
    subjectId: sub.id,
    subjectName: sub.name,
    difficulty: sub.difficulty,
    label: label, // Concept Review | Problem Solving | Revision | Practice Questions
    title: `${label}: ${title}`,
    duration: durationMinutes,
    timeSlot: timeSlot,
    completed: false,
    missed: false,
  };
}

// ==========================================
// 6. PROGRESS TRACKING & ADAPTIVE RECALCULATION
// ==========================================

function handleTaskToggle(taskId) {
  const task = state.todayTasks.find(t => t.id === taskId);
  if (!task) return;

  const wasCompleted = task.completed;
  task.completed = !wasCompleted;
  if (task.completed) {
    task.missed = false; // Cannot be completed and missed simultaneously
  }

  // Dynamic increment based on session duration: ~1% per 15-20 min of study
  const subject = state.subjects.find(s => s.id === task.subjectId);
  if (subject) {
    const bump = Math.max(2, Math.round(task.duration / 18));
    if (task.completed) {
      subject.prepPercentage = Math.min(100, (Number(subject.prepPercentage) || 0) + bump);
      showToast(`🎉 "${task.subjectName}" preparation boosted to ${subject.prepPercentage}%! Priority recalculated.`, "success");
      if (typeof confetti === "function") {
        confetti({ particleCount: 40, spread: 60, origin: { y: 0.8 } });
      }
    } else {
      subject.prepPercentage = Math.max(0, (Number(subject.prepPercentage) || 0) - bump);
      showToast(`Updated preparation for ${task.subjectName}.`, "info");
    }
  }

  saveState();
  renderApp();
}

function handleTaskMissed(taskId) {
  const task = state.todayTasks.find(t => t.id === taskId);
  if (!task) return;

  task.missed = !task.missed;
  if (task.missed) {
    task.completed = false;
    showToast(`Session marked missed. Adapting schedule to recover lost study time...`, "warning");
    adaptScheduleAfterMissedTask();
  } else {
    saveState();
    renderApp();
  }
}

function adaptScheduleAfterMissedTask() {
  const uncompletedTasks = state.todayTasks.filter(t => !t.completed && !t.missed);
  if (uncompletedTasks.length > 0) {
    uncompletedTasks.forEach(t => {
      if (t.label === "Concept Review") {
        t.label = "Practice Questions";
        t.title = `Practice Questions: High-Yield Condensed Exam Drills (Adapted)`;
      }
    });
  }
  saveState();
  renderApp();
  showToast("Plan adapted: priorities shifted to high-yield drills.", "info");
}

function recalculateAdaptivePlan() {
  generateStudyPlan(true);
  renderApp();
  showToast("Study plan dynamically adapted to current priorities & available hours!", "success");
}

// ==========================================
// 7. AI STUDY COACH ENGINE
// ==========================================

function getAICoachInsights() {
  const analyzed = getAnalyzedSubjects();
  if (analyzed.length === 0) {
    return {
      triage: {
        title: "No Active Subjects",
        message: "Add your college subjects and upcoming exam dates to receive personalized AI coaching.",
        level: "info"
      },
      rhythm: {
        title: "Study Habit Foundation",
        message: "Consistent daily study hours prevent eleventh-hour cramming and retain 400% more information long-term."
      },
      subjectAdvice: []
    };
  }

  const highest = analyzed[0];
  let triage = {
    title: `🚨 Urgent Focus: ${highest.name}`,
    message: `${highest.name} has a priority score of ${highest.priorityScore}. With only ${highest.daysRemaining} days left and a ${highest.prepGap}% preparation gap, this requires your primary focus block today.`,
    level: highest.priorityScore >= 70 ? "urgent" : "recommended",
    subjectName: highest.name,
    score: highest.priorityScore
  };

  let rhythm = {
    title: "🧠 Cognitive Interleaving Strategy",
    message: "Do not spend your entire study day on a single hard subject. After 60-90 minutes of high-intensity problem solving, switch to an Easy or Medium subject for Revision. This prevents mental fatigue and maximizes neural consolidation."
  };

  if (state.dailyHours > 6) {
    rhythm.message = "You have scheduled heavy daily study hours (> 6 hrs). Ensure you take a mandatory 15-minute cognitive break every 50 minutes to prevent diminishing returns.";
  }

  const subjectAdvice = analyzed.map(sub => {
    let actionableTip = "";
    let recommendedLabel = "";

    if (sub.daysRemaining <= 2) {
      recommendedLabel = "Practice Questions";
      actionableTip = `Exam in ${sub.daysRemaining} days! Stop passive reading. Focus 100% on timed mock exam questions and past papers. Review mistakes immediately.`;
    } else if (sub.priorityScore >= 70) {
      recommendedLabel = "Concept Review & Problem Solving";
      actionableTip = `Critical priority due to ${sub.difficulty} difficulty and ${sub.prepGap}% prep gap. Dedicate prime morning hours. Use the Feynman technique: explain complex topics in simple words.`;
    } else if (sub.priorityScore >= 45) {
      recommendedLabel = "Problem Solving & Retrieval";
      actionableTip = `Steady progress (${sub.prepPercentage}%). You have ${sub.daysRemaining} days remaining. Focus on medium-difficulty practice drills and flashcard spaced repetition.`;
    } else {
      recommendedLabel = "Revision";
      actionableTip = `Good mastery level (${sub.prepPercentage}% prep). Keep sharp with short 30-minute spaced retrieval drills every other day to prevent forgetting.`;
    }

    return {
      id: sub.id,
      name: sub.name,
      priorityLevel: sub.priorityLevel,
      priorityScore: sub.priorityScore,
      daysRemaining: sub.daysRemaining,
      prepPercentage: sub.prepPercentage,
      recommendedLabel,
      actionableTip,
      badgeClass: sub.badgeClass
    };
  });

  return { triage, rhythm, subjectAdvice };
}

function askCoachPrompt(type) {
  const analyzed = getAnalyzedSubjects();
  const highest = analyzed[0] || { name: "your highest priority exam", prepGap: 60 };
  const safeHighestName = escapeHtml(highest.name);
  const responseBox = document.getElementById("coachResponseBox");
  const responseTitle = document.getElementById("coachResponseTitle");
  const responseContent = document.getElementById("coachResponseContent");

  if (type === "triage") {
    responseTitle.innerText = `Triage Strategy: ${highest.name}`;
    responseContent.innerHTML = `
      <p class="font-medium text-slate-200">Recommended 3-Step Attack Plan for <strong>${safeHighestName}</strong>:</p>
      <ul class="list-disc pl-4 space-y-1 mt-1 text-slate-300">
        <li><strong>Step 1:</strong> Identify high-weightage chapters from past exams immediately.</li>
        <li><strong>Step 2:</strong> Spend 45 minutes on active recall formulas/definitions without looking at notes.</li>
        <li><strong>Step 3:</strong> Solve 3 past exam problems under timed conditions.</li>
      </ul>
    `;
  } else if (type === "cramming") {
    responseTitle.innerText = "Burnout Prevention Protocol";
    responseContent.innerHTML = `
      <p class="text-slate-300">
        Cramming spikes cortisol and impairs prefrontal cortex retrieval during the exam. Instead of an all-nighter:
        <br>&bull; Protect <strong>7 hours of sleep</strong> — sleep is when memory consolidation occurs.
        <br>&bull; Study in <strong>50-minute bursts</strong> with 10-minute away-from-screens breaks.
        <br>&bull; Hydrate and take a brisk 5-minute walk between subject switches.
      </p>
    `;
  } else if (type === "interleaving") {
    responseTitle.innerText = "Subject Interleaving Science";
    responseContent.innerHTML = `
      <p class="text-slate-300">
        Cognitive science proves that alternating disciplines (e.g. studying <strong>${safeHighestName}</strong> for 1 hour, then shifting to a lighter revision topic) forces your brain to continually reload concepts, increasing exam recall accuracy by up to <strong>43%</strong> compared to blocked studying.
      </p>
    `;
  } else if (type === "retention") {
    responseTitle.innerText = "Highest-Yield Active Recall Methods";
    responseContent.innerHTML = `
      <p class="text-slate-300">
        <strong>1. The Blurting Method:</strong> Read a concept for 5 minutes, close the book, and write down everything you remember on a blank sheet. Highlight what you missed.
        <br><strong>2. Reverse Problem Solving:</strong> Look at solved past exam problems, cover the steps, and attempt to reconstruct the solution path.
      </p>
    `;
  }

  if (responseBox) responseBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function submitCustomCoachQuestion() {
  const input = document.getElementById("coachCustomInput");
  if (!input) return;
  const question = input.value.trim();
  if (!question) return;

  const analyzed = getAnalyzedSubjects();
  const highest = analyzed[0];
  const safeHighestName = escapeHtml(highest ? highest.name : "upcoming exams");
  const responseTitle = document.getElementById("coachResponseTitle");
  const responseContent = document.getElementById("coachResponseContent");

  responseTitle.innerText = `Coach Answer: "${question.substring(0, 35)}..."`;
  
  let answer = "";
  const qLower = question.toLowerCase();

  if (qLower.includes("time") || qLower.includes("hour") || qLower.includes("schedule")) {
    answer = `Given your <strong>${state.dailyHours} available hours today</strong>, allocate approximately 60% of your time to <strong>${safeHighestName}</strong>. Ensure you leave at least 30 minutes for a quick spaced review of your other subjects.`;
  } else if (qLower.includes("hard") || qLower.includes("difficult") || qLower.includes("fail") || qLower.includes("scared")) {
    answer = `Exam anxiety is normal when facing hard subjects. The most effective antidote is <em>action over contemplation</em>: pick one specific formula or theorem in <strong>${safeHighestName}</strong> right now, solve one problem, and build incremental momentum.`;
  } else if (qLower.includes("formula") || qLower.includes("memoriz")) {
    answer = `For fast formula retention: create a one-page "cheat sheet" by hand. Test yourself 3 times today: morning, midday, and right before sleeping. Spacing the recall triggers synaptic consolidation.`;
  } else {
    answer = `Great question! Based on your current priority analysis, your top focus must remain on <strong>${safeHighestName}</strong> (Days left: ${highest ? highest.daysRemaining : 5}, Prep Gap: ${highest ? highest.prepGap : 50}%). Tackle high-difficulty concepts when your energy is highest, and use practice questions as your primary learning vehicle.`;
  }

  responseContent.innerHTML = `<p class="text-slate-200 leading-relaxed">${answer}</p>`;
  input.value = "";
}

function refreshAICoachRecommendations() {
  renderAICoachSection();
  showToast("AI Coach analysis refreshed with latest subject parameters!", "info");
}

// ==========================================
// 8. UI RENDERING & DOM UPDATES
// ==========================================

function renderApp() {
  const analyzed = getAnalyzedSubjects();

  renderHeaderAndMetrics(analyzed);
  renderTodayTasks(analyzed);
  renderUpcomingExams(analyzed);
  renderPriorityTable(analyzed);
  renderSubjectCards(analyzed);
  renderAICoachSection();

  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function renderHeaderAndMetrics(analyzed) {
  const hoursFormatted = `${state.dailyHours} hrs`;
  const headerHours = document.getElementById("headerHoursDisplay");
  if (headerHours) headerHours.innerText = hoursFormatted;
  
  const statHours = document.getElementById("statDailyHours");
  if (statHours) statHours.innerText = state.dailyHours;

  const totalSubEl = document.getElementById("statTotalSubjects");
  if (totalSubEl) totalSubEl.innerText = analyzed.length;
  
  const pillCount = document.getElementById("subjectCountPill");
  if (pillCount) pillCount.innerText = analyzed.length;

  const highestSub = analyzed[0];
  const statHighestSub = document.getElementById("statHighestSubject");
  const statHighestBadge = document.getElementById("statHighestBadge");
  const statHighestScore = document.getElementById("statHighestScore");

  if (highestSub) {
    if (statHighestSub) statHighestSub.innerText = highestSub.name;
    if (statHighestBadge) {
      statHighestBadge.className = `text-[10px] px-2 py-0.5 rounded-full font-bold ${highestSub.badgeClass}`;
      statHighestBadge.innerText = `${highestSub.priorityLevel} Priority`;
    }
    if (statHighestScore) statHighestScore.innerText = `Score: ${highestSub.priorityScore}`;
  } else {
    if (statHighestSub) statHighestSub.innerText = "No subjects";
    if (statHighestBadge) {
      statHighestBadge.className = "text-[10px] px-2 py-0.5 rounded-full font-bold bg-slate-800 text-slate-400";
      statHighestBadge.innerText = "No data";
    }
    if (statHighestScore) statHighestScore.innerText = "Score: —";
  }

  const highCount = analyzed.filter(s => s.priorityLevel === "High").length;
  const highBadge = document.getElementById("highPriorityCountBadge");
  if (highBadge) {
    if (highCount > 0) {
      highBadge.classList.remove("hidden");
      highBadge.innerText = highCount;
    } else {
      highBadge.classList.add("hidden");
    }
  }

  let avgPrep = 0;
  if (analyzed.length > 0) {
    const totalPrep = analyzed.reduce((acc, s) => acc + (Number(s.prepPercentage) || 0), 0);
    avgPrep = Math.round(totalPrep / analyzed.length);
  }
  const statPrep = document.getElementById("statOverallPrep");
  const statPrepBar = document.getElementById("statPrepBar");
  if (statPrep) statPrep.innerText = `${avgPrep}%`;
  if (statPrepBar) statPrepBar.style.width = `${avgPrep}%`;

  const statTasks = document.getElementById("statAllocatedTasks");
  if (statTasks) {
    statTasks.innerText = `${state.todayTasks.length} sessions scheduled`;
  }

  const alertBanner = document.getElementById("urgentAlertBanner");
  const alertText = document.getElementById("urgentAlertText");
  const urgentBadge = document.getElementById("urgentSubjectBadge");

  if (highestSub && highestSub.priorityScore >= 70.0) {
    if (alertBanner) alertBanner.classList.remove("hidden");
    if (urgentBadge) urgentBadge.innerText = `${highestSub.priorityScore} Pts`;
    if (alertText) {
      alertText.innerHTML = `<strong>${escapeHtml(highestSub.name)}</strong> exam is in <strong>${highestSub.daysRemaining} days</strong> with a <strong>${highestSub.prepGap}%</strong> preparation gap. High study allocation recommended.`;
    }
  } else {
    if (alertBanner) alertBanner.classList.add("hidden");
  }
}

function renderTodayTasks(analyzed = []) {
  const container = document.getElementById("todayTaskList");
  const progressText = document.getElementById("planProgressText");
  const progressBar = document.getElementById("todayProgressBar");
  const totalSummary = document.getElementById("planTotalTimeSummary");

  if (!container) return;

  if (state.todayTasks.length === 0) {
    container.innerHTML = `
      <div class="text-center py-12 text-slate-500 glass-panel-subtle rounded-2xl p-6">
        <i data-lucide="book-marked" class="w-12 h-12 mx-auto mb-3 opacity-30 text-indigo-400"></i>
        <h4 class="text-base font-semibold text-slate-300">No study sessions generated</h4>
        <p class="text-xs text-slate-400 mt-1 max-w-sm mx-auto">Add subjects with upcoming exams or adjust your daily hours to generate an adaptive schedule.</p>
        <button onclick="openSubjectModal()" class="mt-4 px-4 py-2 rounded-xl btn-glow text-xs font-semibold text-white">
          + Add First Subject
        </button>
      </div>
    `;
    if (progressText) progressText.innerText = "0% (0 / 0 tasks)";
    if (progressBar) progressBar.style.width = "0%";
    if (totalSummary) totalSummary.innerText = "0 hrs allocated";
    return;
  }

  const completedCount = state.todayTasks.filter(t => t.completed).length;
  const pct = Math.round((completedCount / state.todayTasks.length) * 100);
  const totalMins = state.todayTasks.reduce((acc, t) => acc + (t.duration || 0), 0);
  const totalHoursFormatted = (totalMins / 60).toFixed(1);

  if (progressText) progressText.innerText = `${pct}% (${completedCount} / ${state.todayTasks.length} completed)`;
  if (progressBar) progressBar.style.width = `${pct}%`;
  if (totalSummary) totalSummary.innerText = `Total: ${totalHoursFormatted} hrs allocated across ${state.todayTasks.length} structured sessions (Max: ${state.dailyHours} hrs)`;

  const analyzedMap = new Map();
  analyzed.forEach(s => analyzedMap.set(s.id, s));

  container.innerHTML = state.todayTasks.map((task) => {
    let labelBadgeStyle = "bg-indigo-500/15 text-indigo-300 border border-indigo-500/30";
    let labelIcon = "book-open";

    if (task.label === "Problem Solving") {
      labelBadgeStyle = "bg-amber-500/15 text-amber-300 border border-amber-500/30";
      labelIcon = "code-2";
    } else if (task.label === "Practice Questions") {
      labelBadgeStyle = "bg-rose-500/15 text-rose-300 border border-rose-500/30";
      labelIcon = "help-circle";
    } else if (task.label === "Revision") {
      labelBadgeStyle = "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30";
      labelIcon = "repeat";
    }

    const sub = analyzedMap.get(task.subjectId);
    const priorityLevel = sub ? sub.priorityLevel : "Medium";
    const badgeClass = sub ? sub.badgeClass : "badge-medium";

    const isDone = Boolean(task.completed);
    const isMissed = Boolean(task.missed);

    return `
      <div class="task-card ${isDone ? 'completed' : ''} glass-panel p-4 rounded-xl border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-all duration-200 hover:border-indigo-500/40">
        
        <!-- Left: Checkbox & Task Info -->
        <div class="flex items-start sm:items-center gap-3.5 flex-1 min-w-0">
          <input 
            type="checkbox" 
            class="task-checkbox mt-1 sm:mt-0" 
            ${isDone ? 'checked' : ''} 
            onchange="handleTaskToggle('${escapeHtml(task.id)}')"
            title="Mark as completed & boost subject preparation"
          >
          
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2 mb-1">
              <span class="text-xs font-bold text-white tracking-wide">${escapeHtml(task.subjectName)}</span>
              <span class="text-[10px] px-2 py-0.5 rounded font-semibold ${labelBadgeStyle} flex items-center gap-1">
                <i data-lucide="${labelIcon}" class="w-3 h-3"></i>
                <span>${task.label}</span>
              </span>
              <span class="text-[10px] px-2 py-0.5 rounded-full font-bold ${badgeClass}">
                ${priorityLevel}
              </span>
            </div>
            <p class="task-title text-xs text-slate-300 font-medium truncate">${escapeHtml(task.title)}</p>
          </div>
        </div>

        <!-- Right: Time Block & Action Buttons -->
        <div class="flex items-center justify-between sm:justify-end gap-3 flex-shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-white/5">
          <div class="text-right">
            <div class="text-xs font-bold text-slate-200 flex items-center gap-1 sm:justify-end">
              <i data-lucide="clock" class="w-3.5 h-3.5 text-cyan-400"></i>
              <span>${task.duration} mins</span>
            </div>
            <span class="text-[10px] text-slate-400 block">${task.timeSlot}</span>
          </div>

          <div class="flex items-center gap-1.5">
            <button 
              onclick="startPomodoroForTaskId('${escapeHtml(task.id)}')"
              title="Launch Focus Pomodoro for this task"
              class="p-2 rounded-lg bg-white/5 hover:bg-indigo-600/20 text-slate-300 hover:text-indigo-300 border border-white/10 transition"
            >
              <i data-lucide="play" class="w-3.5 h-3.5"></i>
            </button>

            <button 
              onclick="handleTaskMissed('${escapeHtml(task.id)}')"
              title="${isMissed ? 'Mark Active' : 'Mark Missed & Adapt Plan'}"
              class="p-2 rounded-lg ${isMissed ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-white/5 hover:bg-white/10 text-slate-400 border border-white/10'} transition text-[11px]"
            >
              <i data-lucide="alert-circle" class="w-3.5 h-3.5"></i>
            </button>
          </div>
        </div>

      </div>
    `;
  }).join("");
}

function renderUpcomingExams(analyzed) {
  const container = document.getElementById("upcomingExamsList");
  if (!container) return;

  if (analyzed.length === 0) {
    container.innerHTML = `<p class="text-xs text-slate-500 text-center py-6">No exams added yet.</p>`;
    return;
  }

  const sortedByDate = [...analyzed].sort((a, b) => a.daysRemaining - b.daysRemaining);

  container.innerHTML = sortedByDate.slice(0, 5).map(sub => {
    let daysBadge = "";
    if (sub.daysRemaining < 0) {
      daysBadge = `<span class="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-bold">Passed</span>`;
    } else if (sub.daysRemaining === 0) {
      daysBadge = `<span class="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/30 text-rose-300 font-bold animate-pulse">TODAY</span>`;
    } else if (sub.daysRemaining === 1) {
      daysBadge = `<span class="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30">Tomorrow</span>`;
    } else if (sub.daysRemaining <= 3) {
      daysBadge = `<span class="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30">In ${sub.daysRemaining} days</span>`;
    } else {
      daysBadge = `<span class="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-semibold">In ${sub.daysRemaining} days</span>`;
    }

    return `
      <div class="p-3.5 rounded-xl bg-slate-900/60 border border-white/5 hover:border-white/15 transition space-y-2">
        <div class="flex items-center justify-between gap-2">
          <div class="truncate">
            <h4 class="text-xs font-bold text-white truncate">${escapeHtml(sub.name)}</h4>
            <span class="text-[10px] text-slate-400">${sub.examDate}</span>
          </div>
          ${daysBadge}
        </div>

        <div class="space-y-1">
          <div class="flex items-center justify-between text-[11px] text-slate-400">
            <span>Preparation</span>
            <span class="font-bold text-slate-200">${sub.prepPercentage}%</span>
          </div>
          <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div class="bg-indigo-500 h-1.5 rounded-full transition-all duration-300" style="width: ${sub.prepPercentage}%"></div>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function renderPriorityTable(analyzed) {
  const tbody = document.getElementById("priorityTableBody");
  if (!tbody) return;

  if (analyzed.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="9" class="px-5 py-8 text-center text-slate-500 text-xs">
          No subjects registered. Click "+ Add Subject" to calculate priority scores.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = analyzed.map((sub, index) => {
    return `
      <tr class="hover:bg-white/5 transition">
        <!-- Rank & Subject -->
        <td class="px-5 py-4 font-medium text-white flex items-center gap-3">
          <span class="w-6 h-6 rounded-md bg-white/5 flex items-center justify-center text-xs font-mono text-slate-400 font-bold">
            #${index + 1}
          </span>
          <div>
            <div class="font-bold text-slate-100">${escapeHtml(sub.name)}</div>
            <div class="text-[11px] text-slate-400">ID: ${sub.id}</div>
          </div>
        </td>

        <!-- Exam Date -->
        <td class="px-4 py-4 text-xs text-slate-300 font-mono">
          ${sub.examDate}
        </td>

        <!-- Days Left -->
        <td class="px-4 py-4 text-xs">
          ${sub.daysRemaining <= 0 ?
            `<span class="font-bold text-rose-400 animate-pulse">TODAY</span>` :
            sub.daysRemaining <= 3 ? 
            `<span class="font-bold text-rose-400">${sub.daysRemaining} days</span>` : 
            `<span class="text-slate-300">${sub.daysRemaining} days</span>`
          }
        </td>

        <!-- Difficulty -->
        <td class="px-4 py-4 text-xs">
          <span class="px-2 py-0.5 rounded-md font-semibold ${
            sub.difficulty === 'Hard' ? 'text-rose-300 bg-rose-500/10' :
            sub.difficulty === 'Medium' ? 'text-amber-300 bg-amber-500/10' :
            'text-emerald-300 bg-emerald-500/10'
          }">
            ${sub.difficulty} (${sub.difficultyScore})
          </span>
        </td>

        <!-- Preparation % -->
        <td class="px-4 py-4 text-xs font-semibold text-slate-200">
          <div class="flex items-center gap-2">
            <span>${sub.prepPercentage}%</span>
            <div class="w-12 bg-slate-800 rounded-full h-1.5 hidden sm:block">
              <div class="bg-cyan-500 h-1.5 rounded-full" style="width: ${sub.prepPercentage}%"></div>
            </div>
          </div>
        </td>

        <!-- Preparation Gap -->
        <td class="px-4 py-4 text-xs text-rose-300 font-mono font-bold">
          ${sub.prepGap}%
        </td>

        <!-- Score Breakdown Tooltip Details -->
        <td class="px-4 py-4 text-[11px] text-slate-400 font-mono">
          <div class="flex flex-col gap-0.5">
            <span>Urg: ${(sub.urgency * 0.4).toFixed(1)} <span class="text-slate-500">(${sub.urgency}×0.4)</span></span>
            <span>Dif: ${(sub.difficultyScore * 0.25).toFixed(1)} <span class="text-slate-500">(${sub.difficultyScore}×0.25)</span></span>
            <span>Gap: ${(sub.prepGap * 0.35).toFixed(1)} <span class="text-slate-500">(${sub.prepGap}×0.35)</span></span>
          </div>
        </td>

        <!-- Priority Score -->
        <td class="px-4 py-4 text-center">
          <span class="text-base font-extrabold font-mono text-white bg-slate-900/80 px-2.5 py-1 rounded-lg border border-white/10">
            ${sub.priorityScore}
          </span>
        </td>

        <!-- Priority Level -->
        <td class="px-5 py-4 text-right">
          <span class="text-xs px-2.5 py-1 rounded-full font-bold ${sub.badgeClass} inline-block">
            ${sub.priorityLevel}
          </span>
        </td>
      </tr>
    `;
  }).join("");
}

function renderSubjectCards(analyzed) {
  const container = document.getElementById("subjectsCardGrid");
  if (!container) return;

  if (analyzed.length === 0) {
    container.innerHTML = `
      <div class="col-span-full text-center py-12 text-slate-500 glass-panel rounded-2xl p-6">
        <i data-lucide="book-plus" class="w-12 h-12 mx-auto mb-3 opacity-30 text-indigo-400"></i>
        <h4 class="text-base font-semibold text-slate-300">No subjects currently registered</h4>
        <p class="text-xs text-slate-400 mt-1">Add your college semester subjects to begin adaptive priority scheduling.</p>
        <button onclick="openSubjectModal()" class="mt-4 px-4 py-2 rounded-xl btn-glow text-xs font-semibold text-white">
          + Add Subject
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = analyzed.map(sub => {
    return `
      <div class="glass-panel p-5 rounded-2xl border border-white/10 space-y-4 hover:border-indigo-500/30 transition flex flex-col justify-between">
        
        <div>
          <!-- Card Header: Title & Badges -->
          <div class="flex items-start justify-between gap-2">
            <div>
              <h3 class="text-base font-bold text-white brand-font">${escapeHtml(sub.name)}</h3>
              <p class="text-xs text-slate-400 mt-0.5 flex items-center gap-1.5">
                <i data-lucide="calendar" class="w-3.5 h-3.5"></i>
                <span>Exam: ${sub.examDate}</span>
                <span class="text-slate-500">&bull;</span>
                <span class="${sub.daysRemaining <= 3 ? 'text-rose-400 font-bold' : 'text-slate-400'}">
                  ${sub.daysRemaining <= 0 ? 'TODAY' : `${sub.daysRemaining} days left`}
                </span>
              </p>
            </div>
            <span class="text-xs px-2 py-0.5 rounded-full font-bold ${sub.badgeClass}">
              ${sub.priorityLevel}
            </span>
          </div>

          <!-- Metrics Grid -->
          <div class="grid grid-cols-3 gap-2 mt-4 text-center">
            <div class="p-2 rounded-xl bg-slate-900/60 border border-white/5">
              <span class="text-[10px] text-slate-400 uppercase font-semibold block">Difficulty</span>
              <span class="text-xs font-bold text-slate-200 mt-0.5 block">${sub.difficulty}</span>
            </div>
            <div class="p-2 rounded-xl bg-slate-900/60 border border-white/5">
              <span class="text-[10px] text-slate-400 uppercase font-semibold block">Prep Gap</span>
              <span class="text-xs font-bold text-rose-300 mt-0.5 block">${sub.prepGap}%</span>
            </div>
            <div class="p-2 rounded-xl bg-slate-900/60 border border-white/5">
              <span class="text-[10px] text-slate-400 uppercase font-semibold block">Priority</span>
              <span class="text-xs font-bold text-indigo-300 mt-0.5 block">${sub.priorityScore}</span>
            </div>
          </div>

          <!-- Preparation Slider Preview -->
          <div class="mt-4 space-y-1.5">
            <div class="flex items-center justify-between text-xs">
              <span class="text-slate-400">Current Preparation</span>
              <span class="font-bold text-white">${sub.prepPercentage}%</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
              <div class="bg-gradient-to-r from-indigo-500 to-cyan-400 h-2 rounded-full" style="width: ${sub.prepPercentage}%"></div>
            </div>
          </div>
        </div>

        <!-- Card Footer Actions -->
        <div class="flex items-center justify-end gap-2 pt-3 border-t border-white/5">
          <button onclick="editSubject('${escapeHtml(sub.id)}')" class="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-semibold text-slate-300 border border-white/5 flex items-center gap-1 transition">
            <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
            <span>Edit</span>
          </button>
          <button onclick="deleteSubject('${escapeHtml(sub.id)}')" class="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-xs font-semibold text-rose-300 border border-rose-500/20 flex items-center gap-1 transition">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
            <span>Delete</span>
          </button>
        </div>

      </div>
    `;
  }).join("");
}

function renderAICoachSection() {
  const insights = getAICoachInsights();

  const triageContainer = document.getElementById("coachPrimaryTriageCard");
  if (triageContainer) {
    triageContainer.innerHTML = `
      <div class="flex items-start gap-3">
        <div class="p-2.5 rounded-xl ${insights.triage.level === 'urgent' ? 'bg-rose-500/20 text-rose-400' : 'bg-indigo-500/20 text-indigo-400'} flex-shrink-0">
          <i data-lucide="alert-octagon" class="w-6 h-6"></i>
        </div>
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <h3 class="text-sm font-bold text-white">${escapeHtml(insights.triage.title)}</h3>
            ${insights.triage.score ? `<span class="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30">Priority ${insights.triage.score}</span>` : ''}
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">${escapeHtml(insights.triage.message)}</p>
        </div>
      </div>
    `;
  }

  const rhythmContainer = document.getElementById("coachRhythmCard");
  if (rhythmContainer) {
    rhythmContainer.innerHTML = `
      <div class="flex items-start gap-3">
        <div class="p-2.5 rounded-xl bg-cyan-500/20 text-cyan-400 flex-shrink-0">
          <i data-lucide="shuffle" class="w-6 h-6"></i>
        </div>
        <div class="space-y-1">
          <h3 class="text-sm font-bold text-white">${escapeHtml(insights.rhythm.title)}</h3>
          <p class="text-xs text-slate-300 leading-relaxed">${escapeHtml(insights.rhythm.message)}</p>
        </div>
      </div>
    `;
  }

  const subjectCardsList = document.getElementById("coachSubjectCardsList");
  if (subjectCardsList) {
    if (insights.subjectAdvice.length === 0) {
      subjectCardsList.innerHTML = `<p class="text-xs text-slate-500 text-center py-4">No subject advice available.</p>`;
    } else {
      subjectCardsList.innerHTML = insights.subjectAdvice.map(item => {
        return `
          <div class="p-4 rounded-xl bg-slate-900/60 border border-white/5 space-y-2">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-white">${escapeHtml(item.name)}</span>
                <span class="text-[10px] px-2 py-0.5 rounded-full font-bold ${item.badgeClass}">${item.priorityLevel}</span>
              </div>
              <div class="text-[11px] text-slate-400">
                <span>In ${item.daysRemaining} days</span> &bull; <span>${item.prepPercentage}% ready</span>
              </div>
            </div>
            
            <div class="flex items-center gap-2 text-[11px] text-indigo-300">
              <i data-lucide="tag" class="w-3 h-3 text-indigo-400"></i>
              <span>Recommended Drill: <strong>${item.recommendedLabel}</strong></span>
            </div>

            <p class="text-xs text-slate-300 leading-relaxed bg-slate-950/50 p-2.5 rounded-lg border border-white/5">
              ${escapeHtml(item.actionableTip)}
            </p>
          </div>
        `;
      }).join("");
    }
  }
}

// ==========================================
// 9. SUBJECT CRUD MODAL & HANDLERS
// ==========================================

function openSubjectModal(subjectToEdit = null) {
  const modal = document.getElementById("subjectModal");
  const form = document.getElementById("subjectForm");
  const formId = document.getElementById("subjectFormId");
  const nameInput = document.getElementById("subjectNameInput");
  const dateInput = document.getElementById("subjectDateInput");
  const prepSlider = document.getElementById("subjectPrepSlider");
  const modalTitle = document.getElementById("subjectModalTitle");
  const submitText = document.getElementById("subjectSubmitBtnText");

  const todayStr = getTodayDateStr();
  dateInput.min = todayStr;

  if (subjectToEdit) {
    modalTitle.innerHTML = `<i data-lucide="edit-3" class="w-4 h-4 text-indigo-400"></i> Edit Subject`;
    submitText.innerText = "Update Subject";
    formId.value = subjectToEdit.id;
    nameInput.value = subjectToEdit.name;
    dateInput.value = subjectToEdit.examDate;
    prepSlider.value = subjectToEdit.prepPercentage || 0;
    updatePrepSliderDisplay(prepSlider.value);

    const radio = document.querySelector(`input[name="difficultyRadio"][value="${subjectToEdit.difficulty}"]`);
    if (radio) radio.checked = true;
  } else {
    modalTitle.innerHTML = `<i data-lucide="book-plus" class="w-4 h-4 text-indigo-400"></i> Add New Subject`;
    submitText.innerText = "Save Subject";
    form.reset();
    formId.value = "";
    
    const d = new Date();
    d.setDate(d.getDate() + 7);
    dateInput.value = formatLocalDate(d);
    
    prepSlider.value = 40;
    updatePrepSliderDisplay(40);
  }

  updateDaysPreview(dateInput.value);
  dateInput.oninput = (e) => updateDaysPreview(e.target.value);
  dateInput.onchange = (e) => updateDaysPreview(e.target.value);

  modal.classList.remove("hidden");
  nameInput.focus();

  if (window.lucide) window.lucide.createIcons();
}

function updateDaysPreview(dateValue) {
  const preview = document.getElementById("examDaysPreview");
  if (!preview) return;

  if (!dateValue) {
    preview.innerText = "Select an exam date";
    return;
  }

  const days = calculateDaysRemaining(dateValue);

  if (days < 0) {
    preview.innerText = "⚠️ Selected date is in the past";
    preview.className = "text-[11px] text-rose-400";
  } else if (days === 0) {
    preview.innerText = "⚠️ Exam is scheduled for TODAY";
    preview.className = "text-[11px] text-rose-400 font-bold";
  } else if (days === 1) {
    preview.innerText = "Exam is TOMORROW (1 day left)";
    preview.className = "text-[11px] text-amber-300 font-bold";
  } else {
    preview.innerText = `Exam is in ${days} days`;
    preview.className = "text-[11px] text-indigo-300";
  }
}

function closeSubjectModal() {
  const modal = document.getElementById("subjectModal");
  if (modal) modal.classList.add("hidden");
}

function updatePrepSliderDisplay(val) {
  const el = document.getElementById("prepSliderValue");
  if (el) el.innerText = `${val}%`;
}

function handleSubjectSubmit(e) {
  e.preventDefault();
  
  const idInput = document.getElementById("subjectFormId").value;
  const name = document.getElementById("subjectNameInput").value.trim();
  const examDate = document.getElementById("subjectDateInput").value;
  const prepPercentage = Math.max(0, Math.min(100, parseInt(document.getElementById("subjectPrepSlider").value, 10) || 0));
  
  const diffRadio = document.querySelector('input[name="difficultyRadio"]:checked');
  const difficulty = diffRadio ? diffRadio.value : "Medium";

  if (!name || !examDate) {
    showToast("Please fill in subject name and exam date.", "error");
    return;
  }

  if (idInput) {
    const existingIndex = state.subjects.findIndex(s => s.id === idInput);
    if (existingIndex !== -1) {
      state.subjects[existingIndex] = {
        ...state.subjects[existingIndex],
        name,
        examDate,
        difficulty,
        prepPercentage,
      };
      showToast(`Subject "${name}" updated.`, "success");
    }
  } else {
    const newSubject = {
      id: `sub_${Date.now()}`,
      name,
      examDate,
      difficulty,
      prepPercentage,
      color: "#6366f1",
    };
    state.subjects.push(newSubject);
    showToast(`Subject "${name}" added to study roster.`, "success");
  }

  closeSubjectModal();
  saveState();
  generateStudyPlan(true);
  renderApp();
}

function editSubject(subjectId) {
  const subject = state.subjects.find(s => s.id === subjectId);
  if (subject) {
    openSubjectModal(subject);
  }
}

function deleteSubject(subjectId) {
  const subject = state.subjects.find(s => s.id === subjectId);
  const name = subject ? subject.name : "subject";

  if (confirm(`Are you sure you want to remove "${name}" from your study plan?`)) {
    state.subjects = state.subjects.filter(s => s.id !== subjectId);
    state.todayTasks = state.todayTasks.filter(t => t.subjectId !== subjectId);
    saveState();
    generateStudyPlan(true);
    renderApp();
    showToast(`Removed "${name}". Plan recalculated.`, "info");
  }
}

function resetToSampleSubjects() {
  if (confirm("Reset to default Computer Science college exam subjects?")) {
    state.subjects = getSampleSubjects("cs-college");
    saveState();
    generateStudyPlan(false);
    renderApp();
    showToast("Loaded default exam subjects.", "success");
  }
}

function loadSamplePreset(presetKey) {
  const menu = document.getElementById("presetsMenu");
  if (menu) menu.classList.add("hidden");

  state.subjects = getSampleSubjects(presetKey);
  saveState();
  generateStudyPlan(false);
  renderApp();
  showToast("Loaded sample exam preset plan!", "success");
}

// ==========================================
// 10. DAILY HOURS ADJUSTER & MODAL
// ==========================================

function openHoursSliderModal() {
  const modal = document.getElementById("hoursModal");
  const slider = document.getElementById("modalHoursSlider");
  const display = document.getElementById("modalHoursDisplay");

  slider.value = state.dailyHours;
  display.innerText = `${state.dailyHours} hrs`;
  modal.classList.remove("hidden");
}

function closeHoursSliderModal() {
  const modal = document.getElementById("hoursModal");
  if (modal) modal.classList.add("hidden");
}

function updateModalHoursDisplay(val) {
  document.getElementById("modalHoursDisplay").innerText = `${val} hrs`;
}

function saveModalHours() {
  const val = parseFloat(document.getElementById("modalHoursSlider").value);
  state.dailyHours = Math.max(1.0, Math.min(12.0, val));
  closeHoursSliderModal();
  saveState();
  recalculateAdaptivePlan();
}

function adjustDailyHours(delta) {
  const newHours = Math.max(1.0, Math.min(12.0, Math.round((state.dailyHours + delta) * 10) / 10));
  if (newHours !== state.dailyHours) {
    state.dailyHours = newHours;
    saveState();
    recalculateAdaptivePlan();
  }
}

// ==========================================
// 11. POMODORO TIMER MODULE
// ==========================================

function setTimerDuration(mins) {
  if (timerInterval) clearInterval(timerInterval);
  timerRunning = false;
  timerSeconds = mins * 60;
  updateTimerDisplay();
  updateTimerButtonState();
}

function startPomodoroForTaskId(taskId) {
  const task = state.todayTasks.find(t => t.id === taskId);
  if (!task) return;
  startPomodoroForTask(`${task.subjectName} - ${task.label}`, task.duration);
}

function startPomodoroForTask(taskTitle, durationMinutes = 25) {
  switchTab("timerTab");
  const topicEl = document.getElementById("timerActiveTopic");
  if (topicEl) topicEl.innerText = taskTitle;

  const timerMins = Math.min(60, durationMinutes);
  setTimerDuration(timerMins);
  togglePomodoroTimer();
  showToast(`Focus timer started for "${taskTitle}" (${timerMins}m)`, "info");
}

function togglePomodoroTimer() {
  if (timerRunning) {
    clearInterval(timerInterval);
    timerRunning = false;
  } else {
    timerRunning = true;
    timerInterval = setInterval(() => {
      if (timerSeconds > 0) {
        timerSeconds--;
        updateTimerDisplay();
      } else {
        clearInterval(timerInterval);
        timerRunning = false;
        updateTimerButtonState();
        showToast("⏰ Pomodoro session complete! Great work.", "success");
        if (typeof confetti === "function") {
          confetti({ particleCount: 35, spread: 50 });
        }
      }
    }, 1000);
  }
  updateTimerButtonState();
}

function resetPomodoroTimer() {
  if (timerInterval) clearInterval(timerInterval);
  timerRunning = false;
  timerSeconds = 25 * 60;
  updateTimerDisplay();
  updateTimerButtonState();
}

function updateTimerDisplay() {
  const mins = Math.floor(timerSeconds / 60);
  const secs = timerSeconds % 60;
  const display = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  const el = document.getElementById("timerDisplay");
  if (el) el.innerText = display;
}

function updateTimerButtonState() {
  const btn = document.getElementById("timerToggleBtn");
  const icon = document.getElementById("timerToggleIcon");
  const text = document.getElementById("timerToggleText");

  if (!btn || !icon || !text) return;

  if (timerRunning) {
    text.innerText = "Pause Session";
    icon.setAttribute("data-lucide", "pause");
  } else {
    text.innerText = "Start Session";
    icon.setAttribute("data-lucide", "play");
  }

  if (window.lucide) window.lucide.createIcons();
}

// ==========================================
// 12. EXPORT TO MARKDOWN
// ==========================================

function exportPlanMarkdown() {
  const analyzed = getAnalyzedSubjects();
  let md = `# 🎓 SmartStudy AI — Master Daily Study Plan\n`;
  md += `**Date**: ${new Date().toLocaleDateString()} | **Daily Study Target**: ${state.dailyHours} hours\n\n`;

  md += `## 📊 Priority Matrix Summary\n\n`;
  md += `| Subject | Exam Date | Days Left | Difficulty | Prep % | Priority Score | Priority Level |\n`;
  md += `| :--- | :--- | :---: | :---: | :---: | :---: | :---: |\n`;
  analyzed.forEach(s => {
    md += `| ${s.name} | ${s.examDate} | ${s.daysRemaining} | ${s.difficulty} | ${s.prepPercentage}% | **${s.priorityScore}** | ${s.priorityLevel} |\n`;
  });

  md += `\n## 📝 Today's Scheduled Tasks\n\n`;
  state.todayTasks.forEach((t) => {
    const status = t.completed ? "x" : " ";
    md += `- [${status}] **${t.timeSlot}** (${t.duration}m) — **${t.subjectName}** [${t.label}]: ${t.title}\n`;
  });

  md += `\n---\n*Generated by SmartStudy AI — Adaptive Exam Intelligence*\n`;

  const blob = new Blob([md], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `smartstudy_plan_${getTodayDateStr()}.md`;
  a.click();
  URL.revokeObjectURL(url);
  showToast("Study plan exported as Markdown!", "success");
}

// ==========================================
// 13. TAB NAVIGATION & NOTIFICATIONS
// ==========================================

function switchTab(tabId) {
  document.querySelectorAll(".nav-tab").forEach(tab => {
    if (tab.dataset.target === tabId) {
      tab.classList.add("active");
      tab.classList.remove("text-slate-400");
    } else {
      tab.classList.remove("active");
      tab.classList.add("text-slate-400");
    }
  });

  document.querySelectorAll(".tab-pane").forEach(pane => {
    if (pane.id === tabId) {
      pane.classList.remove("hidden");
      pane.classList.add("active");
    } else {
      pane.classList.add("hidden");
      pane.classList.remove("active");
    }
  });

  if (window.lucide) window.lucide.createIcons();
}

function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast-msg pointer-events-auto flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-2xl border text-xs font-semibold backdrop-blur-md transition-all ${
    type === "success" ? "bg-emerald-950/90 text-emerald-200 border-emerald-500/40" :
    type === "error" ? "bg-rose-950/90 text-rose-200 border-rose-500/40" :
    type === "warning" ? "bg-amber-950/90 text-amber-200 border-amber-500/40" :
    "bg-slate-900/90 text-indigo-200 border-indigo-500/40"
  }`;

  let icon = "info";
  if (type === "success") icon = "check-circle";
  if (type === "error") icon = "alert-circle";
  if (type === "warning") icon = "alert-triangle";

  toast.innerHTML = `
    <i data-lucide="${icon}" class="w-4 h-4 flex-shrink-0"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  if (window.lucide) window.lucide.createIcons();

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px) scale(0.95)";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (typeof str !== "string") return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ==========================================
// 14. DOM INITIALIZATION
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
  loadState();
  renderApp();

  document.querySelectorAll(".nav-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.target;
      if (target) switchTab(target);
    });
  });

  const presetsBtn = document.getElementById("presetsBtn");
  const presetsMenu = document.getElementById("presetsMenu");
  if (presetsBtn && presetsMenu) {
    presetsBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      presetsMenu.classList.toggle("hidden");
    });
    document.addEventListener("click", () => {
      presetsMenu.classList.add("hidden");
    });
  }

  const decBtn = document.getElementById("decrementHoursBtn");
  const incBtn = document.getElementById("incrementHoursBtn");
  if (decBtn) decBtn.addEventListener("click", () => adjustDailyHours(-0.5));
  if (incBtn) incBtn.addEventListener("click", () => adjustDailyHours(0.5));

  const addBtn = document.getElementById("openAddSubjectBtn");
  if (addBtn) addBtn.addEventListener("click", () => openSubjectModal());

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeSubjectModal();
      closeHoursSliderModal();
    }
  });

  if (window.lucide) window.lucide.createIcons();
});
