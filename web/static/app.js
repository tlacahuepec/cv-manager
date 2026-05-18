const $ = (sel) => document.querySelector(sel);

function initTabs() {
  const tabs = document.querySelectorAll(".nav-tab");
  const panels = document.querySelectorAll(".tab-panel");

  function activate(tabName) {
    tabs.forEach(t => t.classList.toggle("active", t.dataset.tab === tabName));
    panels.forEach(p => p.classList.toggle("active", p.id === `tab-${tabName}`));
    if (tabName === "history") loadHistory();
  }

  tabs.forEach(t => t.addEventListener("click", () => {
    const name = t.dataset.tab;
    activate(name);
    history.replaceState(null, "", `#${name}`);
  }));

  const hash = location.hash.replace("#", "");
  const valid = [...tabs].map(t => t.dataset.tab);
  activate(valid.includes(hash) ? hash : "generate");
}

const ENV_LABELS = {
  full_name: "Full name",
  headline: "Headline",
  summary: "Summary",
  email: "Email",
  phone: "Phone",
  location: "Location",
  linkedin: "LinkedIn URL",
  github: "GitHub URL",
  website: "Website",
};

let state = null;
let selectedTemplate = null;

async function loadState() {
  const res = await fetch("/api/state");
  state = await res.json();
  renderEnvForm();
  renderDataTextarea();
  renderTemplateGrid();
  renderMatchTemplateSelect();
  renderAtsTemplateSelect();
  $("#env-warning").hidden = state.env_file_exists;
  $("#data-warning").hidden = state.data_file_exists;
}

function renderEnvForm() {
  const form = $("#env-form");
  form.innerHTML = "";
  for (const key of state.env_keys) {
    const wrap = document.createElement("label");
    wrap.className = "field";
    const span = document.createElement("span");
    span.textContent = ENV_LABELS[key] || key;
    wrap.appendChild(span);
    const isLong = key === "summary";
    const input = document.createElement(isLong ? "textarea" : "input");
    input.name = key;
    input.value = state.env[key] || "";
    if (!isLong) input.type = "text";
    wrap.appendChild(input);
    form.appendChild(wrap);
  }
}

function renderDataTextarea() {
  $("#data-json").value = JSON.stringify(state.data, null, 2);
}

function renderTemplateGrid() {
  const grid = $("#template-grid");
  grid.innerHTML = "";
  selectedTemplate = state.templates[0] || null;
  for (const name of state.templates) {
    const stem = name.replace(/\.[^.]+$/, "");
    const card = document.createElement("div");
    card.className = "template-card" + (name === selectedTemplate ? " selected" : "");
    card.dataset.template = name;
    const previewUrl = state.previews && state.previews[stem];
    if (previewUrl) {
      card.innerHTML = `<img src="${previewUrl}" alt="${name}"><div class="tpl-name">${name}</div>`;
    } else {
      card.innerHTML = `<div class="placeholder">No preview</div><div class="tpl-name">${name}</div>`;
    }
    card.addEventListener("click", () => {
      grid.querySelectorAll(".template-card").forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");
      selectedTemplate = name;
    });
    grid.appendChild(card);
  }
}

function renderMatchTemplateSelect() {
  const select = $("#match-template-select");
  select.innerHTML = "";
  for (const name of state.templates) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    select.appendChild(opt);
  }
}

function renderAtsTemplateSelect() {
  const select = $("#ats-template-select");
  select.innerHTML = "";
  for (const name of state.templates) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    select.appendChild(opt);
  }
}

function flash(el, msg, ok = true) {
  el.textContent = msg;
  el.className = "status " + (ok ? "ok" : "err");
  if (ok) setTimeout(() => { if (el.textContent === msg) el.textContent = ""; }, 2500);
}

$("#save-env").addEventListener("click", async () => {
  const form = $("#env-form");
  const values = {};
  for (const el of form.elements) {
    if (el.name) values[el.name] = el.value;
  }
  const res = await fetch("/api/env", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(values),
  });
  const body = await res.json();
  if (res.ok) {
    flash($("#env-status"), "saved");
    state.env_file_exists = true;
    $("#env-warning").hidden = true;
  } else {
    flash($("#env-status"), body.error || "error", false);
  }
});

$("#save-data").addEventListener("click", async () => {
  const raw = $("#data-json").value;
  try {
    JSON.parse(raw);
  } catch (e) {
    flash($("#data-status"), "invalid JSON: " + e.message, false);
    return;
  }
  const res = await fetch("/api/data", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: raw,
  });
  const body = await res.json();
  if (res.ok) {
    flash($("#data-status"), "saved");
    state.data_file_exists = true;
    $("#data-warning").hidden = true;
  } else {
    flash($("#data-status"), body.error || "error", false);
  }
});

$("#generate-btn").addEventListener("click", async () => {
  const status = $("#generate-status");
  if (!selectedTemplate) {
    flash(status, "please select a template", false);
    return;
  }
  status.textContent = "generating...";
  status.className = "status";
  const format = $("#format-select").value;
  const res = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      template: selectedTemplate,
      format: format,
      pdf: format === "pdf",
    }),
  });
  if (!res.ok) {
    let msg = "error";
    try { msg = (await res.json()).error || msg; } catch {}
    status.textContent = msg;
    status.className = "status err";
    return;
  }
  const disposition = res.headers.get("content-disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : "cv";
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  flash(status, `downloaded ${filename}`);
});

$("#match-btn").addEventListener("click", async () => {
  const status = $("#match-status");
  const jobDesc = $("#job-description").value.trim();

  if (!jobDesc) {
    flash(status, "please paste a job description", false);
    return;
  }

  status.textContent = "analyzing job description...";
  status.className = "status";

  const res = await fetch("/api/match-job", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_description: jobDesc,
      template: $("#match-template-select").value,
      pdf: $("#match-pdf-checkbox").checked,
    }),
  });

  if (!res.ok) {
    let msg = "error";
    try { msg = (await res.json()).error || msg; } catch {}
    status.textContent = msg;
    status.className = "status err";
    return;
  }

  const disposition = res.headers.get("content-disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : "cv_matched";
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  flash(status, `downloaded ${filename}`);
});

$("#cover-letter-btn").addEventListener("click", async () => {
  const status = $("#match-status");
  const jobDesc = $("#job-description").value.trim();

  if (!jobDesc) {
    flash(status, "please paste a job description", false);
    return;
  }

  status.textContent = "generating cover letter...";
  status.className = "status";

  const res = await fetch("/api/cover-letter", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_description: jobDesc,
      recipient_name: $("#cl-recipient-name").value.trim(),
      recipient_company: $("#cl-recipient-company").value.trim(),
      pdf: $("#cl-pdf-checkbox").checked,
    }),
  });

  if (!res.ok) {
    let msg = "error";
    try { msg = (await res.json()).error || msg; } catch {}
    status.textContent = msg;
    status.className = "status err";
    return;
  }

  const disposition = res.headers.get("content-disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : "cover_letter";
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  flash(status, `downloaded ${filename}`);
});

async function loadHistory() {
  const container = $("#history-list");
  try {
    const res = await fetch("/api/history");
    const entries = await res.json();
    if (!entries.length) {
      container.innerHTML = '<p class="muted">No generations yet.</p>';
      return;
    }
    container.innerHTML = entries.map(e => {
      const date = new Date(e.timestamp).toLocaleString();
      const badge = e.matched ? ' <span class="badge">matched</span>' :
                    e.is_cover_letter ? ' <span class="badge">cover letter</span>' : '';
      const disabled = e.available ? '' : ' disabled title="File no longer on disk"';
      return `<div class="history-entry">
        <span class="history-meta">${date} &mdash; <code>${e.template}</code>${badge}</span>
        <span class="history-file">${e.filename}</span>
        <button class="history-dl"${disabled} data-id="${e.id}">Download</button>
      </div>`;
    }).join("");
  } catch {
    container.innerHTML = '<p class="muted">Could not load history.</p>';
  }
}

document.addEventListener("click", async (ev) => {
  if (!ev.target.classList.contains("history-dl")) return;
  const id = ev.target.dataset.id;
  const res = await fetch(`/api/history/${id}/download`);
  if (!res.ok) return;
  const disposition = res.headers.get("content-disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : "cv";
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
});

$("#ats-btn").addEventListener("click", async () => {
  const status = $("#ats-status");
  const results = $("#ats-results");
  const card = $("#ats-score-card");

  status.textContent = "analyzing ATS compatibility...";
  status.className = "status";
  results.hidden = true;

  const jobDesc = $("#job-description") ? $("#job-description").value.trim() : "";

  const res = await fetch("/api/ats-check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      template: $("#ats-template-select").value,
      job_description: jobDesc,
    }),
  });

  const data = await res.json();

  if (!res.ok || !data.ok) {
    status.textContent = data.error || "error";
    status.className = "status err";
    return;
  }

  status.textContent = "";

  const scoreColor = data.score >= 80 ? "#2a8" : data.score >= 60 ? "#e90" : "#c33";
  const cats = data.categories;

  card.innerHTML = `
    <div class="ats-total" style="border-color: ${scoreColor}">
      <span class="ats-number" style="color: ${scoreColor}">${data.score}</span>
      <span class="ats-label">/ 100</span>
    </div>
    <div class="ats-categories">
      ${Object.entries(cats).map(([name, c]) => `
        <div class="ats-cat">
          <strong>${name}</strong>: ${c.score}/25
          <span class="muted">&mdash; ${c.feedback}</span>
        </div>
      `).join("")}
    </div>
    ${data.suggestions ? `
      <div class="ats-suggestions">
        <strong>Suggestions:</strong>
        <ul>${data.suggestions.map(s => `<li>${s}</li>`).join("")}</ul>
      </div>
    ` : ""}
  `;
  results.hidden = false;
});

loadState();
loadHistory();
initTabs();
