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
  renderDataView();
  renderTemplateGrid();
  renderMatchTemplateSelect();
  renderAtsTemplateSelect();
  $("#env-warning").hidden = state.env_file_exists;
  $("#data-warning").hidden = state.data_file_exists;
}

let dataEditing = false;

function setDataEditing(editing) {
  dataEditing = editing;
  $("#data-view").hidden = editing;
  $("#data-edit").hidden = !editing;
  $("#data-edit-toggle").textContent = editing ? "Cancel" : "Edit";
}

let envEditing = false;

function setEnvEditing(editing) {
  envEditing = editing;
  const form = $("#env-form");
  for (const el of form.elements) {
    el.disabled = !editing;
  }
  $("#env-actions").hidden = !editing;
  $("#env-edit-toggle").textContent = editing ? "Cancel" : "Edit";
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
  setEnvEditing(false);
}

function renderDataTextarea() {
  $("#data-json").value = JSON.stringify(state.data, null, 2);
}

function formatDate(str) {
  if (!str) return "";
  if (str.toLowerCase() === "present") return "Present";
  const parts = str.split("-");
  if (parts.length === 2) {
    const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    return `${months[parseInt(parts[1], 10) - 1]} ${parts[0]}`;
  }
  return str;
}

function renderDataView() {
  const d = state.data;
  const container = $("#data-view");
  let html = "";

  if (d.summary) {
    html += `<div class="cv-section-title">Summary</div>`;
    html += `<p class="cv-summary">${d.summary}</p>`;
  }

  if (d.experiences?.length) {
    html += `<div class="cv-section-title">Experience</div>`;
    for (const exp of d.experiences) {
      html += `<div class="cv-card">
        <div class="cv-card-header">
          <div><span class="cv-card-title">${exp.title}</span> <span class="cv-card-subtitle">&mdash; ${exp.company}</span></div>
          <span class="cv-card-dates">${formatDate(exp.start_date)} &ndash; ${formatDate(exp.end_date)}</span>
        </div>
        ${exp.location ? `<div class="cv-card-location">${exp.location}</div>` : ""}
        ${exp.highlights?.length ? `<ul class="cv-highlights">${exp.highlights.map(h => `<li>${h}</li>`).join("")}</ul>` : ""}
        ${exp.tech?.length ? `<div class="cv-tech-list">${exp.tech.map(t => `<span class="cv-tech-badge">${t}</span>`).join("")}</div>` : ""}
      </div>`;
    }
  }

  if (d.education?.length) {
    html += `<div class="cv-section-title">Education</div>`;
    for (const edu of d.education) {
      html += `<div class="cv-card">
        <div class="cv-card-header">
          <div><span class="cv-card-title">${edu.degree}</span> <span class="cv-card-subtitle">&mdash; ${edu.institution}</span></div>
          <span class="cv-card-dates">${formatDate(edu.start_date)} &ndash; ${formatDate(edu.end_date)}</span>
        </div>
        ${edu.location ? `<div class="cv-card-location">${edu.location}</div>` : ""}
        ${edu.notes ? `<p class="cv-card-notes">${edu.notes}</p>` : ""}
      </div>`;
    }
  }

  if (d.skills?.length) {
    html += `<div class="cv-section-title">Skills</div>`;
    for (const group of d.skills) {
      html += `<div class="cv-skills-group">
        <span class="cv-skills-label">${group.category}</span>
        <div class="cv-tech-list">${group.items.map(i => `<span class="cv-tech-badge">${i}</span>`).join("")}</div>
      </div>`;
    }
  }

  if (d.projects?.length) {
    html += `<div class="cv-section-title">Projects</div>`;
    for (const proj of d.projects) {
      const nameHtml = proj.url ? `<a href="${proj.url}" target="_blank">${proj.name}</a>` : proj.name;
      html += `<div class="cv-card">
        <span class="cv-card-title">${nameHtml}</span>
        ${proj.description ? `<p class="cv-card-notes">${proj.description}</p>` : ""}
        ${proj.tech?.length ? `<div class="cv-tech-list">${proj.tech.map(t => `<span class="cv-tech-badge">${t}</span>`).join("")}</div>` : ""}
      </div>`;
    }
  }

  if (d.certifications?.length) {
    html += `<div class="cv-section-title">Certifications</div>`;
    for (const cert of d.certifications) {
      const nameHtml = cert.url ? `<a href="${cert.url}" target="_blank">${cert.name}</a>` : cert.name;
      html += `<div class="cv-card">
        <div class="cv-card-header">
          <span class="cv-card-title">${nameHtml}</span>
          <span class="cv-card-dates">${cert.date || ""}</span>
        </div>
        ${cert.issuer ? `<div class="cv-card-subtitle">${cert.issuer}</div>` : ""}
      </div>`;
    }
  }

  if (d.languages?.length) {
    html += `<div class="cv-section-title">Languages</div>`;
    html += `<p class="cv-languages">${d.languages.map(l => `${l.name} (${l.level})`).join(", ")}</p>`;
  }

  container.innerHTML = html;
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

$("#env-edit-toggle").addEventListener("click", () => {
  if (envEditing) {
    renderEnvForm();
  } else {
    setEnvEditing(true);
  }
});

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
    for (const el of $("#env-form").elements) {
      if (el.name) state.env[el.name] = el.value;
    }
    setEnvEditing(false);
  } else {
    flash($("#env-status"), body.error || "error", false);
  }
});

$("#data-edit-toggle").addEventListener("click", () => {
  if (dataEditing) {
    setDataEditing(false);
  } else {
    renderDataTextarea();
    setDataEditing(true);
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
    state.data = JSON.parse(raw);
    state.data_file_exists = true;
    $("#data-warning").hidden = true;
    renderDataView();
    setDataEditing(false);
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

initTabs();
loadState();
loadHistory();
