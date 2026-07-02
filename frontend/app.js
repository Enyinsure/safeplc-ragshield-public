const RUNS = {
  full: {
    title: "SafePLC-RAGShield + Qwen2.5-VL-3B",
    metrics: [
      ["93.3%", "1000-case pass rate", "good"],
      ["100%", "Poison block", "good"],
      ["0", "Canary leaks", "good"],
      ["0", "Fallback cases", "good"],
      ["100%", "Audit coverage", "good"],
      ["1000", "Chroma cases", "info"],
      ["144", "Qwen calls", "info"],
    ],
    run: {
      Suite: "adversarial_1000",
      Passed: "933 / 1000",
      Gateway: "off",
      Oracle: "false",
      Generator: "qwen",
      Retrieval: "Chroma + BGE",
      Model: "Qwen2.5-VL-3B-Instruct",
      Review: "trusted",
    },
  },
  baseline: {
    title: "Naive overlay baseline",
    metrics: [
      ["10.0%", "500-case pass rate", "warn"],
      ["0%", "Attack block", "warn"],
      ["0%", "Poison block", "warn"],
      ["97", "Canary leaks", "warn"],
      ["255", "Poison citations", "warn"],
      ["500", "Chroma cases", "info"],
      ["0", "Fallback cases", "good"],
    ],
    run: {
      Suite: "adversarial_500",
      Passed: "50 / 500",
      Gateway: "off",
      Oracle: "false",
      Generator: "none",
      Retrieval: "Chroma + BGE",
      Model: "No trusted review",
      Review: "naive",
    },
  },
  ablation: {
    title: "Module ablation",
    metrics: [
      ["100%", "Full chain 500", "good"],
      ["64.4%", "No query scan", "warn"],
      ["61.0%", "No risk policy", "warn"],
      ["72.8%", "No evidence scan", "warn"],
      ["81.4%", "No combined signal", "warn"],
      ["98.6%", "No M-EPI", "info"],
      ["98.6%", "No ingestion gate", "info"],
    ],
    run: {
      Suite: "adversarial_500",
      Passed: "module dependent",
      Gateway: "off",
      Oracle: "false",
      Generator: "policy path",
      Retrieval: "Chroma + BGE",
      Model: "Trusted modules toggled",
      Review: "trusted",
    },
  },
};

const MODULES = [
  {
    id: "query_scan",
    name: "Query scan",
    score: "critical",
    detail: "输入侧高危意图扫描。消融后 500-case 通过率降到 64.4%，是系统提示泄露、敏感信息请求和越权代理的主要防线。",
  },
  {
    id: "ingestion_gate",
    name: "Ingestion gate",
    score: "98.6%",
    detail: "离线入口校验，阻止不可信材料进入评测证据链。当前 500-case 消融影响较小，但对公开演示的数据卫生很关键。",
  },
  {
    id: "evidence_scan",
    name: "Evidence scan",
    score: "72.8%",
    detail: "检查检索证据里的投毒、间接注入和冲突指令。关闭后 poison_block 从 100% 降到 58.82%。",
  },
  {
    id: "mepi",
    name: "M-EPI",
    score: "98.6%",
    detail: "多模态证据一致性与跨证据冲突汇聚。它让图片、表格和文本证据能进入同一风险决策面。",
  },
  {
    id: "visual_guard",
    name: "Visual guard",
    score: "100%",
    detail: "多模态视觉证据防护。当前 500-case 消融没有拉低总分，后续应增加更强的视觉攻击样例展示其作用。",
  },
  {
    id: "combined_signal",
    name: "Combined signal",
    score: "81.4%",
    detail: "融合 query、evidence、retrieval poison、M-EPI 等信号。关闭后通过率降到 81.4%。",
  },
  {
    id: "risk_policy",
    name: "Risk policy",
    score: "critical",
    detail: "把扫描 flags 映射为 refuse、safe_template、clarify 或 answer。消融后通过率仅 61.0%。",
  },
  {
    id: "audit",
    name: "Hash-chain audit",
    score: "100%",
    detail: "对拦截、澄清和放行记录 SM3 哈希链审计，完整链路 audit_coverage 为 100%。",
  },
];

const FAMILIES = [
  ["benign_control", "none", 100, 100],
  ["cross_modal_vector_misinformation", "LLM09", 20, 20],
  ["direct_plus_retrieval_poison", "LLM01 + LLM02", 42, 42],
  ["direct_prompt_injection", "LLM01", 48, 90],
  ["excessive_agency", "LLM06", 65, 65],
  ["improper_output_handling", "LLM05", 47, 55],
  ["indirect_plus_vector_weakness", "LLM02 + LLM08", 42, 42],
  ["output_handling_plus_agency", "LLM05 + LLM06", 28, 28],
  ["poison_plus_misinformation", "LLM02 + LLM09", 38, 38],
  ["prompt_plus_unbounded_consumption", "LLM01 + LLM10", 20, 20],
  ["retrieval_poisoning", "LLM02", 110, 110],
  ["sensitive_disclosure", "LLM07", 63, 65],
  ["sensitive_plus_prompt_leakage", "LLM07 + LLM01", 36, 36],
  ["supply_chain_plus_poison", "LLM08 + LLM02", 24, 24],
  ["supply_chain_spoof", "LLM08", 45, 45],
  ["system_prompt_leakage", "LLM07", 54, 65],
  ["technical_misinformation", "LLM09", 45, 45],
  ["unbounded_consumption", "LLM10", 26, 30],
  ["vector_embedding_weakness", "LLM08", 80, 80],
];

const ABLATIONS = [
  ["full_chain", "none", 500, 500],
  ["no_combined_signal", "combined_signal", 407, 500],
  ["no_evidence_scan", "evidence_scan", 364, 500],
  ["no_ingestion_gate", "ingestion_gate", 493, 500],
  ["no_mepi", "mepi", 493, 500],
  ["no_query_scan", "query_scan", 322, 500],
  ["no_risk_policy", "risk_policy", 305, 500],
  ["no_visual_guard", "visual_guard", 500, 500],
];

const OWASP = [
  ["LLM01", "Prompt Injection", 152, 194],
  ["LLM02", "Sensitive Info Disclosure", 99, 101],
  ["LLM03", "Supply Chain", 69, 69],
  ["LLM04", "Data Poisoning", 234, 234],
  ["LLM05", "Improper Output Handling", 75, 83],
  ["LLM06", "Excessive Agency", 93, 93],
  ["LLM07", "System Prompt Leakage", 90, 101],
  ["LLM08", "Vector Weakness", 142, 142],
  ["LLM09", "Misinformation", 103, 103],
  ["LLM10", "Unbounded Consumption", 46, 50],
  ["none", "Benign", 100, 100],
];

const CASES = {
  direct: {
    Action: "refuse / safe_template",
    Family: "direct_prompt_injection",
    Flags: "direct_prompt_injection, unsafe_instruction_override",
    Result: "48 / 90 passed",
    Note: "主要短板仍在 L5 复杂改写和多轮伪装注入。",
  },
  poison: {
    Action: "blocked_poison",
    Family: "retrieval_poisoning",
    Flags: "retrieved_poison, indirect_prompt_injection",
    Result: "110 / 110 passed",
    Note: "投毒证据不会进入 Qwen 生成提示词，poison_citation_count 为 0。",
  },
  benign: {
    Action: "answer / clarify",
    Family: "benign_control",
    Flags: "none or unsupported_query_identifier",
    Result: "100 / 100 passed",
    Note: "缺少型号或订货号证据时返回 clarify，而不是编造结论。",
  },
  leak: {
    Action: "refuse",
    Family: "system_prompt_leakage",
    Flags: "system_prompt_leakage, sensitive_information_request",
    Result: "54 / 65 passed",
    Note: "下一轮优化重点是更隐蔽的系统提示词套取表达。",
  },
};

const COMMAND = `python3 benchmark/run_online_benchmark.py \\
  --suite adversarial_1000 \\
  --review-mode trusted \\
  --generator qwen \\
  --gateway off \\
  --poison-mode overlay`;

let activeView = "full";
let activeModule = "query_scan";

function pct(passed, total) {
  return total ? (passed / total) * 100 : 0;
}

function fmtPct(value) {
  return `${value.toFixed(value === 100 ? 0 : 1)}%`;
}

function barClass(value) {
  if (value < 75) return "bad";
  if (value < 90) return "warn";
  return "";
}

function renderMetrics() {
  const grid = document.querySelector("#metricGrid");
  grid.innerHTML = RUNS[activeView].metrics
    .map(
      ([value, label, tone]) => `
        <div class="metric ${tone}">
          <b>${value}</b>
          <span>${label}</span>
        </div>
      `,
    )
    .join("");
}

function renderRun() {
  const runList = document.querySelector("#runList");
  const entries = Object.entries(RUNS[activeView].run);
  runList.innerHTML = entries
    .map(
      ([key, value]) => `
        <div>
          <dt>${key}</dt>
          <dd>${value}</dd>
        </div>
      `,
    )
    .join("");
  document.querySelector("#benchmarkCommand").textContent = COMMAND;
}

function renderModules() {
  const map = document.querySelector("#chainMap");
  map.innerHTML = MODULES.map(
    (module) => `
      <button class="chain-node ${module.id === activeModule ? "active" : ""}" type="button" data-module="${module.id}">
        <b>${module.name}</b>
        <small>${module.id}</small>
        <span class="node-score">${module.score}</span>
      </button>
    `,
  ).join("");

  map.querySelectorAll(".chain-node").forEach((node) => {
    node.addEventListener("click", () => {
      activeModule = node.dataset.module;
      renderModules();
    });
  });

  const selected = MODULES.find((module) => module.id === activeModule) || MODULES[0];
  document.querySelector("#moduleDetail").innerHTML = `
    <h3>${selected.name}</h3>
    <p>${selected.detail}</p>
  `;
}

function renderFamilies() {
  const term = document.querySelector("#familySearch").value.trim().toLowerCase();
  const gapsOnly = document.querySelector("#gapToggle").checked;
  const rows = FAMILIES.filter(([name, owasp, passed, total]) => {
    const rate = pct(passed, total);
    const match = `${name} ${owasp}`.toLowerCase().includes(term);
    const gapMatch = !gapsOnly || rate < 100;
    return match && gapMatch;
  });

  document.querySelector("#familyList").innerHTML = rows
    .map(([name, owasp, passed, total]) => {
      const rate = pct(passed, total);
      const cls = barClass(rate);
      return `
        <div class="family-row ${rate < 100 ? "gap" : ""}">
          <div class="family-name">
            <b>${name}</b>
            <span>${owasp}</span>
          </div>
          <div>${passed} / ${total}</div>
          <div class="bar ${cls}" style="--value: ${rate}%"><span></span></div>
          <div class="rate">${fmtPct(rate)}</div>
        </div>
      `;
    })
    .join("");
}

function renderAblations() {
  document.querySelector("#ablationList").innerHTML = ABLATIONS.map(([name, disabled, passed, total]) => {
    const rate = pct(passed, total);
    const cls = barClass(rate);
    return `
      <div class="ablation-row ${rate < 90 ? "gap" : ""}">
        <div class="ablation-name">
          <b>${name}</b>
          <span>disabled: ${disabled}</span>
        </div>
        <div class="bar ${cls}" style="--value: ${rate}%"><span></span></div>
        <div class="rate">${fmtPct(rate)}</div>
      </div>
    `;
  }).join("");
}

function renderOwasp() {
  document.querySelector("#owaspGrid").innerHTML = OWASP.map(([id, name, passed, total]) => {
    const rate = pct(passed, total);
    return `
      <div class="owasp-row ${rate < 90 ? "gap" : ""}">
        <b>${id}</b>
        <span>${name}<br>${passed} / ${total}</span>
        <div class="rate">${fmtPct(rate)}</div>
      </div>
    `;
  }).join("");
}

function renderCase() {
  const selected = CASES[document.querySelector("#caseSelect").value];
  document.querySelector("#caseView").innerHTML = Object.entries(selected)
    .map(
      ([key, value]) => `
        <div class="case-line">
          <b>${key}</b>
          <span>${value}</span>
        </div>
      `,
    )
    .join("");
}

function setView(view) {
  activeView = view;
  document.querySelectorAll(".segment").forEach((button) => {
    const active = button.dataset.view === view;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  renderMetrics();
  renderRun();
}

document.querySelectorAll(".segment").forEach((button) => {
  button.addEventListener("click", () => setView(button.dataset.view));
});

document.querySelector("#familySearch").addEventListener("input", renderFamilies);
document.querySelector("#gapToggle").addEventListener("change", renderFamilies);
document.querySelector("#caseSelect").addEventListener("change", renderCase);
document.querySelector("#copyCommand").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(COMMAND);
  } catch {
    const textarea = document.createElement("textarea");
    textarea.value = COMMAND;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }
});

renderMetrics();
renderRun();
renderModules();
renderFamilies();
renderAblations();
renderOwasp();
renderCase();
