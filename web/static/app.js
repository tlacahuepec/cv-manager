const $ = (sel) => document.querySelector(sel);

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

async function loadState() {
  const res = await fetch("/api/state");
  state = await res.json();
  renderEnvForm();
  renderDataTextarea();
  renderTemplateSelect();
  renderMatchTemplateSelect();
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

function renderTemplateSelect() {
  const select = $("#template-select");
  select.innerHTML = "";
  for (const name of state.templates) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    select.appendChild(opt);
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
  status.textContent = "generating...";
  status.className = "status";
  const res = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      template: $("#template-select").value,
      pdf: $("#pdf-checkbox").checked,
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

loadState();
