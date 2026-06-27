const els = {
  starfield: document.querySelector("#starfield"),
  scene: document.querySelector("#scene"),
  planetField: document.querySelector("#planetField"),
  oracleCore: document.querySelector("#oracleCore"),
  oracleForm: document.querySelector("#oracleForm"),
  questionInput: document.querySelector("#questionInput"),
  modelSelect: document.querySelector("#modelSelect"),
  askButton: document.querySelector("#askButton"),
  resetButton: document.querySelector("#resetButton"),
  status: document.querySelector("#status"),
  overallPercent: document.querySelector("#overallPercent"),
  overallMeta: document.querySelector("#overallMeta"),
  controllerPreview: document.querySelector("#controllerPreview"),
  controllerPreviewQuestionType: document.querySelector("#controllerPreviewQuestionType"),
  controllerPreviewStatus: document.querySelector("#controllerPreviewStatus"),
  controllerPreviewSummary: document.querySelector("#controllerPreviewSummary"),
  controllerPreviewDirectCount: document.querySelector("#controllerPreviewDirectCount"),
  controllerPreviewSupportCount: document.querySelector("#controllerPreviewSupportCount"),
  controllerPreviewNeedCount: document.querySelector("#controllerPreviewNeedCount"),
  controllerPreviewComputable: document.querySelector("#controllerPreviewComputable"),
  controllerPreviewSupport: document.querySelector("#controllerPreviewSupport"),
  controllerPreviewNeeds: document.querySelector("#controllerPreviewNeeds"),
  followUpPanel: document.querySelector("#followUpPanel"),
  followUpConversation: document.querySelector("#followUpConversation"),
  followUpBadge: document.querySelector("#followUpBadge"),
  followUpTitle: document.querySelector("#followUpTitle"),
  followUpSummary: document.querySelector("#followUpSummary"),
  followUpPrompt: document.querySelector("#followUpPrompt"),
  followUpBaseQuestion: document.querySelector("#followUpBaseQuestion"),
  followUpMissingFields: document.querySelector("#followUpMissingFields"),
  followUpSuggestedSystems: document.querySelector("#followUpSuggestedSystems"),
  followUpReset: document.querySelector("#followUpReset"),
  cutscene: document.querySelector("#cutscene"),
  ritualCanvas: document.querySelector("#ritualCanvas"),
  blindBox: document.querySelector("#blindBox"),
  ritualCursor: document.querySelector("#ritualCursor"),
  ritualPrompt: document.querySelector("#ritualPrompt"),
  incenseSticks: [...document.querySelectorAll(".incense-stick")],
  oracleRunes: document.querySelector("#oracleRunes"),
  thinkingVoices: document.querySelector("#thinkingVoices"),
  answerConstellation: document.querySelector("#answerConstellation"),
  finalChamber: document.querySelector("#finalChamber"),
  finalClose: document.querySelector("#finalClose"),
  directVerdictCard: document.querySelector("#directVerdictCard"),
  directVerdictLead: document.querySelector("#directVerdictLead"),
  directVerdictMeta: document.querySelector("#directVerdictMeta"),
  controllerPanel: document.querySelector("#controllerPanel"),
  controllerQuestionType: document.querySelector("#controllerQuestionType"),
  controllerSelectedCount: document.querySelector("#controllerSelectedCount"),
  controllerSummary: document.querySelector("#controllerSummary"),
  controllerSelectedSystems: document.querySelector("#controllerSelectedSystems"),
  controllerSignals: document.querySelector("#controllerSignals"),
  controllerGaps: document.querySelector("#controllerGaps"),
  summaryAnswer: document.querySelector("#summaryAnswer"),
  systemAnswerCards: document.querySelector("#systemAnswerCards"),
  systemStatusCards: document.querySelector("#systemStatusCards"),
  agreements: document.querySelector("#agreements"),
  differences: document.querySelector("#differences"),
  cautions: document.querySelector("#cautions"),
  progressToggle: document.querySelector("#progressToggle"),
  progressDrawer: document.querySelector("#progressDrawer"),
  drawerClose: document.querySelector("#drawerClose"),
  progressList: document.querySelector("#progressList"),
  planetGuide: document.querySelector("#planetGuide"),
  guideFocus: document.querySelector("#guideFocus"),
  guideClose: document.querySelector("#guideClose"),
  guideMode: document.querySelector("#guideMode"),
  guideTitle: document.querySelector("#guideTitle"),
  guideSummary: document.querySelector("#guideSummary"),
  guideGlyph: document.querySelector("#guideGlyph"),
  guideBestFor: document.querySelector("#guideBestFor"),
  guideNeeds: document.querySelector("#guideNeeds"),
  guideAskFormat: document.querySelector("#guideAskFormat"),
  guideAvoid: document.querySelector("#guideAvoid"),
  guideQuestionInput: document.querySelector("#guideQuestionInput"),
  guideQuestionLabel: document.querySelector("#guideQuestionLabel"),
  guideQuestionHint: document.querySelector("#guideQuestionHint"),
  guideUsePrompt: document.querySelector("#guideUsePrompt"),
  guideWorkbench: document.querySelector("#guideWorkbench"),
  guideWorkbenchTitle: document.querySelector("#guideWorkbenchTitle"),
  guideWorkbenchIntro: document.querySelector("#guideWorkbenchIntro"),
  guideWorkbenchFields: document.querySelector("#guideWorkbenchFields"),
  guideWorkbenchHint: document.querySelector("#guideWorkbenchHint"),
  guideWorkbenchMapLookup: document.querySelector("#guideWorkbenchMapLookup"),
  guideWorkbenchFill: document.querySelector("#guideWorkbenchFill"),
  guideWorkbenchMapPreview: document.querySelector("#guideWorkbenchMapPreview"),
  divinationWorkbench: document.querySelector("#divinationWorkbench"),
  divinationWorkbenchTitle: document.querySelector("#divinationWorkbenchTitle"),
  divinationWorkbenchIntro: document.querySelector("#divinationWorkbenchIntro"),
  divinationStepStrip: document.querySelector("#divinationStepStrip"),
  divinationStepHint: document.querySelector("#divinationStepHint"),
  divinationModeButtons: [...document.querySelectorAll("[data-divination-mode]")],
  divinationQuestionInput: document.querySelector("#divinationQuestionInput"),
  divinationHorizonInput: document.querySelector("#divinationHorizonInput"),
  divinationBackgroundInput: document.querySelector("#divinationBackgroundInput"),
  divinationRollButton: document.querySelector("#divinationRollButton"),
  divinationQuickButton: document.querySelector("#divinationQuickButton"),
  divinationResetButton: document.querySelector("#divinationResetButton"),
  divinationDiceBoard: document.querySelector("#divinationDiceBoard"),
  divinationLineBoard: document.querySelector("#divinationLineBoard"),
  divinationResultText: document.querySelector("#divinationResultText"),
  physiognomyWorkbench: document.querySelector("#physiognomyWorkbench"),
  physiognomyStepStrip: document.querySelector("#physiognomyStepStrip"),
  physiognomyStepHint: document.querySelector("#physiognomyStepHint"),
  physiognomyContextSelect: document.querySelector("#physiognomyContextSelect"),
  physiognomyGoalInput: document.querySelector("#physiognomyGoalInput"),
  physiognomyNotesInput: document.querySelector("#physiognomyNotesInput"),
  physiognomyImageInput: document.querySelector("#physiognomyImageInput"),
  physiognomyImageHint: document.querySelector("#physiognomyImageHint"),
  physiognomyPreviewList: document.querySelector("#physiognomyPreviewList"),
  physiognomyTraitGroups: document.querySelector("#physiognomyTraitGroups"),
  physiognomySelectedSummary: document.querySelector("#physiognomySelectedSummary"),
  physiognomyFill: document.querySelector("#physiognomyFill"),
  physiognomyReset: document.querySelector("#physiognomyReset"),
  tarotWorkbench: document.querySelector("#tarotWorkbench"),
  tarotStepStrip: document.querySelector("#tarotStepStrip"),
  tarotStepHint: document.querySelector("#tarotStepHint"),
  tarotSpreadSelect: document.querySelector("#tarotSpreadSelect"),
  tarotShuffle: document.querySelector("#tarotShuffle"),
  tarotDeal: document.querySelector("#tarotDeal"),
  tarotSpreadBoard: document.querySelector("#tarotSpreadBoard"),
  tarotResultText: document.querySelector("#tarotResultText"),
};
const defaultQuestionPlaceholder = els.questionInput?.getAttribute("placeholder") || "";
if (els.followUpPanel && els.oracleCore && els.followUpPanel.parentElement !== els.oracleCore) {
  els.oracleCore.appendChild(els.followUpPanel);
}
const homeHeadline = document.querySelector("#oracleCore h1");
if (homeHeadline) homeHeadline.textContent = "问天";
if (els.overallMeta) els.overallMeta.textContent = "诸术潜听";
if (els.status) els.status.textContent = "黑池静候，你只需先落下这一问";

const homeInvocation = document.querySelector(".oracle-invocation");
if (homeInvocation) {
  homeInvocation.textContent = "先把真正困住你的那一问写下。其余诸术，会在幕后自行择法、补问、合参，最后只把最该听的那句带回来。";
}

const homeEyebrow = document.querySelector("#oracleCore .eyebrow");
if (homeEyebrow) homeEyebrow.textContent = "天门未启 只候一问";

function prefersLitePerformanceMode() {
  if (document.documentElement.dataset.performanceMode === "lite") {
    return true;
  }
  const host = String(window.location.hostname || "").toLowerCase();
  const isRemoteHost = host && host !== "localhost" && host !== "127.0.0.1";
  const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  const saveData = Boolean(connection && connection.saveData);
  const effectiveType = String((connection && connection.effectiveType) || "").toLowerCase();
  return isRemoteHost || saveData || /(?:slow-2g|2g|3g)/.test(effectiveType) || window.innerWidth <= 900;
}

const performanceMode = document.documentElement.dataset.performanceMode || (prefersLitePerformanceMode() ? "lite" : "full");
document.documentElement.dataset.performanceMode = performanceMode;

document.querySelectorAll("[data-suggestion]").forEach((button) => {
  button.addEventListener("click", () => {
    if (!els.questionInput) return;
    els.questionInput.value = button.getAttribute("data-suggestion") || "";
    els.questionInput.focus();
    const end = els.questionInput.value.length;
    if (typeof els.questionInput.setSelectionRange === "function") {
      els.questionInput.setSelectionRange(end, end);
    }
    setStatus("已写入示例问法，你可以直接推演或继续改写");
  });
});

function ensureLuopanDecor() {
  const stage = document.querySelector(".luopan-stage");
  if (!stage || stage.dataset.decorReady === "true") return;

  const aura = stage.querySelector(".luopan-aura");
  const spin = stage.querySelector(".luopan-spin");
  const disc = stage.querySelector(".luopan-disc");
  if (!aura || !spin || !disc) return;

  const board = document.createElement("div");
  board.className = "luopan-board";
  board.setAttribute("aria-hidden", "true");
  board.innerHTML = `
    <div class="luopan-board-frame"></div>
    <div class="luopan-board-core"></div>
    <div class="luopan-cardinals">
      <span class="luopan-cardinal luopan-cardinal-north">子</span>
      <span class="luopan-cardinal luopan-cardinal-east">卯</span>
      <span class="luopan-cardinal luopan-cardinal-south">午</span>
      <span class="luopan-cardinal luopan-cardinal-west">酉</span>
    </div>
    <div class="luopan-bagua">
      <span class="luopan-bagua-mark luopan-bagua-qian">乾</span>
      <span class="luopan-bagua-mark luopan-bagua-kan">坎</span>
      <span class="luopan-bagua-mark luopan-bagua-gen">艮</span>
      <span class="luopan-bagua-mark luopan-bagua-zhen">震</span>
      <span class="luopan-bagua-mark luopan-bagua-xun">巽</span>
      <span class="luopan-bagua-mark luopan-bagua-li">离</span>
      <span class="luopan-bagua-mark luopan-bagua-kun">坤</span>
      <span class="luopan-bagua-mark luopan-bagua-dui">兑</span>
    </div>
  `;
  stage.insertBefore(board, aura);

  const needle = document.createElement("div");
  needle.className = "luopan-needle";
  needle.setAttribute("aria-hidden", "true");
  stage.insertBefore(needle, spin);

  const sectors = document.createElement("div");
  sectors.className = "luopan-ring luopan-ring-sectors";
  const midRing = disc.querySelector(".luopan-ring-mid");
  disc.insertBefore(sectors, midRing || disc.firstChild);

  const branches = document.createElement("div");
  branches.className = "luopan-branches";
  branches.setAttribute("aria-hidden", "true");
  const earthlyBranches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];
  branches.innerHTML = earthlyBranches
    .map((label, index) => {
      const angle = index * 30;
      return `<span style="--angle:${angle}deg; --reverse-angle:${-angle}deg">${label}</span>`;
    })
    .join("");
  const taiji = disc.querySelector(".luopan-taiji");
  disc.insertBefore(branches, taiji || null);

  stage.dataset.decorReady = "true";
}

ensureLuopanDecor();

function rebuildFinalChamberLayout() {
  const chamber = els.finalChamber;
  if (!chamber || chamber.dataset.oracleLayout === "rebuilt") return;

  const chamberChildren = Array.from(chamber.children);
  const riverStage = chamberChildren.find((node) => node.classList?.contains("river-stage"));
  const eyebrow = chamberChildren.find((node) => node.classList?.contains("eyebrow"));
  const title = chamberChildren.find((node) => node.tagName === "H2");
  const resultBands = chamberChildren.filter((node) => node.classList?.contains("result-band"));
  const finalColumns = chamberChildren.find((node) => node.classList?.contains("final-columns"));

  if (
    !riverStage ||
    !eyebrow ||
    !title ||
    !els.summaryAnswer ||
    !els.directVerdictCard ||
    !els.controllerPanel ||
    !finalColumns ||
    resultBands.length === 0
  ) {
    return;
  }

  eyebrow.classList.add("oracle-stage-eyebrow");
  title.classList.add("oracle-verdict-title");
  els.summaryAnswer.classList.add("oracle-summary-scroll");
  els.directVerdictCard.classList.add("oracle-direct-verdict");
  els.controllerPanel.classList.add("oracle-controller-desk");
  finalColumns.classList.add("oracle-council-grid");
  resultBands.forEach((band, index) => {
    band.classList.add("oracle-evidence-band", `oracle-evidence-band-${index + 1}`);
  });

  const verdictStage = document.createElement("section");
  verdictStage.className = "oracle-verdict-stage";
  verdictStage.setAttribute("aria-label", "最终神谕");

  const verdictHalo = document.createElement("div");
  verdictHalo.className = "oracle-verdict-halo";
  verdictHalo.setAttribute("aria-hidden", "true");

  const verdictCore = document.createElement("div");
  verdictCore.className = "oracle-verdict-core";
  verdictCore.append(els.directVerdictCard, els.summaryAnswer);

  verdictStage.append(verdictHalo, eyebrow, title, verdictCore);

  const supportStage = document.createElement("div");
  supportStage.className = "oracle-support-stage";

  const evidenceGrid = document.createElement("div");
  evidenceGrid.className = "oracle-evidence-grid";
  evidenceGrid.append(...resultBands);

  supportStage.append(els.controllerPanel, evidenceGrid, finalColumns);

  chamber.append(riverStage, verdictStage, supportStage);
  chamber.dataset.oracleLayout = "rebuilt";
}

rebuildFinalChamberLayout();

function buildPlanetPositions(count) {
  const compact = window.innerWidth <= 720;
  const centerX = 50;
  const centerY = compact ? 52 : 50;
  if (count >= 16) {
    const outerCount = Math.max(10, Math.ceil(count * 0.62));
    const innerCount = Math.max(0, count - outerCount);
    const outerRadius = compact ? 40 : 42;
    const innerRadius = compact ? 26 : 28;
    const outerStep = 360 / outerCount;
    const innerStep = innerCount ? 360 / innerCount : 0;
    const positions = [];

    for (let index = 0; index < outerCount; index += 1) {
      const angle = (-90 + outerStep * index) * (Math.PI / 180);
      positions.push([
        Number((centerX + Math.cos(angle) * outerRadius).toFixed(2)),
        Number((centerY + Math.sin(angle) * outerRadius).toFixed(2)),
      ]);
    }

    for (let index = 0; index < innerCount; index += 1) {
      const angle = (-90 + innerStep * index + innerStep / 2) * (Math.PI / 180);
      positions.push([
        Number((centerX + Math.cos(angle) * innerRadius).toFixed(2)),
        Number((centerY + Math.sin(angle) * innerRadius).toFixed(2)),
      ]);
    }

    return positions;
  }

  const radius = compact ? 39 : 41;
  const gapAngle = compact ? 88 : 110;
  const startAngle = 90 + gapAngle / 2;
  const angleStep = count > 1 ? (360 - gapAngle) / (count - 1) : 0;

  return Array.from({ length: count }, (_, index) => {
    const angle = (startAngle + angleStep * index) * (Math.PI / 180);
    const x = centerX + Math.cos(angle) * radius;
    const y = centerY + Math.sin(angle) * radius;

    return [Number(x.toFixed(2)), Number(y.toFixed(2))];
  });
}

const planetColors = [
  ["#c9a45b", "#27304c", "#7edbd3"],
  ["#b85d4f", "#271528", "#d8b86a"],
  ["#7edbd3", "#122d3e", "#d8e3ef"],
  ["#7ca866", "#152b3f", "#d8b86a"],
  ["#d48a84", "#351927", "#7edbd3"],
  ["#6db9df", "#10243a", "#b85d4f"],
];

const deityProfiles = {
  yijing_and_symbolism: { className: "deity-yijing", glyph: "易", colors: ["#b08d57", "#151826", "#7edbd3"] },
  bazi: { className: "deity-bazi", glyph: "命", colors: ["#c6a267", "#1a1526", "#cf8d6e"] },
  ziwei_doushu: { className: "deity-ziwei", glyph: "紫", colors: ["#d7c58a", "#1a1830", "#97b9ff"] },
  qizheng_siyu: { className: "deity-qizheng", glyph: "曜", colors: ["#c0a36e", "#101b30", "#77c7d4"] },
  qimen_dunjia: { className: "deity-qimen", glyph: "遁", colors: ["#b99352", "#171519", "#7abf8e"] },
  liu_ren: { className: "deity-liuren", glyph: "壬", colors: ["#d7b980", "#15151e", "#7082a8"] },
  liuyao_and_meihua: { className: "deity-liuyao", glyph: "卦", colors: ["#c7a067", "#191827", "#b79ad1"] },
  date_selection: { className: "deity-date", glyph: "时", colors: ["#d0b679", "#181a22", "#7a97a9"] },
  name_studies: { className: "deity-name", glyph: "名", colors: ["#cba977", "#211a1a", "#b6825c"] },
  physiognomy: { className: "deity-face", glyph: "相", colors: ["#c4b38c", "#14151e", "#8ca89e"] },
  fengshui: { className: "deity-fengshui", glyph: "风", colors: ["#baa05d", "#141b1c", "#73b49d"] },
  daoist_arts: { className: "deity-dao", glyph: "道", colors: ["#c2a26d", "#1b1721", "#8fd2c8"] },
  western_astrology: { className: "deity-western", glyph: "星", colors: ["#b7a06d", "#151a2a", "#7ca7d7"] },
  vedic_astrology: { className: "deity-vedic", glyph: "梵", colors: ["#ccb28e", "#151c28", "#d0d5e6"] },
  tarot: { className: "deity-tarot", glyph: "牌", colors: ["#d8c096", "#1c1620", "#a888c1"] },
  kabbalah: { className: "deity-kabbalah", glyph: "树", colors: ["#d0b57d", "#171522", "#8ec0b6"] },
  alchemy_and_hermeticism: { className: "deity-alchemy", glyph: "炼", colors: ["#c79d62", "#191717", "#a56f55"] },
  onmyodo: { className: "deity-onmyodo", glyph: "阴", colors: ["#d4c48f", "#101018", "#7e92c8"] },
  numerology: { className: "deity-numerology", glyph: "数", colors: ["#c9ab72", "#161a22", "#79b9d2"] },
  human_design: { className: "deity-human", glyph: "图", colors: ["#d0af82", "#171922", "#d68f84"] },
  modern_esotericism: { className: "deity-modern", glyph: "玄", colors: ["#bfa77d", "#14161f", "#8b9ab9"] },
};

const divineGlyphs = ["命", "曜", "火", "卦", "玄", "星", "海", "谶", "时", "相", "数", "神"];

const ritualGroups = {
  ignite: ["bazi", "ziwei_doushu", "western_astrology"],
  ascend: ["qimen_dunjia", "liu_ren", "liuyao_and_meihua", "date_selection"],
  reveal: ["yijing_and_symbolism", "fengshui", "tarot", "daoist_arts", "kabbalah", "onmyodo"],
  chorus: [
    "bazi",
    "ziwei_doushu",
    "western_astrology",
    "qimen_dunjia",
    "liu_ren",
    "yijing_and_symbolism",
    "fengshui",
    "tarot",
    "daoist_arts",
    "onmyodo",
  ],
};

const ritualCourtLayout = [
  [12, 70],
  [22, 48],
  [34, 28],
  [50, 16],
  [66, 28],
  [78, 48],
  [88, 70],
  [30, 82],
  [50, 86],
  [70, 82],
];

const ritualCourtKeys = [...new Set(ritualGroups.chorus)];

const deityPortraitAnchors = {
  yijing_and_symbolism: [18, 28],
  bazi: [30, 70],
  ziwei_doushu: [72, 28],
  qizheng_siyu: [51, 14],
  qimen_dunjia: [76, 66],
  liu_ren: [26, 58],
  liuyao_and_meihua: [45, 72],
  date_selection: [74, 14],
  name_studies: [33, 40],
  physiognomy: [68, 60],
  fengshui: [57, 68],
  daoist_arts: [18, 70],
  western_astrology: [74, 22],
  vedic_astrology: [62, 34],
  tarot: [86, 18],
  kabbalah: [48, 26],
  alchemy_and_hermeticism: [64, 74],
  onmyodo: [84, 42],
  numerology: [36, 20],
  human_design: [24, 46],
  modern_esotericism: [82, 58],
};

const modelLabels = {
  auto: "自动选择",
  "local-vault": "本地资料推演",
};

const systemLabelMap = {
  yijing_and_symbolism: "易经象数",
  bazi: "八字",
  ziwei_doushu: "紫微斗数",
  qizheng_siyu: "七政四余",
  qimen_dunjia: "奇门遁甲",
  liu_ren: "大六壬",
  liuyao_and_meihua: "六爻梅花",
  date_selection: "择日",
  name_studies: "姓名学",
  physiognomy: "相术",
  fengshui: "风水",
  daoist_arts: "道术法脉",
  western_astrology: "西洋占星",
  vedic_astrology: "吠陀占星",
  tarot: "塔罗",
  kabbalah: "卡巴拉",
  alchemy_and_hermeticism: "炼金赫尔墨斯",
  onmyodo: "阴阳道",
  numerology: "数字命理",
  human_design: "人类图",
  modern_esotericism: "现代神秘学",
};

const questionGuideOverrides = {
  yijing_and_symbolism: {
    bestFor: "当前局势、象意判断、阶段转折与走势拆解",
    needs: ["具体问题", "起卦数字或起问时点"],
    askFormat: "例如：我想问这次合作能不能成，数字 3 8 5。",
    avoid: "只说“帮我看看全部人生”时，象意会过散，难以落地。",
  },
  bazi: {
    bestFor: "人生结构、事业财运、关系模式、阶段运势",
    needs: ["出生日期", "出生时辰", "出生地", "性别"],
    askFormat: "例如：我出生于 1990-05-12 14:30，男，河南信阳，想看今年工作和财运。",
    avoid: "出生时辰不准时，不适合做精批。",
  },
  ziwei_doushu: {
    bestFor: "命盘格局、宫位主题、阶段趋势",
    needs: ["出生日期", "出生时辰", "性别"],
    askFormat: "例如：1990-05-12 14:30，女，想看婚姻和事业主轴。",
    avoid: "出生时辰偏差太大时，宫位会直接漂移。",
  },
  qizheng_siyu: {
    bestFor: "中西合参的命盘结构、天时节律、阶段主题",
    needs: ["出生日期", "出生时辰", "出生地"],
    askFormat: "例如：1990-05-12 14:30，北京，想看接下来两年的事业变化。",
    avoid: "没有出生地时，盘面精度会下降。",
  },
  qimen_dunjia: {
    bestFor: "短期决策、时机判断、先后顺序与临门一脚",
    needs: ["起问时间", "具体问题"],
    askFormat: "例如：现在是 2026-06-08 21:10，我想问这周先谈合作还是先推进招聘？",
    avoid: "不适合拿来替代完整人生盘。",
  },
  liu_ren: {
    bestFor: "事件占时、过程推演、问成败与阻碍",
    needs: ["占问时间", "具体问题"],
    askFormat: "例如：2026-06-08 21:10 起问，这次签约最终能不能落地？",
    avoid: "问题过空时，很难落到明确结论。",
  },
  liuyao_and_meihua: {
    bestFor: "短期走势、结果倾向、应期判断",
    needs: ["起卦方式或卦象", "具体问题"],
    askFormat: "例如：我问这次谈判能不能成，数字 3 8 5。或直接给本卦、变卦、动爻。",
    avoid: "不给起卦信息时，只能停留在方向判断。",
  },
  date_selection: {
    bestFor: "选日子、看某天宜不宜、对比几个日期",
    needs: ["事项类型", "候选日期", "地点"],
    askFormat: "例如：我想搬家，候选日期是 6 月 10 日、6 月 12 日，地点在上海。",
    avoid: "没有事项类型时，只能给通用择日判断。",
  },
  name_studies: {
    bestFor: "名字适配、候选名比较、改名方向",
    needs: ["姓名或候选名", "用途"],
    askFormat: "例如：给2026年6月13日23点42分出生的女宝宝，姓彭，起三个偏诗意的正式名字。",
    avoid: "不适合直接替代完整命盘判断。",
  },
  physiognomy: {
    bestFor: "外貌特征观察、气色与结构判断",
    needs: ["外貌描述或观察记录", "观察场景"],
    askFormat: "例如：额头宽、眼神清、鼻梁直、下巴饱满，日间正面照片观察，想看整体面相倾向。",
    avoid: "没有清晰描述或观察场景时，很难稳定判断。",
  },
  fengshui: {
    bestFor: "住宅、办公室、朝向、布局调整",
    needs: ["城市或地址", "坐向或平面图"],
    askFormat: "例如：上海某小区 12 栋 1802，坐北朝南，想看这个房子适不适合长期住。",
    avoid: "没有坐向、户型或场景描述时，只能做粗判。",
  },
  daoist_arts: {
    bestFor: "法脉背景、仪式用途、文化语境与边界提醒",
    needs: ["事项类型或目的", "来源或法脉", "仪式文本或描述"],
    askFormat: "例如：正一道法脉，想了解净宅护身类仪式通常怎么分类与使用。",
    avoid: "不适合替代现实医疗、法律或高风险决策。",
  },
  western_astrology: {
    bestFor: "人格结构、关系互动、长期发展主题",
    needs: ["出生日期", "出生时辰", "出生地"],
    askFormat: "例如：1990-05-12 14:30，北京，想看我的职业优势和关系模式。",
    avoid: "出生时间偏差大会明显影响上升和宫位。",
  },
  vedic_astrology: {
    bestFor: "业力主题、阶段运势、婚恋与事业方向",
    needs: ["出生日期", "出生时辰", "出生地"],
    askFormat: "例如：1990-05-12 14:30，北京，想看这两年的事业和婚恋趋势。",
    avoid: "同样依赖准确出生时间与地点。",
  },
  tarot: {
    bestFor: "短期问题、心理面向、当前局势启示",
    needs: ["牌阵或抽牌结果", "问题时间范围"],
    askFormat: "例如：三张牌分别是愚者正位、死神逆位、圣杯首牌，想问这个月项目走向。",
    avoid: "没有抽牌结果时，本地无法直接实算。",
  },
  kabbalah: {
    bestFor: "生命之树路径、象征主题、修行语境",
    needs: ["事项类型或目的", "Sephirah / Path / 主题对象"],
    askFormat: "例如：从 Tiphereth 的角度看 career direction 和 visible purpose。",
    avoid: "没有明确路径与主题时，结果会偏抽象。",
  },
  alchemy_and_hermeticism: {
    bestFor: "转化阶段、象征材料、修炼模型",
    needs: ["事项类型或目的", "文本或图像符号", "转化阶段或模型"],
    askFormat: "例如：nigredo 阶段的 shadow work，材料是 crow / mercury / salt。",
    avoid: "更适合象征分析，不适合直接现实占断。",
  },
  onmyodo: {
    bestFor: "方位禁忌、日期方位、出行与空间判断",
    needs: ["事项类型", "地点", "日期或方向信息"],
    askFormat: "例如：2026-06-10 去东京西南方向出行，这个方向与时点合不合适？",
    avoid: "没有时间与方向时，无法有效落盘。",
  },
  numerology: {
    bestFor: "生命灵数、年份主题、数字倾向",
    needs: ["出生日期"],
    askFormat: "例如：1990-05-12，想看我的生命灵数和今年主题。",
    avoid: "适合做辅助观察，不宜单独替代复杂命盘。",
  },
  human_design: {
    bestFor: "类型、权威、决策方式、能量运作",
    needs: ["出生日期", "出生时辰", "出生地"],
    askFormat: "例如：1990-05-12 14:30，北京，想看我的人类图类型和决策方式。",
    avoid: "出生时间不准时，定义中心和权威都可能变化。",
  },
  modern_esotericism: {
    bestFor: "显化、脉轮、灵气与现代修行体系的语境分析",
    needs: ["事项类型或目的", "来源", "实践描述"],
    askFormat: "例如：我在做显化和脉轮冥想，来源是某课程体系，想看这个实践路径的风险和偏差。",
    avoid: "不适合替代医学、金融或法律判断。",
  },
};

const tarotDeck = [
  "愚者", "魔术师", "女祭司", "女皇", "皇帝", "教皇", "恋人", "战车", "力量", "隐士",
  "命运之轮", "正义", "倒吊人", "死神", "节制", "恶魔", "高塔", "星星", "月亮", "太阳",
  "审判", "世界",
  "权杖首牌", "权杖二", "权杖三", "权杖四", "权杖五", "权杖六", "权杖七", "权杖八", "权杖九", "权杖十", "权杖侍从", "权杖骑士", "权杖皇后", "权杖国王",
  "圣杯首牌", "圣杯二", "圣杯三", "圣杯四", "圣杯五", "圣杯六", "圣杯七", "圣杯八", "圣杯九", "圣杯十", "圣杯侍从", "圣杯骑士", "圣杯皇后", "圣杯国王",
  "宝剑首牌", "宝剑二", "宝剑三", "宝剑四", "宝剑五", "宝剑六", "宝剑七", "宝剑八", "宝剑九", "宝剑十", "宝剑侍从", "宝剑骑士", "宝剑皇后", "宝剑国王",
  "星币首牌", "星币二", "星币三", "星币四", "星币五", "星币六", "星币七", "星币八", "星币九", "星币十", "星币侍从", "星币骑士", "星币皇后", "星币国王",
];

const tarotSpreadPresets = {
  single: [{ key: "focus", label: "焦点" }],
  three_card: [
    { key: "past", label: "过去" },
    { key: "present", label: "现在" },
    { key: "future", label: "未来" },
  ],
  celtic_cross: [
    { key: "present", label: "现状" },
    { key: "challenge", label: "阻碍" },
    { key: "root", label: "根因" },
    { key: "past", label: "过去" },
    { key: "goal", label: "目标" },
    { key: "near_future", label: "近期" },
    { key: "self", label: "自己" },
    { key: "environment", label: "环境" },
    { key: "hopes_fears", label: "期待/顾虑" },
    { key: "outcome", label: "结果" },
  ],
};

let systems = [];
let planetNodes = new Map();
let currentRunId = 0;
let pendingOracle = null;
let followUpState = null;
let activeGuideKey = null;
let guideAnimationFrame = null;
let guideWorkbenchState = {
  key: "",
  fields: [],
};
let guideWorkbenchMapState = {
  loading: false,
  data: null,
  error: "",
  requestedAddress: "",
  requestedFacing: "",
};
let divinationState = {
  systemKey: "",
  mode: "dice",
  dice: { upper: null, lower: null, moving: null },
  lines: [],
  movingLine: null,
  timeSeed: null,
};
let physiognomyState = {
  selectedTraits: new Set(),
  previewUrls: [],
};
let tarotState = {
  spread: "three_card",
  deck: [],
  drawn: [],
  dealStarted: false,
};

const customGuideWorkbenchKeys = new Set(["tarot", "liuyao_and_meihua", "yijing_and_symbolism", "physiognomy"]);
const divinationSystemKeys = new Set(["liuyao_and_meihua", "yijing_and_symbolism"]);
const trigramCatalog = {
  1: { label: "乾", image: "天", lines: [1, 1, 1] },
  2: { label: "兑", image: "泽", lines: [1, 1, 0] },
  3: { label: "离", image: "火", lines: [1, 0, 1] },
  4: { label: "震", image: "雷", lines: [1, 0, 0] },
  5: { label: "巽", image: "风", lines: [0, 1, 1] },
  6: { label: "坎", image: "水", lines: [0, 1, 0] },
  7: { label: "艮", image: "山", lines: [0, 0, 1] },
  8: { label: "坤", image: "地", lines: [0, 0, 0] },
};
const trigramNumberByPattern = new Map(
  Object.entries(trigramCatalog).map(([key, meta]) => [meta.lines.join(""), Number(key)]),
);
const linePositionLabels = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"];
const physiognomyTraitGroups = [
  {
    label: "额与眉",
    traits: ["额头开阔", "额头饱满", "额头低窄", "眉清整齐", "眉乱或断"],
  },
  {
    label: "眼神",
    traits: ["眼神清", "眼睛明亮", "眼神散", "眼周疲惫"],
  },
  {
    label: "鼻部",
    traits: ["鼻梁直", "鼻头饱满", "鼻梁塌", "鼻色偏暗"],
  },
  {
    label: "口与下庭",
    traits: ["嘴唇饱满", "嘴薄", "下巴饱满", "下巴后缩"],
  },
  {
    label: "气色与手相",
    traits: ["气色红润", "气色暗黄", "掌纹清", "掌纹乱"],
  },
];
const ritualState = {
  activeRunId: 0,
  litSticks: new Set(),
  resolveIgnition: null,
  pointerX: -9999,
  pointerY: -9999,
  hoverStick: null,
  hoverSince: 0,
  activeCourtKeys: [],
  particleSeed: 0,
  smokeParticles: [],
  emberParticles: [],
  riverParticles: [],
};

const sleep = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

function setStatus(text) {
  els.status.textContent = text;
}

function setBusy(isBusy) {
  const busy = Boolean(isBusy);
  if (els.askButton) els.askButton.disabled = busy;
  if (els.resetButton) els.resetButton.disabled = busy;
  if (els.modelSelect) els.modelSelect.disabled = busy;
  if (els.questionInput) {
    els.questionInput.readOnly = busy;
    els.questionInput.setAttribute("aria-busy", busy ? "true" : "false");
  }
  if (els.oracleForm) els.oracleForm.dataset.busy = busy ? "true" : "false";
  syncAskActionLabel();
}

function syncAskActionLabel() {
  if (!els.askButton) return;
  if (els.askButton.disabled) {
    els.askButton.textContent = "推演中...";
    return;
  }
  els.askButton.textContent = followUpState ? "继续补充" : "启门问天";
}

function extractController(oracleData) {
  if (oracleData?.controller && typeof oracleData.controller === "object") return oracleData.controller;
  if (oracleData?.oracle?.controller && typeof oracleData.oracle.controller === "object") return oracleData.oracle.controller;
  return null;
}

function extractSystemDiagnostics(oracleData) {
  if (Array.isArray(oracleData?.systemDiagnostics)) return oracleData.systemDiagnostics;
  if (Array.isArray(oracleData?.oracle?.system_diagnostics)) return oracleData.oracle.system_diagnostics;
  if (Array.isArray(oracleData?.result?.system_diagnostics)) return oracleData.result.system_diagnostics;
  return [];
}

function uniqueText(values) {
  return [...new Set((Array.isArray(values) ? values : []).filter(Boolean))];
}

function clearFollowUpList(node) {
  if (node) node.innerHTML = "";
}

function renderFollowUpList(node, items, fallback) {
  if (!node) return;
  node.innerHTML = "";
  const values = items.length ? items : [fallback];
  values.forEach((text) => {
    const li = document.createElement("li");
    li.textContent = text;
    node.appendChild(li);
  });
}

function renderFollowUpConversation(messages = []) {
  if (!els.followUpConversation) return;
  els.followUpConversation.innerHTML = "";
  messages
    .filter((item) => item && item.text)
    .forEach((item) => {
      const bubble = document.createElement("div");
      bubble.className = "follow-up-message";
      bubble.dataset.role = item.role === "user" ? "user" : "assistant";
      bubble.textContent = item.text;
      els.followUpConversation.appendChild(bubble);
    });
}

function conclusionModeLabel(mode, structureFirst = false) {
  if (structureFirst) return "先出结构";
  const labels = {
    direct: "直接结论",
    direct_conclusion: "直接结论",
    structure_then_conclusion: "先结构后结论",
    structure_first: "先出结构",
    question_adaptive: "按问题适配",
    advisory: "辅助建议",
  };
  return labels[mode] || "按问题适配";
}

function previewStatusLabel(controller, directCount, missingCount) {
  const status = controller?.executionStatus || "idle";
  if (status === "answered") return directCount > 0 ? "可进入起算" : "已有分流";
  if (status === "needs_input") return missingCount > 0 ? "等待补充" : "待澄清";
  if (status === "blocked") return "先处理风险";
  if (status === "no_route") return "需改写问题";
  return "等待问题";
}

function summarizeQuestionGuide(system = {}) {
  const guide = system.questionGuide || {};
  const minimumNeeds = Array.isArray(system.minimumNeeds) && system.minimumNeeds.length
    ? system.minimumNeeds
    : Array.isArray(guide.minimumNeeds)
      ? guide.minimumNeeds
      : [];
  const optionalEnhancements = Array.isArray(system.optionalEnhancements) && system.optionalEnhancements.length
    ? system.optionalEnhancements
    : Array.isArray(guide.optionalEnhancements)
      ? guide.optionalEnhancements
      : [];
  return {
    minimumNeeds,
    optionalEnhancements,
    directConclusionCapable: Boolean(
      system.directConclusionCapable ?? guide.directConclusionCapable,
    ),
    structureFirst: Boolean(system.structureFirst ?? guide.structureFirst),
    conclusionMode: system.conclusionMode || guide.conclusionMode || "question_adaptive",
  };
}

function clearControllerPreview() {
  els.controllerPreview?.classList.add("hidden");
  if (els.controllerPreview) delete els.controllerPreview.dataset.state;
  if (els.controllerPreviewQuestionType) els.controllerPreviewQuestionType.textContent = "智能总控待机中";
  if (els.controllerPreviewStatus) els.controllerPreviewStatus.textContent = "等待问题";
  if (els.controllerPreviewSummary) els.controllerPreviewSummary.textContent = "";
  if (els.controllerPreviewDirectCount) els.controllerPreviewDirectCount.textContent = "0";
  if (els.controllerPreviewSupportCount) els.controllerPreviewSupportCount.textContent = "0";
  if (els.controllerPreviewNeedCount) els.controllerPreviewNeedCount.textContent = "0";
  [els.controllerPreviewComputable, els.controllerPreviewSupport, els.controllerPreviewNeeds].forEach(clearFollowUpList);
}

function renderControllerPreview(controller, diagnostics = [], systems = []) {
  if (!els.controllerPreview) return;
  const selected = Array.isArray(controller?.selectedSystems) ? controller.selectedSystems : [];
  const alternates = Array.isArray(controller?.alternateSystems) ? controller.alternateSystems : [];
  const missing = Array.isArray(controller?.missingInputs) ? controller.missingInputs : [];
  const diagnosticList = Array.isArray(diagnostics) ? diagnostics : [];
  const systemList = Array.isArray(systems) ? systems : [];
  const selectedKeys = new Set(selected.map((item) => item?.key).filter(Boolean));
  const alternateKeys = new Set(alternates.map((item) => item?.key).filter(Boolean));
  const systemMap = new Map(systemList.map((item) => [item.key, item]));
  const diagnosticMap = new Map(diagnosticList.map((item) => [item.key, item]));

  const computableItems = [];
  selected.forEach((item) => {
    if (!item?.key) return;
    const diagnostic = diagnosticMap.get(item.key) || {};
    const meta = summarizeQuestionGuide({ ...systemMap.get(item.key), ...diagnostic });
    computableItems.push({
      key: item.key,
      title: displaySystemName(item.key || item.title),
      reason: item.reason || diagnostic.reason || diagnostic.matchReason || "已被总控选为主调体系。",
      meta,
      status: diagnostic.replyStatus || item.status || "",
    });
  });

  if (!computableItems.length) {
    diagnosticList
      .filter((item) => item?.replyStatus === "computable")
      .slice(0, 4)
      .forEach((item) => {
        const meta = summarizeQuestionGuide({ ...systemMap.get(item.key), ...item });
        computableItems.push({
          key: item.key,
          title: displaySystemName(item.key || item.title),
          reason: item.reason || item.matchReason || "当前已具备最低起算条件。",
          meta,
          status: item.replyStatus || "",
        });
      });
  }

  const supportItems = [];
  const supportCandidates = diagnosticList.filter((item) => {
    if (!item?.key) return false;
    if (selectedKeys.has(item.key)) return false;
    if (item.replyStatus === "not_applicable") return false;
    return alternateKeys.has(item.key) || item.replyStatus === "computable" || item.structureFirst;
  });
  supportCandidates.slice(0, 6).forEach((item) => {
    const meta = summarizeQuestionGuide({ ...systemMap.get(item.key), ...item });
    supportItems.push({
      key: item.key,
      title: displaySystemName(item.key || item.title),
      reason: item.reason || item.matchReason || "可作为补充参考。",
      meta,
      missingInputs: Array.isArray(item.missingInputs) ? item.missingInputs : [],
    });
  });

  const needsItems = [];
  const seenNeed = new Set();
  missing.forEach((item) => {
    const systemName = item?.system ? displaySystemName(item.system) : "当前问题";
    const field = item?.field || "必要信息";
    const key = `${systemName}:${field}`;
    if (!seenNeed.has(key)) {
      needsItems.push(`${systemName}：${field}`);
      seenNeed.add(key);
    }
  });
  diagnosticList
    .filter((item) => item?.replyStatus === "missing_inputs")
    .slice(0, 6)
    .forEach((item) => {
      const title = displaySystemName(item.key || item.title);
      const meta = summarizeQuestionGuide({ ...systemMap.get(item.key), ...item });
      const values = Array.isArray(item.missingInputs) && item.missingInputs.length
        ? item.missingInputs
        : meta.minimumNeeds;
      values.slice(0, 3).forEach((field) => {
        const key = `${title}:${field}`;
        if (!seenNeed.has(key)) {
          needsItems.push(`${title}：${field}`);
          seenNeed.add(key);
        }
      });
    });

  const directCount = computableItems.filter((item) => item.meta.directConclusionCapable && !item.meta.structureFirst).length;
  const supportCount = supportItems.length + computableItems.filter((item) => item.meta.structureFirst).length;
  const needCount = needsItems.length;

  const summary = controller?.routingSummary
    || (computableItems.length
      ? "总控已识别出可进入本地计算的体系，并标明哪些只能先出结构。"
      : "先把问题补到最低起算条件，再进入本地实算。");

  els.controllerPreview.classList.remove("hidden");
  els.controllerPreview.dataset.state = controller?.executionStatus || "answered";
  if (els.controllerPreviewQuestionType) {
    els.controllerPreviewQuestionType.textContent = controller?.questionType || "问题类型待识别";
  }
  if (els.controllerPreviewStatus) {
    els.controllerPreviewStatus.textContent = previewStatusLabel(controller, directCount, needCount);
  }
  if (els.controllerPreviewSummary) {
    els.controllerPreviewSummary.textContent = summary;
  }
  if (els.controllerPreviewDirectCount) els.controllerPreviewDirectCount.textContent = String(directCount);
  if (els.controllerPreviewSupportCount) els.controllerPreviewSupportCount.textContent = String(supportCount);
  if (els.controllerPreviewNeedCount) els.controllerPreviewNeedCount.textContent = String(needCount);

  renderFollowUpList(
    els.controllerPreviewComputable,
    computableItems.map((item) => {
      const modeText = conclusionModeLabel(item.meta.conclusionMode, item.meta.structureFirst);
      return `${item.title} [${modeText}]：${item.reason}`;
    }),
    "还没有稳定落入可直接起算的体系。",
  );
  renderFollowUpList(
    els.controllerPreviewSupport,
    supportItems.map((item) => {
      const modeText = conclusionModeLabel(item.meta.conclusionMode, item.meta.structureFirst);
      const extra = item.missingInputs?.length ? ` 还缺：${item.missingInputs.slice(0, 3).join("、")}` : "";
      return `${item.title} [${modeText}]：${item.reason}${extra}`;
    }),
    "当前没有额外辅助体系。",
  );
  renderFollowUpList(
    els.controllerPreviewNeeds,
    needsItems,
    "最低起算条件已基本齐备。",
  );
}

function applyFollowUpMode(mode, text = {}) {
  const state = mode || "needs_input";
  if (els.followUpPanel) els.followUpPanel.dataset.state = state;
  if (els.followUpBadge) els.followUpBadge.textContent = text.badge || "继续补充";
  if (els.followUpTitle) els.followUpTitle.textContent = text.title || "信息还不够，先继续对话补齐条件";
  if (els.followUpSummary) els.followUpSummary.textContent = text.summary || "";
  if (els.followUpPrompt) els.followUpPrompt.textContent = text.prompt || "";
  renderFollowUpConversation(
    Array.isArray(text.conversation) && text.conversation.length
      ? text.conversation
      : (text.prompt ? [{ role: "assistant", text: text.prompt }] : []),
  );
}

function hideFollowUpPanel() {
  els.followUpPanel?.classList.add("hidden");
  if (els.followUpPanel) delete els.followUpPanel.dataset.state;
  if (els.followUpBadge) els.followUpBadge.textContent = "";
  if (els.followUpTitle) els.followUpTitle.textContent = "";
  if (els.followUpSummary) els.followUpSummary.textContent = "";
  if (els.followUpPrompt) els.followUpPrompt.textContent = "";
  if (els.followUpBaseQuestion) els.followUpBaseQuestion.textContent = "";
  if (els.followUpConversation) els.followUpConversation.innerHTML = "";
  clearFollowUpList(els.followUpMissingFields);
  clearFollowUpList(els.followUpSuggestedSystems);
  if (els.questionInput) els.questionInput.placeholder = defaultQuestionPlaceholder;
  syncAskActionLabel();
}

function clearFollowUpState() {
  followUpState = null;
  hideFollowUpPanel();
}

function composeOracleQuestion(question) {
  const trimmed = String(question || "").trim();
  if (!followUpState) {
    return {
      requestQuestion: trimmed,
      baseQuestion: trimmed,
      supplements: [],
    };
  }

  const priorSupplements = Array.isArray(followUpState.supplements) ? followUpState.supplements : [];
  const supplements = [...priorSupplements, trimmed].filter(Boolean);
  const requestParts = [String(followUpState.baseQuestion || "").trim()];
  if (supplements.length) {
    requestParts.push(...supplements);
  }

  return {
    requestQuestion: requestParts.filter(Boolean).join("\n"),
    baseQuestion: followUpState.baseQuestion,
    supplements,
  };
}

function displayModelName(model) {
  return modelLabels[model] || model;
}

function displaySystemName(input) {
  if (!input) return "未命名体系";
  return systemLabelMap[input] || String(input).replace(/_/g, " ");
}

function clipText(value, limit = 32) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (!text) return "";
  if (text.length <= limit) return text;
  return `${text.slice(0, Math.max(1, limit)).trimEnd()}...`;
}

function sanitizeSystemTitle(system = {}) {
  return displaySystemName(system.key) || displaySystemName(system.title);
}

function buildFollowUpExperience(controller, question, supplements = []) {
  const followUpPrompt = controller?.followUpPrompt || "请继续补充关键信息后再起算。";
  const missing = Array.isArray(controller?.missingInputs) ? controller.missingInputs : [];
  const selected = Array.isArray(controller?.selectedSystems) ? controller.selectedSystems : [];
  const primaryKey = selected[0]?.key || "";
  const baseMissingList = missing
    .slice(0, 4)
    .map((item) => `${displaySystemName(item.system || primaryKey || "当前问题")}：${item.field || "必要信息"}`);
  let example = "";

  if (primaryKey === "name_studies") {
    const missingFields = new Set(missing.map((item) => item?.field).filter(Boolean));
    if (
      missingFields.has("姓氏") ||
      missingFields.has("出生年月日时") ||
      missingFields.has("性别")
    ) {
      example = "例如：2026年6月13日23点42分出生，姓彭，男孩，用于正式姓名，想起三个偏书卷、清朗、稳重的名字。";
    } else if (missingFields.has("姓名或候选名") && missingFields.has("用途")) {
      example = "例如：2026年6月13日23点42分出生，姓彭，男孩，用于正式姓名，想起三个偏书卷、清朗、稳重的名字。";
    } else if (missingFields.has("姓名或候选名")) {
      example = "例如：2026年6月13日23点42分出生，姓彭，男孩，想起三个用于正式姓名的名字。";
    } else if (missingFields.has("用途")) {
      example = "例如：用于正式姓名，想走书卷、清朗、稳重一点的风格。";
    } else {
      example = "例如：2026年6月13日23点42分出生，姓彭，男孩，用于正式姓名，想起三个偏书卷、清朗、稳重的名字。";
    }
  }

  const summary = baseMissingList.length
    ? `还差 ${baseMissingList.join("、")}。${example ? ` ${example}` : ""}`
    : `现在先继续补条件，还不会进入点香起算。${example ? ` ${example}` : ""}`;

  const prompt = example ? `${followUpPrompt} ${example}` : followUpPrompt;
  const placeholder = example || followUpPrompt;
  const conversation = [];
  if (question) {
    conversation.push({ role: "user", text: question });
  }
  (Array.isArray(supplements) ? supplements : []).filter(Boolean).forEach((item) => {
    conversation.push({ role: "user", text: item });
  });
  conversation.push({ role: "assistant", text: prompt });

  return {
    prompt,
    summary,
    placeholder,
    conversation,
  };
}

function normalizeSystemLookupText(input) {
  return String(input || "")
    .replace(/[，,].*$/, "")
    .replace(/\s*\d+%\s*(已实装|有规则|待启算)?\s*$/u, "")
    .replace(/\s+/g, "")
    .trim()
    .toLowerCase();
}

function getSystemByKey(key) {
  const normalized = normalizeSystemLookupText(key);
  if (!normalized) return null;
  return systems.find((item) => normalizeSystemLookupText(item?.key) === normalized) || null;
}

function getSystemByTitle(title) {
  const normalized = normalizeSystemLookupText(title);
  if (!normalized) return null;
  return systems.find((item) => {
    const titleCandidates = [
      item?.title,
      item?.system,
      item?.name,
      item?.label,
      item?.key,
      displaySystemName(item?.key),
    ];
    return titleCandidates.some((candidate) => normalizeSystemLookupText(candidate) === normalized);
  }) || null;
}

function mergedQuestionGuide(system = {}) {
  const key = system.key || "";
  const baseGuide = system.questionGuide || {};
  const override = questionGuideOverrides[key] || {};
  return {
    mode: baseGuide.mode || override.mode || "symbolic",
    bestFor: override.bestFor || baseGuide.bestFor || "用于这个体系最擅长处理的问题类型。",
    needs: override.needs || baseGuide.needs || ["先把问题场景写清楚"],
    askFormat: override.askFormat || baseGuide.askFormat || "请尽量给出明确问题和必要条件。",
    avoid: override.avoid || baseGuide.avoid || "输入越完整，本地计算越稳定。",
  };
}

const guideWorkbenchPresets = {
  bazi: {
    title: "命盘起算台",
    intro: "把出生信息和你想看的重点填进去，系统会组装成适合本地命盘实算的问法。",
    hint: "适合八字、紫微、七政四余、西洋占星、吠陀占星、人类图这类要出生信息的体系。",
    fields: [
      { key: "birthDate", label: "出生日期", type: "text", placeholder: "例如 1990-05-12" },
      { key: "birthTime", label: "出生时间", type: "text", placeholder: "例如 14:30" },
      { key: "gender", label: "性别", type: "text", placeholder: "例如 男 / 女" },
      { key: "birthLocation", label: "出生地", type: "text", placeholder: "例如 北京 / 河南信阳" },
      { key: "focus", label: "想看什么", type: "textarea", placeholder: "例如 今年工作、财运、婚姻、性格主轴" },
    ],
    build(values, system) {
      const base = [values.birthDate, values.birthTime].filter(Boolean).join(" ");
      const parts = [base, values.gender, values.birthLocation, values.focus].filter(Boolean);
      return `${parts.join("，")}。请从${sanitizeSystemTitle(system)}角度推演。`.replace("。。", "。");
    },
  },
  ziwei_doushu: "bazi",
  qizheng_siyu: "bazi",
  western_astrology: "bazi",
  vedic_astrology: "bazi",
  human_design: "bazi",
  numerology: {
    title: "数字命理起算台",
    intro: "数字命理只需要出生日期和想问的主题，不必填太多无关条件。",
    hint: "如果你想看年度主题，直接把今年要关注的领域写清楚即可。",
    fields: [
      { key: "birthDate", label: "出生日期", type: "text", placeholder: "例如 1990-05-12" },
      { key: "focus", label: "想看什么", type: "textarea", placeholder: "例如 生命灵数、今年主题、职业倾向" },
    ],
    build(values) {
      return [values.birthDate, values.focus].filter(Boolean).join("，");
    },
  },
  qimen_dunjia: {
    title: "时机起算台",
    intro: "把起问时点和实际要决策的问题写明白，系统才能按这一刻起局。",
    hint: "适合问先后顺序、是否推进、短期动作窗口。",
    fields: [
      { key: "askTime", label: "起问时间", type: "text", placeholder: "例如 2026-06-08 21:10" },
      { key: "question", label: "具体问题", type: "textarea", placeholder: "例如 这周先谈合作还是先推进招聘？" },
    ],
    build(values) {
      return [values.askTime, values.question].filter(Boolean).join("，");
    },
  },
  liu_ren: "qimen_dunjia",
  liuyao_and_meihua: {
    title: "起卦辅助台",
    intro: "这种体系需要数字、卦象或起问结构。你给起卦条件，系统再替你整理成可起算提问。",
    hint: "如果你还没有卦象，至少给数字或明确起问时点。",
    fields: [
      { key: "question", label: "具体问题", type: "textarea", placeholder: "例如 这次合作能不能成？" },
      { key: "numbers", label: "数字或卦象", type: "text", placeholder: "例如 3 8 5 / 本卦某某，变卦某某，动爻六" },
      { key: "method", label: "起卦方式", type: "text", placeholder: "例如 数字起卦 / 时间起卦" },
    ],
    build(values) {
      const parts = [values.question, values.numbers ? `起卦信息 ${values.numbers}` : "", values.method ? `方式 ${values.method}` : ""].filter(Boolean);
      return parts.join("，");
    },
  },
  yijing_and_symbolism: "liuyao_and_meihua",
  date_selection: {
    title: "择日起算台",
    intro: "把事项类型、日期和地点填进去，系统会自动整理成择日问法。",
    hint: "单个日期和多个候选日期都支持。",
    fields: [
      { key: "eventType", label: "事项类型", type: "text", placeholder: "例如 搬家 / 开业 / 出行 / 签约" },
      { key: "dates", label: "日期", type: "textarea", placeholder: "例如 2026-06-08 或 6月10日、6月12日" },
      { key: "location", label: "地点", type: "text", placeholder: "例如 上海浦东" },
    ],
    build(values) {
      const parts = [values.eventType ? `我想看${values.eventType}` : "我想择日", values.dates ? `日期是${values.dates}` : "", values.location ? `地点在${values.location}` : ""].filter(Boolean);
      return parts.join("，");
    },
  },
  fengshui: {
    title: "风水起算台",
    intro: "风水类至少要有地址或场景，再配坐向、朝向、户型这类信息才能进入有效判断。",
    hint: "没有户型图也可以先用地址和坐向做粗筛。",
    fields: [
      { key: "address", label: "地址或场景", type: "textarea", placeholder: "例如 上海某小区 12 栋 1802 / 办公室前台区域" },
      { key: "facing", label: "坐向或朝向", type: "text", placeholder: "例如 坐北朝南 / 朝东南" },
      { key: "goal", label: "想看什么", type: "textarea", placeholder: "例如 适不适合长期住 / 财位怎么调 / 工位怎么摆" },
    ],
    build(values) {
      const parts = [values.address, values.facing, values.goal].filter(Boolean);
      return parts.join("，");
    },
  },
  name_studies: {
    title: "姓名起算台",
    intro: "姓名类既可以直接起名，也可以比较候选名。把姓氏、出生信息、性别和风格讲清楚，系统才会像真正选名那样给结果。",
    hint: "如果你是想直接起名，不必先给候选名，写清姓氏、对象、风格就行。",
    fields: [
      { key: "names", label: "姓名或候选名", type: "textarea", placeholder: "例如 暂时没有候选名，想直接起名 / 林清和、林知远、林承岳" },
      { key: "purpose", label: "用途", type: "text", placeholder: "例如 女宝宝正式姓名 / 男孩学名 / 品牌名" },
      { key: "goal", label: "侧重点", type: "textarea", placeholder: "例如 姓彭，2026年6月13日23点42分出生，想要偏诗经楚辞、清雅稳重的名字" },
    ],
    build(values) {
      const parts = [values.names ? `候选名是${values.names}` : "", values.purpose ? `用途是${values.purpose}` : "", values.goal ? `主要想看${values.goal}` : ""].filter(Boolean);
      return parts.join("，");
    },
  },
  physiognomy: {
    title: "相术观察台",
    intro: "相术类需要的是稳定描述，而不是一句“帮我看看长相”。把观察到的部位和场景写清楚。",
    hint: "如果后面接图片能力，也能复用同一套结构。",
    fields: [
      { key: "context", label: "观察场景", type: "text", placeholder: "例如 日间正面照片 / 视频截图 / 当面观察" },
      { key: "features", label: "外貌特征", type: "textarea", placeholder: "例如 额头宽、眼神清、鼻梁直、下巴饱满" },
      { key: "goal", label: "想看什么", type: "textarea", placeholder: "例如 整体面相倾向 / 事业气质 / 情感表达" },
    ],
    build(values) {
      return [values.context, values.features, values.goal].filter(Boolean).join("，");
    },
  },
  daoist_arts: {
    title: "法脉语境台",
    intro: "道术这类不是直接算命，更像是围绕法脉、仪式、用途和边界做本地判断。",
    hint: "把你参考的法脉或资料来源写出来，结果会稳得多。",
    fields: [
      { key: "lineage", label: "来源或法脉", type: "text", placeholder: "例如 正一 / 全真 / 某课程体系" },
      { key: "topic", label: "事项或目的", type: "textarea", placeholder: "例如 想了解净宅护身类仪式怎么分类与使用" },
      { key: "ritual", label: "仪式文本或描述", type: "textarea", placeholder: "例如 目前手头仪式文本、做法、步骤描述" },
    ],
    build(values) {
      return [values.lineage, values.topic, values.ritual].filter(Boolean).join("，");
    },
  },
  kabbalah: {
    title: "卡巴拉路径台",
    intro: "卡巴拉类最好明确路径、球体或主题对象，不然只会落成抽象泛谈。",
    hint: "适合问路径象征、修行主题和主题对象映射。",
    fields: [
      { key: "path", label: "Sephirah / Path", type: "text", placeholder: "例如 Tiphereth / Yesod / Path 24" },
      { key: "topic", label: "主题对象", type: "textarea", placeholder: "例如 career direction / visible purpose / relationship pattern" },
    ],
    build(values) {
      return [values.path ? `从${values.path}的角度看` : "", values.topic].filter(Boolean).join(" ");
    },
  },
  alchemy_and_hermeticism: {
    title: "炼金转化台",
    intro: "炼金与赫尔墨斯体系更适合阶段、象征材料和转化主题的结构化输入。",
    hint: "如果你不写阶段，系统就很难判断你在问哪一层转化。",
    fields: [
      { key: "stage", label: "阶段或模型", type: "text", placeholder: "例如 nigredo / albedo / rubedo" },
      { key: "topic", label: "主题", type: "textarea", placeholder: "例如 shadow work / 自我净化 / 关系转化" },
      { key: "symbols", label: "材料或符号", type: "textarea", placeholder: "例如 crow / mercury / salt / 某图像符号" },
    ],
    build(values) {
      const parts = [values.stage ? `${values.stage} 阶段` : "", values.topic, values.symbols ? `材料是 ${values.symbols}` : ""].filter(Boolean);
      return parts.join("，");
    },
  },
  onmyodo: {
    title: "方位判断台",
    intro: "阴阳道更依赖日期、方向、地点和事项类型，问法里至少要占到三项。",
    hint: "适合问出行、禁忌、方位与日期配合。",
    fields: [
      { key: "date", label: "日期时间", type: "text", placeholder: "例如 2026-06-10 / 2026-06-10 09:00" },
      { key: "direction", label: "方向", type: "text", placeholder: "例如 西南方向 / 东北方向" },
      { key: "location", label: "地点", type: "text", placeholder: "例如 东京 / 上海虹桥" },
      { key: "goal", label: "事项", type: "textarea", placeholder: "例如 出行 / 搬迁 / 安排日程" },
    ],
    build(values) {
      return [values.date, values.location, values.direction, values.goal].filter(Boolean).join("，");
    },
  },
  modern_esotericism: {
    title: "现代修行台",
    intro: "现代神秘学类更像在分析你的实践路径、来源和风险，不是直接给神谕式一句话。",
    hint: "来源和实践描述尽量一起填，不然只会变成空泛建议。",
    fields: [
      { key: "source", label: "来源", type: "text", placeholder: "例如 某课程 / 某老师 / 某练习体系" },
      { key: "practice", label: "实践描述", type: "textarea", placeholder: "例如 我在做显化、脉轮冥想、灵气练习" },
      { key: "goal", label: "想看什么", type: "textarea", placeholder: "例如 想看这个路径的风险、偏差和适配性" },
    ],
    build(values) {
      return [values.practice, values.source ? `来源是${values.source}` : "", values.goal].filter(Boolean).join("，");
    },
  },
};

function resolveWorkbenchPreset(key) {
  const preset = guideWorkbenchPresets[key];
  if (!preset) return null;
  if (typeof preset === "string") return guideWorkbenchPresets[preset] || null;
  return preset;
}

function readGuideWorkbenchValues() {
  const values = {};
  els.guideWorkbenchFields?.querySelectorAll("[data-field-key]").forEach((node) => {
    if (node instanceof HTMLInputElement || node instanceof HTMLTextAreaElement || node instanceof HTMLSelectElement) {
      values[node.dataset.fieldKey] = node.value.trim();
    }
  });
  return values;
}

function fillGuideQuestionFromWorkbench() {
  const system = getSystemByKey(activeGuideKey);
  if (!system) return;
  const preset = resolveWorkbenchPreset(system.key);
  if (!preset || typeof preset.build !== "function") return;
  const values = readGuideWorkbenchValues();
  const prompt = String(preset.build(values, system) || "").trim();
  if (!prompt) {
    setStatus("先把这个体系需要的条件填进去");
    return;
  }
  if (els.guideQuestionInput) {
    els.guideQuestionInput.value = prompt;
  }
  setStatus("结构化条件已转成可推演提问");
}

function setGuideQuestionMeta(label, hint) {
  if (els.guideQuestionLabel && label) {
    els.guideQuestionLabel.textContent = label;
  }
  if (els.guideQuestionHint && hint) {
    els.guideQuestionHint.textContent = hint;
  }
}

function markStepStrip(strip, activeKey, completedKeys = []) {
  if (!strip) return;
  const done = new Set(completedKeys);
  strip.querySelectorAll("[data-step-key]").forEach((node) => {
    const key = node.getAttribute("data-step-key") || "";
    node.classList.toggle("active", key === activeKey);
    node.classList.toggle("done", done.has(key));
  });
}

function syncDivinationStepState() {
  const hasQuestion = Boolean((els.divinationQuestionInput?.value || "").trim());
  const hasSeed = Boolean(
    divinationState.timeSeed
      || (divinationState.mode === "lines" && divinationState.lines.length === 6)
      || (divinationState.mode !== "lines" && divinationState.dice.upper && divinationState.dice.lower && divinationState.dice.moving),
  );
  const hasPrompt = Boolean((els.guideQuestionInput?.value || "").trim());
  let active = "question";
  let hint = "先在上方写具体问题，再决定起卦方式。";
  if (hasQuestion && !hasSeed) {
    active = "seed";
    hint = divinationState.mode === "lines"
      ? "问题已定，继续把六爻摇满。"
      : divinationState.mode === "time"
        ? "问题已定，现在可以记录此刻起问时点。"
        : "问题已定，现在可以摇出三组数字。";
  } else if (hasSeed && !hasPrompt) {
    active = "review";
    hint = "起卦信息已经齐了，系统正在整理成最终问法。";
  } else if (hasPrompt) {
    active = "launch";
    hint = "最终问法已经写好，直接点下方按钮开启推演。";
  }
  const completed = [];
  if (hasQuestion) completed.push("question");
  if (hasSeed) completed.push("seed");
  if (hasPrompt) completed.push("review");
  markStepStrip(els.divinationStepStrip, active, completed);
  if (els.divinationStepHint) els.divinationStepHint.textContent = hint;
}

function syncPhysiognomyStepState() {
  const hasContext = Boolean((els.physiognomyContextSelect?.value || "").trim());
  const hasTraits = physiognomyState.selectedTraits.size > 0 || Boolean((els.physiognomyNotesInput?.value || "").trim());
  const hasPrompt = Boolean((els.guideQuestionInput?.value || "").trim());
  let active = "context";
  let hint = "先确认观察场景，再勾选真正看得见的特征。";
  if (hasContext && !hasTraits) {
    active = "traits";
    hint = "场景已定，现在把能稳定观察到的部位特征记下来。";
  } else if (hasTraits && !hasPrompt) {
    active = "review";
    hint = "观察记录已经足够，可以写入最终提问框。";
  } else if (hasPrompt) {
    active = "launch";
    hint = "相术观察记录已经成问，可以直接开启推演。";
  }
  const completed = [];
  if (hasContext) completed.push("context");
  if (hasTraits) completed.push("traits");
  if (hasPrompt) completed.push("review");
  markStepStrip(els.physiognomyStepStrip, active, completed);
  if (els.physiognomyStepHint) els.physiognomyStepHint.textContent = hint;
}

function syncTarotStepState() {
  const hasQuestion = Boolean((els.guideQuestionInput?.value || "").trim());
  const revealedCount = tarotState.drawn.filter(Boolean).length;
  const total = (tarotSpreadPresets[tarotState.spread] || tarotSpreadPresets.three_card).length;
  const allDone = total > 0 && revealedCount === total;
  let active = "question";
  let hint = "先把真正要问的事写清楚，再点开始翻牌。";
  if (hasQuestion && !tarotState.dealStarted) {
    active = "start";
    hint = "问题已定，现在可以启牌并进入翻牌。";
  } else if (tarotState.dealStarted && !allDone) {
    active = "reveal";
    hint = `牌阵已展开，按顺序翻开剩余 ${Math.max(total - revealedCount, 0)} 张牌。`;
  } else if (allDone) {
    active = "launch";
    hint = "牌面已经落定，最终问法已写好，可以直接推演。";
  }
  const completed = [];
  if (hasQuestion) completed.push("question");
  if (tarotState.dealStarted) completed.push("start");
  if (allDone) completed.push("reveal");
  markStepStrip(els.tarotStepStrip, active, completed);
  if (els.tarotStepHint) els.tarotStepHint.textContent = hint;
}

function renderGuideWorkbench(system) {
  const preset = resolveWorkbenchPreset(system?.key || "");
  const show = Boolean(preset && !customGuideWorkbenchKeys.has(system?.key || ""));
  const previousKey = guideWorkbenchState.key;
  els.guideWorkbench?.classList.toggle("hidden", !show);
  if (els.guideWorkbench) els.guideWorkbench.dataset.active = show ? "true" : "false";
  if (!show) {
    guideWorkbenchState = { key: "", fields: [] };
    if (els.guideWorkbenchFields) els.guideWorkbenchFields.innerHTML = "";
    if (els.guideWorkbenchTitle) els.guideWorkbenchTitle.textContent = "结构化起算";
    if (els.guideWorkbenchIntro) els.guideWorkbenchIntro.textContent = "把这个体系真正需要的条件填进去，系统会替你组装成可直接推演的提问。";
    if (els.guideWorkbenchHint) els.guideWorkbenchHint.textContent = "填写完成后会自动生成一段更适合本地起算的提问。";
    resetGuideWorkbenchMapPreview();
    return;
  }
  guideWorkbenchState = {
    key: system.key,
    fields: Array.isArray(preset.fields) ? preset.fields : [],
  };
  if (system.key !== previousKey) {
    resetGuideWorkbenchMapPreview();
  }
  if (els.guideWorkbenchTitle) els.guideWorkbenchTitle.textContent = preset.title || "结构化起算";
  if (els.guideWorkbenchIntro) els.guideWorkbenchIntro.textContent = preset.intro || "填写必要条件后，系统会帮你生成更适合本地实算的提问。";
  if (els.guideWorkbenchHint) els.guideWorkbenchHint.textContent = preset.hint || "填写完成后会自动生成一段更适合本地起算的提问。";
  if (!els.guideWorkbenchFields) return;
  els.guideWorkbenchFields.innerHTML = "";
  guideWorkbenchState.fields.forEach((field) => {
    const row = document.createElement("label");
    row.className = "guide-field";
    row.innerHTML = `<span class="guide-field-label">${field.label}</span>`;
    const control = field.type === "textarea" ? document.createElement("textarea") : document.createElement("input");
    if (control instanceof HTMLInputElement) {
      control.type = "text";
    } else {
      control.rows = 3;
    }
    control.className = "guide-field-input";
    control.placeholder = field.placeholder || "";
    control.dataset.fieldKey = field.key;
    control.addEventListener("input", () => {
      if (guideWorkbenchState.key === "fengshui" && (field.key === "address" || field.key === "facing")) {
        resetGuideWorkbenchMapPreview();
      }
      if (field.autofill !== false) {
        fillGuideQuestionFromWorkbench();
      }
    });
    row.appendChild(control);
    els.guideWorkbenchFields.appendChild(row);
  });
  fillGuideQuestionFromWorkbench();
  renderGuideWorkbenchMapPreview();
}

function mod1(value, base) {
  const remainder = value % base;
  return remainder === 0 ? base : remainder;
}

function currentShanghaiTimeStamp() {
  const formatter = new Intl.DateTimeFormat("sv-SE", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  return formatter.format(new Date()).replace(" ", " ");
}

function cleanPromptSegment(value) {
  return String(value || "")
    .trim()
    .replace(/^[，。；、,\s]+|[，。；、,\s]+$/gu, "");
}

function normalizeQuestionLead(question) {
  return cleanPromptSegment(String(question || "").replace(/^(我想问|想问|请问)/u, ""));
}

function lineMetaFromTotal(total) {
  if (total <= 7) return { value: 0, moving: true, label: "老阴" };
  if (total === 8) return { value: 0, moving: false, label: "少阴" };
  if (total === 9) return { value: 1, moving: false, label: "少阳" };
  return { value: 1, moving: true, label: "老阳" };
}

function formatLineText(line, index) {
  const base = `${linePositionLabels[index] || `第${index + 1}爻`} ${line.label}`;
  return line.moving ? `${base}（动）` : base;
}

function computeDivinationFromLines(lines) {
  if (!Array.isArray(lines) || lines.length !== 6) return null;
  const lowerPattern = lines.slice(0, 3).map((item) => item.value).join("");
  const upperPattern = lines.slice(3, 6).map((item) => item.value).join("");
  const lower = trigramNumberByPattern.get(lowerPattern) || null;
  const upper = trigramNumberByPattern.get(upperPattern) || null;
  const movingLines = lines.map((item, index) => (item.moving ? index + 1 : 0)).filter(Boolean);
  const movingLine = movingLines[0] || null;
  if (!lower || !upper) return null;
  return { upper, lower, movingLine, movingLines };
}

function divinationPromptFromState() {
  const system = getSystemByKey(divinationState.systemKey);
  if (!system) return "";
  const question = normalizeQuestionLead(els.divinationQuestionInput?.value || "");
  const horizon = cleanPromptSegment(els.divinationHorizonInput?.value || "");
  const background = cleanPromptSegment(els.divinationBackgroundInput?.value || "");
  if (!question) return "";
  const systemTitle = sanitizeSystemTitle(system);
  if (divinationState.mode === "lines") {
    const lines = divinationState.lines;
    if (!Array.isArray(lines) || lines.length !== 6 || !divinationState.movingLine) return "";
    const computed = computeDivinationFromLines(lines);
    const movingLines = computed?.movingLines || [];
    const parts = [
      `${systemTitle}起卦`,
      `所问 ${question}`,
      lines.map((line, index) => formatLineText(line, index)).join("，"),
      movingLines.length > 1
        ? `本轮出现多动爻，当前本地分支先取第${divinationState.movingLine}爻入算`
        : `动爻第${divinationState.movingLine}爻`,
      computed ? `数字 ${computed.upper} ${computed.lower} ${computed.movingLine}` : "",
    ];
    if (horizon) parts.push(`时间范围 ${horizon}`);
    if (background) parts.push(`补充背景 ${background}`);
    return `${parts.join("，")}。`;
  }
  if (divinationState.mode === "time") {
    if (!divinationState.timeSeed) return "";
    const parts = [
      `${systemTitle}起卦`,
      `所问 ${question}`,
      `现在是${divinationState.timeSeed}`,
      "按此刻起问时间起卦",
    ];
    if (horizon) parts.push(`时间范围 ${horizon}`);
    if (background) parts.push(`补充背景 ${background}`);
    return `${parts.join("，")}。`;
  }
  const { upper, lower, moving } = divinationState.dice;
  if (!upper || !lower || !moving) return "";
  const upperMeta = trigramCatalog[upper];
  const lowerMeta = trigramCatalog[lower];
  const parts = [
    `${systemTitle}起卦`,
    `所问 ${question}`,
    `数字 ${upper} ${lower} ${moving}`,
    `上卦 ${upperMeta?.label || upper}${upperMeta?.image ? `（${upperMeta.image}）` : ""}`,
    `下卦 ${lowerMeta?.label || lower}${lowerMeta?.image ? `（${lowerMeta.image}）` : ""}`,
    `动爻第${moving}爻`,
  ];
  if (horizon) parts.push(`时间范围 ${horizon}`);
  if (background) parts.push(`补充背景 ${background}`);
  return `${parts.join("，")}。`;
}

function renderDivinationDiceBoard() {
  if (!els.divinationDiceBoard) return;
  const slots = [
    { key: "upper", label: "上卦数", value: divinationState.dice.upper },
    { key: "lower", label: "下卦数", value: divinationState.dice.lower },
    { key: "moving", label: "动爻数", value: divinationState.dice.moving },
  ];
  els.divinationDiceBoard.innerHTML = "";
  slots.forEach((slot) => {
    const value = slot.value || "未定";
    const meta = slot.key === "moving" ? null : trigramCatalog[Number(slot.value)] || null;
    const node = document.createElement("div");
    node.className = "divination-die";
    node.innerHTML = `
      <span class="divination-die-label">${slot.label}</span>
      <strong>${value}</strong>
      <span>${meta ? `${meta.label} ${meta.image}` : slot.key === "moving" && slot.value ? `${slot.value} 爻` : "摇出后自动显示"}</span>
    `;
    els.divinationDiceBoard.appendChild(node);
  });
}

function renderDivinationLineBoard() {
  if (!els.divinationLineBoard) return;
  els.divinationLineBoard.innerHTML = "";
  for (let index = 5; index >= 0; index -= 1) {
    const line = divinationState.lines[index];
    const node = document.createElement("div");
    node.className = `divination-line ${line ? (line.value ? "yang" : "yin") : "pending"} ${line?.moving ? "moving" : ""}`;
    const label = line ? formatLineText(line, index) : `${linePositionLabels[index]} 待摇`;
    node.innerHTML = `
      <div class="divination-line-bars">
        <span class="divination-line-bar"></span>
        <span class="divination-line-gap"></span>
        <span class="divination-line-bar"></span>
      </div>
      <span class="divination-line-label">${label}</span>
    `;
    if (line?.value) {
      node.classList.add("solid");
    }
    els.divinationLineBoard.appendChild(node);
  }
}

function syncDivinationPrompt() {
  const prompt = divinationPromptFromState();
  if (els.guideQuestionInput) {
    els.guideQuestionInput.value = prompt;
  }
  syncDivinationStepState();
}

function updateDivinationResultText(message = "") {
  if (!els.divinationResultText) return;
  if (message) {
    els.divinationResultText.textContent = message;
    return;
  }
  if (divinationState.mode === "lines" && divinationState.lines.length) {
    const summary = divinationState.lines.map((line, index) => formatLineText(line, index)).join("，");
    const computed = computeDivinationFromLines(divinationState.lines);
    const movingLines = computed?.movingLines || [];
    const note = movingLines.length > 1 ? ` 当前先取第${computed?.movingLine}爻入算。` : "";
    els.divinationResultText.textContent = `本轮已摇出：${summary}。${note}`.trim();
    return;
  }
  if (divinationState.mode === "time" && divinationState.timeSeed) {
    els.divinationResultText.textContent = `已记录此刻起问时点：${divinationState.timeSeed}。`;
    return;
  }
  if (divinationState.dice.upper && divinationState.dice.lower && divinationState.dice.moving) {
    const upper = trigramCatalog[divinationState.dice.upper];
    const lower = trigramCatalog[divinationState.dice.lower];
    els.divinationResultText.textContent = `本轮数字起卦：${divinationState.dice.upper} ${divinationState.dice.lower} ${divinationState.dice.moving}，上卦${upper?.label || ""}，下卦${lower?.label || ""}，动爻第${divinationState.dice.moving}爻。`;
    return;
  }
  els.divinationResultText.textContent = "先写问题，再摇卦或取此刻时点，系统会把起卦信息写入提问框。";
}

function resetDivinationState(systemKey = divinationState.systemKey || "") {
  divinationState = {
    systemKey,
    mode: systemKey === "yijing_and_symbolism" ? "dice" : "lines",
    dice: { upper: null, lower: null, moving: null },
    lines: [],
    movingLine: null,
    timeSeed: null,
  };
  els.divinationModeButtons.forEach((button) => {
    const active = button.dataset.divinationMode === divinationState.mode;
    button.classList.toggle("active", active);
  });
  renderDivinationDiceBoard();
  renderDivinationLineBoard();
  updateDivinationResultText();
  syncDivinationStepState();
}

function syncDivinationWorkbench(system) {
  const show = divinationSystemKeys.has(system?.key || "");
  els.divinationWorkbench?.classList.toggle("hidden", !show);
  if (els.divinationWorkbench) els.divinationWorkbench.dataset.active = show ? "true" : "false";
  if (!show) return;
  divinationState.systemKey = system.key;
  if (els.divinationQuestionInput) els.divinationQuestionInput.value = "";
  if (els.divinationHorizonInput) els.divinationHorizonInput.value = "";
  if (els.divinationBackgroundInput) els.divinationBackgroundInput.value = "";
  if (els.guideQuestionInput) els.guideQuestionInput.value = "";
  if (els.divinationWorkbenchTitle) {
    els.divinationWorkbenchTitle.textContent = system.key === "liuyao_and_meihua" ? "六爻起卦台" : "易经象数起卦台";
  }
  if (els.divinationWorkbenchIntro) {
    els.divinationWorkbenchIntro.textContent = system.key === "liuyao_and_meihua"
      ? "先落具体问题，再用六次摇卦或三骰取数。系统会把起卦过程整理成可直接实算的提问。"
      : "先落具体问题，再用三骰取数或此刻起问时点起卦。系统会把象数信息自动写回提问框。";
  }
  setGuideQuestionMeta("最终起算问法", "上面的起卦动作会自动把结果整理到这里，你只需要检查是否符合你的本意。");
  resetDivinationState(system.key);
}

function applyDivinationMode(mode) {
  if (!divinationSystemKeys.has(divinationState.systemKey) || !mode) return;
  divinationState.dice = { upper: null, lower: null, moving: null };
  divinationState.lines = [];
  divinationState.movingLine = null;
  divinationState.timeSeed = null;
  divinationState.mode = mode;
  els.divinationModeButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.divinationMode === mode);
  });
  renderDivinationDiceBoard();
  renderDivinationLineBoard();
  if (els.guideQuestionInput) {
    els.guideQuestionInput.value = "";
  }
  updateDivinationResultText();
  syncDivinationStepState();
}

function rollDivinationDice() {
  divinationState.dice = {
    upper: Math.floor(Math.random() * 8) + 1,
    lower: Math.floor(Math.random() * 8) + 1,
    moving: Math.floor(Math.random() * 6) + 1,
  };
  divinationState.lines = [];
  divinationState.movingLine = divinationState.dice.moving;
  divinationState.timeSeed = null;
  renderDivinationDiceBoard();
  renderDivinationLineBoard();
  syncDivinationPrompt();
  updateDivinationResultText();
  setStatus("数字起卦完成，已把上卦、下卦和动爻带入提问框");
}

function rollDivinationLine() {
  if (divinationState.lines.length >= 6) {
    setStatus("六爻已经摇满了，可以重置后再来一轮");
    return;
  }
  const throws = Array.from({ length: 3 }, () => (Math.random() > 0.5 ? 3 : 2));
  const total = throws.reduce((sum, value) => sum + value, 0);
  const meta = lineMetaFromTotal(total);
  divinationState.lines.push({ ...meta, total, throws });
  const computed = computeDivinationFromLines(divinationState.lines);
  if (computed) {
    divinationState.dice.upper = computed.upper;
    divinationState.dice.lower = computed.lower;
    divinationState.dice.moving = computed.movingLine;
    divinationState.movingLine = computed.movingLine;
  }
  divinationState.timeSeed = null;
  renderDivinationLineBoard();
  renderDivinationDiceBoard();
  if (divinationState.lines.length === 6) {
    syncDivinationPrompt();
    updateDivinationResultText();
    setStatus("六次摇卦完成，已把六爻结果写入提问框");
  } else {
    updateDivinationResultText(`已摇出${divinationState.lines.length}爻，还差${6 - divinationState.lines.length}爻。`);
    setStatus(`已摇出第${divinationState.lines.length}爻，继续摇下一爻`);
  }
}

function stampDivinationTimeSeed() {
  divinationState.timeSeed = currentShanghaiTimeStamp();
  divinationState.lines = [];
  divinationState.dice = { upper: null, lower: null, moving: null };
  divinationState.movingLine = null;
  renderDivinationDiceBoard();
  renderDivinationLineBoard();
  syncDivinationPrompt();
  updateDivinationResultText();
  setStatus("已记录此刻起问时点，并写入提问框");
}

function bindDivinationWorkbench() {
  els.divinationModeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      applyDivinationMode(button.dataset.divinationMode || "");
      const statusMap = {
        dice: "已切到三骰取数",
        lines: "已切到六次摇卦",
        time: "已切到此刻起卦",
      };
      setStatus(statusMap[button.dataset.divinationMode || ""] || "起卦方式已切换");
    });
  });
  [els.divinationQuestionInput, els.divinationHorizonInput, els.divinationBackgroundInput].forEach((node) => {
    node?.addEventListener("input", () => {
      syncDivinationPrompt();
      syncDivinationStepState();
    });
  });
  els.divinationRollButton?.addEventListener("click", () => {
    if (!(els.divinationQuestionInput?.value || "").trim()) {
      els.divinationQuestionInput?.focus();
      setStatus("先把这次到底想问什么写清楚，再起卦");
      return;
    }
    if (divinationState.mode === "lines") {
      rollDivinationLine();
      return;
    }
    if (divinationState.mode === "time") {
      stampDivinationTimeSeed();
      return;
    }
    rollDivinationDice();
  });
  els.divinationQuickButton?.addEventListener("click", () => {
    if (!(els.divinationQuestionInput?.value || "").trim()) {
      els.divinationQuestionInput?.focus();
      setStatus("先把这次到底想问什么写清楚，再生成");
      return;
    }
    if (divinationState.mode === "lines") {
      while (divinationState.lines.length < 6) {
        const throws = Array.from({ length: 3 }, () => (Math.random() > 0.5 ? 3 : 2));
        const total = throws.reduce((sum, value) => sum + value, 0);
        divinationState.lines.push({ ...lineMetaFromTotal(total), total, throws });
      }
      const computed = computeDivinationFromLines(divinationState.lines);
      if (computed) {
        divinationState.dice.upper = computed.upper;
        divinationState.dice.lower = computed.lower;
        divinationState.dice.moving = computed.movingLine;
        divinationState.movingLine = computed.movingLine;
      }
      divinationState.timeSeed = null;
      renderDivinationLineBoard();
      renderDivinationDiceBoard();
      syncDivinationPrompt();
      updateDivinationResultText();
      setStatus("六次摇卦已一次生成，结果已写入提问框");
      return;
    }
    if (divinationState.mode === "time") {
      stampDivinationTimeSeed();
      return;
    }
    rollDivinationDice();
  });
  els.divinationResetButton?.addEventListener("click", () => {
    resetDivinationState(divinationState.systemKey);
    if (els.guideQuestionInput) {
      els.guideQuestionInput.value = "";
    }
    setStatus("起卦台已重置，可以重新起一轮");
    syncDivinationStepState();
  });
}

function buildPhysiognomyPrompt() {
  const context = cleanPromptSegment(els.physiognomyContextSelect?.value || "");
  const goal = cleanPromptSegment(els.physiognomyGoalInput?.value || "");
  const notes = cleanPromptSegment(els.physiognomyNotesInput?.value || "");
  const traits = [...physiognomyState.selectedTraits];
  if (!traits.length && !goal && !notes) return "";
  const parts = [];
  if (traits.length) parts.push(traits.join("、"));
  if (notes) parts.push(notes);
  if (context) parts.push(/观察$/u.test(context) ? context : `${context}观察`);
  if (goal) parts.push(`想看${goal}`);
  return parts.join("，");
}

function renderPhysiognomyPreviewList() {
  if (!els.physiognomyPreviewList) return;
  els.physiognomyPreviewList.innerHTML = "";
  physiognomyState.previewUrls.forEach((url, index) => {
    const item = document.createElement("figure");
    item.className = "physiognomy-preview-item";
    item.innerHTML = `<img src="${url}" alt="观察图片 ${index + 1}">`;
    els.physiognomyPreviewList.appendChild(item);
  });
  if (els.physiognomyImageHint) {
    els.physiognomyImageHint.textContent = physiognomyState.previewUrls.length
      ? "图片只做观察辅助与自检预览，当前本地相术模块仍以你填写的描述为准。"
      : "可上传正面照片或截图做观察辅助；当前本地模块不会直接读像素，只会使用你勾选和填写的描述。";
  }
}

function syncPhysiognomyPrompt() {
  const prompt = buildPhysiognomyPrompt();
  if (els.guideQuestionInput) {
    els.guideQuestionInput.value = prompt;
  }
  if (els.physiognomySelectedSummary) {
    els.physiognomySelectedSummary.textContent = prompt || "还没有形成稳定观察记录。";
  }
  syncPhysiognomyStepState();
}

function renderPhysiognomyTraitGroups() {
  if (!els.physiognomyTraitGroups) return;
  els.physiognomyTraitGroups.innerHTML = "";
  physiognomyTraitGroups.forEach((group) => {
    const section = document.createElement("section");
    section.className = "physiognomy-trait-group";
    const chips = group.traits.map((trait) => {
      const active = physiognomyState.selectedTraits.has(trait);
      return `<button class="physiognomy-chip ${active ? "active" : ""}" type="button" data-trait="${trait}">${trait}</button>`;
    }).join("");
    section.innerHTML = `
      <h4>${group.label}</h4>
      <div class="physiognomy-chip-row">${chips}</div>
    `;
    els.physiognomyTraitGroups.appendChild(section);
  });
  els.physiognomyTraitGroups.querySelectorAll("[data-trait]").forEach((button) => {
    button.addEventListener("click", () => {
      const trait = button.getAttribute("data-trait") || "";
      if (!trait) return;
      if (physiognomyState.selectedTraits.has(trait)) {
        physiognomyState.selectedTraits.delete(trait);
      } else {
        physiognomyState.selectedTraits.add(trait);
      }
      renderPhysiognomyTraitGroups();
      syncPhysiognomyPrompt();
    });
  });
}

function resetPhysiognomyWorkbench() {
  physiognomyState.selectedTraits = new Set();
  physiognomyState.previewUrls.forEach((url) => URL.revokeObjectURL(url));
  physiognomyState.previewUrls = [];
  if (els.physiognomyContextSelect) els.physiognomyContextSelect.value = "日间正面照片";
  if (els.physiognomyGoalInput) els.physiognomyGoalInput.value = "";
  if (els.physiognomyNotesInput) els.physiognomyNotesInput.value = "";
  if (els.physiognomyImageInput) els.physiognomyImageInput.value = "";
  renderPhysiognomyTraitGroups();
  renderPhysiognomyPreviewList();
  syncPhysiognomyPrompt();
}

function syncPhysiognomyWorkbench(system) {
  const show = system?.key === "physiognomy";
  els.physiognomyWorkbench?.classList.toggle("hidden", !show);
  if (els.physiognomyWorkbench) els.physiognomyWorkbench.dataset.active = show ? "true" : "false";
  if (!show) return;
  setGuideQuestionMeta("最终观察问法", "先在观察台把场景和特征整理好，这里会自动汇总成最终提问。");
  resetPhysiognomyWorkbench();
}

function bindPhysiognomyWorkbench() {
  [els.physiognomyContextSelect, els.physiognomyGoalInput, els.physiognomyNotesInput].forEach((node) => {
    node?.addEventListener("input", () => {
      syncPhysiognomyPrompt();
    });
    node?.addEventListener("change", () => {
      syncPhysiognomyPrompt();
    });
  });
  els.physiognomyImageInput?.addEventListener("change", () => {
    physiognomyState.previewUrls.forEach((url) => URL.revokeObjectURL(url));
    physiognomyState.previewUrls = [];
    const files = [...(els.physiognomyImageInput?.files || [])].slice(0, 3);
    physiognomyState.previewUrls = files.map((file) => URL.createObjectURL(file));
    renderPhysiognomyPreviewList();
    setStatus(files.length ? "已载入观察图片预览，请继续勾选并描述可见特征" : "已清空观察图片");
    syncPhysiognomyStepState();
  });
  els.physiognomyFill?.addEventListener("click", () => {
    syncPhysiognomyPrompt();
    if (!(els.guideQuestionInput?.value || "").trim()) {
      setStatus("先勾选你观察到的部位特征，或者补几句描述");
      return;
    }
    setStatus("相术观察记录已写入提问框");
  });
  els.physiognomyReset?.addEventListener("click", () => {
    resetPhysiognomyWorkbench();
    if (els.guideQuestionInput) {
      els.guideQuestionInput.value = "";
    }
    setStatus("相术观察台已重置");
    syncPhysiognomyStepState();
  });
}

function shuffleArray(items) {
  const values = [...items];
  for (let i = values.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [values[i], values[j]] = [values[j], values[i]];
  }
  return values;
}

function formatTarotCard(card) {
  if (!card) return "";
  return `${card.name}${card.orientation === "reversed" ? "逆位" : "正位"}`;
}

function tarotPromptFromState(questionText = "") {
  const slots = tarotSpreadPresets[tarotState.spread] || tarotSpreadPresets.three_card;
  const spreadLabel = tarotState.spread === "single" ? "单张牌" : tarotState.spread === "celtic_cross" ? "凯尔特十字牌阵" : "三张牌";
  const cardText = tarotState.drawn.map((card) => formatTarotCard(card)).join("、");
  const detailText = tarotState.drawn.map((card, index) => `${slots[index]?.label || `位置${index + 1}`}是${formatTarotCard(card)}`).join("，");
  const question = questionText || "想问当前局势的走向。";
  return `${spreadLabel}分别是${cardText}。${detailText}。${question}`;
}

function renderTarotBoard() {
  if (!els.tarotSpreadBoard) return;
  const slots = tarotSpreadPresets[tarotState.spread] || tarotSpreadPresets.three_card;
  els.tarotSpreadBoard.innerHTML = "";
  slots.forEach((slot, index) => {
    const drawn = tarotState.drawn[index];
    const node = document.createElement("button");
    node.type = "button";
    node.className = `tarot-card-slot ${drawn ? "revealed" : "hidden-card"}`;
    node.dataset.index = String(index);
    node.innerHTML = drawn
      ? `
        <span class="tarot-card-label">${slot.label}</span>
        <span class="tarot-card-name">${drawn.name}</span>
        <span class="tarot-card-orientation">${drawn.orientation === "reversed" ? "逆位" : "正位"}</span>
      `
      : `
        <span class="tarot-card-label">${slot.label}</span>
        <span class="tarot-card-back">未翻开</span>
      `;
    node.addEventListener("click", () => {
      if (!tarotState.dealStarted) {
        setStatus("先点开始翻牌，再按顺序翻开每一张牌");
        syncTarotStepState();
        return;
      }
      if (tarotState.drawn[index]) return;
      const next = tarotState.deck.shift();
      if (!next) return;
      tarotState.drawn[index] = next;
      renderTarotBoard();
      const allDone = tarotState.drawn.filter(Boolean).length === slots.length;
      if (allDone) {
        const prompt = tarotPromptFromState((els.guideQuestionInput?.value || "").trim());
        if (els.tarotResultText) {
          els.tarotResultText.textContent = `本轮牌面：${tarotState.drawn.map(formatTarotCard).join("、")}。`;
        }
        if (els.guideQuestionInput) {
          els.guideQuestionInput.value = prompt;
        }
        setStatus("塔罗翻牌完成，牌面已带入提问框");
      }
      syncTarotStepState();
    });
    els.tarotSpreadBoard.appendChild(node);
  });
  syncTarotStepState();
}

function resetTarotWorkbench() {
  tarotState = {
    spread: els.tarotSpreadSelect?.value || tarotState.spread || "three_card",
    deck: shuffleArray(
      tarotDeck.map((name) => ({
        name,
        orientation: Math.random() > 0.5 ? "upright" : "reversed",
      })),
    ),
    drawn: [],
    dealStarted: false,
  };
  renderTarotBoard();
  if (els.tarotResultText) {
    const slots = tarotSpreadPresets[tarotState.spread] || tarotSpreadPresets.three_card;
    els.tarotResultText.textContent = `牌阵已就位，共 ${slots.length} 张，按顺序翻开即可。`;
  }
}

function syncTarotWorkbench(system) {
  const show = system?.key === "tarot";
  els.tarotWorkbench?.classList.toggle("hidden", !show);
  if (els.tarotWorkbench) els.tarotWorkbench.dataset.active = show ? "true" : "false";
  if (!show) return;
  if (els.tarotSpreadSelect && !els.tarotSpreadSelect.value) {
    els.tarotSpreadSelect.value = "three_card";
  }
  setGuideQuestionMeta("塔罗最终问法", "先写问题，再启牌翻牌；牌面会自动整理成最终提问。");
  resetTarotWorkbench();
}

function bindTarotWorkbench() {
  els.tarotSpreadSelect?.addEventListener("change", () => {
    tarotState.spread = els.tarotSpreadSelect?.value || "three_card";
    resetTarotWorkbench();
    setStatus("牌阵已切换，可以重新洗牌并翻牌");
  });
  els.tarotShuffle?.addEventListener("click", () => {
    resetTarotWorkbench();
    setStatus("塔罗牌已洗好，先想清楚问题，再开始翻牌");
  });
  els.tarotDeal?.addEventListener("click", () => {
    if (!(els.guideQuestionInput?.value || "").trim()) {
      els.guideQuestionInput?.focus();
      setStatus("先把这次想问的事情写清楚，再开始翻牌");
      syncTarotStepState();
      return;
    }
    tarotState.dealStarted = true;
    if (!tarotState.deck.length) {
      resetTarotWorkbench();
      tarotState.dealStarted = true;
    } else {
      renderTarotBoard();
    }
    if (els.tarotResultText) {
      const slots = tarotSpreadPresets[tarotState.spread] || tarotSpreadPresets.three_card;
      els.tarotResultText.textContent = `请依次翻开 ${slots.length} 张牌，系统会把牌面自动写回提问框。`;
    }
    setStatus("牌阵已展开，按顺序翻开每一张牌");
    syncTarotStepState();
  });
}

function bindPlanetGuideNodes() {
  if (!els.planetField) return;
  if (els.planetField.dataset.guideBound === "true") return;
  els.planetField.dataset.guideBound = "true";
  els.planetField.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target.closest(".planet-node") : null;
    if (!target) return;
    const key = target.getAttribute("data-system-key") || "";
    const byKey = key ? systems.find((item) => item?.key === key) : null;
    const title = (target.querySelector(".planet-name")?.textContent || "").trim();
    const label = target.getAttribute("aria-label") || target.getAttribute("title") || "";
    const system = byKey || getSystemByKey(key) || getSystemByTitle(title) || getSystemByTitle(label);
    if (!system) return;
    setStatus(`${sanitizeSystemTitle(system)}：完成度 ${system.score}%${system.calculatorImplemented ? "，已接入本地实算" : system.calculatorReady ? "，已有计算规则但还没完全接入实算" : ""}`);
    openGuide(system);
  });
}

function renderPlanets(items) {
  els.planetField.innerHTML = "";
  planetNodes = new Map();
  const positions = buildPlanetPositions(items.length);
  items.forEach((system, index) => {
    const title = sanitizeSystemTitle(system);
    const profile = deityProfiles[system.key] || {};
    const [a, b, c] = profile.colors || colorFor(index);
    const [x, y] = positions[index] || [50, 50];
    const glyph = profile.glyph || divineGlyphs[index % divineGlyphs.length];
    const statusMark = system.calculatorImplemented ? "可直断" : system.calculatorReady ? "待启算" : `${system.score}%`;
    const statusMeta = system.calculatorImplemented ? " 已实装" : system.calculatorReady ? " 有规则" : "";
    const node = document.createElement("button");
    node.type = "button";
    const angleDeg = Number((((Math.atan2(y - 49.5, x - 50) * 180) / Math.PI) + 90 + 360) % 360).toFixed(2);
    const anchorClass = y <= 18
      ? "anchor-top"
      : y >= 82
        ? "anchor-bottom"
        : x <= 14
          ? "anchor-left"
          : x >= 86
            ? "anchor-right"
            : "anchor-arc";
    node.className = `planet-node compass-node ${anchorClass} ${profile.className || ""} ${system.status || ""} ${system.calculatorReady ? "calculator" : ""}`;
    node.style.setProperty("--x", `${x}%`);
    node.style.setProperty("--y", `${y}%`);
    node.style.setProperty("--angle", `${angleDeg}deg`);
    node.style.setProperty("--planet-a", a);
    node.style.setProperty("--planet-b", b);
    node.style.setProperty("--planet-c", c);
    node.style.setProperty("--delay", `${index * 18}ms`);
    node.style.setProperty("--float-speed", `${8 + (index % 6)}s`);
    node.title = `${title} ${system.score}%${statusMeta}`;
    node.setAttribute("aria-label", `${title}，完成度 ${system.score}%${statusMeta}`);
    node.dataset.systemKey = system.key || "";
    node.innerHTML = `
      <span class="compass-node-inner">
        <span class="compass-node-body">
          <span class="planet-thread"></span>
          <span class="planet-crown"></span>
          <span class="planet-orbit"></span>
          <span class="planet-sphere"><span class="planet-glyph">${glyph}</span></span>
          <span class="planet-nameplate">
            <span class="planet-nameplate-edge planet-nameplate-edge-start"></span>
            <span class="planet-nameplate-main">
              <span class="planet-name">${title}</span>
              <span class="planet-mark">${statusMark}</span>
            </span>
            <span class="planet-nameplate-edge planet-nameplate-edge-end"></span>
          </span>
        </span>
      </span>
    `;
    els.planetField.appendChild(node);
    planetNodes.set(system.key, node);
    planetNodes.set(title, node);
  });
}

function renderProgress(items) {
  els.progressList.innerHTML = "";
  items.forEach((system) => {
    const title = sanitizeSystemTitle(system);
    const progressMeta = system.calculatorImplemented ? " / 已实装" : system.calculatorReady ? " / 有规则" : "";
    const card = document.createElement("article");
    card.className = "progress-card";
    card.innerHTML = `
      <strong>${title}</strong>
      <span>${system.score}%${progressMeta}</span>
      <div class="progress-bar"><div class="progress-fill" style="--score:${system.score}%"></div></div>
      <p>${system.summary || `${title} 已纳入神域卷宗。`}</p>
    `;
    els.progressList.appendChild(card);
  });
}

async function loadProgress() {
  try {
    const response = await fetch("/api/progress");
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "资料库读取失败");
    systems = Array.isArray(data.systems) ? data.systems : [];
    els.overallPercent.textContent = `${data.overallPercent || 0}%`;
    els.overallMeta.textContent = `深度 ${data.completedDeepCount || 0} / 已实装 ${systems.filter((item) => item.calculatorImplemented).length} / 有规则 ${systems.filter((item) => item.calculatorReady).length}`;
    renderPlanets(systems);
    bindPlanetGuideNodes();
    renderProgress(systems);
    progressLoaded = true;
    setStatus("诸术总盘已就位，你只需先问");
  } catch (error) {
    setStatus(error.message);
  }
}

let planetLayoutCompact = window.innerWidth <= 720;
window.addEventListener("resize", () => {
  const nextCompact = window.innerWidth <= 720;
  if (nextCompact === planetLayoutCompact) return;
  planetLayoutCompact = nextCompact;
  if (systems.length) renderPlanets(systems);
});

function addModelOption(model, selected = false) {
  if (!els.modelSelect) return;
  const option = document.createElement("option");
  option.value = model;
  option.textContent = displayModelName(model);
  option.selected = selected;
  els.modelSelect.appendChild(option);
}

async function loadModels() {
  if (!els.modelSelect) return;
  try {
    const response = await fetch("/api/models");
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "模型列表读取失败");
    const models = data.models || [];
    els.modelSelect.innerHTML = "";
    if (!models.length) {
      addModelOption(data.default || "auto", true);
      return;
    }
    models.forEach((model) => addModelOption(model, model === data.default));
  } catch {
    els.modelSelect.innerHTML = "";
    addModelOption("auto", true);
    addModelOption("local-vault", false);
  }
}

function renderList(target, items) {
  target.innerHTML = "";
  const values = Array.isArray(items) && items.length ? items : ["暂无"];
  values.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = typeof item === "string" ? item : JSON.stringify(item);
    target.appendChild(li);
  });
}

function diagnosticStatusLabel(status) {
  const labels = {
    answered: "已参与实算",
    computable: "可参与但本轮未采用",
    missing_inputs: "缺少必要条件",
    not_applicable: "当前问题不适用",
    calculator_unavailable: "规则已建，实算未接通",
    compute_error: "当前问法不足以稳定起算",
  };
  return labels[status] || "状态未明";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

const fengshuiPoiLabelMap = {
  hospital: "医院",
  funeral: "殡葬场所",
  school: "学校",
  mall: "商业综合体",
  park: "公园绿地",
  water: "水系",
  bridge: "桥梁",
  elevated: "高架/快速路",
  subway: "地铁站",
  government: "政府设施",
};

const fengshuiVerdictLabelMap = {
  supportive: "外局偏可用",
  mixed: "外局需结合细节",
  caution: "外局需谨慎复核",
};

function normalizeFengshuiMapInsight(source = {}) {
  const mapContext = source?.mapContext || source?.map_context || source || {};
  const externalEnvironment = source?.externalEnvironment || source?.external_environment || mapContext?.external_environment || {};
  const rawStatus = mapContext.map_status || mapContext.mapStatus || source?.mapStatus || {};
  const warnings = Array.isArray(rawStatus?.warnings)
    ? rawStatus.warnings.map((item) => String(item || "").trim()).filter(Boolean)
    : [];
  const nextSignals = Array.isArray(source?.nextSignals || source?.next_signals)
    ? (source.nextSignals || source.next_signals).map((item) => String(item || "").trim()).filter(Boolean)
    : [];
  const rawPoiSummary = mapContext.poi_summary || mapContext.poiSummary || source?.poiSummary || {};
  const poiSummary = rawPoiSummary && typeof rawPoiSummary === "object" ? rawPoiSummary : {};
  const address = [
    source?.address,
    mapContext?.address,
    source?.title,
    mapContext?.title,
    source?.fallbackAddress,
  ].map((item) => String(item || "").trim()).find(Boolean) || "";
  return {
    address,
    staticMapUrl: String(source?.staticMapUrl || mapContext?.staticMapUrl || mapContext?.static_map_url || "").trim(),
    poiSummary,
    mapStatus: {
      poiSearch: String(rawStatus?.poiSearch || rawStatus?.poi_search || "").trim(),
      warnings,
    },
    summary: String(source?.summary || mapContext?.summary || "").trim(),
    nextSignals,
    externalEnvironment: externalEnvironment && typeof externalEnvironment === "object" ? externalEnvironment : {},
  };
}

function renderFengshuiMapEmptyPanel(message, options = {}) {
  const panelClass = ["fengshui-map-panel", "is-empty", options.inline ? "is-inline" : ""].filter(Boolean).join(" ");
  return `
    <section class="${panelClass}">
      <div class="fengshui-map-head">
        <div>
          <p class="fengshui-map-eyebrow">地图外局</p>
          <h4>${escapeHtml(options.title || "地图外局暂未生成")}</h4>
        </div>
        <span class="fengshui-map-badge">${escapeHtml(options.badge || "待补充")}</span>
      </div>
      <p class="fengshui-map-empty">${escapeHtml(message)}</p>
    </section>
  `;
}

function renderFengshuiMapPanel(source = {}, options = {}) {
  const insight = normalizeFengshuiMapInsight(source);
  const address = insight.address || "地址已定位";
  const verdictKey = String(insight.externalEnvironment?.verdict || "").trim();
  const verdictLabel = fengshuiVerdictLabelMap[verdictKey] || "外局初筛";
  const summaryText = insight.summary || (
    insight.mapStatus.poiSearch === "quota_exceeded"
      ? "当前周边 POI 外局信号已降级，可先结合定位与卫星视角做初筛。"
      : "已完成地址定位，可先结合卫星视角做外局初筛。"
  );
  const poiRows = Object.entries(insight.poiSummary).slice(0, 6).map(([key, value]) => {
    const item = value || {};
    const count = item.count ?? 0;
    const nearest = item.nearest_distance ?? item.nearestDistance;
    return `
      <div class="fengshui-poi-row">
        <span>${escapeHtml(fengshuiPoiLabelMap[key] || key)}</span>
        <strong>${escapeHtml(count)}${nearest ? ` · 最近 ${escapeHtml(nearest)}m` : ""}</strong>
      </div>
    `;
  }).join("");
  const supportNotes = [
    ...(Array.isArray(insight.externalEnvironment?.supportive) ? insight.externalEnvironment.supportive : []),
    ...(Array.isArray(insight.externalEnvironment?.signals) ? insight.externalEnvironment.signals : []),
  ].map((item) => String(item || "").trim()).filter(Boolean).slice(0, 4);
  const cautionNotes = Array.isArray(insight.externalEnvironment?.cautions)
    ? insight.externalEnvironment.cautions.map((item) => String(item || "").trim()).filter(Boolean).slice(0, 4)
    : [];
  const warningNotes = insight.mapStatus.warnings.slice(0, 3);
  const nextSignals = insight.nextSignals.slice(0, 3);
  const panelClass = ["fengshui-map-panel", options.inline ? "is-inline" : ""].filter(Boolean).join(" ");
  return `
    <section class="${panelClass}">
      <div class="fengshui-map-head">
        <div>
          <p class="fengshui-map-eyebrow">地图外局</p>
          <h4>${escapeHtml(address)}</h4>
        </div>
        <div class="fengshui-map-badges">
          <span class="fengshui-map-badge${verdictKey === "caution" ? " is-caution" : ""}">${escapeHtml(verdictLabel)}</span>
          ${insight.mapStatus.poiSearch === "quota_exceeded" ? '<span class="fengshui-map-badge is-caution">外局信号降级</span>' : ""}
        </div>
      </div>
      ${summaryText ? `<p class="fengshui-map-summary">${escapeHtml(summaryText)}</p>` : ""}
      ${insight.staticMapUrl ? `
        <a class="fengshui-map-link" href="${escapeHtml(insight.staticMapUrl)}" target="_blank" rel="noreferrer">
          <img class="fengshui-map-image" src="${escapeHtml(insight.staticMapUrl)}" alt="房屋地图预览" />
        </a>
      ` : ""}
      ${warningNotes.length ? `
        <div class="fengshui-note-block is-caution">
          <p class="fengshui-note-title">当前提醒</p>
          <ul>${warningNotes.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </div>
      ` : ""}
      ${poiRows ? `<div class="fengshui-poi-grid">${poiRows}</div>` : (
        insight.mapStatus.poiSearch === "quota_exceeded"
          ? '<p class="fengshui-poi-empty">今日周边 POI 检索已降级，当前先按定位、卫星图与朝向做外局初筛。</p>'
          : ""
      )}
      ${supportNotes.length ? `
        <div class="fengshui-note-block">
          <p class="fengshui-note-title">可用信号</p>
          <ul>${supportNotes.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </div>
      ` : ""}
      ${cautionNotes.length ? `
        <div class="fengshui-note-block is-caution">
          <p class="fengshui-note-title">谨慎点</p>
          <ul>${cautionNotes.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </div>
      ` : ""}
      ${nextSignals.length ? `
        <div class="fengshui-map-next">
          <p class="fengshui-note-title">下一步补充</p>
          <div class="fengshui-signal-chip-row">
            ${nextSignals.map((item) => `<span class="fengshui-signal-chip">${escapeHtml(item)}</span>`).join("")}
          </div>
        </div>
      ` : ""}
    </section>
  `;
}

function renderGuideWorkbenchMapPreview() {
  const isFengshui = guideWorkbenchState.key === "fengshui";
  if (els.guideWorkbenchMapLookup) {
    els.guideWorkbenchMapLookup.hidden = !isFengshui;
    els.guideWorkbenchMapLookup.disabled = !isFengshui || guideWorkbenchMapState.loading;
    els.guideWorkbenchMapLookup.textContent = guideWorkbenchMapState.loading ? "速查中..." : "地图速查";
  }
  if (!els.guideWorkbenchMapPreview) return;
  if (!isFengshui) {
    els.guideWorkbenchMapPreview.hidden = true;
    els.guideWorkbenchMapPreview.innerHTML = "";
    return;
  }
  if (guideWorkbenchMapState.loading) {
    els.guideWorkbenchMapPreview.hidden = false;
    els.guideWorkbenchMapPreview.innerHTML = '<div class="guide-workbench-feedback">正在定位地址并读取地图外局，请稍候。</div>';
    return;
  }
  if (guideWorkbenchMapState.error) {
    els.guideWorkbenchMapPreview.hidden = false;
    els.guideWorkbenchMapPreview.innerHTML = `<div class="guide-workbench-feedback is-error">${escapeHtml(guideWorkbenchMapState.error)}</div>`;
    return;
  }
  if (guideWorkbenchMapState.data) {
    els.guideWorkbenchMapPreview.hidden = false;
    els.guideWorkbenchMapPreview.innerHTML = renderFengshuiMapPanel(guideWorkbenchMapState.data, { inline: true });
    return;
  }
  els.guideWorkbenchMapPreview.hidden = true;
  els.guideWorkbenchMapPreview.innerHTML = "";
}

function resetGuideWorkbenchMapPreview() {
  guideWorkbenchMapState = {
    loading: false,
    data: null,
    error: "",
    requestedAddress: "",
    requestedFacing: "",
  };
  renderGuideWorkbenchMapPreview();
}

async function previewGuideWorkbenchFengshuiMap() {
  if (guideWorkbenchState.key !== "fengshui") return;
  const values = readGuideWorkbenchValues();
  const address = String(values.address || "").trim();
  const facing = String(values.facing || "").trim();
  if (!address) {
    els.guideWorkbenchFields?.querySelector('[data-field-key="address"]')?.focus();
    setStatus("先填地址或场景，再做地图速查");
    return;
  }
  if (!facing) {
    els.guideWorkbenchFields?.querySelector('[data-field-key="facing"]')?.focus();
    setStatus("先填坐向或朝向，再做地图速查");
    return;
  }
  guideWorkbenchMapState = {
    loading: true,
    data: null,
    error: "",
    requestedAddress: address,
    requestedFacing: facing,
  };
  renderGuideWorkbenchMapPreview();
  setStatus("正在定位房屋并读取地图外局");
  try {
    const response = await fetch("/api/maps/property-context", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        address,
        facing_direction: facing,
      }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(String(payload?.error || "地图速查暂时不可用"));
    }
    guideWorkbenchMapState = {
      loading: false,
      data: payload,
      error: "",
      requestedAddress: address,
      requestedFacing: facing,
    };
    renderGuideWorkbenchMapPreview();
    const warnings = Array.isArray(payload?.mapStatus?.warnings) ? payload.mapStatus.warnings : [];
    setStatus(warnings.length ? "地图速查已完成，当前先展示降级外局结果" : "地图速查已完成，可以先看外局再决定如何推演");
  } catch (error) {
    guideWorkbenchMapState = {
      loading: false,
      data: null,
      error: String(error?.message || "地图速查失败，请稍后重试"),
      requestedAddress: address,
      requestedFacing: facing,
    };
    renderGuideWorkbenchMapPreview();
    setStatus(guideWorkbenchMapState.error);
  }
}

function findNamingAnswer(answers) {
  const values = Array.isArray(answers) ? answers : [];
  return values.find((answer) => {
    const profile = answer?.naming_profile;
    return (
      answer?.key === "name_studies" &&
      Array.isArray(profile?.top_candidates) &&
      profile.top_candidates.length
    );
  }) || null;
}

function renderNamingReport(answer) {
  if (!els.systemAnswerCards) return;
  const profile = answer?.naming_profile || {};
  const birthInfo = profile.birth_info || {};
  const baziSummary = profile.bazi_summary || {};
  const pillars = Array.isArray(baziSummary.pillars) ? baziSummary.pillars : [];
  const candidates = Array.isArray(profile.top_candidates) ? profile.top_candidates : [];
  const leadCandidate = candidates[0] || {};
  const surname = String(profile.surname || "").trim();
  const reportTitle = surname
    ? `${surname}氏命名详盘`
    : profile.purpose === "personal"
      ? "个人命名详盘"
      : "命名详盘";
  const pillarMap = new Map(pillars.map((item) => [item?.key, item || {}]));
  const orderedPillars = ["year", "month", "day", "hour"].map((key) => pillarMap.get(key) || {});
  const asText = (value, fallback = "未提供") => {
    const text = String(value || "").trim();
    return text || fallback;
  };
  const asJoin = (items, fallback = "未提供") => {
    const values = Array.isArray(items) ? items.map((item) => String(item || "").trim()).filter(Boolean) : [];
    return values.length ? values.join("、") : fallback;
  };
  const renderStack = (items) => {
    const values = Array.isArray(items) ? items.map((item) => String(item || "").trim()).filter(Boolean) : [];
    if (!values.length) return '<span class="naming-empty">--</span>';
    return values.map((item) => `<span>${escapeHtml(item)}</span>`).join("");
  };
  const renderInlineTags = (items, className = "naming-inline-tag") => {
    const values = Array.isArray(items) ? items.map((item) => String(item || "").trim()).filter(Boolean) : [];
    if (!values.length) return '<span class="naming-empty">--</span>';
    return values.map((item) => `<span class="${className}">${escapeHtml(item)}</span>`).join("");
  };
  const metaItems = [
    { label: "阳历", value: asText(birthInfo.solar_datetime) },
    { label: "农历", value: asText(birthInfo.lunar_text) },
    { label: "性别", value: asText(birthInfo.gender) },
    { label: "出生地", value: asText(birthInfo.birth_location) },
    {
      label: "日主",
      value: [baziSummary.day_master, baziSummary.day_master_element, baziSummary.day_master_polarity]
        .map((item) => String(item || "").trim())
        .filter(Boolean)
        .join(" / ") || "未提供",
    },
    { label: "日柱", value: asText(baziSummary.day_pillar) },
    { label: "季节", value: asText(baziSummary.season || birthInfo.season) },
    { label: "五行", value: asText(baziSummary.five_elements) },
  ];
  const metaMarkup = metaItems.map((item) => `
    <article class="naming-meta-card">
      <span>${escapeHtml(item.label)}</span>
      <strong>${escapeHtml(item.value)}</strong>
    </article>
  `).join("");
  const countItems = Array.isArray(baziSummary.five_element_counts) ? baziSummary.five_element_counts : [];
  const elementMarkup = countItems.length
    ? countItems
      .map((item) => `
        <span class="naming-element-chip">
          <em>${escapeHtml(item?.label || "")}</em>
          <strong>${escapeHtml(item?.value ?? "--")}</strong>
        </span>
      `)
      .join("")
    : '<span class="naming-empty">未提供五行分布</span>';
  const tendencyMarkup = `
    <article class="naming-tendency-card">
      <span>偏强</span>
      <strong>${escapeHtml(asJoin(baziSummary.strongest_elements, "未明"))}</strong>
    </article>
    <article class="naming-tendency-card">
      <span>偏弱</span>
      <strong>${escapeHtml(asJoin(baziSummary.weakest_elements, "未明"))}</strong>
    </article>
  `;
  const candidateRows = candidates.map((item, index) => {
    const reason = [
      item?.why_selected,
      item?.primary_finding,
      item?.birth_support_note,
    ].map((value) => String(value || "").trim()).find(Boolean) || "--";
    const source = [item?.source_title, item?.source_quote]
      .map((value) => String(value || "").trim())
      .filter(Boolean)
      .join(" · ") || "--";
    return `
      <tr>
        <td>${index + 1}</td>
        <td class="naming-name-cell">
          <strong>${escapeHtml(item?.name || "--")}</strong>
          ${item?.bridge_number ? `<span>桥接数 ${escapeHtml(item.bridge_number)}</span>` : ""}
        </td>
        <td>${renderInlineTags(item?.style_tags)}</td>
        <td>${renderInlineTags(item?.preferred_elements, "naming-inline-tag is-cyan")}</td>
        <td>${escapeHtml(asText(item?.meaning))}</td>
        <td>${escapeHtml(reason)}</td>
        <td>${escapeHtml(source)}</td>
      </tr>
    `;
  }).join("");

  els.systemAnswerCards.innerHTML = `
    <section class="naming-report">
      <header class="naming-report-head">
        <div class="naming-report-title">
          <p class="naming-report-eyebrow">命名详盘</p>
          <h3>${escapeHtml(reportTitle)}</h3>
        </div>
        ${leadCandidate?.name ? `
          <aside class="naming-report-lead">
            <span>首推名</span>
            <strong>${escapeHtml(leadCandidate.name)}</strong>
            <p>${escapeHtml(asJoin(leadCandidate.preferred_elements, "综合平衡"))}</p>
          </aside>
        ` : ""}
      </header>

      <section class="naming-meta-grid">
        ${metaMarkup}
      </section>

      <section class="naming-bazi-sheet">
        <div class="naming-sheet-head">
          <div>
            <p class="naming-sheet-eyebrow">生辰八字</p>
            <h4>四柱命局</h4>
          </div>
          ${baziSummary.note ? `<p class="naming-sheet-note">${escapeHtml(baziSummary.note)}</p>` : ""}
        </div>
        <div class="naming-bazi-table-wrap">
          <table class="naming-bazi-table">
            <thead>
              <tr>
                <th>项目</th>
                ${orderedPillars.map((item) => `<th>${escapeHtml(item?.label || "--")}</th>`).join("")}
              </tr>
            </thead>
            <tbody>
              <tr>
                <th>四柱</th>
                ${orderedPillars.map((item) => `<td>${escapeHtml(asText(item?.pillar, "--"))}</td>`).join("")}
              </tr>
              <tr>
                <th>十神</th>
                ${orderedPillars.map((item) => `<td>${escapeHtml(asText(item?.ten_god, "--"))}</td>`).join("")}
              </tr>
              <tr>
                <th>天干</th>
                ${orderedPillars.map((item) => `<td>${escapeHtml(asText(item?.stem, "--"))}</td>`).join("")}
              </tr>
              <tr>
                <th>地支</th>
                ${orderedPillars.map((item) => `<td>${escapeHtml(asText(item?.branch, "--"))}</td>`).join("")}
              </tr>
              <tr>
                <th>藏干</th>
                ${orderedPillars.map((item) => `<td><div class="naming-stack-list">${renderStack(item?.hidden_stems)}</div></td>`).join("")}
              </tr>
              <tr>
                <th>藏干十神</th>
                ${orderedPillars.map((item) => `<td><div class="naming-stack-list">${renderStack(item?.hidden_ten_gods)}</div></td>`).join("")}
              </tr>
            </tbody>
          </table>
        </div>
        <div class="naming-summary-strip">
          <div class="naming-element-strip">${elementMarkup}</div>
          <div class="naming-tendency-grid">${tendencyMarkup}</div>
        </div>
      </section>

      <section class="naming-candidates-section">
        <div class="naming-sheet-head">
          <div>
            <p class="naming-sheet-eyebrow">名字推荐</p>
            <h4>候选名字</h4>
          </div>
        </div>
        <div class="naming-candidates-table-wrap">
          <table class="naming-candidates-table">
            <thead>
              <tr>
                <th>序</th>
                <th>名字</th>
                <th>风格</th>
                <th>补益五行</th>
                <th>释义</th>
                <th>入选说明</th>
                <th>出处</th>
              </tr>
            </thead>
            <tbody>
              ${candidateRows || '<tr><td colspan="7">暂无候选名字</td></tr>'}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  `;
}

function renderSystemAnswerCards(answers, options = {}) {
  if (!els.systemAnswerCards) return;
  const append = options.append === true;
  const compactNaming = options.compactNaming === true;
  if (!append) {
    els.systemAnswerCards.innerHTML = "";
  }
  let mount = els.systemAnswerCards;
  if (append) {
    mount = els.systemAnswerCards.querySelector(".system-answer-card-grid");
    if (!mount) {
      mount = document.createElement("div");
      mount.className = "system-answer-card-grid";
      els.systemAnswerCards.appendChild(mount);
    }
    mount.innerHTML = "";
  }
  const values = Array.isArray(answers) ? answers : [];
  if (!values.length) {
    mount.innerHTML = '<div class="empty-result-card">本轮没有体系实际参与计算。</div>';
    return;
  }
  values.forEach((answer) => {
    const card = document.createElement("article");
    card.className = "system-answer-card";
    const systemName = displaySystemName(answer.key || answer.system);
    const missing = Array.isArray(answer.missing_inputs) && answer.missing_inputs.length
      ? `仍缺：${answer.missing_inputs.join("、")}`
      : answer.used_local_calculation ? "已完成本地实算" : "当前仅给资料层判断";
    const namingProfile = answer?.naming_profile;
    const rawResult = answer?.raw_result || {};
    const fengshuiMapContext = rawResult?.derived_factors?.map_context || rawResult?.used_inputs?.map_context || null;
    const fengshuiExternal = rawResult?.derived_factors?.external_environment || null;
    let namingBlock = "";
    let fengshuiBlock = "";
    if (!compactNaming && namingProfile && Array.isArray(namingProfile.top_candidates) && namingProfile.top_candidates.length) {
      const baziSummary = namingProfile.bazi_summary || {};
      const strongest = Array.isArray(baziSummary.strongest_elements) && baziSummary.strongest_elements.length
        ? baziSummary.strongest_elements.join("、")
        : "未明";
      const weakest = Array.isArray(baziSummary.weakest_elements) && baziSummary.weakest_elements.length
        ? baziSummary.weakest_elements.join("、")
        : "未明";
      const baziLines = [];
      if (baziSummary.day_pillar) baziLines.push(`日柱：${baziSummary.day_pillar}`);
      if (baziSummary.day_master) baziLines.push(`日主：${baziSummary.day_master}`);
      if (baziSummary.five_elements) baziLines.push(`五行：${baziSummary.five_elements}`);
      if (baziLines.length) {
        baziLines.push(`偏强：${strongest}`);
        baziLines.push(`偏弱：${weakest}`);
      }
      const leadCandidate = namingProfile.top_candidates[0] || {};
      const leadMeta = [
        leadCandidate.bridge_number ? `桥接数 ${leadCandidate.bridge_number}` : "",
        Array.isArray(leadCandidate.preferred_elements) && leadCandidate.preferred_elements.length
          ? `补偏 ${leadCandidate.preferred_elements.join("、")}`
          : "",
      ].filter(Boolean).join(" / ");
      const candidateCards = namingProfile.top_candidates.slice(0, 5).map((item, index) => {
        const tags = Array.isArray(item.style_tags) && item.style_tags.length
          ? `<p class="naming-chip-row">${item.style_tags.map((tag) => `<span class="naming-chip">${tag}</span>`).join("")}</p>`
          : "";
        const meta = [
          item.bridge_number ? `桥接数 ${item.bridge_number}` : "",
          Array.isArray(item.preferred_elements) && item.preferred_elements.length ? `倾向 ${item.preferred_elements.join("、")}` : "",
        ].filter(Boolean).join(" / ");
        const source = item.source_title ? `<p class="naming-candidate-source">${item.source_title}${item.source_quote ? ` · ${item.source_quote}` : ""}</p>` : "";
        return `
          <article class="naming-candidate-card${index === 0 ? " is-lead" : ""}">
            <div class="naming-candidate-head">
              <strong>${index === 0 ? "首选" : `备选 ${index}`}</strong>
              <span>${item.name || "未命名"}</span>
            </div>
            ${item.meaning ? `<p class="naming-candidate-meaning">${item.meaning}</p>` : ""}
            ${item.why_selected ? `<p class="naming-candidate-why">${item.why_selected}</p>` : ""}
            ${source}
            ${tags}
            ${meta ? `<p class="naming-candidate-meta">${meta}</p>` : ""}
          </article>
        `;
      }).join("");
      namingBlock = `
        <section class="naming-ritual-card">
          <div class="naming-ritual-head">
            <div>
              <p class="naming-ritual-eyebrow">宝宝起名结果</p>
              <h4>${namingProfile.surname || ""}${namingProfile.purpose === "personal" ? "正式姓名" : "命名方案"}</h4>
            </div>
            ${leadCandidate.name ? `
              <div class="naming-lead-oracle">
                <p class="naming-lead-label">本轮首荐</p>
                <strong>${leadCandidate.name}</strong>
                ${leadMeta ? `<span>${leadMeta}</span>` : ""}
              </div>
            ` : ""}
          </div>
          ${baziLines.length ? `
            <div class="naming-bazi-panel">
              <div class="naming-bazi-title-row">
                <p class="naming-bazi-title">先看八字结构</p>
                ${baziSummary.note ? `<span class="naming-bazi-note">${baziSummary.note}</span>` : ""}
              </div>
              <div class="naming-bazi-grid">
                ${baziLines.map((line) => `<p>${line}</p>`).join("")}
              </div>
            </div>
          ` : ""}
          <div class="naming-candidate-grid">
            ${candidateCards}
          </div>
        </section>
      `;
    }
    if ((answer.key === "fengshui" || answer.system === "风水") && fengshuiMapContext) {
      fengshuiBlock = renderFengshuiMapPanel({
        mapContext: fengshuiMapContext,
        externalEnvironment: fengshuiExternal,
        fallbackAddress: rawResult?.used_inputs?.location_or_floorplan || "",
      });
    } else if (answer.key === "fengshui" || answer.system === "风水") {
      fengshuiBlock = renderFengshuiMapEmptyPanel(
        "这一轮还没有拿到地址级地图结果，当前只做了朝向与场景粗筛。补充地址、楼栋或先用风水起算台里的地图速查，再做完整风水判断会更稳。",
        { title: "地图外局待补充" },
      );
    }
    card.innerHTML = `
      <div class="system-answer-head">
        <strong>${systemName}</strong>
        <span>${diagnosticStatusLabel(answer.used_local_calculation ? "answered" : "computable")}</span>
      </div>
      <p class="system-answer-verdict">${answer.verdict || "暂无直断结论"}</p>
      <p class="system-answer-detail">${answer.answer || "暂无详细说明"}</p>
      ${fengshuiBlock}
      ${namingBlock}
      <p class="system-answer-meta">${missing}</p>
    `;
    mount.appendChild(card);
  });
}

function renderSystemStatusCards(items) {
  if (!els.systemStatusCards) return;
  els.systemStatusCards.innerHTML = "";
  const values = Array.isArray(items) ? items : [];
  if (!values.length) {
    els.systemStatusCards.innerHTML = '<div class="empty-result-card">本轮没有可展示的体系状态。</div>';
    return;
  }
  values.forEach((item) => {
    const card = document.createElement("article");
    card.className = `system-status-card status-${item.replyStatus || "unknown"}`;
    const title = displaySystemName(item.key || item.title);
    const missing = Array.isArray(item.missingInputs) && item.missingInputs.length
      ? `缺少：${item.missingInputs.join("、")}`
      : "条件完整";
    card.innerHTML = `
      <div class="system-status-head">
        <strong>${title}</strong>
        <span>${diagnosticStatusLabel(item.replyStatus)}</span>
      </div>
      <p class="system-status-reason">${item.reason || item.matchReason || "暂无说明"}</p>
      <p class="system-status-meta">${missing}</p>
    `;
    els.systemStatusCards.appendChild(card);
  });
}

function renderController(controller) {
  if (!els.controllerPanel) return;
  if (!controller || typeof controller !== "object") {
    els.controllerPanel.classList.add("hidden");
    return;
  }

  const selected = Array.isArray(controller.selectedSystems) ? controller.selectedSystems : [];
  const alternates = Array.isArray(controller.alternateSystems) ? controller.alternateSystems : [];
  const missing = Array.isArray(controller.missingInputs) ? controller.missingInputs : [];
  const signals = Array.isArray(controller.signals) && controller.signals.length
    ? controller.signals
    : ["总控已完成问题类型与体系匹配。"];

  els.controllerPanel.classList.remove("hidden");
  if (els.controllerQuestionType) els.controllerQuestionType.textContent = controller.questionType || "问题类型研判";
  if (els.controllerSelectedCount) els.controllerSelectedCount.textContent = `${selected.length} 个主调体系`;
  if (els.controllerSummary) els.controllerSummary.textContent = controller.routingSummary || "总控已完成本轮路由。";

  if (els.controllerSelectedSystems) {
    els.controllerSelectedSystems.innerHTML = "";
    const values = selected.length ? selected : [{ title: "暂无", reason: "当前问题还没有稳定落入某个可起算体系。" }];
    values.forEach((item) => {
      const li = document.createElement("li");
      const title = displaySystemName(item.key || item.title);
      const mode = item.modeLabel ? ` / ${item.modeLabel}` : "";
      li.textContent = `${title}${mode}：${item.reason || "匹配当前问题"}`;
      els.controllerSelectedSystems.appendChild(li);
    });
  }

  if (els.controllerSignals) {
    els.controllerSignals.innerHTML = "";
    signals.forEach((signal) => {
      const li = document.createElement("li");
      li.textContent = signal;
      els.controllerSignals.appendChild(li);
    });
  }

  if (els.controllerGaps) {
    els.controllerGaps.innerHTML = "";
    const gapItems = [];
    alternates.slice(0, 3).forEach((item) => {
      gapItems.push(`可作为辅助：${displaySystemName(item.key || item.title)}。${item.reason || ""}`);
    });
    missing.slice(0, 5).forEach((item) => {
      gapItems.push(`${item.system || "某体系"}还缺：${item.field || "必要信息"}`);
    });
    (gapItems.length ? gapItems : ["暂无额外缺口。"]).forEach((text) => {
      const li = document.createElement("li");
      li.textContent = text;
      els.controllerGaps.appendChild(li);
    });
  }
}

function renderAskPageFollowUp(controller, question, supplements = []) {
  if (!els.followUpPanel || !controller) return;

  const executionStatus = controller.executionStatus || "needs_input";
  const questionType = controller.questionType || "当前问题";
  const experience = buildFollowUpExperience(controller, question, supplements);

  followUpState = {
    baseQuestion: question,
    supplements: Array.isArray(supplements) ? supplements.slice() : [],
    controller,
  };

  els.followUpPanel.classList.remove("hidden");
  applyFollowUpMode(executionStatus, {
    badge: executionStatus === "no_route" ? "需改写问题" : "继续补充",
    title: `${questionType}还在补条件`,
    summary: experience.summary,
    prompt: experience.prompt,
    conversation: experience.conversation,
  });

  if (els.questionInput) {
    els.questionInput.value = "";
    els.questionInput.placeholder = experience.placeholder;
  }
  syncAskActionLabel();
}

function modeLabel(mode) {
  const labels = {
    destiny: "命盘体系",
    timing: "时机体系",
    space: "空间体系",
    ritual: "仪式体系",
    symbolic: "象征体系",
  };
  return labels[mode] || "玄学体系";
}

function setGuideFocusFromNode(node) {
  if (!node || !els.guideFocus || !els.scene) return;
  const sceneRect = els.scene.getBoundingClientRect();
  const nodeRect = node.getBoundingClientRect();
  const centerX = nodeRect.left + nodeRect.width / 2 - sceneRect.left;
  const centerY = nodeRect.top + nodeRect.height / 2 - sceneRect.top;
  const startScale = Math.max(0.18, Math.min(0.42, nodeRect.width / 520));

  els.planetGuide.style.setProperty("--guide-from-x", `${centerX}px`);
  els.planetGuide.style.setProperty("--guide-from-y", `${centerY}px`);
  els.planetGuide.style.setProperty("--guide-start-scale", `${startScale}`);
}

function syncGuideGeometry(node) {
  if (!node || !els.guideFocus) return;
  const styles = getComputedStyle(node);
  const geometryVars = [
    "--crown-w",
    "--crown-h",
    "--crown-rotate",
    "--crown-clip",
    "--orbit-w",
    "--orbit-h",
    "--orbit-rotate",
    "--orbit-radius",
    "--orbit-clip",
    "--orbit-before-inset",
    "--orbit-before-radius",
    "--orbit-after-inset",
    "--orbit-after-radius",
    "--orbit-after-rotate",
    "--sigil-clip",
    "--sigil-radius",
    "--sigil-inset",
    "--sigil-inner-radius",
    "--sigil-after-inset",
    "--sigil-after-rotate",
    "--glyph-size",
  ];
  geometryVars.forEach((name) => {
    const value = styles.getPropertyValue(name);
    if (value) {
      els.guideFocus.style.setProperty(name, value.trim());
    }
  });
}

function openGuide(system) {
  if (!system || !els.planetGuide) return;
  const guide = mergedQuestionGuide(system);
  const profile = deityProfiles[system.key] || {};
  const [a, b, c] = profile.colors || colorFor(systems.findIndex((item) => item.key === system.key));
  activeGuideKey = system.key || null;
  document.querySelectorAll(".planet-node.guide-focus").forEach((node) => node.classList.remove("guide-focus"));
  const node = planetNodes.get(system.key);
  if (guideAnimationFrame) {
    window.cancelAnimationFrame(guideAnimationFrame);
    guideAnimationFrame = null;
  }
  if (node) {
    node.classList.add("guide-focus");
    syncGuideGeometry(node);
    setGuideFocusFromNode(node);
  }
  els.planetGuide.style.setProperty("--guide-a", a);
  els.planetGuide.style.setProperty("--guide-b", b);
  els.planetGuide.style.setProperty("--guide-c", c);
  if (els.guideGlyph) {
    els.guideGlyph.textContent = profile.glyph || "玄";
  }
  els.guideMode.textContent = `${modeLabel(guide.mode)} / ${system.calculatorImplemented ? "已接入本地实算" : system.calculatorReady ? "已有计算规则" : "资料整理中"}`;
  const title = sanitizeSystemTitle(system);
  els.guideTitle.textContent = title || "玄学体系说明";
  setGuideQuestionMeta("按要求把关键信息与问题写在这里", "这里放最终用于推演的完整问法。");
  els.guideSummary.textContent = system.summary || `${title} 的资料已经纳入本地星图。`;
  els.guideBestFor.textContent = guide.bestFor || "用于这个体系最擅长处理的问题类型。";
  els.guideNeeds.innerHTML = "";
  (Array.isArray(guide.needs) && guide.needs.length ? guide.needs : ["先把问题场景写清楚"]).forEach((item) => {
    const li = document.createElement("li");
    const text = typeof item === "string" ? item : JSON.stringify(item);
    const naturalMap = {
      "出生日期": "把出生日期写清楚",
      "出生时辰": "把出生时间尽量写到几点几分",
      "出生地": "把出生城市或出生地写出来",
      "性别": "把性别写清楚",
      "起问时间": "把你起念头提问的时间写出来",
      "占问时间": "把正式起问的时间写出来",
      "起卦方式或卦象": "给出起卦方式、数字，或者直接给卦象",
      "具体问题": "把你到底想问什么直接写明白",
      "候选日期": "把你要比较的日期都列出来",
      "事项类型": "先说你是想问搬家、开业、结婚还是别的事项",
      "地点": "把地点写出来",
      "城市或地址": "把城市、小区、地址这类信息写出来",
      "坐向或平面图": "最好写清坐向、朝向，或者给户型或平面信息",
      "牌阵或抽牌结果": "把牌阵和抽到的牌面结果写出来",
      "问题时间范围": "写清你问的是这周、这个月还是更长时间",
      "姓名或候选名": "把姓名或几个候选名字写出来",
      "用途": "写清这个名字是给谁用、用在什么场景",
      "外貌描述或观察记录": "把看到的外貌特征直接描述出来",
      "观察场景": "说明是照片、视频，还是当面观察",
      "来源或法脉": "写清你参考的是哪一门、哪一路来源",
      "仪式文本或描述": "把仪式内容、做法或文本写出来",
      "文本或图像符号": "把相关文本、符号或图像内容写出来",
      "转化阶段或模型": "说明你现在对应哪一阶段或哪套模型",
      "来源": "把课程、书、老师或体系来源写清楚",
      "实践描述": "把你具体在做什么、做到哪一步写出来",
      "Sephirah / Path / 主题对象": "写清你对应哪条路径、哪颗球体，或者具体主题",
    };
    li.textContent = naturalMap[text] || `请写明：${text}`;
    els.guideNeeds.appendChild(li);
  });
  if (els.guideQuestionInput) {
    const placeholderMap = {
      date_selection: "例如：我想看 2026年6月8号适不适合搬家，地点在上海浦东。",
      fengshui: "例如：上海浦东某小区 12 栋 1802，坐北朝南，想看适不适合长期居住。",
      bazi: "例如：1990-05-12 14:30，男，河南信阳，想看今年工作和财运。",
      qimen_dunjia: "例如：现在是 2026-06-08 21:10，我想问这周先谈合作还是先推进招聘。",
      liu_ren: "例如：2026-06-08 21:10 起问，这次签约最终能不能落地。",
      liuyao_and_meihua: "例如：我想问这次合作能不能成，数字 3 8 5。",
      tarot: "例如：三张牌分别是愚者正位、死神逆位、圣杯首牌，想问这个月项目走向。",
      name_studies: "例如：给2026年6月13日23点42分出生的女宝宝，姓彭，起三个偏诗意、适合正式姓名的名字。",
    };
    els.guideQuestionInput.placeholder = placeholderMap[system.key] || guide.askFormat || "把这个体系需要的信息和你的问题一起写进来。";
  }
  els.guideAskFormat.textContent = guide.askFormat || "请尽量给出明确问题和必要条件。";
  els.guideAvoid.textContent = guide.avoid || "输入越完整，本地计算越稳定。";
  renderGuideWorkbench(system);
  syncDivinationWorkbench(system);
  syncPhysiognomyWorkbench(system);
  syncTarotWorkbench(system);
  els.planetGuide.classList.remove("hidden");
  els.planetGuide.classList.remove("animating");
  document.body.classList.add("guide-open");
  guideAnimationFrame = window.requestAnimationFrame(() => {
    els.planetGuide.classList.add("animating");
    guideAnimationFrame = null;
  });
}

function closeGuide() {
  if (!els.planetGuide) return;
  if (guideAnimationFrame) {
    window.cancelAnimationFrame(guideAnimationFrame);
    guideAnimationFrame = null;
  }
  document.querySelectorAll(".planet-node.guide-focus").forEach((node) => node.classList.remove("guide-focus"));
  activeGuideKey = null;
  els.planetGuide.classList.add("hidden");
  els.planetGuide.classList.remove("animating");
  document.body.classList.remove("guide-open");
  els.guideWorkbench?.classList.add("hidden");
  if (els.guideWorkbench) els.guideWorkbench.dataset.active = "false";
  if (els.guideWorkbenchFields) els.guideWorkbenchFields.innerHTML = "";
  resetGuideWorkbenchMapPreview();
  els.divinationWorkbench?.classList.add("hidden");
  if (els.divinationWorkbench) els.divinationWorkbench.dataset.active = "false";
  els.physiognomyWorkbench?.classList.add("hidden");
  if (els.physiognomyWorkbench) els.physiognomyWorkbench.dataset.active = "false";
  els.tarotWorkbench?.classList.add("hidden");
  if (els.tarotWorkbench) els.tarotWorkbench.dataset.active = "false";
}

function submitGuideQuestion() {
  if (!activeGuideKey) return;
  const system = getSystemByKey(activeGuideKey);
  if (!system) return;
  const title = sanitizeSystemTitle(system);
  const prompt = (els.guideQuestionInput?.value || "").trim();
  if (!prompt) {
    els.guideQuestionInput?.focus();
    setStatus(`先把 ${title} 需要的信息和问题写进去`);
    return;
  }
  els.questionInput.value = prompt;
  closeGuide();
  els.questionInput.focus();
  els.questionInput.setSelectionRange(els.questionInput.value.length, els.questionInput.value.length);
  setStatus(`已带入 ${title} 的提问内容，可以直接开启推演`);
}

function useGuidePrompt() {
  if (!activeGuideKey) return;
  const system = getSystemByKey(activeGuideKey);
  if (!system) return;
  const title = sanitizeSystemTitle(system);
  const guide = mergedQuestionGuide(system);
  const prompt = guide.askFormat || "";
  els.questionInput.value = prompt.replace(/^例如[:：]?\s*/, "");
  closeGuide();
  els.questionInput.focus();
  els.questionInput.setSelectionRange(els.questionInput.value.length, els.questionInput.value.length);
  setStatus(`已带入 ${title} 的推荐问法，你可以直接修改后提问`);
}

function deactivatePlanets() {
  document.querySelectorAll(".planet-node.active").forEach((node) => node.classList.remove("active"));
}

function activateKeys(keys) {
  keys.forEach((key) => {
    const node = planetNodes.get(key);
    if (node) node.classList.add("active");
  });
}

function setCutscenePhase(phase, prompt = "") {
  els.cutscene.dataset.phase = phase;
  els.ritualPrompt.textContent = prompt;
  els.ritualPrompt.classList.toggle("visible", Boolean(prompt));
}

function moveRitualCursor(event) {
  ritualState.pointerX = event.clientX;
  ritualState.pointerY = event.clientY;
  els.ritualCursor.style.transform = `translate(${event.clientX}px, ${event.clientY}px)`;
  if (els.cutscene.classList.contains("interactive")) {
    updateIncenseContact();
  }
}

function showRitualCursor(visible) {
  els.ritualCursor.classList.toggle("active", visible);
}

function resetIncenseSticks() {
  ritualState.litSticks.clear();
  ritualState.hoverStick = null;
  ritualState.hoverSince = 0;
  els.incenseSticks.forEach((stick) => {
    stick.classList.remove("lit", "arming");
    stick.removeAttribute("data-lit");
  });
  els.ritualCursor.classList.remove("touching");
}

function settleIgnition(result = false) {
  const resolve = ritualState.resolveIgnition;
  ritualState.resolveIgnition = null;
  ritualState.activeRunId = 0;
  if (resolve) resolve(result);
}

function setResultViewMode(mode = "") {
  document.body.classList.remove("result-view-naming");
  if (mode === "naming") {
    document.body.classList.add("result-view-naming");
  }
}

function resetPresentation() {
  hideFollowUpPanel();
  clearControllerPreview();
  setResultViewMode("");
  els.cutscene.className = "cutscene";
  delete els.cutscene.dataset.phase;
  els.blindBox.className = "ritual-altar";
  els.oracleRunes.innerHTML = "";
  els.thinkingVoices.innerHTML = "";
  els.answerConstellation.innerHTML = "";
  els.summaryAnswer.textContent = "";
  els.finalChamber.className = "final-chamber hidden";
  if (els.directVerdictLead) els.directVerdictLead.textContent = "";
  if (els.directVerdictMeta) els.directVerdictMeta.textContent = "";
  els.directVerdictCard?.classList.add("hidden");
  els.ritualPrompt.textContent = "";
  els.ritualPrompt.classList.remove("visible");
  ritualState.activeCourtKeys = [];
  ritualState.smokeParticles.length = 0;
  ritualState.emberParticles.length = 0;
  ritualState.riverParticles.length = 0;
  resetIncenseSticks();
  showRitualCursor(false);
  [els.agreements, els.differences, els.cautions].forEach((list) => {
    list.innerHTML = "";
  });
  document.querySelector(".final-columns")?.classList.remove("final-columns-hidden");
  if (els.systemAnswerCards) els.systemAnswerCards.innerHTML = "";
  if (els.systemStatusCards) els.systemStatusCards.innerHTML = "";
  els.controllerPanel?.classList.add("hidden");
  if (els.controllerSelectedSystems) els.controllerSelectedSystems.innerHTML = "";
  if (els.controllerSignals) els.controllerSignals.innerHTML = "";
  if (els.controllerGaps) els.controllerGaps.innerHTML = "";
  deactivatePlanets();
}

function clearReading() {
  currentRunId += 1;
  pendingOracle = null;
  settleIgnition(false);
  resetPresentation();
  clearFollowUpState();
  closeGuide();
}

function buildCourtRecord(key, index) {
  const system = getSystemByKey(key);
  const profile = deityProfiles[key] || {};
  return {
    key,
    title: sanitizeSystemTitle(system || { key }),
    glyph: profile.glyph || divineGlyphs[index % divineGlyphs.length],
    className: profile.className || "",
    colors: profile.colors || colorFor(index),
    portrait: deityPortraitAnchors[key] || [50, 50],
  };
}

function courtLayoutForCount(count) {
  const layouts = {
    1: [[50, 42]],
    2: [[30, 42], [70, 42]],
    3: [[22, 56], [50, 28], [78, 56]],
    4: [[18, 58], [38, 28], [62, 28], [82, 58]],
    5: [[14, 60], [32, 34], [50, 18], [68, 34], [86, 60]],
    6: [[12, 62], [28, 40], [44, 22], [56, 22], [72, 40], [88, 62]],
    7: [[10, 64], [24, 42], [38, 24], [50, 16], [62, 24], [76, 42], [90, 64]],
  };
  return layouts[Math.max(1, Math.min(7, count))] || ritualCourtLayout;
}

function spawnDivineCourt(keys = ritualCourtKeys) {
  els.oracleRunes.innerHTML = "";
  const layout = courtLayoutForCount(keys.length || 1);
  keys.forEach((key, index) => {
    const record = buildCourtRecord(key, index);
    const [x, y] = layout[index % layout.length];
    const [a, b, c] = record.colors;
    const [px, py] = record.portrait;
    const sigil = document.createElement("article");
    sigil.className = `divine-sigil ${record.className}`.trim();
    sigil.dataset.key = record.key;
    sigil.dataset.title = record.title;
    sigil.style.setProperty("--rx", `${x}%`);
    sigil.style.setProperty("--ry", `${y}%`);
    sigil.style.setProperty("--deity-a", a);
    sigil.style.setProperty("--deity-b", b);
    sigil.style.setProperty("--deity-c", c);
    sigil.style.setProperty("--portrait-x", `${px}%`);
    sigil.style.setProperty("--portrait-y", `${py}%`);
    sigil.style.setProperty("--deity-delay", `${index * 90}ms`);
    sigil.innerHTML = `
      <span class="divine-mist"></span>
      <span class="divine-halo"></span>
      <span class="divine-throne"></span>
      <span class="divine-portrait"></span>
      <span class="divine-hand"></span>
      <span class="divine-glyph">${record.glyph}</span>
      <span class="divine-name">${clipText(record.title, 7)}</span>
    `;
    els.oracleRunes.appendChild(sigil);
  });
}

function courtNodes() {
  return [...els.oracleRunes.querySelectorAll(".divine-sigil")];
}

function setResponsiveCourt(keys) {
  const wanted = new Set(keys);
  courtNodes().forEach((node) => {
    node.classList.remove("responsive", "casting", "answered");
    if (wanted.has(node.dataset.key)) node.classList.add("responsive");
  });
}

function markCourtCasting(node) {
  if (!node) return;
  node.classList.add("responsive", "casting");
}

function markCourtAnswered(node) {
  if (!node) return;
  node.classList.remove("casting");
  node.classList.add("answered");
}

function applyAnimationStyles(element, frame) {
  if (!element || !frame || typeof frame !== "object") return;
  Object.entries(frame).forEach(([property, value]) => {
    if (property === "offset" || value == null) return;
    try {
      element.style[property] = value;
    } catch {}
  });
}

function playAnimation(element, keyframes, options) {
  const frames = Array.isArray(keyframes) ? keyframes : [];
  const finalFrame = frames[frames.length - 1] || null;
  const duration = Number(options?.duration) || 0;
  const delay = Number(options?.delay) || 0;
  const fallbackMs = Math.max(180, duration + delay + 120);
  if (!element?.animate || !frames.length) {
    applyAnimationStyles(element, finalFrame);
    return Promise.resolve(null);
  }
  try {
    const animation = element.animate(frames, options);
    return new Promise((resolve) => {
      let settled = false;
      const settle = () => {
        if (settled) return;
        settled = true;
        window.clearTimeout(timer);
        applyAnimationStyles(element, finalFrame);
        resolve(null);
      };
      const timer = window.setTimeout(settle, fallbackMs);
      animation.finished.then(settle).catch(settle);
    });
  } catch {
    applyAnimationStyles(element, finalFrame);
    return Promise.resolve(null);
  }
}

function incenseTipCenter(stick) {
  const target = stick.querySelector(".incense-tip") || stick;
  const rect = target.getBoundingClientRect();
  return {
    x: rect.left + rect.width * 0.5,
    y: rect.top + rect.height * 0.5,
  };
}

function clearIncenseArming() {
  ritualState.hoverStick = null;
  ritualState.hoverSince = 0;
  els.ritualCursor.classList.remove("touching");
  els.incenseSticks.forEach((stick) => stick.classList.remove("arming"));
}

function igniteStick(stick) {
  const stickIndex = Number(stick.dataset.stick);
  if (ritualState.litSticks.has(stickIndex)) return;
  ritualState.litSticks.add(stickIndex);
  stick.classList.remove("arming");
  stick.classList.add("lit");
  stick.dataset.lit = "true";
  ritualState.emberParticles.push({
    x: ritualState.pointerX,
    y: ritualState.pointerY,
    vx: (Math.random() - 0.5) * 0.8,
    vy: -1.8 - Math.random() * 1.6,
    size: 18 + Math.random() * 12,
    alpha: 0.42,
    life: 34,
    age: 0,
    tint: "warm",
  });
  if (ritualState.litSticks.size === els.incenseSticks.length) {
    clearIncenseArming();
    els.cutscene.classList.remove("interactive");
    setCutscenePhase("smoke", "三炷已明，烟路已开");
    showRitualCursor(false);
    settleIgnition(true);
  }
}

function updateIncenseContact(now = performance.now()) {
  if (els.cutscene.dataset.phase !== "ignite") {
    clearIncenseArming();
    return;
  }
  if (ritualState.activeRunId !== currentRunId) {
    clearIncenseArming();
    return;
  }
  const radius = window.innerWidth < 760 ? 74 : 88;
  let winner = null;
  let winnerDistance = Infinity;
  els.incenseSticks.forEach((stick) => {
    if (stick.classList.contains("lit")) return;
    const tip = incenseTipCenter(stick);
    const rect = stick.getBoundingClientRect();
    const expandedLeft = rect.left - 22;
    const expandedRight = rect.right + 22;
    const expandedTop = rect.top - 30;
    const expandedBottom = rect.top + 52;
    const insideTipLane =
      ritualState.pointerX >= expandedLeft &&
      ritualState.pointerX <= expandedRight &&
      ritualState.pointerY >= expandedTop &&
      ritualState.pointerY <= expandedBottom;
    const dx = ritualState.pointerX - tip.x;
    const dy = ritualState.pointerY - tip.y;
    const distance = Math.hypot(dx, dy);
    if (insideTipLane && distance < winnerDistance) {
      winnerDistance = distance;
      winner = stick;
    }
  });

  els.incenseSticks.forEach((stick) => stick.classList.remove("arming"));
  if (!winner || winnerDistance > radius) {
    clearIncenseArming();
    return;
  }

  const stickIndex = Number(winner.dataset.stick);
  winner.classList.add("arming");
  els.ritualCursor.classList.add("touching");
  if (ritualState.hoverStick !== stickIndex) {
    ritualState.hoverStick = stickIndex;
    ritualState.hoverSince = now;
    return;
  }
  if (now - ritualState.hoverSince >= 90) {
    igniteStick(winner);
  }
}

function waitForIncenseIgnition(runId) {
  ritualState.activeRunId = runId;
  ritualState.resolveIgnition = null;
  resetIncenseSticks();
  showRitualCursor(true);
  els.cutscene.classList.add("interactive");
  setCutscenePhase("ignite", "依次点燃三炷问天香");
  const fallbackTimer = window.setTimeout(() => {
    if (runId !== currentRunId || ritualState.litSticks.size === els.incenseSticks.length) return;
    els.incenseSticks.forEach((stick, index) => {
      window.setTimeout(() => {
        if (runId !== currentRunId || stick.classList.contains("lit")) return;
        const tip = incenseTipCenter(stick);
        ritualState.pointerX = tip.x;
        ritualState.pointerY = tip.y;
        igniteStick(stick);
      }, index * 280);
    });
  }, 4800);
  return new Promise((resolve) => {
    ritualState.resolveIgnition = (result) => {
      window.clearTimeout(fallbackTimer);
      resolve(result);
    };
  });
}

function ritualCourtKeysFromOracle(oracleData) {
  const answers = Array.isArray(oracleData?.oracle?.system_answers) ? oracleData.oracle.system_answers : [];
  const ordered = [];
  answers.forEach((answer) => {
    const key = resolveAnswerKey(answer);
    if (key && !ordered.includes(key)) ordered.push(key);
  });
  return ordered.slice(0, 7);
}

async function playRitualCutscene(runId) {
  els.cutscene.classList.add("active");
  ritualState.activeCourtKeys = [];
  els.oracleRunes.innerHTML = "";
  deactivatePlanets();
  activateKeys(ritualGroups.ignite);
  setResponsiveCourt([]);
  setStatus("仪式已启，天门渐开");
  const ignited = await waitForIncenseIgnition(runId);
  if (!ignited || runId !== currentRunId) return false;

  setStatus("三炷已明，烟路成桥");
  await sleep(760);
  if (runId !== currentRunId) return false;

  setCutscenePhase("ascend", "青烟上行");
  setStatus("青烟上行，请候应签");
  deactivatePlanets();
  activateKeys(ritualGroups.ascend);
  await sleep(1550);
  if (runId !== currentRunId) return false;

  setCutscenePhase("awaiting", "神门已开，候诸术应签");
  setStatus("本轮应签正在凝成");
  const oracleData = await waitForOracleResult(runId);
  if (!oracleData || runId !== currentRunId) return false;
  if (oracleData.error) return true;

  const activeKeys = ritualCourtKeysFromOracle(oracleData);
  ritualState.activeCourtKeys = activeKeys.length ? activeKeys : ritualCourtKeys.slice(0, 4);
  spawnDivineCourt(ritualState.activeCourtKeys);
  deactivatePlanets();
  activateKeys(ritualState.activeCourtKeys);
  setResponsiveCourt(ritualState.activeCourtKeys);
  setCutscenePhase("reveal", "应签已现");
  setStatus("诸术已就位");
  await sleep(1280);
  if (runId !== currentRunId) return false;

  setCutscenePhase("awaiting");
  setResponsiveCourt(ritualState.activeCourtKeys);
  setStatus("诸签将入时间之河");
  await sleep(520);
  return runId === currentRunId;
}

function resolveAnswerKey(answer) {
  if (answer?.key && deityProfiles[answer.key]) return answer.key;
  const system = getSystemByTitle(answer?.system);
  return system?.key || null;
}

function preferredAnswers(oracleData) {
  const answers = Array.isArray(oracleData?.oracle?.system_answers) ? oracleData.oracle.system_answers : [];
  const keyOrder = ritualState.activeCourtKeys.length ? ritualState.activeCourtKeys : ritualCourtKeys;
  const ordered = keyOrder
    .map((key) => answers.find((answer) => resolveAnswerKey(answer) === key))
    .filter(Boolean);
  const remainder = answers.filter((answer) => !ordered.includes(answer));
  return [...ordered, ...remainder].slice(0, 7);
}

function getCourtNodeForAnswer(answer, index) {
  const key = resolveAnswerKey(answer);
  if (key) {
    const matched = courtNodes().find((node) => node.dataset.key === key);
    if (matched) return matched;
  }
  const nodes = courtNodes();
  return nodes[index % Math.max(nodes.length, 1)] || null;
}

function createAnswerFragment(answer, index) {
  const systemName = displaySystemName(answer.key || answer.system);
  const fragment = document.createElement("article");
  fragment.className = "answer-fragment";
  fragment.innerHTML = `
    <span class="slip-rune">${divineGlyphs[index % divineGlyphs.length]}</span>
    <strong>${systemName}</strong>
    <p>${clipText(answer.answer || "神谕仍在汇聚", 110)}</p>
  `;
  els.answerConstellation.appendChild(fragment);
  return fragment;
}

async function animateAnswerThrow(answer, courtNode, index) {
  const fragment = createAnswerFragment(answer, index);
  const constellationRect = els.answerConstellation.getBoundingClientRect();
  const courtRect = courtNode?.getBoundingClientRect();
  const landingSpots = [
    [30, 56],
    [48, 49],
    [67, 54],
    [39, 66],
    [60, 67],
    [50, 78],
    [76, 65],
  ];
  const [targetXPct, targetYPct] = landingSpots[index % landingSpots.length];
  const startX = courtRect
    ? courtRect.left + courtRect.width * 0.5 - constellationRect.left
    : constellationRect.width * 0.5;
  const startY = courtRect
    ? courtRect.top + courtRect.height * 0.6 - constellationRect.top
    : constellationRect.height * 0.16;
  const targetX = constellationRect.width * (targetXPct / 100);
  const targetY = constellationRect.height * (targetYPct / 100);
  const midX = (startX + targetX) * 0.5 + (index % 2 === 0 ? -70 : 70);
  const midY = Math.min(startY, targetY) - 128 - ((index % 3) * 18);
  const tilt = index % 2 === 0 ? -8 : 9;

  fragment.style.left = `${startX}px`;
  fragment.style.top = `${startY}px`;
  fragment.dataset.settleX = `${targetX}`;
  fragment.dataset.settleY = `${targetY}`;

  markCourtCasting(courtNode);
  await playAnimation(
    fragment,
    [
      {
        left: `${startX}px`,
        top: `${startY}px`,
        opacity: 0,
        transform: `translate(-50%, -50%) scale(0.24) rotate(${tilt * 1.3}deg)`,
        filter: "blur(8px)",
      },
      {
        left: `${midX}px`,
        top: `${midY}px`,
        opacity: 1,
        transform: `translate(-50%, -50%) scale(1.04) rotate(${tilt * 0.28}deg)`,
        filter: "blur(0px)",
        offset: 0.56,
      },
      {
        left: `${targetX}px`,
        top: `${targetY}px`,
        opacity: 1,
        transform: `translate(-50%, -50%) scale(0.96) rotate(${tilt}deg)`,
        filter: "blur(0px)",
      },
    ],
    {
      duration: 1380,
      easing: "cubic-bezier(0.22, 0.74, 0.2, 1)",
      fill: "forwards",
    },
  );
  markCourtAnswered(courtNode);
  return fragment;
}

async function gatherFragmentsToRiver(runId) {
  const fragments = [...els.answerConstellation.querySelectorAll(".answer-fragment")];
  const constellationRect = els.answerConstellation.getBoundingClientRect();
  await Promise.all(
    fragments.map((fragment, index) => {
      const startX = Number(fragment.dataset.settleX || constellationRect.width * 0.5);
      const startY = Number(fragment.dataset.settleY || constellationRect.height * 0.65);
      const targetX = constellationRect.width * (0.5 + ((index - (fragments.length - 1) * 0.5) * 0.035));
      const targetY = constellationRect.height * 1.02;
      return playAnimation(
        fragment,
        [
          {
            left: `${startX}px`,
            top: `${startY}px`,
            opacity: 1,
            transform: "translate(-50%, -50%) scale(0.96) rotate(var(--tilt, 0deg))",
            filter: "blur(0px)",
          },
          {
            left: `${targetX}px`,
            top: `${targetY}px`,
            opacity: 0,
            transform: "translate(-50%, -50%) scale(0.18) rotate(12deg)",
            filter: "blur(8px)",
          },
        ],
        {
          delay: index * 85,
          duration: 980,
          easing: "cubic-bezier(0.3, 0.08, 0.18, 1)",
          fill: "forwards",
        },
      );
    }),
  );
  if (runId === currentRunId) {
    fragments.forEach((fragment) => fragment.remove());
  }
}

async function waitForOracleResult(runId) {
  while (runId === currentRunId) {
    if (pendingOracle) return pendingOracle;
    await sleep(120);
  }
  return null;
}

async function showFinalResult(oracleData, runId) {
  if (runId !== currentRunId || !oracleData) return;
  clearFollowUpState();
  clearControllerPreview();
  setResultViewMode("");
  const answers = preferredAnswers(oracleData);
  const finalAnswer = oracleData?.oracle?.final_answer || {};
  const activeSystems = Array.isArray(oracleData?.systems) ? oracleData.systems : [];
  const directDateOnly = activeSystems.length === 1 && activeSystems[0]?.key === "date_selection";
  const namingAnswer = findNamingAnswer(answers);
  const finalColumns = document.querySelector(".final-columns");

  setCutscenePhase("casting", "诸术落签");
  setStatus("诸术正在落签");
  const launches = [];
  for (const [index, answer] of answers.entries()) {
    if (runId !== currentRunId) return;
    const courtNode = getCourtNodeForAnswer(answer, index);
    launches.push(animateAnswerThrow(answer, courtNode, index));
    await sleep(180);
  }
  await Promise.all(launches);
  if (runId !== currentRunId) return;

  setCutscenePhase("river", "众签归河");
  setStatus("众签归河，终谕待出");
  await gatherFragmentsToRiver(runId);
  if (runId !== currentRunId) return;

  setCutscenePhase("harvest", "终谕出卷");
  setStatus("终谕即将显形");
  els.finalChamber.classList.remove("hidden");
  els.finalChamber.classList.add("harvesting");
  els.finalChamber.scrollTop = 0;
  window.scrollTo(0, 0);
  await sleep(1600);
  if (runId !== currentRunId) return;

  els.directVerdictCard?.classList.add("hidden");
  els.finalChamber.classList.remove("naming-mode");

  if (namingAnswer) {
    setResultViewMode("naming");
    els.finalChamber.classList.remove("final-chamber-direct-only");
    els.finalChamber.classList.add("naming-mode");
    els.summaryAnswer.textContent = "";
    els.controllerPanel?.classList.add("hidden");
    renderNamingReport(namingAnswer);
    els.agreements.innerHTML = "";
    els.differences.innerHTML = "";
    els.cautions.innerHTML = "";
    finalColumns?.classList.add("final-columns-hidden");
  } else {
    renderController(oracleData.controller || oracleData?.oracle?.controller);
    els.summaryAnswer.textContent = finalAnswer.synthesis || "暂无最终答案";
    renderSystemAnswerCards(answers);
  }

  if (directDateOnly && !namingAnswer) {
    els.finalChamber.classList.add("final-chamber-direct-only");
    const agreementItems = Array.isArray(finalAnswer.agreements) ? finalAnswer.agreements : [];
    els.directVerdictLead.textContent = finalAnswer.synthesis || "已经得到本地直算结果。";
    els.directVerdictMeta.textContent = agreementItems[0] || "这次只保留了能够直接落地计算的择日体系。";
    els.directVerdictCard?.classList.remove("hidden");
    els.summaryAnswer.textContent = "";
    els.agreements.innerHTML = "";
    els.differences.innerHTML = "";
    els.cautions.innerHTML = "";
    finalColumns?.classList.add("final-columns-hidden");
  } else if (!namingAnswer) {
    renderList(els.agreements, finalAnswer.agreements);
    renderList(els.differences, finalAnswer.differences);
    renderList(els.cautions, finalAnswer.cautions);
    finalColumns?.classList.remove("final-columns-hidden");
    els.finalChamber.classList.remove("final-chamber-direct-only");
  }

  els.finalChamber.classList.remove("harvesting");
  els.finalChamber.scrollTop = 0;
  window.scrollTo(0, 0);
  setStatus(`最终答案已经显形：${displayModelName(oracleData.model || oracleData._requestedModel || "")}`);
}

async function requestOracle(question, runId) {
  const requestedModel = els.modelSelect?.value || "auto";
  try {
    const response = await fetch("/api/oracle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, model: requestedModel }),
    });
    const raw = await response.text();
    let data = {};
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch {
      data = { error: raw || "神谕请求失败" };
    }
    if (!response.ok) throw new Error(data.error || "神谕请求失败");
    data._requestedModel = requestedModel;
    if (runId === currentRunId) pendingOracle = data;
  } catch (error) {
    if (runId === currentRunId) pendingOracle = { error: error.message };
  }
}

async function askOracle(question) {
  const previousFollowUp = followUpState
    ? {
        ...followUpState,
        supplements: Array.isArray(followUpState.supplements) ? followUpState.supplements.slice() : [],
      }
    : null;
  const runId = currentRunId + 1;
  const composed = composeOracleQuestion(question);
  clearReading();
  currentRunId = runId;
  setBusy(true);
  setStatus(previousFollowUp ? "正在吸收你补充的信息" : "智能总控正在研判问题");
  await requestOracle(composed.requestQuestion, runId);
  const oracleData = pendingOracle;
  if (!oracleData || runId !== currentRunId) return;
  if (oracleData.error) {
    resetPresentation();
    if (previousFollowUp) {
      renderAskPageFollowUp(previousFollowUp.controller, previousFollowUp.baseQuestion, previousFollowUp.supplements);
    } else {
      clearFollowUpState();
    }
    setStatus(oracleData.error);
    setBusy(false);
    if (previousFollowUp) els.questionInput?.focus();
    return;
  }

  const controller = extractController(oracleData);
  const diagnostics = Array.isArray(oracleData?.systemDiagnostics)
    ? oracleData.systemDiagnostics
    : Array.isArray(oracleData?.oracle?.system_diagnostics)
      ? oracleData.oracle.system_diagnostics
      : [];
  const activeSystems = Array.isArray(oracleData?.systems) ? oracleData.systems : [];
  renderControllerPreview(controller, diagnostics, activeSystems);
  const executionStatus = controller?.executionStatus || "answered";
  if (executionStatus === "blocked" && oracleData?.safety) {
    resetPresentation();
    pendingOracle = null;
    followUpState = null;
    if (els.followUpPanel) els.followUpPanel.classList.remove("hidden");
    const safety = oracleData.safety || {};
    const safetyText = [
      safety.summary || controller?.routingSummary || "当前问题需要先处理现实风险。",
      Array.isArray(safety.actions) && safety.actions.length ? `先做这几件事：${safety.actions.join("；")}` : "",
      Array.isArray(safety.cautions) && safety.cautions.length ? `提醒：${safety.cautions.join("；")}` : "",
      "等现实风险处理完，再重新输入一个新的问题。",
    ].filter(Boolean).join("\n");
    setStatus(safety.summary || controller?.routingSummary || "当前问题需要先处理现实风险。");
    applyFollowUpMode("blocked", {
      prompt: safetyText,
      conversation: [
        ...(composed.baseQuestion ? [{ role: "user", text: composed.baseQuestion }] : []),
        { role: "assistant", text: safetyText },
      ],
    });
    if (els.questionInput) {
      els.questionInput.value = "";
      els.questionInput.placeholder = "先处理现实风险";
    }
    syncAskActionLabel();
    setBusy(false);
    els.questionInput?.focus();
    return;
  }
  if (executionStatus === "needs_input" && controller?.issueType === "birth_issue") {
    const diagnostics = extractSystemDiagnostics(oracleData);
    const birthReason = diagnostics.find((item) => item?.replyStatus === "missing_inputs");
    resetPresentation();
    pendingOracle = null;
    followUpState = null;
    if (els.followUpPanel) els.followUpPanel.classList.remove("hidden");
    const birthPrompt = [
      controller?.followUpPrompt || birthReason?.reason || "出生信息有误，请重新确认。",
      "请直接重新输入完整问题，并把出生日期、时辰、历法和出生地一次写正确。",
    ].join("\n");
    applyFollowUpMode("birth_issue", {
      prompt: birthPrompt,
      conversation: [
        ...(composed.baseQuestion ? [{ role: "user", text: composed.baseQuestion }] : []),
        { role: "assistant", text: birthPrompt },
      ],
    });
    if (els.questionInput) {
      els.questionInput.value = "";
      els.questionInput.placeholder = "请重新输入出生信息和问题";
    }
    syncAskActionLabel();
    setStatus(controller?.followUpPrompt || birthReason?.reason || "出生信息需要先校正。");
    setBusy(false);
    els.questionInput?.focus();
    return;
  }
  if (executionStatus !== "answered") {
    resetPresentation();
    pendingOracle = null;
    renderAskPageFollowUp(controller, composed.baseQuestion, composed.supplements);
    setStatus("请继续补充信息");
    setBusy(false);
    els.questionInput?.focus();
    return;
  }

  pendingOracle = oracleData;
  setStatus("总控已完成分流，准备进入点香起算");
  const cutsceneOk = await playRitualCutscene(runId);
  if (!cutsceneOk) {
    if (runId === currentRunId) setBusy(false);
    return;
  }
  const resultData = await waitForOracleResult(runId);
  if (!resultData || runId !== currentRunId) return;
  if (resultData.error) {
    resetPresentation();
    setStatus(resultData.error);
    setBusy(false);
    return;
  }
  await showFinalResult(resultData, runId);
  if (runId === currentRunId) setBusy(false);
}

function initRitualCanvas() {
  const ctx = els.ritualCanvas?.getContext("2d");
  if (!ctx) return;

  let width = 0;
  let height = 0;
  let ratio = 1;
  let lastFrame = 0;

  function resize() {
    const rect = els.cutscene.getBoundingClientRect();
    width = Math.max(1, Math.floor(rect.width));
    height = Math.max(1, Math.floor(rect.height));
    ratio = window.devicePixelRatio || 1;
    els.ritualCanvas.width = Math.floor(width * ratio);
    els.ritualCanvas.height = Math.floor(height * ratio);
    els.ritualCanvas.style.width = `${width}px`;
    els.ritualCanvas.style.height = `${height}px`;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  }

  function canvasPointForStick(stick) {
    const tip = incenseTipCenter(stick);
    const rect = els.cutscene.getBoundingClientRect();
    return {
      x: tip.x - rect.left,
      y: tip.y - rect.top,
    };
  }

  function emitSmoke(x, y, phase, scale = 1) {
    ritualState.smokeParticles.push({
      x,
      y,
      vx: (Math.random() - 0.5) * (0.4 + scale * 0.2),
      vy: -0.6 - Math.random() * (1.2 + scale * 0.7),
      sway: Math.random() * Math.PI * 2,
      size: 18 + Math.random() * 24 * scale,
      grow: 0.18 + Math.random() * 0.12,
      alpha: 0.16 + Math.random() * 0.12,
      age: 0,
      life: 90 + Math.random() * 60,
      phase,
    });
  }

  function emitEmber(x, y, count = 1) {
    for (let i = 0; i < count; i += 1) {
      ritualState.emberParticles.push({
        x,
        y,
        vx: (Math.random() - 0.5) * 1.6,
        vy: -1.2 - Math.random() * 2.2,
        size: 4 + Math.random() * 8,
        alpha: 0.32 + Math.random() * 0.28,
        age: 0,
        life: 24 + Math.random() * 32,
        tint: Math.random() > 0.45 ? "warm" : "cyan",
      });
    }
  }

  function emitRiver() {
    ritualState.riverParticles.push({
      x: width * (0.14 + Math.random() * 0.72),
      y: height * (0.62 + Math.random() * 0.16),
      vx: 0.8 + Math.random() * 1.8,
      vy: -0.08 + Math.random() * 0.16,
      length: 26 + Math.random() * 78,
      alpha: 0.06 + Math.random() * 0.1,
      age: 0,
      life: 80 + Math.random() * 70,
    });
  }

  function drawSmokeParticle(item) {
    const gradient = ctx.createRadialGradient(item.x, item.y, 0, item.x, item.y, item.size);
    gradient.addColorStop(0, `rgba(229, 243, 255, ${item.alpha})`);
    gradient.addColorStop(0.35, `rgba(176, 214, 235, ${item.alpha * 0.74})`);
    gradient.addColorStop(1, "rgba(176, 214, 235, 0)");
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(item.x, item.y, item.size, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawEmberParticle(item) {
    const color = item.tint === "cyan" ? "126,219,211" : "242,191,117";
    ctx.fillStyle = `rgba(${color}, ${item.alpha})`;
    ctx.beginPath();
    ctx.arc(item.x, item.y, item.size, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawRiverParticle(item) {
    ctx.strokeStyle = `rgba(126,219,211,${item.alpha})`;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(item.x, item.y);
    ctx.bezierCurveTo(
      item.x + item.length * 0.3,
      item.y - 8,
      item.x + item.length * 0.68,
      item.y + 10,
      item.x + item.length,
      item.y + 2,
    );
    ctx.stroke();
  }

  function updateParticles(collection, dt) {
    for (let index = collection.length - 1; index >= 0; index -= 1) {
      const item = collection[index];
      item.age += dt;
      if (item.age >= item.life) {
        collection.splice(index, 1);
      }
    }
  }

  function loop(timestamp) {
    const dt = Math.min(34, timestamp - lastFrame || 16);
    lastFrame = timestamp;
    if (width !== Math.floor(els.cutscene.clientWidth) || height !== Math.floor(els.cutscene.clientHeight)) {
      resize();
    }

    ctx.clearRect(0, 0, width, height);
    const phase = els.cutscene.dataset.phase || "";
    const active = els.cutscene.classList.contains("active");
    if (!active) {
      requestAnimationFrame(loop);
      return;
    }

    if (els.cutscene.classList.contains("interactive")) {
      updateIncenseContact(timestamp);
    }

    ritualState.particleSeed += dt * 0.0012;

    if (["ignite", "smoke", "ascend", "awaiting", "reveal", "casting"].includes(phase)) {
      els.incenseSticks.forEach((stick) => {
        if (!stick.classList.contains("lit")) return;
        const point = canvasPointForStick(stick);
        const scale = phase === "ascend" ? 1.9 : phase === "smoke" ? 1.45 : 1;
        emitSmoke(point.x, point.y, phase, scale);
        if (Math.random() > 0.72) emitEmber(point.x, point.y - 3, 1);
      });
    }

    if (["ascend", "awaiting", "reveal", "casting"].includes(phase)) {
      emitSmoke(width * 0.5 + Math.sin(ritualState.particleSeed * 2.4) * width * 0.02, height * 0.48, phase, 1.8);
      emitSmoke(width * 0.48 + Math.cos(ritualState.particleSeed * 2.1) * width * 0.024, height * 0.4, phase, 2.4);
    }

    if (["casting", "river", "harvest"].includes(phase) && Math.random() > 0.24) {
      emitRiver();
    }

    ritualState.smokeParticles.forEach((item) => {
      item.x += item.vx * dt * 0.08 + Math.sin(item.sway + item.age * 0.035) * 0.32;
      item.y += item.vy * dt * 0.08;
      item.size += item.grow * dt * 0.06;
      item.alpha *= 0.994;
      drawSmokeParticle(item);
    });

    ritualState.emberParticles.forEach((item) => {
      item.x += item.vx * dt * 0.08;
      item.y += item.vy * dt * 0.08;
      item.size *= 0.987;
      item.alpha *= 0.965;
      drawEmberParticle(item);
    });

    if (["casting", "river", "harvest"].includes(phase)) {
      const riverGlow = ctx.createLinearGradient(width * 0.14, height * 0.74, width * 0.86, height * 0.84);
      riverGlow.addColorStop(0, "rgba(126,219,211,0)");
      riverGlow.addColorStop(0.5, "rgba(126,219,211,0.22)");
      riverGlow.addColorStop(1, "rgba(126,219,211,0)");
      ctx.strokeStyle = riverGlow;
      ctx.lineWidth = 2.4;
      ctx.beginPath();
      ctx.moveTo(width * 0.18, height * 0.72);
      ctx.bezierCurveTo(width * 0.34, height * 0.68, width * 0.62, height * 0.84, width * 0.82, height * 0.8);
      ctx.stroke();
    }

    ritualState.riverParticles.forEach((item) => {
      item.x += item.vx * dt * 0.04;
      item.y += item.vy * dt * 0.04 + Math.sin(item.age * 0.04) * 0.18;
      item.alpha *= 0.992;
      drawRiverParticle(item);
    });

    updateParticles(ritualState.smokeParticles, dt);
    updateParticles(ritualState.emberParticles, dt);
    updateParticles(ritualState.riverParticles, dt);

    requestAnimationFrame(loop);
  }

  window.addEventListener("resize", resize);
  resize();
  requestAnimationFrame(loop);
}

function initStarfield() {
  const ctx = els.starfield.getContext("2d");
  if (!ctx) return;
  let width = 0;
  let height = 0;
  let tick = 0;
  const stars = [];
  const currents = [];

  function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    const ratio = window.devicePixelRatio || 1;
    els.starfield.width = Math.floor(width * ratio);
    els.starfield.height = Math.floor(height * ratio);
    els.starfield.style.width = `${width}px`;
    els.starfield.style.height = `${height}px`;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    stars.length = 0;
    currents.length = 0;
    const starCount = Math.max(260, Math.floor((width * height) / 3800));
    for (let i = 0; i < starCount; i += 1) {
      stars.push({
        x: Math.random() * width,
        y: Math.random() * height,
        r: Math.random() * 1.8 + 0.2,
        a: Math.random() * 0.56 + 0.16,
        phase: Math.random() * Math.PI * 2,
      });
    }
    for (let i = 0; i < 26; i += 1) {
      currents.push({
        y: height * (0.58 + Math.random() * 0.3),
        x: Math.random() * width,
        speed: 0.4 + Math.random() * 1.2,
        length: 120 + Math.random() * 260,
        alpha: 0.04 + Math.random() * 0.08,
      });
    }
  }

  function draw() {
    tick += 1;
    ctx.clearRect(0, 0, width, height);
    const grad = ctx.createRadialGradient(width * 0.5, height * 0.45, 0, width * 0.5, height * 0.45, Math.max(width, height));
    grad.addColorStop(0, "rgba(22,26,53,0.52)");
    grad.addColorStop(0.55, "rgba(4,7,18,0.82)");
    grad.addColorStop(1, "rgba(1,2,8,1)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, width, height);

    for (const star of stars) {
      const alpha = star.a + Math.sin(tick * 0.018 + star.phase) * 0.16;
      ctx.beginPath();
      ctx.fillStyle = `rgba(247,241,220,${Math.max(0.05, alpha)})`;
      ctx.arc(star.x, star.y, star.r, 0, Math.PI * 2);
      ctx.fill();
    }

    for (const line of currents) {
      line.x += line.speed;
      if (line.x > width + line.length) line.x = -line.length;
      const wave = Math.sin(tick * 0.02 + line.y * 0.01) * 18;
      ctx.strokeStyle = `rgba(126,219,211,${line.alpha})`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(line.x, line.y + wave);
      ctx.bezierCurveTo(line.x + line.length * 0.33, line.y - 22, line.x + line.length * 0.66, line.y + 26, line.x + line.length, line.y + wave);
      ctx.stroke();
    }
    requestAnimationFrame(draw);
  }

  window.addEventListener("resize", resize);
  resize();
  draw();
}

els.oracleForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = els.questionInput.value.trim();
  if (!question) {
    setStatus("先说出你要问的事情");
    return;
  }
  askOracle(question);
});

els.questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    els.oracleForm.requestSubmit();
  }
});

els.resetButton?.addEventListener("click", () => {
  els.questionInput.value = "";
  clearReading();
  setBusy(false);
  setStatus("星域已重置");
});

els.followUpReset?.addEventListener("click", () => {
  els.questionInput.value = "";
  clearReading();
  setBusy(false);
  setStatus("已结束当前追问，你可以重新输入一个新问题");
  els.questionInput.focus();
});

els.finalClose.addEventListener("click", () => {
  clearReading();
  setBusy(false);
  setStatus("已退出结果，回到星空提问");
});

els.progressToggle?.addEventListener("click", () => {
  ensureProgressLoaded();
  els.progressDrawer?.classList.toggle("open");
});

els.drawerClose?.addEventListener("click", () => {
  els.progressDrawer?.classList.remove("open");
});

els.guideClose?.addEventListener("click", () => {
  closeGuide();
});

els.guideUsePrompt?.addEventListener("click", () => {
  submitGuideQuestion();
});

els.guideWorkbenchFill?.addEventListener("click", () => {
  fillGuideQuestionFromWorkbench();
});

els.guideWorkbenchMapLookup?.addEventListener("click", () => {
  void previewGuideWorkbenchFengshuiMap();
});

els.planetGuide?.addEventListener("click", (event) => {
  const target = event.target;
  if (target instanceof HTMLElement && target.dataset.guideClose === "true") {
    closeGuide();
  }
});

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !els.planetGuide?.classList.contains("hidden")) {
    closeGuide();
  }
});

syncAskActionLabel();

window.addEventListener("pointermove", moveRitualCursor);

bindDivinationWorkbench();
bindPhysiognomyWorkbench();
bindTarotWorkbench();
loadProgress();
if (performanceMode !== "lite") {
  loadModels();
}

function runDeferredBoot() {
  if (performanceMode !== "lite") {
    initStarfield();
    initRitualCanvas();
  }
}

if ("requestIdleCallback" in window) {
  window.requestIdleCallback(runDeferredBoot, { timeout: 1800 });
} else {
  window.setTimeout(runDeferredBoot, 600);
}

let progressLoaded = false;
let progressLoading = false;

function ensureProgressLoaded() {
  if (progressLoaded || progressLoading) return;
  progressLoading = true;
  loadProgress().finally(() => {
    progressLoading = false;
  });
}


