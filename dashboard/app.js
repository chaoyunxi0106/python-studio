const state = {
  catalog: null,
  current: null,
  hintLevel: 1,
  view: "practice",
  history: null,
  companion: null,
  maintenance: null,
  chatSessionId: null,
  chatSessions: [],
  chatSessionTitle: "",
  chatMessages: [],
  chatContexts: [],
  activeSubjectId: localStorage.getItem("pythonStudioSubject") || "python",
  workshopSessionId: null,
  workshopSelectedNodeId: null,
  workshopGraph: null,
  historySubview: "overview",
  settingsSubview: "ai",
  workshopSubview: "workshop",
  appMode: "course",
};

const elements = {
  loading: document.querySelector("#loading"),
  brandTitle: document.querySelector("#brandTitle"),
  brandTagline: document.querySelector("#brandTagline"),
  workspaceSelect: document.querySelector("#workspaceSelect"),
  exerciseView: document.querySelector("#exerciseView"),
  roadmap: document.querySelector("#roadmap"),
  app: document.querySelector("#app"),
  rail: document.querySelector("#rail"),
  railHideButton: document.querySelector("#railHideButton"),
  railShowButton: document.querySelector("#railShowButton"),
  mapExpandButton: document.querySelector("#mapExpandButton"),
  railMapTitle: document.querySelector("#railMapTitle"),
  railMapEyebrow: document.querySelector("#railMapEyebrow"),
  railGraph: document.querySelector("#railGraph"),
  courseButton: document.querySelector("#courseButton"),
  courseMenu: document.querySelector("#courseMenu"),
  modeList: document.querySelector("#modeList"),
  exerciseCount: document.querySelector("#exerciseCount"),
  statCompletion: document.querySelector("#statCompletion"),
  statMinutes: document.querySelector("#statMinutes"),
  statToday: document.querySelector("#statToday"),
  exerciseStage: document.querySelector("#exerciseStage"),
  exerciseTitle: document.querySelector("#exerciseTitle"),
  exerciseSummary: document.querySelector("#exerciseSummary"),
  exerciseStatus: document.querySelector("#exerciseStatus"),
  exerciseMinutes: document.querySelector("#exerciseMinutes"),
  exerciseProgress: document.querySelector("#exerciseProgress"),
  exerciseProgressLabel: document.querySelector("#exerciseProgressLabel"),
  exercisePath: document.querySelector("#exercisePath"),
  readmePath: document.querySelector("#readmePath"),
  starterPath: document.querySelector("#starterPath"),
  testPath: document.querySelector("#testPath"),
  copyExercisePathButton: document.querySelector("#copyExercisePathButton"),
  copyContextButton: document.querySelector("#copyContextButton"),
  concepts: document.querySelector("#concepts"),
  exerciseDoc: document.querySelector("#exerciseDoc"),
  attemptCount: document.querySelector("#attemptCount"),
  checkButton: document.querySelector("#checkButton"),
  hintButton: document.querySelector("#hintButton"),
  nextPracticeButton: document.querySelector("#nextPracticeButton"),
  assessmentPanel: document.querySelector("#assessmentPanel"),
  assessmentItems: document.querySelector("#assessmentItems"),
  hintBox: document.querySelector("#hintBox"),
  hintLabel: document.querySelector("#hintLabel"),
  hintText: document.querySelector("#hintText"),
  checkOutput: document.querySelector("#checkOutput"),
  knowledgeTitle: document.querySelector("#knowledgeTitle"),
  knowledgeSummary: document.querySelector("#knowledgeSummary"),
  knowledgeSyntax: document.querySelector("#knowledgeSyntax"),
  knowledgePoints: document.querySelector("#knowledgePoints"),
  knowledgePitfall: document.querySelector("#knowledgePitfall"),
  aiContext: document.querySelector("#aiContext"),
  playbookGrid: document.querySelector("#playbookGrid"),
  historyView: document.querySelector("#historyView"),
  historyEyebrow: document.querySelector("#historyEyebrow"),
  historyTitle: document.querySelector("#historyTitle"),
  historySummary: document.querySelector("#historySummary"),
  companionView: document.querySelector("#companionView"),
  settingsView: document.querySelector("#settingsView"),
  workshopView: document.querySelector("#workshopView"),
  workshopEyebrow: document.querySelector("#workshopEyebrow"),
  workshopTitle: document.querySelector("#workshopTitle"),
  workshopSummary: document.querySelector("#workshopSummary"),
  settingsEyebrow: document.querySelector("#settingsEyebrow"),
  settingsTitle: document.querySelector("#settingsTitle"),
  settingsSummary: document.querySelector("#settingsSummary"),
  historyAttempts: document.querySelector("#historyAttempts"),
  historyPassRate: document.querySelector("#historyPassRate"),
  historyLatest: document.querySelector("#historyLatest"),
  historyList: document.querySelector("#historyList"),
  practiceReviewList: document.querySelector("#practiceReviewList"),
  loadCurrentToChatButton: document.querySelector("#loadCurrentToChatButton"),
  loadCurrentExerciseButton: document.querySelector("#loadCurrentExerciseButton"),
  analyzeCurrentButton: document.querySelector("#analyzeCurrentButton"),
  workshopModeButton: document.querySelector("#workshopModeButton"),
  companionWidget: document.querySelector("#companionWidget"),
  widgetToggle: document.querySelector("#widgetToggle"),
  widgetPanel: document.querySelector("#widgetPanel"),
  widgetClose: document.querySelector("#widgetClose"),
  widgetMessages: document.querySelector("#widgetMessages"),
  widgetContext: document.querySelector("#widgetContext"),
  widgetForm: document.querySelector("#widgetForm"),
  widgetInput: document.querySelector("#widgetInput"),
  widgetLoadCurrent: document.querySelector("#widgetLoadCurrent"),
  widgetAnalyze: document.querySelector("#widgetAnalyze"),
  historyTrend: document.querySelector("#historyTrend"),
  historyTrendNote: document.querySelector("#historyTrendNote"),
  historyRecent: document.querySelector("#historyRecent"),
  companionStatus: document.querySelector("#companionStatus"),
  companionEyebrow: document.querySelector("#companionEyebrow"),
  companionTitle: document.querySelector("#companionTitle"),
  companionSummary: document.querySelector("#companionSummary"),
  companionMessage: document.querySelector("#companionMessage"),
  analyzeButton: document.querySelector("#analyzeButton"),
  analysisSummary: document.querySelector("#analysisSummary"),
  masteryList: document.querySelector("#masteryList"),
  weaknessList: document.querySelector("#weaknessList"),
  practiceList: document.querySelector("#practiceList"),
  maintenanceRecords: document.querySelector("#maintenanceRecords"),
  maintenanceGenerated: document.querySelector("#maintenanceGenerated"),
  maintenanceMistakes: document.querySelector("#maintenanceMistakes"),
  maintenanceSize: document.querySelector("#maintenanceSize"),
  aiUsageSummary: document.querySelector("#aiUsageSummary"),
  backupList: document.querySelector("#backupList"),
  createBackupButton: document.querySelector("#createBackupButton"),
  generatedExerciseList: document.querySelector("#generatedExerciseList"),
  chatPanel: document.querySelector(".chat-panel"),
  chatMessages: document.querySelector("#chatMessages"),
  chatInput: document.querySelector("#chatInput"),
  chatForm: document.querySelector("#chatForm"),
  sendChatButton: document.querySelector("#sendChatButton"),
  chatContextList: document.querySelector("#chatContextList"),
  clearChatContextButton: document.querySelector("#clearChatContextButton"),
  historyExerciseSelect: document.querySelector("#historyExerciseSelect"),
  loadHistoryContextButton: document.querySelector("#loadHistoryContextButton"),
  newChatButton: document.querySelector("#newChatButton"),
  chatSessionSelect: document.querySelector("#chatSessionSelect"),
  chatTitleInput: document.querySelector("#chatTitleInput"),
  renameChatButton: document.querySelector("#renameChatButton"),
  clearChatButton: document.querySelector("#clearChatButton"),
  deleteChatButton: document.querySelector("#deleteChatButton"),
  aiSettingsForm: document.querySelector("#aiSettingsForm"),
  aiSettingsStatus: document.querySelector("#aiSettingsStatus"),
  aiApiKeyInput: document.querySelector("#aiApiKeyInput"),
  aiBaseUrlInput: document.querySelector("#aiBaseUrlInput"),
  aiModelInput: document.querySelector("#aiModelInput"),
  aiTimeoutInput: document.querySelector("#aiTimeoutInput"),
  aiHistoryLimitInput: document.querySelector("#aiHistoryLimitInput"),
  clearAiKeyInput: document.querySelector("#clearAiKeyInput"),
  saveAiSettingsButton: document.querySelector("#saveAiSettingsButton"),
  testAiSettingsButton: document.querySelector("#testAiSettingsButton"),
  aiSettingsMessage: document.querySelector("#aiSettingsMessage"),
  studioSettingsForm: document.querySelector("#studioSettingsForm"),
  studioNameInput: document.querySelector("#studioNameInput"),
  studioTaglineInput: document.querySelector("#studioTaglineInput"),
  studioDomainInput: document.querySelector("#studioDomainInput"),
  studioSettingsMessage: document.querySelector("#studioSettingsMessage"),
  subjectCompilerForm: document.querySelector("#subjectCompilerForm"),
  compilerSubjectInput: document.querySelector("#compilerSubjectInput"),
  compilerModeInput: document.querySelector("#compilerModeInput"),
  compilerMaterialInput: document.querySelector("#compilerMaterialInput"),
  compileSubjectButton: document.querySelector("#compileSubjectButton"),
  compilerMessage: document.querySelector("#compilerMessage"),
  subjectList: document.querySelector("#subjectList"),
  blueprintView: document.querySelector("#blueprintView"),
  thoughtGraph: document.querySelector("#thoughtGraph"),
  workshopMessages: document.querySelector("#workshopMessages"),
  workshopForm: document.querySelector("#workshopForm"),
  workshopInput: document.querySelector("#workshopInput"),
  workshopStatus: document.querySelector("#workshopStatus"),
  nodeDetail: document.querySelector("#nodeDetail"),
  fitGraphButton: document.querySelector("#fitGraphButton"),
};

// Buttons can carry an inline icon; update only the label so the icon survives.
function setButtonLabel(button, text) {
  if (!button) {
    return;
  }
  const label = button.querySelector(".btn-label");
  if (label) {
    label.textContent = text;
  } else {
    button.textContent = text;
  }
}

function getButtonLabel(button) {
  if (!button) {
    return "";
  }
  const label = button.querySelector(".btn-label");
  return label ? label.textContent : button.textContent;
}

async function api(path, options = {}) {
  return window.StudioCore.api(path, options, {
    subjectId: state.activeSubjectId,
    mode: state.appMode,
  });
}

function escapeHtml(value) {
  return window.StudioCore.escapeHtml(value);
}

function renderInline(value) {
  return window.StudioCore.renderInline(value);
}

function renderMarkdown(markdown) {
  return window.StudioCore.renderMarkdown(markdown);
}

function stageById(stageId) {
  return state.catalog.roadmap.stages.find((stage) => stage.id === stageId);
}

function formatDateTime(value) {
  if (!value) {
    return "暂无";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function statusText(exercise) {
  if (exercise.completed) {
    return "已通过";
  }
  if (exercise.attempts > 0) {
    return "已有尝试";
  }
  return "待完成";
}

function renderStats() {
  const stats = state.catalog.stats;
  elements.statCompletion.textContent = `${stats.percent}%`;
  elements.statMinutes.textContent = `${stats.practice_minutes}/${stats.total_minutes}`;
  elements.statToday.textContent = String(stats.today_passed);
  elements.exerciseCount.textContent = `${stats.completed}/${stats.total} 关`;
}

const ROADMAP_STATE_KEY = "python-studio.roadmap.expanded";
let roadmapExpandedModules = null;

function defaultExpandedModules() {
  const target = state.current?.id || state.catalog?.progress?.last_exercise;
  const exercise = state.catalog?.exercises?.find((item) => item.id === target);
  if (exercise) {
    return new Set([exercise.stage]);
  }
  const firstActive = state.catalog?.roadmap?.stages?.find(
    (stage) => (stage.exercise_count || 0) > 0,
  );
  return new Set(firstActive ? [firstActive.id] : []);
}

function getExpandedModules() {
  if (!roadmapExpandedModules) {
    let stored = null;
    try {
      const raw = window.localStorage.getItem(ROADMAP_STATE_KEY);
      stored = raw ? JSON.parse(raw) : null;
    } catch {
      stored = null;
    }
    roadmapExpandedModules =
      Array.isArray(stored) ? new Set(stored) : defaultExpandedModules();
  }
  return new Set(roadmapExpandedModules);
}

function saveExpandedModules(next) {
  roadmapExpandedModules = new Set(next);
  try {
    window.localStorage.setItem(
      ROADMAP_STATE_KEY,
      JSON.stringify([...roadmapExpandedModules]),
    );
  } catch {
    /* storage unavailable, keep in-memory state only */
  }
}

function renderRoadmap() {
  elements.roadmap.replaceChildren();

  for (const stage of state.catalog.roadmap.stages) {
    const exercises = state.catalog.exercises.filter(
      (exercise) => exercise.stage === stage.id,
    );

    const completed = exercises.filter((exercise) => exercise.completed).length;
    const isActiveModule = exercises.length > 0;
    const isCurrentModule = Boolean(
      state.current && exercises.some((exercise) => exercise.id === state.current.id),
    );
    const isComplete = isActiveModule && completed === exercises.length;
    const expandedModules = getExpandedModules();
    const isExpanded = isActiveModule && expandedModules.has(stage.id);

    const section = document.createElement("section");
    section.className = "roadmap-module";
    if (isActiveModule) {
      section.classList.add("active-module");
      if (!isExpanded) {
        section.classList.add("collapsed");
      }
    } else {
      section.classList.add("planned-stage", "collapsed");
    }
    if (isCurrentModule) {
      section.classList.add("current-module");
    }

    const header = document.createElement("button");
    header.type = "button";
    header.className = "module-toggle";
    header.setAttribute("aria-expanded", String(isExpanded));

    const moduleCode = document.createElement("span");
    moduleCode.className = "module-code";
    moduleCode.textContent = String(stage.module).padStart(2, "0");

    const moduleCopy = document.createElement("span");
    moduleCopy.className = "module-copy";
    const title = document.createElement("span");
    title.className = "module-title";
    title.textContent = stage.title.replace(/^模块\s*\d+\s*·\s*/, "");
    const description = document.createElement("span");
    description.className = "module-description";
    if (isActiveModule) {
      description.textContent = `${completed}/${exercises.length} 关 · ${
        isComplete ? "已完成" : isCurrentModule ? "当前模块" : "进行中"
      }`;
    } else {
      description.textContent = `${stage.planned_levels || 0} 关规划`;
    }
    moduleCopy.append(title, description);

    const chevron = document.createElement("span");
    chevron.className = "module-chevron";
    chevron.textContent = isExpanded ? "−" : "+";
    header.append(moduleCode, moduleCopy, chevron);

    const nav = document.createElement("div");
    nav.className = "exercise-nav module-levels";
    nav.hidden = !isExpanded;

    if (exercises.length) {
      exercises.forEach((exercise, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "exercise-link";
        if (exercise.completed) {
          button.classList.add("completed");
        }
        if (state.current && exercise.id === state.current.id) {
          button.classList.add("active");
        }
        button.addEventListener("click", () => {
          const expanded = getExpandedModules();
          expanded.add(stage.id);
          saveExpandedModules(expanded);
          switchView("practice");
          loadExercise(exercise.id);
          closeRailAfterSelect();
        });

        const levelIndex = document.createElement("span");
        levelIndex.className = "level-index";
        levelIndex.textContent = String(index + 1).padStart(2, "0");
        const exerciseCopy = document.createElement("span");
        exerciseCopy.className = "exercise-link-copy";
        const exerciseTitle = document.createElement("span");
        exerciseTitle.className = "exercise-link-title";
        exerciseTitle.textContent = exercise.title;
        const exerciseSummary = document.createElement("span");
        exerciseSummary.className = "exercise-link-summary";
        exerciseSummary.textContent = `${exercise.minutes} 分钟 · ${statusText(exercise)}`;
        exerciseCopy.append(exerciseTitle, exerciseSummary);
        button.append(levelIndex, exerciseCopy);
        nav.append(button);
      });
    } else {
      const placeholder = document.createElement("div");
      placeholder.className = "stage-placeholder";
      const status = document.createElement("strong");
      status.textContent = "规划中";
      const description = document.createElement("span");
      description.textContent = stage.description;
      placeholder.append(status, description);
      nav.append(placeholder);
    }

    header.addEventListener("click", () => {
      const willExpand = section.classList.contains("collapsed");
      const expanded = getExpandedModules();
      if (willExpand) {
        expanded.add(stage.id);
      } else {
        expanded.delete(stage.id);
      }
      saveExpandedModules(expanded);
      section.classList.toggle("collapsed", !willExpand);
      nav.hidden = !willExpand;
      header.setAttribute("aria-expanded", String(willExpand));
      chevron.textContent = willExpand ? "−" : "+";
    });

    section.append(header, nav);
    elements.roadmap.append(section);
  }
}

// The companion AI can replace the built-in collaboration playbook per lesson.
// Tool calls from the chat can rewrite exercises, so the page reloads after them.
async function refreshAfterAuthoring() {
  try {
    await refreshCatalog();
    if (state.current) {
      state.current = await api(
        `/api/exercise?id=${encodeURIComponent(state.current.id)}`,
      );
      renderExercise();
    }
  } catch {
    /* the edited exercise may have moved; the catalog refresh is enough */
  }
  await loadHistory();
}

function renderAuthoredMentor(mentor) {
  const grid = elements.playbookGrid;
  if (!grid) {
    return;
  }
  if (!state.playbookDefaultHtml) {
    state.playbookDefaultHtml = grid.innerHTML;
  }
  const steps = Array.isArray(mentor?.steps) ? mentor.steps : [];
  if (!steps.length) {
    if (grid.dataset.authored === "1") {
      grid.innerHTML = state.playbookDefaultHtml;
      delete grid.dataset.authored;
    }
    return;
  }
  grid.replaceChildren();
  steps.forEach((step, index) => {
    const article = document.createElement("article");
    article.className = "playbook-step";
    const number = document.createElement("span");
    number.className = "step-number";
    number.textContent = String(index + 1).padStart(2, "0");
    const title = document.createElement("h4");
    title.textContent = step.title || "";
    article.append(number, title);
    if (step.body) {
      const body = document.createElement("p");
      body.textContent = step.body;
      article.append(body);
    }
    grid.append(article);
  });
  grid.dataset.authored = "1";
  if (mentor.intro) {
    elements.aiContext.textContent = mentor.intro;
  }
}

function renderExercise() {
  const exercise = state.current;
  const stage = stageById(exercise.stage);

  elements.exerciseStage.textContent = stage ? stage.title : "当前练习";
  elements.exerciseTitle.textContent = exercise.title;
  elements.exerciseSummary.textContent = exercise.summary;
  elements.exerciseMinutes.textContent = `${exercise.minutes} 分钟预算`;
  elements.exerciseStatus.textContent = statusText(exercise);
  elements.exerciseStatus.classList.toggle("passed", Boolean(exercise.completed));
  const moduleExercises = state.catalog.exercises.filter(
    (item) => item.stage === exercise.stage,
  );
  const moduleDone = moduleExercises.filter((item) => item.completed).length;
  const modulePercent = moduleExercises.length
    ? Math.round((moduleDone / moduleExercises.length) * 100)
    : 0;
  elements.exerciseProgress.style.width = `${modulePercent}%`;
  elements.exerciseProgressLabel.textContent = `模块进度 ${moduleDone}/${moduleExercises.length} 关`;
  elements.nextPracticeButton.hidden = !(
    exercise.generated && exercise.completed
  );
  const exerciseRoot = `exercises/${exercise.path}`;
  elements.exercisePath.textContent = `${exerciseRoot}/`;
  elements.readmePath.textContent = `${exerciseRoot}/README.md`;
  elements.starterPath.textContent = `${exerciseRoot}/starter.py`;
  elements.testPath.textContent = `${exerciseRoot}/test_exercise.py`;

  elements.concepts.replaceChildren();
  for (const concept of exercise.concepts || []) {
    const chip = document.createElement("span");
    chip.className = "concept-chip";
    chip.textContent = concept;
    elements.concepts.append(chip);
  }

  elements.exerciseDoc.innerHTML = renderMarkdown(exercise.readme || "");
  renderAssessment(exercise.assessment);
  const knowledge = exercise.knowledge || {};
  elements.knowledgeTitle.textContent = knowledge.title || exercise.title;
  elements.knowledgeSummary.textContent = knowledge.summary || exercise.summary;
  elements.knowledgeSyntax.textContent = knowledge.syntax || "无补充语法";
  elements.knowledgePitfall.textContent =
    knowledge.pitfall || "先阅读输入和输出契约，再做最小修改。";
  elements.knowledgePoints.replaceChildren();
  for (const point of knowledge.points || []) {
    const item = document.createElement("li");
    item.textContent = point;
    elements.knowledgePoints.append(item);
  }
  elements.aiContext.textContent = `当前关卡是「${exercise.title}」，重点：${
    (exercise.concepts || []).join("、") || "基础操作"
  }。先自己预测结果，再让 AI 给提示；模型生成代码后，必须运行本关测试并解释关键表达式。`;
  renderAuthoredMentor(exercise.mentor);


  const attempts = exercise.progress?.attempts || 0;
  elements.attemptCount.textContent = `${attempts} 次尝试`;
  elements.hintBox.hidden = true;
  state.hintLevel = 1;

  const previousOutput = exercise.progress?.last_output;
  elements.checkOutput.classList.toggle(
    "failed",
    Boolean(attempts && exercise.progress?.passed === false),
  );
  elements.checkOutput.textContent =
    previousOutput || "完成 starter.py 后点「运行」。";
  setButtonLabel(
    elements.checkButton,
    exercise.assessment ? "提交" : "运行",
  );
}

function renderAssessment(assessment) {
  elements.assessmentItems.replaceChildren();
  if (!assessment?.items?.length) {
    elements.assessmentPanel.hidden = true;
    return;
  }
  elements.assessmentPanel.hidden = false;
  for (const item of assessment.items) {
    const card = document.createElement("article");
    card.className = "assessment-item";
    card.dataset.itemId = item.id;
    const question = document.createElement("h4");
    question.textContent = item.question;
    card.append(question);
    if (item.type === "multiple_choice") {
      for (const [index, option] of (item.options || []).entries()) {
        const label = document.createElement("label");
        label.className = "assessment-option";
        const input = document.createElement("input");
        input.type = "radio";
        input.name = `assessment-${item.id}`;
        input.value = String(index);
        const text = document.createElement("span");
        text.textContent = option;
        label.append(input, text);
        card.append(label);
      }
    } else {
      const textarea = document.createElement("textarea");
      textarea.placeholder = "写出你的解释、推理或证明过程";
      card.append(textarea);
    }
    elements.assessmentItems.append(card);
  }
}

function collectAssessmentAnswers() {
  const answers = {};
  for (const card of elements.assessmentItems.querySelectorAll(
    ".assessment-item",
  )) {
    const itemId = card.dataset.itemId;
    const selected = card.querySelector('input[type="radio"]:checked');
    const textarea = card.querySelector("textarea");
    if (selected) {
      answers[itemId] = Number(selected.value);
    } else if (textarea) {
      answers[itemId] = textarea.value.trim();
    }
  }
  return answers;
}

async function runAssessment() {
  elements.checkButton.disabled = true;
    setButtonLabel(elements.checkButton, "评阅中...");
  elements.checkOutput.classList.remove("failed");
  elements.checkOutput.textContent = "正在评价答案...";
  try {
    const result = await api("/api/assessment/check", {
      method: "POST",
      body: JSON.stringify({
        exercise_id: state.current.id,
        answers: collectAssessmentAnswers(),
      }),
    });
    elements.checkOutput.textContent = `${result.output}\n\n${
      result.passed ? "PASSED" : "FAILED"
    } · ${result.assessment.passed_count}/${result.assessment.total}`;
    elements.checkOutput.classList.toggle("failed", !result.passed);
    await refreshCatalog();
    state.current = await api(
      `/api/exercise?id=${encodeURIComponent(state.current.id)}`,
    );
    renderExercise();
  } catch (error) {
    elements.checkOutput.textContent = error.message;
    elements.checkOutput.classList.add("failed");
  } finally {
    elements.checkButton.disabled = false;
    setButtonLabel(elements.checkButton, "提交");
  }
}

async function refreshCatalog() {
  state.catalog = await api("/api/catalog");
  renderStats();
  renderRoadmap();
}

async function loadExercise(exerciseId) {
  elements.loading.hidden = false;
  elements.exerciseView.hidden = true;
  try {
    const exercise = await api(`/api/exercise?id=${encodeURIComponent(exerciseId)}`);
    state.current = exercise;
    await refreshCatalog();
    renderExercise();
    if (state.history) {
      renderHistory();
    }
    elements.loading.hidden = true;
    elements.exerciseView.hidden = false;
  } catch (error) {
    elements.loading.textContent = error.message;
  }
}

async function runCheck() {
  if (!state.current) {
    return;
  }
  if (state.current.assessment) {
    await runAssessment();
    return;
  }
  elements.checkButton.disabled = true;
    setButtonLabel(elements.checkButton, "运行中...");
  elements.checkOutput.classList.remove("failed");
  elements.checkOutput.textContent = "正在运行自动检查...";

  try {
    const result = await api(
      `/api/check?id=${encodeURIComponent(state.current.id)}`,
      { method: "POST" },
    );
    elements.checkOutput.textContent = `${result.output}\n\n${
      result.passed ? "PASSED" : "FAILED"
    } in ${result.duration_seconds}s`;
    elements.checkOutput.classList.toggle("failed", !result.passed);
    await refreshCatalog();
    const refreshed = await api(
      `/api/exercise?id=${encodeURIComponent(state.current.id)}`,
    );
    state.current = refreshed;
    renderStats();
    renderRoadmap();
    renderExercise();
    await loadHistory();
  } catch (error) {
    elements.checkOutput.textContent = error.message;
    elements.checkOutput.classList.add("failed");
  } finally {
    elements.checkButton.disabled = false;
    setButtonLabel(elements.checkButton, "运行");
  }
}

async function showHint() {
  if (!state.current) {
    return;
  }
  try {
    const payload = await api(
      `/api/hint?id=${encodeURIComponent(state.current.id)}&level=${state.hintLevel}`,
    );
    elements.hintLabel.textContent = `提示 ${payload.level}/${payload.total}`;
    elements.hintText.textContent = payload.hint;
    elements.hintBox.hidden = false;
    state.hintLevel = Math.min(state.hintLevel + 1, payload.total);
  } catch (error) {
    elements.hintText.textContent = error.message;
    elements.hintBox.hidden = false;
  }
}

async function copyPath(button = elements.copyExercisePathButton) {
  if (!state.current) {
    return;
  }
  const text = state.current.directory;
  const originalLabel = getButtonLabel(button);
  try {
    await navigator.clipboard.writeText(text);
    setButtonLabel(button, "已复制");
  } catch {
    setButtonLabel(button, "复制失败");
  }
  window.setTimeout(() => {
    setButtonLabel(button, originalLabel);
  }, 1600);
}

function compactChatContext(context) {
  return {
    exercise_id: context.exercise_id,
    attempt_id: context.attempt_id,
    title: context.title,
    summary: context.summary,
    knowledge: context.knowledge,
    instructions: context.instructions,
    my_code: context.my_code,
    task_results: context.task_results,
    test_output_excerpt: context.test_output_excerpt,
    ai_review: context.ai_review,
    last_checked: context.last_checked,
    passed: context.passed,
  };
}

async function fetchExerciseContext({ exerciseId, attemptId }) {
  const params = new URLSearchParams();
  if (exerciseId) {
    params.set("exercise_id", exerciseId);
  }
  if (attemptId) {
    params.set("attempt_id", attemptId);
  }
  return api(`/api/context/export?${params}`);
}

async function copyCurrentContext() {
  if (!state.current) {
    return;
  }
  const original = getButtonLabel(elements.copyContextButton);
  elements.copyContextButton.disabled = true;
  try {
    const payload = await fetchExerciseContext({
      exerciseId: state.current.id,
    });
    await navigator.clipboard.writeText(payload.markdown);
    setButtonLabel(elements.copyContextButton, "已复制");
  } catch (error) {
    setButtonLabel(elements.copyContextButton, "复制失败");
  } finally {
    window.setTimeout(() => {
      elements.copyContextButton.disabled = false;
      setButtonLabel(elements.copyContextButton, original);
    }, 1200);
  }
}

async function copyAttemptContext(attemptId, button) {
  const original = button.textContent;
  button.disabled = true;
  try {
    const payload = await fetchExerciseContext({ attemptId });
    await navigator.clipboard.writeText(payload.markdown);
    button.textContent = "已复制";
  } catch (error) {
    button.textContent = "复制失败";
  } finally {
    window.setTimeout(() => {
      button.disabled = false;
      button.textContent = original;
    }, 1200);
  }
}

function renderChatContexts() {
  const targets = [elements.chatContextList, elements.widgetContext].filter(
    Boolean,
  );
  for (const target of targets) {
    target.replaceChildren();
    if (!state.chatContexts.length) {
      const empty = document.createElement("span");
      empty.className = "practice-source";
      empty.textContent = "尚未载入题目";
      target.append(empty);
      continue;
    }
    for (const context of state.chatContexts) {
      const chip = document.createElement("div");
      chip.className = "chat-context-chip";
      const title = document.createElement("span");
      title.textContent = context.title || context.exercise_id;
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "context-remove";
      remove.textContent = "×";
      remove.title = "移除这道题";
      remove.addEventListener("click", () =>
        removeChatContext(context.attempt_id || context.exercise_id),
      );
      chip.append(title, remove);
      target.append(chip);
    }
  }
}

async function setChatContexts(
  contexts,
  { persist = true, marker = null } = {},
) {
  state.chatContexts = contexts.map(compactChatContext);
  elements.clearChatContextButton.hidden = !state.chatContexts.length;
  renderChatContexts();
  if (persist && state.chatSessionId) {
    await api("/api/chat/session", {
      method: "POST",
      body: JSON.stringify({
        action: "set_context",
        session_id: state.chatSessionId,
        context: { items: state.chatContexts },
        marker,
      }),
    });
    if (marker) {
      state.chatMessages = await api(
        `/api/chat?session_id=${state.chatSessionId}`,
      ).then((payload) => payload.messages || []);
      renderChatMessages();
    }
  }
}

async function loadAttemptIntoChat(attemptId) {
  const payload = await fetchExerciseContext({ attemptId });
  const context = compactChatContext(payload.context);
  const identity = context.attempt_id || context.exercise_id;
  state.chatContexts = state.chatContexts.filter(
    (item) => (item.attempt_id || item.exercise_id) !== identity,
  );
  state.chatContexts.push(context);
  state.chatContexts = state.chatContexts.slice(-4);
  await setChatContexts(state.chatContexts, {
    marker: `载入题目：${context.title || context.exercise_id}`,
  });
  switchView("companion");
  elements.chatInput.focus();
}

async function loadCurrentExerciseIntoChat() {
  if (!state.current) {
    return;
  }
  const payload = await fetchExerciseContext({
    exerciseId: state.current.id,
  });
  const context = compactChatContext(payload.context);
  const identity = context.attempt_id || context.exercise_id;
  state.chatContexts = state.chatContexts.filter(
    (item) => (item.attempt_id || item.exercise_id) !== identity,
  );
  state.chatContexts.push(context);
  state.chatContexts = state.chatContexts.slice(-4);
  await setChatContexts(state.chatContexts, {
    marker: `载入题目：${context.title || context.exercise_id}`,
  });
}

async function populateHistoryExerciseSelect() {
  if (!state.history) {
    state.history = await api("/api/learning/history");
  }
  elements.historyExerciseSelect.replaceChildren();
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "选择历史题目";
  elements.historyExerciseSelect.append(placeholder);
  for (const attempt of state.history.attempts || []) {
    const option = document.createElement("option");
    option.value = String(attempt.id);
    option.textContent = `${formatDateTime(attempt.checked_at)} · ${
      attempt.title
    } · ${attempt.passed ? "通过" : "未通过"}`;
    elements.historyExerciseSelect.append(option);
  }
}

async function loadSelectedHistoryContext() {
  const attemptId = Number(elements.historyExerciseSelect.value);
  if (!attemptId) {
    return;
  }
  await loadAttemptIntoChat(attemptId);
}

async function removeChatContext(identity) {
  const removed = state.chatContexts.find(
    (item) => (item.attempt_id || item.exercise_id) === identity,
  );
  state.chatContexts = state.chatContexts.filter(
    (item) => (item.attempt_id || item.exercise_id) !== identity,
  );
  await setChatContexts(state.chatContexts, {
    marker: removed ? `移除题目：${removed.title}` : null,
  });
}

async function clearAllChatContexts() {
  state.chatContexts = [];
  await setChatContexts([], { marker: "清除全部题目上下文" });
}

function renderChatMessages() {
  const targets = [elements.chatMessages, elements.widgetMessages].filter(
    Boolean,
  );
  for (const target of targets) {
    target.replaceChildren();
    if (!state.chatMessages.length) {
      renderEmpty(
        target,
        "可以直接提问，也可以先载入一道题目的压缩上下文。",
      );
      continue;
    }
    for (const message of state.chatMessages) {
      const bubble = document.createElement("article");
      bubble.className = `chat-message ${message.role}`;
      if (message.role === "assistant") {
        bubble.innerHTML = renderMarkdown(message.content || "");
      } else {
        bubble.textContent = message.content || "";
      }
      target.append(bubble);
    }
    target.scrollTop = target.scrollHeight;
  }
}

async function loadChat(sessionId = state.chatSessionId) {
  try {
    if (sessionId) {
      state.chatSessionId = sessionId;
    }
    const sessionsPayload = await api("/api/chat/sessions");
    state.chatSessions = sessionsPayload.sessions || [];
    const targetSessionId =
      state.chatSessionId && state.chatSessions.some(
        (session) => session.id === state.chatSessionId,
      )
        ? state.chatSessionId
        : state.chatSessions[0]?.id;
    if (!targetSessionId) {
      await startNewChat();
      return;
    }
    const payload = await api(`/api/chat?session_id=${targetSessionId}`);
    state.chatSessionId = payload.session_id;
    state.chatSessionTitle = payload.session?.title || "伴学对话";
    state.chatMessages = payload.messages || [];
    elements.chatTitleInput.value = state.chatSessionTitle;
    const storedContext = payload.session?.context;
    const contexts = Array.isArray(storedContext?.items)
      ? storedContext.items
      : storedContext
        ? [storedContext]
        : [];
    await setChatContexts(contexts, { persist: false });
    await populateHistoryExerciseSelect();
    renderChatSessions();
    renderChatMessages();
  } catch (error) {
    renderEmpty(elements.chatMessages, error.message);
  }
}

async function startNewChat() {
  try {
    const payload = await api("/api/chat/new", {
      method: "POST",
      body: JSON.stringify({
        title: "新的伴学对话",
        context: null,
      }),
    });
    state.chatSessionId = payload.session_id;
    state.chatSessionTitle = payload.session?.title || "新的伴学对话";
    state.chatMessages = [];
    await setChatContexts([], { persist: false });
    await loadChat();
    renderChatMessages();
    elements.chatInput.focus();
  } catch (error) {
    renderEmpty(elements.chatMessages, error.message);
  }
}

function renderChatSessions() {
  elements.chatSessionSelect.replaceChildren();
  for (const session of state.chatSessions) {
    const option = document.createElement("option");
    option.value = String(session.id);
    option.textContent = session.title;
    option.selected = session.id === state.chatSessionId;
    elements.chatSessionSelect.append(option);
  }
}

async function renameCurrentChat() {
  const title = elements.chatTitleInput.value.trim();
  if (!title || !state.chatSessionId) {
    return;
  }
  await api("/api/chat/session", {
    method: "POST",
    body: JSON.stringify({
      action: "rename",
      session_id: state.chatSessionId,
      title,
    }),
  });
  state.chatSessionTitle = title;
  await loadChat();
}

async function clearCurrentChat() {
  if (!state.chatSessionId || !window.confirm("清空当前对话的全部消息？")) {
    return;
  }
  await api("/api/chat/session", {
    method: "POST",
    body: JSON.stringify({
      action: "clear",
      session_id: state.chatSessionId,
    }),
  });
  state.chatMessages = [];
  renderChatMessages();
}

async function deleteCurrentChat() {
  if (!state.chatSessionId || !window.confirm("删除整个对话及其消息？")) {
    return;
  }
  await api("/api/chat/session", {
    method: "POST",
    body: JSON.stringify({
      action: "delete",
      session_id: state.chatSessionId,
    }),
  });
  state.chatSessionId = null;
  state.chatMessages = [];
  await loadChat();
}

async function sendChatMessage(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const input = form?.querySelector("textarea");
  const submit = form?.querySelector('button[type="submit"]');
  const message = input?.value.trim();
  if (!message || submit?.disabled) {
    return;
  }
  state.chatMessages.push({ role: "user", content: message });
  if (input) {
    input.value = "";
  }
  renderChatMessages();
  if (submit) {
    submit.disabled = true;
    submit.textContent = "思考中...";
  }
  try {
    const payload = await api("/api/chat/message", {
      method: "POST",
      body: JSON.stringify({
        session_id: state.chatSessionId,
        message,
        context: { items: state.chatContexts },
      }),
    });
    state.chatSessionId = payload.session_id;
    state.chatMessages.push(payload.message);
    renderChatMessages();
    const actions = Array.isArray(payload.actions) ? payload.actions : [];
    if (actions.length) {
      state.chatMessages.push({
        role: "assistant",
        content: actions
          .map((action) => `${action.ok ? "✓" : "✗"} ${action.summary}`)
          .join("\n"),
      });
      renderChatMessages();
      await refreshAfterAuthoring();
    }
  } catch (error) {
    state.chatMessages.push({
      role: "assistant",
      content: `请求失败：${error.message}`,
    });
    renderChatMessages();
  } finally {
    if (submit) {
      submit.disabled = false;
      submit.textContent = "发送";
    }
  }
}

function renderEmpty(container, text) {
  const empty = document.createElement("div");
  empty.className = "empty-state";
  empty.textContent = text;
  container.replaceChildren(empty);
}

function renderSetupRequired() {
  elements.exerciseView.hidden = true;
  elements.loading.hidden = false;
  elements.loading.replaceChildren();

  const panel = document.createElement("section");
  panel.className = "setup-empty";

  const eyebrow = document.createElement("p");
  eyebrow.className = "eyebrow";
  eyebrow.textContent = "首次使用";

  const title = document.createElement("h2");
  title.textContent = "从零创建你的第一门学习科目";

  const summary = document.createElement("p");
  summary.textContent =
    "当前发行版不内置课程和题目。请先配置 AI 服务，再输入学习目标或知识材料，由 AI 生成知识大纲、知识讲解和对应练习。";

  const steps = document.createElement("ol");
  for (const text of [
    "在“设置 > 模型”填写并保存 API 密钥。",
    "前往“工坊 > 编译”，填写科目名称和学习材料。",
    "生成课程蓝图并物化练习，随后即可开始学习。",
  ]) {
    const item = document.createElement("li");
    item.textContent = text;
    steps.append(item);
  }

  const actions = document.createElement("div");
  actions.className = "setup-empty-actions";

  const settingsButton = document.createElement("button");
  settingsButton.type = "button";
  settingsButton.className = "secondary-button";
  settingsButton.textContent = "配置 API";
  settingsButton.addEventListener("click", () => switchView("settings"));

  const compilerButton = document.createElement("button");
  compilerButton.type = "button";
  compilerButton.className = "primary-button";
  compilerButton.textContent = "创建学习科目";
  compilerButton.addEventListener("click", () => {
    switchView("workshop");
    switchSubview("workshop", "compiler");
  });

  actions.append(settingsButton, compilerButton);
  panel.append(eyebrow, title, summary, steps, actions);
  elements.loading.append(panel);
}

function renderHistoryOverview(payload) {
  if (!elements.historyTrend || !elements.historyRecent) {
    return;
  }
  const attempts = payload.attempts || [];
  elements.historyTrend.replaceChildren();
  elements.historyRecent.replaceChildren();

  if (!attempts.length) {
    elements.historyTrendNote.textContent = "暂无记录";
    renderEmpty(
      elements.historyTrend,
      "完成一次运行后，这里会显示每次通过的详情。",
    );
    renderEmpty(elements.historyRecent, "还没有运行记录。");
    return;
  }

  const recentWindow = [...attempts].slice(0, 24).reverse();
  const passed = recentWindow.filter((attempt) => attempt.passed).length;
  elements.historyTrendNote.textContent = `近 ${recentWindow.length} 次 · 通过 ${passed} 次`;

  const slowest = Math.max(
    ...recentWindow.map((attempt) => Number(attempt.duration_seconds) || 0),
    1,
  );
  for (const attempt of recentWindow) {
    const bar = document.createElement("span");
    bar.className = `trend-bar ${attempt.passed ? "passed" : "failed"}`;
    const seconds = Number(attempt.duration_seconds) || 0;
    bar.style.height = `${20 + Math.round((seconds / slowest) * 34)}px`;
    bar.title = `${formatDateTime(attempt.checked_at)} · ${
      attempt.passed ? "通过" : "未通过"
    } · ${seconds.toFixed(2)} 秒`;
    elements.historyTrend.append(bar);
  }

  for (const attempt of attempts.slice(0, 5)) {
    const row = document.createElement("article");
    row.className = `recent-item ${attempt.passed ? "passed" : "failed"}`;

    const open = document.createElement("button");
    open.type = "button";
    open.className = "recent-open";
    open.title = "打开这道题的练习";
    const title = document.createElement("span");
    title.className = "recent-title";
    title.textContent = attempt.title || attempt.exercise_id;
    const meta = document.createElement("span");
    meta.className = "recent-meta";
    const seconds = Number(attempt.duration_seconds) || 0;
    meta.textContent = `${formatDateTime(attempt.checked_at)} · ${
      attempt.passed ? "通过" : "未通过"
    } · ${seconds.toFixed(2)}s`;
    open.append(title, meta);
    open.addEventListener("click", () =>
      openAttemptInPractice(attempt.exercise_id),
    );

    const actions = document.createElement("div");
    actions.className = "recent-actions";
    const copyButton = document.createElement("button");
    copyButton.type = "button";
    copyButton.className = "micro-button";
    copyButton.textContent = "复制题目信息";
    copyButton.addEventListener("click", () =>
      copyAttemptContext(attempt.id, copyButton),
    );
    const chatButton = document.createElement("button");
    chatButton.type = "button";
    chatButton.className = "micro-button";
    chatButton.textContent = "载入到对话";
    chatButton.addEventListener("click", () => loadAttemptIntoChat(attempt.id));
    actions.append(copyButton, chatButton);

    row.append(open, actions);
    elements.historyRecent.append(row);
  }
}

async function openAttemptInPractice(exerciseId) {
  if (!exerciseId) {
    return;
  }
  switchView("practice");
  await loadExercise(exerciseId);
}

function renderHistory() {
  const payload = state.history;
  if (!payload) {
    return;
  }
  const { summary, attempts } = payload;
  elements.historyAttempts.textContent = String(summary.attempts);
  elements.historyPassRate.textContent = `${summary.pass_rate}%`;
  elements.historyLatest.textContent = formatDateTime(summary.latest_attempt_at);
  renderHistoryOverview(payload);

  const container = elements.practiceReviewList;
  if (!container) {
    return;
  }
  container.replaceChildren();
  if (!state.current) {
    renderEmpty(container, "先选择一道题目，这里会显示它的运行与审查记录。");
    return;
  }
  const reviewAttempts = attempts.filter(
    (attempt) => attempt.exercise_id === state.current.id,
  );
  if (!reviewAttempts.length) {
    renderEmpty(
      container,
      "这道题还没有记录。点一次「运行」，这里会保存结果、AI 审查、标准答案与代码快照。",
    );
    return;
  }

  for (const attempt of reviewAttempts) {
    const item = document.createElement("article");
    item.className = `history-entry ${attempt.passed ? "passed" : "failed"}`;

    const header = document.createElement("div");
    header.className = "history-entry-header";
    const title = document.createElement("h4");
    title.textContent = attempt.title;
    const time = document.createElement("span");
    time.className = "history-time";
    time.textContent = formatDateTime(attempt.checked_at);
    header.append(title, time);

    const meta = document.createElement("div");
    meta.className = "history-meta";
    const status = document.createElement("span");
    status.textContent = attempt.passed ? "通过" : "未通过";
    status.className = attempt.passed
      ? "history-status passed"
      : "history-status failed";
    const duration = document.createElement("span");
    duration.className = "history-duration";
    duration.textContent = `${attempt.duration_seconds.toFixed(2)} 秒`;
    const concepts = document.createElement("span");
    concepts.textContent = (attempt.concepts || []).join(" · ") || attempt.exercise_id;
    meta.append(status, duration, concepts);

    const taskResults = document.createElement("div");
    taskResults.className = "task-result-row";
    for (const task of attempt.task_results || []) {
      const chip = document.createElement("span");
      chip.className = `task-result-chip ${task.passed ? "passed" : "failed"}`;
      chip.textContent = `${task.passed ? "通过" : "失败"} · ${
        task.task_name || task.test_name
      }`;
      taskResults.append(chip);
    }

    // One action row, then a single disclosure for the rest.
    const actions = document.createElement("div");
    actions.className = "record-actions";

    const chatContextButton = document.createElement("button");
    chatContextButton.type = "button";
    chatContextButton.className = "micro-button";
    chatContextButton.textContent = "载入到对话";
    chatContextButton.addEventListener("click", () =>
      loadAttemptIntoChat(attempt.id),
    );

    const copyContextButton = document.createElement("button");
    copyContextButton.type = "button";
    copyContextButton.className = "micro-button";
    copyContextButton.textContent = "复制题目信息";
    copyContextButton.addEventListener("click", () =>
      copyAttemptContext(attempt.id, copyContextButton),
    );

    const analyzeButton = document.createElement("button");
    analyzeButton.type = "button";
    analyzeButton.className = "micro-button";
    analyzeButton.textContent = "复审";
    analyzeButton.addEventListener("click", () =>
      analyzeAttemptCode(attempt.id, analyzeButton),
    );

    actions.append(chatContextButton, copyContextButton);
    if (!attempt.passed || attempt.ai_analysis) {
      actions.append(analyzeButton);
    }

    const detail = document.createElement("details");
    detail.className = "record-detail";
    const detailSummary = document.createElement("summary");
    detailSummary.textContent = "详情：AI 审查 / 标准答案 / 代码与输出";
    detail.append(detailSummary);
    if (attempt.ai_analysis) {
      detail.append(renderAttemptAnalysis(attempt.ai_analysis));
    }

    const solution = document.createElement("details");
    solution.className = "history-log";
    const solutionSummary = document.createElement("summary");
    solutionSummary.textContent = "标准答案";
    const solutionPre = document.createElement("pre");
    solution.append(solutionSummary);
    if (attempt.standard_solution) {
      solutionPre.textContent = attempt.standard_solution;
      solution.append(solutionPre);
    } else {
      const missing = document.createElement("div");
      missing.className = "missing-solution";
      const message = document.createElement("p");
      message.textContent =
        "这道 AI 动态练习还没有保存标准答案。生成后会写入该练习目录。";
      const generateButton = document.createElement("button");
      generateButton.type = "button";
      generateButton.className = "micro-button";
      generateButton.textContent = "生成并保存标准答案";
      generateButton.addEventListener("click", () =>
        generateStandardSolution(attempt.id, generateButton),
      );
      missing.append(message, generateButton);
      solution.append(missing);
    }

    const output = document.createElement("details");
    output.className = "history-log";
    const outputSummary = document.createElement("summary");
    outputSummary.textContent = "原始测试输出";
    const outputPre = document.createElement("pre");
    outputPre.textContent = attempt.output || "No output.";
    output.append(outputSummary, outputPre);

    const code = document.createElement("details");
    code.className = "history-log";
    const codeSummary = document.createElement("summary");
    codeSummary.textContent = "当时代码快照";
    const codePre = document.createElement("pre");
    codePre.textContent = attempt.code_snapshot || "No code snapshot.";
    code.append(codeSummary, codePre);

    detail.append(solution, code, output);
    item.append(header, meta, taskResults, actions, detail);
    container.append(item);
  }
}

async function generateStandardSolution(attemptId, button) {
  button.disabled = true;
  button.textContent = "生成中...";
  try {
    await api(`/api/learning/generate-solution?id=${attemptId}`, {
      method: "POST",
    });
    await loadHistory();
  } catch (error) {
    button.textContent = error.message;
  }
}

function renderAttemptAnalysis(analysis) {
  const section = document.createElement("section");
  section.className = "attempt-ai-analysis";
  const title = document.createElement("h5");
  title.textContent = `AI 代码审查 · ${analysis.source}`;
  const summary = document.createElement("p");
  summary.textContent = analysis.summary || "";
  section.append(title, summary);
  const groups = [
    ["题目差距", analysis.requirement_gaps],
    ["代码问题", analysis.code_issues],
    ["隐藏风险", analysis.hidden_risks],
    ["已掌握", analysis.strengths],
  ];
  for (const [label, values] of groups) {
    if (!values?.length) {
      continue;
    }
    const group = document.createElement("div");
    const groupTitle = document.createElement("strong");
    groupTitle.textContent = label;
    const list = document.createElement("ul");
    for (const value of values) {
      const item = document.createElement("li");
      item.textContent = value;
      list.append(item);
    }
    group.append(groupTitle, list);
    section.append(group);
  }
  return section;
}

async function analyzeAttemptCode(attemptId, button) {
  button.disabled = true;
  button.textContent = "分析中...";
  try {
    await api(`/api/learning/analyze-attempt?id=${attemptId}`, {
      method: "POST",
    });
    await loadHistory();
  } catch (error) {
    button.textContent = error.message;
  }
}

async function loadHistory() {
  try {
    [state.history, state.maintenance] = await Promise.all([
      api("/api/learning/history"),
      api("/api/maintenance"),
    ]);
    renderHistory();
    renderMaintenance();
  } catch (error) {
    if (elements.practiceReviewList) {
      renderEmpty(elements.practiceReviewList, error.message);
    }
  }
}

function renderAnalysis(analysis) {
  elements.analysisSummary.textContent = analysis.summary || "暂无诊断摘要。";
  elements.weaknessList.replaceChildren();
  elements.practiceList.replaceChildren();

  if (analysis.provider_error) {
    const warning = document.createElement("p");
    warning.className = "analysis-summary analysis-warning";
    warning.textContent = `模型调用失败，已回退本地分析：${analysis.provider_error}`;
    elements.weaknessList.append(warning);
  }

  const weaknesses = analysis.weaknesses || [];
  if (!weaknesses.length) {
    renderEmpty(elements.weaknessList, "暂时没有识别到稳定的薄弱知识点。");
  } else {
    for (const weakness of weaknesses) {
      const card = document.createElement("article");
      card.className = "weakness-card";
      const header = document.createElement("div");
      header.className = "history-entry-header";
      const title = document.createElement("h4");
      title.textContent = weakness.knowledge_point || "未命名知识点";
      const estimate = document.createElement("span");
      estimate.className = "practice-source";
      estimate.textContent = `掌握度 ${weakness.mastery_estimate ?? 0}%`;
      header.append(title, estimate);

      const task = document.createElement("p");
      task.className = "evidence-line";
      task.textContent = weakness.task_name
        ? `具体失败函数：${weakness.task_name}`
        : "";
      const reason = document.createElement("p");
      reason.textContent = weakness.reason || "";
      const evidence = document.createElement("p");
      evidence.className = "evidence-line";
      evidence.textContent = weakness.evidence || "";
      const track = document.createElement("div");
      track.className = "mastery-track";
      const fill = document.createElement("span");
      fill.style.width = `${Math.max(0, Math.min(100, weakness.mastery_estimate || 0))}%`;
      fill.className =
        (weakness.mastery_estimate || 0) >= 75 ? "mastery-good" : "mastery-low";
      track.append(fill);
      card.append(header, task, reason, evidence, track);
      elements.weaknessList.append(card);
    }
  }

  const practiceItems = analysis.practice_items || [];
  if (!practiceItems.length) {
    renderEmpty(elements.practiceList, "当前没有需要生成的补练题。");
  } else {
    for (const item of practiceItems) {
      const card = document.createElement("article");
      card.className = "practice-card";
      const header = document.createElement("div");
      header.className = "practice-card-header";
      const title = document.createElement("h4");
      title.textContent = item.knowledge_point || "补练题";
      const source = document.createElement("span");
      source.className = "practice-source";
      source.textContent = `${item.difficulty || "基础"} · ${
        item.source_exercise_id || "同类补练"
      }`;
      header.append(title, source);

      const question = document.createElement("p");
      question.textContent = item.question || "";
      const actions = document.createElement("div");
      actions.className = "practice-actions";
      const startButton = document.createElement("button");
      startButton.type = "button";
      startButton.className = "primary-button";
    startButton.textContent = "再练";
      startButton.addEventListener("click", () =>
        startGeneratedPractice(item, startButton),
      );
      actions.append(startButton);
      card.append(header, question, actions);
      elements.practiceList.append(card);
    }
  }
}

function renderMastery(skills) {
  elements.masteryList.replaceChildren();
  if (!skills.length) {
    renderEmpty(
      elements.masteryList,
      "还没有测试级数据。完成一次运行后，这里会按知识点统计。",
    );
    return;
  }
  for (const skill of skills) {
    const card = document.createElement("article");
    card.className = "mastery-card";
    const header = document.createElement("div");
    header.className = "history-entry-header";
    const title = document.createElement("h4");
    title.textContent = skill.knowledge_point;
    const value = document.createElement("span");
    value.className = "practice-source";
    const trendLabels = {
      improving: "进步中",
      slipping: "近期退步",
      stable: "近期稳定",
      needs_attention: "仍需巩固",
      insufficient: "样本不足",
    };
    value.textContent = `${skill.mastery}% · ${
      trendLabels[skill.trend] || "持续追踪"
    }`;
    header.append(title, value);
    const track = document.createElement("div");
    track.className = "mastery-track";
    const fill = document.createElement("span");
    fill.style.width = `${skill.mastery}%`;
    fill.className = skill.mastery >= 75 ? "mastery-good" : "mastery-low";
    track.append(fill);
    card.append(header, track);
    elements.masteryList.append(card);
  }
}

function renderCompanion() {
  const payload = state.companion;
  if (!payload) {
    return;
  }
  const { status, analysis, skills, history } = payload;
  elements.companionStatus.textContent = status.configured
    ? `DeepSeek · ${status.model}`
    : "本地规则分析";
  elements.companionStatus.classList.toggle("local", !status.configured);
  const sampleNote =
    (history?.attempts || 0) < 3
      ? `当前只有 ${history?.attempts || 0} 次运行记录，诊断可信度有限。`
      : `已有 ${history?.attempts || 0} 次运行记录。`;
  elements.companionMessage.textContent = status.configured
    ? `${sampleNote} 将从本地服务端调用 DeepSeek，结合测试级证据生成诊断。`
    : `${sampleNote} 尚未配置 DeepSeek 密钥，当前使用结构化本地规则分析。`;
  if (analysis) {
    renderAnalysis(analysis);
  }
  renderMastery(skills || []);
}

async function loadCompanion() {
  try {
    state.companion = await api("/api/companion");
    renderCompanion();
  } catch (error) {
    elements.companionMessage.textContent = error.message;
  }
}

async function analyzeLearning() {
  elements.analyzeButton.disabled = true;
    elements.analyzeButton.textContent = "诊断中...";
    elements.companionMessage.textContent =
      "正在分析未处理的错题并生成补练，这个过程会调用模型...";
  try {
    state.companion = await api("/api/companion/analyze", { method: "POST" });
    renderCompanion();
    elements.companionMessage.textContent = `分析完成，来源：${
      state.companion.analysis.source
    }`;
  } catch (error) {
    elements.companionMessage.textContent = error.message;
  } finally {
    elements.analyzeButton.disabled = false;
    elements.analyzeButton.textContent = "诊断";
  }
}

async function markMistake(button, mistakeId) {
  button.disabled = true;
  button.textContent = "更新中...";
  try {
    await api(`/api/mistake/status?id=${mistakeId}&status=mastered`, {
      method: "POST",
    });
    await loadCompanion();
  } catch (error) {
    button.textContent = error.message;
  }
}

async function startGeneratedPractice(item, button) {
  button.disabled = true;
  const originalLabel = button.textContent;
  button.textContent = "生成中...";
  const params = new URLSearchParams({
    knowledge_point: item.knowledge_point || "基础补练",
    source_exercise_id: item.source_exercise_id || "",
    source_task: item.source_task || item.task_name || "",
  });
  try {
    const created = await api(`/api/practice/generate?${params}`, {
      method: "POST",
    });
    await refreshCatalog();
    switchView("practice");
    await loadExercise(created.id);
  } catch (error) {
    button.textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = originalLabel;
  }
}

async function generateNextPractice() {
  if (!state.current?.generated) {
    return;
  }
  const knowledge = state.current.knowledge || {};
  await startGeneratedPractice(
    {
      knowledge_point: knowledge.title || state.current.title,
      source_exercise_id: state.current.source_exercise_id || state.current.id,
      source_task: "",
    },
    elements.nextPracticeButton,
  );
}

function renderMaintenance() {
  const payload = state.maintenance;
  if (!payload) {
    return;
  }
  elements.maintenanceRecords.textContent = String(payload.history.attempts);
  elements.maintenanceGenerated.textContent = String(
    payload.generated_exercises.total,
  );
  elements.maintenanceMistakes.textContent = String(payload.mistakes.active);
  elements.maintenanceSize.textContent = `${Math.max(
    1,
    Math.round(payload.database_size_bytes / 1024),
  )} KB`;
  const usage = payload.ai_usage || {};
  const formatChars = (value) =>
    value < 1000 ? String(value) : `${Math.round(value / 1000)}K`;
  elements.aiUsageSummary.textContent = `AI 任务 ${usage.jobs || 0} 次 · 缓存命中 ${
    usage.cache_hits || 0
  } 次 · 输入 ${formatChars(usage.input_chars || 0)} 字符 · 输出 ${formatChars(
    usage.output_chars || 0,
  )} 字符`;
  elements.backupList.replaceChildren();
  for (const backup of payload.backups || []) {
    const item = document.createElement("div");
    item.className = "backup-item";
    const info = document.createElement("span");
    info.textContent = `${backup.name} · ${Math.max(
      1,
      Math.round(backup.size_bytes / 1024),
    )} KB`;
    const actions = document.createElement("div");
    actions.className = "backup-item-actions";
    const download = document.createElement("a");
    download.className = "micro-button";
    download.href = `/api/maintenance/backups/download?name=${encodeURIComponent(
      backup.name,
    )}`;
    download.textContent = "下载";
    const restore = document.createElement("button");
    restore.type = "button";
    restore.className = "micro-button danger";
    restore.textContent = "恢复";
    restore.addEventListener("click", () =>
      restoreBackup(backup.name, restore),
    );
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "micro-button danger";
    remove.textContent = "删除";
    remove.addEventListener("click", () =>
      deleteBackup(backup.name, remove),
    );
    actions.append(download, restore, remove);
    item.append(info, actions);
    elements.backupList.append(item);
  }
  if (!(payload.backups || []).length) {
    renderEmpty(elements.backupList, "还没有备份。");
  }
  elements.generatedExerciseList.replaceChildren();

  if (!payload.generated_items.length) {
    renderEmpty(
      elements.generatedExerciseList,
      "还没有由 AI 生成的正式补练关卡。",
    );
    return;
  }

  for (const item of payload.generated_items) {
    const card = document.createElement("article");
    card.className = "generated-exercise-item";
    const header = document.createElement("div");
    header.className = "history-entry-header";
    const title = document.createElement("h4");
    title.textContent = item.title;
    const status = document.createElement("span");
    status.className = "practice-source";
    status.textContent = item.archived ? "已归档" : "使用中";
    header.append(title, status);

    const meta = document.createElement("p");
    meta.className = "generated-meta";
    const scopeLabels = {
      course: "课程",
      workshop: "工坊",
      tutoring: "补习",
    };
    const location = [item.relative_path, item.level_id]
      .filter(Boolean)
      .join(" · ");
    meta.textContent = `${scopeLabels[item.scope] || "补习"} · ${
      item.knowledge_point || "综合"
    } · 运行 ${item.attempts} 次 · ${formatDateTime(item.created_at)}${
      location ? ` · ${location}` : ""
    }`;

    const actions = document.createElement("div");
    actions.className = "mistake-actions";
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "micro-button";
    toggle.textContent = item.archived ? "恢复" : "归档";
    toggle.addEventListener("click", () =>
      updateGeneratedExercise(item.id, item.archived ? "restore" : "archive"),
    );
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "micro-button danger";
    remove.textContent = "删除";
    remove.addEventListener("click", () => {
      if (window.confirm(`确定删除“${item.title}”及其目录吗？`)) {
        updateGeneratedExercise(item.id, "delete");
      }
    });
    actions.append(toggle, remove);
    card.append(header, meta, actions);
    elements.generatedExerciseList.append(card);
  }
}

async function loadMaintenance() {
  try {
    state.maintenance = await api("/api/maintenance");
    renderMaintenance();
  } catch (error) {
    renderEmpty(elements.generatedExerciseList, error.message);
  }
}

async function updateGeneratedExercise(exerciseId, action) {
  try {
    await api(
      `/api/maintenance/generated?id=${encodeURIComponent(
        exerciseId,
      )}&action=${action}`,
      { method: "POST" },
    );
    await loadMaintenance();
    await refreshCatalog();
  } catch (error) {
    renderEmpty(elements.generatedExerciseList, error.message);
  }
}

async function createBackup() {
  elements.createBackupButton.disabled = true;
  elements.createBackupButton.textContent = "备份中...";
  try {
    await api("/api/maintenance/backup", { method: "POST" });
    await loadMaintenance();
  } catch (error) {
    renderEmpty(elements.backupList, error.message);
  } finally {
    elements.createBackupButton.disabled = false;
    elements.createBackupButton.textContent = "新建备份";
  }
}

async function restoreBackup(name, button) {
  if (
    !window.confirm(
      `恢复备份“${name}”会替换当前学习数据库。系统会先自动创建保护性备份。继续吗？`,
    )
  ) {
    return;
  }
  button.disabled = true;
  button.textContent = "恢复中...";
  try {
    await api("/api/maintenance/restore", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    await loadHistory();
    await loadCompanion();
    await loadChat();
  } catch (error) {
    button.textContent = error.message;
  }
}

async function deleteBackup(name, button) {
  if (!window.confirm(`确定永久删除备份“${name}”吗？`)) {
    return;
  }
  button.disabled = true;
  button.textContent = "删除中...";
  try {
    await api("/api/maintenance/backup/delete", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    await loadMaintenance();
  } catch (error) {
    button.textContent = error.message;
  }
}

async function cleanupData(scope, button) {
  const labels = {
    records_30d: "清理 30 天前的运行记录",
    mastered_mistakes: "清理已掌握错题",
  };
  if (!window.confirm(`${labels[scope]}？此操作会直接修改本地数据。`)) {
    return;
  }
  const originalLabel = button.textContent;
  button.disabled = true;
  button.textContent = "清理中...";
  try {
    const result = await api(
      `/api/maintenance/cleanup?scope=${encodeURIComponent(scope)}`,
      { method: "POST" },
    );
    button.textContent = `已清理 ${result.deleted}`;
    await loadHistory();
    await loadCompanion();
  } catch (error) {
    button.textContent = error.message;
  } finally {
    window.setTimeout(() => {
      button.disabled = false;
      button.textContent = originalLabel;
    }, 1200);
  }
}

async function loadAiSettings() {
  try {
    const settings = await api("/api/settings/ai");
    elements.aiSettingsStatus.textContent = settings.configured
      ? "已配置"
      : "未配置";
    elements.aiSettingsStatus.classList.toggle("local", !settings.configured);
    elements.aiApiKeyInput.value = "";
    elements.aiBaseUrlInput.value = settings.base_url || "";
    elements.aiModelInput.value = settings.model || "";
    elements.aiTimeoutInput.value = settings.timeout_seconds || 60;
    elements.aiHistoryLimitInput.value = settings.history_limit || 40;
    elements.clearAiKeyInput.checked = false;
    elements.aiSettingsMessage.textContent = "";
  } catch (error) {
    elements.aiSettingsMessage.textContent = error.message;
  }
}

async function loadStudioIdentity() {
  try {
    const studio = await api("/api/studio");
    elements.brandTitle.textContent = studio.name;
    elements.brandTagline.textContent = studio.tagline;
    elements.studioNameInput.value = studio.name || "";
    elements.studioTaglineInput.value = studio.tagline || "";
    elements.studioDomainInput.value = studio.default_domain || "python";
  } catch (error) {
    elements.studioSettingsMessage.textContent = error.message;
  }
}

async function loadWorkspaces() {
  const payload = await api("/api/workspaces");
  elements.workspaceSelect.replaceChildren();
  for (const workspace of payload.workspaces) {
    const option = document.createElement("option");
    option.value = workspace.id;
    option.textContent = `${workspace.title} · ${workspace.mode}`;
    option.selected = workspace.id === state.activeSubjectId;
    elements.workspaceSelect.append(option);
  }
  if (
    !payload.workspaces.some((workspace) => workspace.id === state.activeSubjectId)
  ) {
    state.activeSubjectId = payload.workspaces[0]?.id || "python";
    localStorage.setItem("pythonStudioSubject", state.activeSubjectId);
  }
}

async function loadActiveSubject() {
  await loadStudioIdentity();
  await refreshCatalog();
  const preferred =
    state.catalog.progress.last_exercise ||
    state.catalog.exercises.find((exercise) => !exercise.completed)?.id ||
    state.catalog.exercises[0]?.id;
  if (preferred) {
    await loadExercise(preferred);
  } else {
    renderSetupRequired();
  }
}

async function switchSubject(subjectId) {
  state.activeSubjectId = subjectId;
  localStorage.setItem("pythonStudioSubject", subjectId);
  state.current = null;
  state.history = null;
  state.companion = null;
  state.maintenance = null;
  state.chatSessionId = null;
  state.chatMessages = [];
  state.chatContexts = [];
  await loadWorkspaces();
  await loadActiveSubject();
  await loadHistory();
  await loadCompanion();
  switchView("practice");
  toggleCourseMenu(false);
}

async function saveStudioSettings(event) {
  event.preventDefault();
  elements.studioSettingsMessage.textContent = "保存中...";
  try {
    const payload = await api("/api/studio", {
      method: "POST",
      body: JSON.stringify({
        name: elements.studioNameInput.value,
        tagline: elements.studioTaglineInput.value,
        default_domain: elements.studioDomainInput.value,
      }),
    });
    elements.brandTitle.textContent = payload.studio.name;
    elements.brandTagline.textContent = payload.studio.tagline;
    elements.studioSettingsMessage.textContent = "平台身份已保存。";
  } catch (error) {
    elements.studioSettingsMessage.textContent = error.message;
  }
}

async function saveAiSettings(event) {
  event.preventDefault();
  elements.saveAiSettingsButton.disabled = true;
  elements.saveAiSettingsButton.textContent = "保存中...";
  try {
    const payload = await api("/api/settings/ai", {
      method: "POST",
      body: JSON.stringify({
        api_key: elements.aiApiKeyInput.value,
        base_url: elements.aiBaseUrlInput.value,
        model: elements.aiModelInput.value,
        timeout_seconds: Number(elements.aiTimeoutInput.value),
        history_limit: Number(elements.aiHistoryLimitInput.value),
        clear_api_key: elements.clearAiKeyInput.checked,
      }),
    });
    elements.aiApiKeyInput.value = "";
    elements.clearAiKeyInput.checked = false;
    elements.aiSettingsStatus.textContent = payload.settings.configured
      ? "已配置"
      : "未配置";
    elements.aiSettingsStatus.classList.toggle(
      "local",
      !payload.settings.configured,
    );
    elements.aiSettingsMessage.textContent = "配置已保存，当前服务已生效。";
  } catch (error) {
    elements.aiSettingsMessage.textContent = error.message;
  } finally {
    elements.saveAiSettingsButton.disabled = false;
    elements.saveAiSettingsButton.textContent = "保存配置";
  }
}

async function testAiSettings() {
  elements.testAiSettingsButton.disabled = true;
  elements.testAiSettingsButton.textContent = "测试中...";
  elements.aiSettingsMessage.textContent = "正在发起最小模型请求...";
  try {
    const result = await api("/api/settings/ai/test", { method: "POST" });
    elements.aiSettingsMessage.textContent = `连接成功 · ${result.model} · ${result.latency_ms} ms`;
  } catch (error) {
    elements.aiSettingsMessage.textContent = error.message;
  } finally {
    elements.testAiSettingsButton.disabled = false;
    elements.testAiSettingsButton.textContent = "测试连接";
  }
}

async function loadSubjects() {
  try {
    const payload = await api("/api/subjects");
    elements.subjectList.replaceChildren();
    if (!payload.subjects.length) {
      renderEmpty(elements.subjectList, "还没有生成课程蓝图。");
      return;
    }
    for (const subject of payload.subjects) {
      const item = document.createElement("article");
      item.className = "subject-item";
      const title = document.createElement("h4");
      title.textContent = subject.title;
      const meta = document.createElement("p");
      meta.textContent = `${subject.mode} · ${formatDateTime(
        subject.created_at,
      )} · ${subject.summary}`;
      item.append(title, meta);
      item.addEventListener("click", () => loadSubjectBlueprint(subject.id));
      elements.subjectList.append(item);
    }
  } catch (error) {
    renderEmpty(elements.subjectList, error.message);
  }
}

function renderBlueprint(blueprint) {
  elements.blueprintView.replaceChildren();
  const header = document.createElement("header");
  header.className = "blueprint-header";
  const copy = document.createElement("div");
  const title = document.createElement("h3");
  title.textContent = blueprint.title;
  const summary = document.createElement("p");
  summary.className = "summary";
  summary.textContent = `${blueprint.mode} · ${blueprint.duration_weeks} 周 · ${blueprint.summary}`;
  copy.append(title, summary);
  const capstone = document.createElement("span");
  capstone.className = "provider-badge";
  capstone.textContent = "课程蓝图";
  header.append(copy, capstone);

  const strategy = document.createElement("p");
  strategy.className = "blueprint-objectives";
  strategy.textContent = `评价策略：${blueprint.assessment_strategy}`;
  const objectives = document.createElement("ul");
  objectives.className = "blueprint-objectives";
  for (const objective of blueprint.objectives || []) {
    const item = document.createElement("li");
    item.textContent = objective;
    objectives.append(item);
  }
  elements.blueprintView.append(header, strategy, objectives);

  for (const module of blueprint.modules || []) {
    const section = document.createElement("section");
    section.className = "blueprint-module";
    const heading = document.createElement("h4");
    heading.textContent = `${module.title} · ${module.goal}`;
    const concepts = document.createElement("p");
    concepts.className = "practice-source";
    concepts.textContent = (module.concepts || []).join(" · ");
    const activities = document.createElement("div");
    activities.className = "blueprint-activities";
    for (const activity of module.activities || []) {
      const card = document.createElement("div");
      card.className = "blueprint-activity";
      const name = document.createElement("strong");
      name.textContent = `${activity.title} [${activity.type}]`;
      const detail = document.createElement("span");
      detail.textContent = `${activity.objective} 交付物：${activity.deliverable}`;
      card.append(name, detail);
      activities.append(card);
    }
    section.append(heading, concepts, activities);
    elements.blueprintView.append(section);
  }
  const capstoneSection = document.createElement("p");
  capstoneSection.className = "privacy-note";
  capstoneSection.textContent = `综合成果：${blueprint.capstone}`;
  elements.blueprintView.append(capstoneSection);
}

async function loadSubjectBlueprint(subjectId) {
  try {
    const subject = await api(`/api/subject?id=${subjectId}`);
    renderBlueprint(subject.blueprint);
    switchSubview("compilerSubtabs", "blueprint");
  } catch (error) {
    elements.compilerMessage.textContent = error.message;
  }
}

async function compileSubject(event) {
  event.preventDefault();
  const subject = elements.compilerSubjectInput.value.trim();
  const material = elements.compilerMaterialInput.value.trim();
  if (!subject && !material) {
    elements.compilerMessage.textContent = "请填写科目或知识材料。";
    return;
  }
  elements.compileSubjectButton.disabled = true;
  elements.compileSubjectButton.textContent = "生成中...";
  elements.compilerMessage.textContent = "正在分析材料并设计学习场景...";
  try {
    const result = await api("/api/subjects/compile", {
      method: "POST",
      body: JSON.stringify({
        subject,
        material,
        mode: elements.compilerModeInput.value,
      }),
    });
    renderBlueprint(result.blueprint);
    switchSubview("compilerSubtabs", "blueprint");
    elements.compilerMessage.textContent = `课程蓝图已保存 · ID ${result.id}`;
    await loadWorkspaces();
    if ((await api("/api/workspaces")).workspaces.some((item) => item.id === result.id)) {
      await switchSubject(result.id);
    }
    await loadSubjects();
  } catch (error) {
    elements.compilerMessage.textContent = error.message;
  } finally {
    elements.compileSubjectButton.disabled = false;
    elements.compileSubjectButton.textContent = "生成学习蓝图";
  }
}

function svgElement(tagName, attributes = {}) {
  const element = document.createElementNS(
    "http://www.w3.org/2000/svg",
    tagName,
  );
  for (const [key, value] of Object.entries(attributes)) {
    element.setAttribute(key, String(value));
  }
  return element;
}

function nodeColor(nodeType) {
  const palette = {
    concept: "var(--accent)",
    question: "var(--warning)",
    method: "var(--success)",
    example: "var(--brand-blue)",
    counterexample: "var(--danger)",
    project: "var(--brand-purple)",
    practice: "var(--brand-pink)",
  };
  return palette[nodeType] || "var(--text-subtle)";
}

function renderThoughtGraph() {
  const payload = state.workshopGraph;
  if (!payload) {
    return;
  }
  for (const svg of [elements.thoughtGraph, elements.railGraph]) {
    if (svg) {
      renderThoughtGraphInto(svg, payload);
    }
  }
}

function renderThoughtGraphInto(svg, payload) {
  svg.replaceChildren();
  if (!payload.nodes.length) {
    const hint = svgElement("text", {
      x: 600,
      y: 380,
      "text-anchor": "middle",
      class: "graph-empty",
    });
    hint.textContent = "还没有知识支点。在右侧提问，让这棵树开始生长。";
    svg.append(hint);
    return;
  }

  const nodesById = new Map(payload.nodes.map((node) => [node.id, node]));
  for (const edge of payload.edges) {
    const source = nodesById.get(edge.source_id);
    const target = nodesById.get(edge.target_id);
    if (!source || !target) {
      continue;
    }
    const line = svgElement("line", {
      x1: source.x,
      y1: source.y,
      x2: target.x,
      y2: target.y,
      class: "graph-edge",
    });
    svg.append(line);
  }
  for (const node of payload.nodes) {
    const group = svgElement("g", {
      class: `graph-node ${
        node.id === state.workshopSelectedNodeId ? "selected" : ""
      }`,
      transform: `translate(${node.x}, ${node.y})`,
      "data-node-id": node.id,
    });
    const circle = svgElement("circle", { r: 22 });
    circle.style.fill = nodeColor(node.node_type);
    const label = svgElement("text", {
      x: 0,
      y: 40,
      "text-anchor": "middle",
      class: "graph-node-label",
    });
    label.textContent =
      node.title.length > 16 ? `${node.title.slice(0, 16)}…` : node.title;
    group.append(circle, label);
    group.addEventListener("click", () => selectWorkshopNode(node.id));
    svg.append(group);
  }
}

function selectWorkshopNode(nodeId) {
  state.workshopSelectedNodeId = nodeId;
  renderThoughtGraph();
  const node = state.workshopGraph.nodes.find((item) => item.id === nodeId);
  if (!node) {
    elements.nodeDetail.hidden = true;
    return;
  }
  elements.nodeDetail.hidden = false;
  elements.nodeDetail.replaceChildren();
  const title = document.createElement("h4");
  title.textContent = node.title;
  const type = document.createElement("span");
  type.className = "provider-badge";
  type.textContent = node.node_type;
  const summary = document.createElement("p");
  summary.textContent = node.summary || "暂无说明";
  const actions = document.createElement("div");
  actions.className = "mistake-actions";
  const practiceButton = document.createElement("button");
  practiceButton.type = "button";
  practiceButton.className = "micro-button";
  practiceButton.textContent = node.exercise_id ? "打开练习" : "生成练习";
  practiceButton.addEventListener("click", () =>
    createWorkshopPractice(node, practiceButton),
  );
  actions.append(practiceButton);
  elements.nodeDetail.append(title, type, summary, actions);
}

function fitWorkshopGraph() {
  const nodes = state.workshopGraph?.nodes || [];
  const targets = [elements.thoughtGraph, elements.railGraph].filter(Boolean);
  if (!nodes.length) {
    targets.forEach((svg) => svg.setAttribute("viewBox", "0 0 1200 760"));
    return;
  }
  const xs = nodes.map((node) => node.x);
  const ys = nodes.map((node) => node.y);
  const minX = Math.min(...xs) - 120;
  const maxX = Math.max(...xs) + 120;
  const minY = Math.min(...ys) - 120;
  const maxY = Math.max(...ys) + 160;
  const viewBox = `${minX} ${minY} ${Math.max(400, maxX - minX)} ${Math.max(
    320,
    maxY - minY,
  )}`;
  targets.forEach((svg) => svg.setAttribute("viewBox", viewBox));
}

function renderWorkshopMessages() {
  elements.workshopMessages.replaceChildren();
  const messages = state.workshopGraph?.messages || [];
  if (!messages.length) {
    renderEmpty(
      elements.workshopMessages,
      "还没有知识节点。在下方描述一个主题或问题，AI 会从这里开始生成关系图。",
    );
    return;
  }
  for (const message of messages) {
    const bubble = document.createElement("article");
    bubble.className = `chat-message ${message.role}`;
    if (message.role === "assistant") {
      bubble.innerHTML = renderMarkdown(message.content || "");
    } else {
      bubble.textContent = message.content || "";
    }
    elements.workshopMessages.append(bubble);
  }
  elements.workshopMessages.scrollTop = elements.workshopMessages.scrollHeight;
}

async function loadWorkshop() {
  try {
    state.workshopGraph = await api("/api/workshop");
    state.workshopSessionId = state.workshopGraph.session_id;
    elements.workshopStatus.textContent = `${state.workshopGraph.nodes.length} 个节点`;
    if (
      state.workshopSelectedNodeId &&
      !state.workshopGraph.nodes.some(
        (node) => node.id === state.workshopSelectedNodeId,
      )
    ) {
      state.workshopSelectedNodeId = null;
    }
    renderThoughtGraph();
    renderWorkshopMessages();
    fitWorkshopGraph();
  } catch (error) {
    renderEmpty(elements.workshopMessages, error.message);
  }
}

async function askWorkshop(event) {
  event.preventDefault();
  const question = elements.workshopInput.value.trim();
  if (!question) {
    return;
  }
  const submitButton = elements.workshopForm.querySelector(
    'button[type="submit"]',
  );
  submitButton.disabled = true;
  submitButton.textContent = "生长中...";
  elements.workshopStatus.textContent = "AI 正在生成节点";
  try {
    state.workshopGraph = await api("/api/workshop/ask", {
      method: "POST",
      body: JSON.stringify({
        session_id: state.workshopSessionId,
        question,
        selected_node_id: state.workshopSelectedNodeId,
      }),
    });
    elements.workshopInput.value = "";
    await loadWorkshop();
  } catch (error) {
    elements.workshopStatus.textContent = error.message;
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "生长";
  }
}

async function createWorkshopPractice(node, button) {
  if (node.exercise_id) {
    switchView("practice");
    await loadExercise(node.exercise_id);
    return;
  }
  button.disabled = true;
  button.textContent = "生成中...";
  try {
    const result = await api("/api/workshop/practice", {
      method: "POST",
      body: JSON.stringify({ node_id: node.id }),
    });
    await loadWorkshop();
    await refreshCatalog();
    switchView("practice");
    await loadExercise(result.exercise_id);
  } catch (error) {
    button.textContent = error.message;
  }
}

function switchSubview(group, target) {
  if (group === "history") {
    state.historySubview = target;
  } else if (group === "settings") {
    state.settingsSubview = target;
  } else if (group === "workshop") {
    state.workshopSubview = target;
  }
  document
    .querySelectorAll(`.subnav[data-subnav-group="${group}"] .subnav-button`)
    .forEach((button) => {
      button.classList.toggle("active", button.dataset.subviewTarget === target);
    });
  document
    .querySelectorAll(`[data-subview-group="${group}"]`)
    .forEach((element) => {
      element.hidden = element.dataset.subviewName !== target;
    });
  applyViewHeading(group, target);
}

const VIEW_HEADINGS = {
  history: {
    overview: ["档案", "总览", "路线进度、通过趋势与最近运行。"],
    diagnosis: ["档案", "诊断", "按知识点统计掌握度，归纳薄弱点。"],
    practice: ["档案", "补练", "根据诊断生成同类练习，计入学习记录。"],
    maintenance: ["档案", "维护", "管理运行记录、AI 练习、错题与备份。"],
  },
  settings: {
    ai: ["设置", "模型", "配置只写入本机 .env，现有密钥不会发送到浏览器。"],
    platform: ["设置", "平台", "修改平台名称、副标题与默认领域。"],
  },
  workshop: {
    workshop: [
      "工坊",
      "图谱",
      "提问后 AI 创建知识支点，可继续追问、形成分支，并把节点变成正式练习。",
    ],
    compiler: [
      "工坊",
      "编译",
      "输入主题或材料，生成课程蓝图并物化为可运行的练习。",
    ],
  },
};

function applyViewHeading(group, target) {
  const entry = VIEW_HEADINGS[group]?.[target];
  if (!entry) {
    return;
  }
  const headingTargets = {
    history: [
      elements.historyEyebrow,
      elements.historyTitle,
      elements.historySummary,
    ],
    settings: [
      elements.settingsEyebrow,
      elements.settingsTitle,
      elements.settingsSummary,
    ],
    workshop: [
      elements.workshopEyebrow,
      elements.workshopTitle,
      elements.workshopSummary,
    ],
  };
  const nodes = headingTargets[group] || [];
  nodes.forEach((node, index) => {
    if (node) {
      node.textContent = entry[index];
    }
  });
}

function switchView(view) {
  state.view = view;
  closeRailAfterSelect();
  document.querySelectorAll(".view-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  const practiceSection = elements.exerciseView.closest(".workspace");
  if (practiceSection) {
    practiceSection.hidden = view !== "practice";
  }
  elements.historyView.hidden = view !== "history";
  elements.companionView.hidden = view !== "companion";
  elements.workshopView.hidden = view !== "workshop";
  elements.settingsView.hidden = view !== "settings";

  if (view === "history") {
    switchSubview("history", state.historySubview || "overview");
    loadHistory();
    loadCompanion();
  } else if (view === "companion") {
    loadCompanion();
    loadChat();
  } else if (view === "settings") {
    switchSubview("settings", state.settingsSubview || "ai");
    loadAiSettings();
    loadStudioIdentity();
  } else if (view === "workshop") {
    switchSubview("workshop", state.workshopSubview || "workshop");
    loadWorkshop();
    loadSubjects();
  }
}

async function init() {
  try {
    await loadWorkspaces();
    await loadActiveSubject();
    await loadHistory();
  } catch (error) {
    elements.loading.textContent = `无法连接学习面板：${error.message}`;
  }
}

elements.checkButton.addEventListener("click", runCheck);
elements.hintButton.addEventListener("click", showHint);
elements.copyExercisePathButton.addEventListener("click", () =>
  copyPath(elements.copyExercisePathButton),
);
elements.copyContextButton.addEventListener("click", copyCurrentContext);
elements.nextPracticeButton.addEventListener("click", generateNextPractice);
elements.createBackupButton.addEventListener("click", createBackup);
elements.aiSettingsForm.addEventListener("submit", saveAiSettings);
elements.studioSettingsForm.addEventListener("submit", saveStudioSettings);
elements.subjectCompilerForm.addEventListener("submit", compileSubject);
elements.workspaceSelect.addEventListener("change", () =>
  switchSubject(elements.workspaceSelect.value),
);
elements.testAiSettingsButton.addEventListener("click", testAiSettings);
elements.clearAiKeyInput.addEventListener("change", () => {
  elements.aiApiKeyInput.disabled = elements.clearAiKeyInput.checked;
  if (elements.clearAiKeyInput.checked) {
    elements.aiApiKeyInput.value = "";
  }
});
elements.analyzeButton.addEventListener("click", analyzeLearning);
elements.chatForm.addEventListener("submit", sendChatMessage);
elements.newChatButton.addEventListener("click", startNewChat);
elements.renameChatButton.addEventListener("click", renameCurrentChat);
elements.clearChatButton.addEventListener("click", clearCurrentChat);
elements.deleteChatButton.addEventListener("click", deleteCurrentChat);
elements.chatSessionSelect.addEventListener("change", () =>
  loadChat(Number(elements.chatSessionSelect.value)),
);
elements.loadHistoryContextButton.addEventListener(
  "click",
  loadSelectedHistoryContext,
);
elements.clearChatContextButton.addEventListener(
  "click",
  clearAllChatContexts,
);
elements.workshopForm.addEventListener("submit", askWorkshop);
elements.fitGraphButton.addEventListener("click", fitWorkshopGraph);
document.querySelectorAll("[data-cleanup]").forEach((button) => {
  button.addEventListener("click", () =>
    cleanupData(button.dataset.cleanup, button),
  );
});
document.querySelectorAll(".subnav-button").forEach((button) => {
  button.addEventListener("click", () => {
    const group = button.closest(".subnav").dataset.subnavGroup;
    switchSubview(group, button.dataset.subviewTarget);
    if (group === "companion" && button.dataset.subviewTarget === "compiler") {
      loadSubjects();
    }
    if (group === "companion" && button.dataset.subviewTarget === "workshop") {
      loadWorkshop();
    }
    if (group === "workshop" && button.dataset.subviewTarget === "compiler") {
      loadSubjects();
    }
    if (group === "workshop" && button.dataset.subviewTarget === "workshop") {
      loadWorkshop();
    }
    if (
      group === "compilerSubtabs" &&
      button.dataset.subviewTarget === "list"
    ) {
      loadSubjects();
    }
  });
});
document.querySelectorAll(".view-tab").forEach((button) => {
  button.addEventListener("click", () => switchView(button.dataset.view));
});

async function analyzeCurrentExercise() {
  const exercise = state.current;
  if (!exercise) {
    return;
  }
  if (!state.history) {
    try {
      state.history = await api("/api/learning/history");
    } catch (error) {
      state.history = { attempts: [] };
    }
  }
  const attempts = state.history?.attempts || [];
  const attempt =
    attempts.find((item) => item.exercise_id === exercise.id && !item.passed) ||
    attempts.find((item) => item.exercise_id === exercise.id);
  if (!attempt) {
    state.chatMessages.push({
      role: "assistant",
      content: `「${exercise.title}」还没有记录。先回到练习页点一次「运行」，我才能分析这段代码。`,
    });
    renderChatMessages();
    return;
  }
  const button = elements.analyzeCurrentButton;
  if (button) {
    button.disabled = true;
    setButtonLabel(button, "分析中...");
  }
  try {
    const payload = await api(
      `/api/learning/analyze-attempt?id=${attempt.id}`,
      { method: "POST" },
    );
    const analysis = payload.analysis || {};
    const lines = [analysis.summary || "分析完成。"];
    for (const [label, values] of [
      ["题目差距", analysis.requirement_gaps],
      ["代码问题", analysis.code_issues],
      ["隐藏风险", analysis.hidden_risks],
      ["已掌握", analysis.strengths],
    ]) {
      if (values?.length) {
        lines.push(`\n**${label}**`);
        for (const value of values) {
          lines.push(`- ${value}`);
        }
      }
    }
    state.chatMessages.push({ role: "assistant", content: lines.join("\n") });
    renderChatMessages();
    await loadHistory();
  } catch (error) {
    state.chatMessages.push({
      role: "assistant",
      content: `分析失败：${error.message}`,
    });
    renderChatMessages();
  } finally {
    if (button) {
      button.disabled = false;
      setButtonLabel(button, "分析当前题目");
    }
  }
}

elements.loadCurrentToChatButton?.addEventListener("click", async () => {
  await loadCurrentExerciseIntoChat();
  switchView("companion");
});
elements.loadCurrentExerciseButton?.addEventListener("click", () =>
  loadCurrentExerciseIntoChat(),
);
elements.analyzeCurrentButton?.addEventListener("click", () =>
  analyzeCurrentExercise(),
);
elements.workshopModeButton?.addEventListener("click", () =>
  setAppMode("workshop"),
);

function setWidgetOpen(open) {
  if (!elements.widgetPanel || !elements.companionWidget) {
    return;
  }
  elements.companionWidget.classList.toggle("open", open);
  elements.widgetPanel.hidden = !open;
  elements.widgetToggle?.setAttribute("aria-expanded", String(open));
  if (!open) {
    return;
  }
  renderChatContexts();
  renderChatMessages();
  loadChat();
  elements.widgetInput?.focus();
}

elements.widgetToggle?.addEventListener("click", () => setWidgetOpen(true));
elements.widgetClose?.addEventListener("click", () => setWidgetOpen(false));
elements.widgetForm?.addEventListener("submit", sendChatMessage);
elements.widgetLoadCurrent?.addEventListener("click", () =>
  loadCurrentExerciseIntoChat(),
);
elements.widgetAnalyze?.addEventListener("click", () =>
  analyzeCurrentExercise(),
);

document.querySelectorAll("#modeList .course-menu-item").forEach((button) => {
  button.addEventListener("click", () => setAppMode(button.dataset.mode));
});

// One refresh control per view; its scope follows the active view.
async function refreshActiveView() {
  const view = state.view;
  if (view === "practice") {
    await refreshCatalog();
    if (state.current) {
      state.current = await api(
        `/api/exercise?id=${encodeURIComponent(state.current.id)}`,
      );
      renderExercise();
    }
    await loadHistory();
  } else if (view === "history") {
    await loadHistory();
    await loadCompanion();
  } else if (view === "companion") {
    await loadChat();
  } else if (view === "workshop") {
    await loadWorkshop();
    await loadSubjects();
  } else if (view === "settings") {
    await loadAiSettings();
    await loadStudioIdentity();
  }
}

document.querySelectorAll("[data-refresh]").forEach((button) => {
  button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      await refreshActiveView();
    } finally {
      button.disabled = false;
    }
  });
});

/* --------------------------------------------------------------------------
   Rail: hide/show, full-page map expansion, course + mode switching
   -------------------------------------------------------------------------- */

const RAIL_FLOAT_BREAKPOINT = 900;
let railUserHidden = null;

function setRailHidden(hidden) {
  railUserHidden = hidden;
  if (!elements.app || !elements.railShowButton) {
    return;
  }
  elements.app.classList.toggle("rail-hidden", hidden);
  elements.railShowButton.hidden = !hidden;
  if (hidden) {
    collapseMapOverlay();
  }
}

function applyRailState() {
  if (!elements.app || !elements.railShowButton) {
    return;
  }
  const floating = window.innerWidth <= RAIL_FLOAT_BREAKPOINT;
  if (!floating) {
    elements.rail.classList.remove("is-expanded");
    elements.mapExpandButton?.setAttribute("aria-expanded", "false");
    setRailHidden(false);
    return;
  }
  if (railUserHidden === null) {
    setRailHidden(true);
  } else {
    setRailHidden(railUserHidden);
  }
}

function expandMapOverlay() {
  if (!elements.rail) {
    return;
  }
  setRailHidden(false);
  elements.rail.classList.add("is-expanded");
  elements.mapExpandButton?.setAttribute("aria-expanded", "true");
}

function collapseMapOverlay() {
  elements.rail?.classList.remove("is-expanded");
  elements.mapExpandButton?.setAttribute("aria-expanded", "false");
}

function closeRailAfterSelect() {
  collapseMapOverlay();
  if (window.innerWidth <= RAIL_FLOAT_BREAKPOINT) {
    setRailHidden(true);
  }
}

function toggleMapOverlay() {
  if (elements.rail?.classList.contains("is-expanded")) {
    collapseMapOverlay();
  } else {
    expandMapOverlay();
  }
}

async function refreshActiveScope() {
  state.history = null;
  state.companion = null;
  state.maintenance = null;
  await refreshCatalog();
  const inScope = state.catalog?.exercises?.some(
    (exercise) => exercise.id === state.current?.id,
  );
  if (!inScope) {
    const preferred =
      state.catalog?.exercises?.find((exercise) => !exercise.completed)?.id ||
      state.catalog?.exercises?.[0]?.id;
    if (preferred) {
      await loadExercise(preferred);
    } else {
      state.current = null;
      if (state.appMode === "workshop") {
        elements.exerciseView.hidden = true;
        elements.loading.hidden = false;
        elements.loading.textContent =
          "创造工坊还没有生成练习。可以在关系图里选择节点生成练习。";
      } else {
        renderSetupRequired();
      }
    }
  }
  await loadHistory();
  await loadCompanion();
}

async function setAppMode(mode) {
  const workshop = mode === "workshop";
  state.appMode = workshop ? "workshop" : "course";

  document
    .querySelectorAll("#modeList .course-menu-item")
    .forEach((button) => {
      button.classList.toggle("active", button.dataset.mode === state.appMode);
    });

  if (elements.railMapEyebrow) {
    elements.railMapEyebrow.textContent = workshop ? "图谱" : "路线";
  }
  if (elements.railMapTitle) {
    elements.railMapTitle.textContent = workshop
      ? "知识图"
      : "全部关卡";
  }
  if (elements.exerciseCount) {
    elements.exerciseCount.hidden = workshop;
  }
  if (elements.roadmap) {
    elements.roadmap.hidden = workshop;
  }
  if (elements.railGraph) {
    elements.railGraph.hidden = !workshop;
  }
  toggleCourseMenu(false);

  if (workshop) {
    expandMapOverlay();
    loadWorkshop();
  } else {
    collapseMapOverlay();
  }
  await refreshActiveScope();
}

elements.railHideButton?.addEventListener("click", () => {
  if (elements.rail?.classList.contains("is-expanded")) {
    collapseMapOverlay();
    return;
  }
  setRailHidden(true);
});

elements.railShowButton?.addEventListener("click", () => {
  setRailHidden(false);
});

elements.mapExpandButton?.addEventListener("click", toggleMapOverlay);

function toggleCourseMenu(force) {
  if (!elements.courseMenu || !elements.courseButton) {
    return;
  }
  const next =
    typeof force === "boolean" ? force : elements.courseMenu.hidden;
  elements.courseMenu.hidden = !next;
  elements.courseButton.setAttribute("aria-expanded", String(next));
}

elements.courseButton?.addEventListener("click", (event) => {
  event.stopPropagation();
  toggleCourseMenu();
});

elements.courseMenu?.addEventListener("click", (event) => {
  if (event.target.closest(".course-menu-item")) {
    return;
  }
  event.stopPropagation();
});

document.addEventListener("click", () => toggleCourseMenu(false));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    toggleCourseMenu(false);
    collapseMapOverlay();
  }
});

window.addEventListener("resize", applyRailState);
applyRailState();

init();
