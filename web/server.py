"""Local-only Flask web UI for cv-manager.

Run with:
    python -m web.server

Binds to 127.0.0.1:5000. Refuses non-loopback connections defensively.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

from anthropic import Anthropic
from flask import Flask, abort, jsonify, render_template, request, send_file

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.generate import (  # noqa: E402
    DATA_EXAMPLE,
    DATA_FILE,
    ENV_EXAMPLE,
    ENV_FILE,
    ENV_PREFIX,
    TEMPLATES_DIR,
    CVError,
    compile_pdf,
    export_format,
    render,
)

app = Flask(__name__, template_folder="templates", static_folder="static")

# Keys exposed to the env form (lowercase, no prefix). Mirrors .env.example.
ENV_KEYS = [
    "full_name",
    "headline",
    "summary",
    "email",
    "phone",
    "location",
    "linkedin",
    "github",
    "website",
]


@app.before_request
def _require_loopback():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        abort(403)


def _read_env() -> dict:
    """Parse .env (or .env.example if missing) into a {lower_key: value} dict."""
    path = ENV_FILE if ENV_FILE.exists() else ENV_EXAMPLE
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key.startswith(ENV_PREFIX):
            result[key[len(ENV_PREFIX) :].lower()] = value
    return result


def _write_env(values: dict) -> None:
    """Rewrite .env preserving comments / order. Adds missing keys at the end."""
    seen = set()
    out_lines: list[str] = []
    src = ENV_FILE if ENV_FILE.exists() else ENV_EXAMPLE
    for line in src.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            out_lines.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key.startswith(ENV_PREFIX):
            short = key[len(ENV_PREFIX) :].lower()
            if short in values:
                out_lines.append(f'{key}="{_escape_env(values[short])}"')
                seen.add(short)
                continue
        out_lines.append(line)
    # Append any new keys that weren't in the template.
    for short, value in values.items():
        if short not in seen:
            out_lines.append(f'{ENV_PREFIX}{short.upper()}="{_escape_env(value)}"')
    ENV_FILE.write_text("\n".join(out_lines) + "\n", encoding="utf-8")


def _escape_env(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _read_data() -> dict:
    path = DATA_FILE if DATA_FILE.exists() else DATA_EXAMPLE
    return json.loads(path.read_text(encoding="utf-8"))


def _list_templates() -> list[str]:
    return sorted(
        p.name
        for p in TEMPLATES_DIR.iterdir()
        if p.is_file() and p.suffix in {".tex", ".md"} and p.name.lower() != "readme.md"
    )


def _render_with_custom_data(template_name: str, out_dir: Path, custom_data: dict) -> Path:
    """Render a template with custom CV data (used for job matching)."""
    from datetime import date

    from scripts.generate import build_environment, slugify

    env_ctx = _read_env()
    context = {**custom_data, **env_ctx}

    jenv = build_environment(template_name)
    try:
        template = jenv.get_template(template_name)
    except Exception as exc:
        raise CVError(f"template error: {exc}")

    rendered = template.render(**context)

    name_slug = slugify(env_ctx["full_name"])
    template_stem = Path(template_name).stem
    ext = Path(template_name).suffix
    today = date.today().strftime("%Y%m%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name_slug}_{template_stem}_matched_{today}{ext}"
    out_path.write_text(rendered, encoding="utf-8")
    return out_path


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/state")
def get_state():
    return jsonify(
        {
            "env": _read_env(),
            "env_keys": ENV_KEYS,
            "data": _read_data(),
            "templates": _list_templates(),
            "env_file_exists": ENV_FILE.exists(),
            "data_file_exists": DATA_FILE.exists(),
        }
    )


@app.post("/api/env")
def save_env():
    payload = request.get_json(silent=True) or {}
    values = {k: str(v) for k, v in payload.items() if k in ENV_KEYS}
    _write_env(values)
    return jsonify({"ok": True})


@app.post("/api/data")
def save_data():
    raw = request.get_data(as_text=True)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return jsonify({"ok": False, "error": f"invalid JSON: {exc}"}), 400
    if not isinstance(parsed, dict):
        return jsonify({"ok": False, "error": "top-level must be an object"}), 400
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(parsed, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return jsonify({"ok": True})


@app.post("/api/generate")
def generate():
    payload = request.get_json(silent=True) or {}
    template = payload.get("template", "classic.tex")
    want_pdf = bool(payload.get("pdf", False))
    output_format = (payload.get("format") or "").strip().lower()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", template):
        return jsonify({"ok": False, "error": "invalid template name"}), 400
    if output_format and output_format not in ("pdf", "docx", "html"):
        return jsonify({"ok": False, "error": f"unsupported format: {output_format}"}), 400
    try:
        out_path = render(template, ROOT / "resumes")
        if output_format == "pdf" or want_pdf:
            out_path = compile_pdf(out_path)
        elif output_format in ("docx", "html"):
            out_path = export_format(out_path, output_format)
    except CVError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return send_file(out_path, as_attachment=True, download_name=out_path.name)


@app.post("/api/match-job")
def match_job():
    payload = request.get_json(silent=True) or {}
    job_description = (payload.get("job_description") or "").strip()
    template = payload.get("template", "classic.tex")
    want_pdf = bool(payload.get("pdf", False))

    if not job_description:
        return jsonify({"ok": False, "error": "job_description is required"}), 400
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", template):
        return jsonify({"ok": False, "error": "invalid template name"}), 400

    try:
        data = _read_data()
        if not data.get("experiences") or len(data["experiences"]) == 0:
            raise CVError("No experience entries found in CV data")

        client = Anthropic()
        last_job = data["experiences"][-1]

        prompt = f"""You are a resume expert. Analyze the job description and the candidate's last job experience, then generate updated highlights and technologies that emphasize relevant skills.

Job Description:
{job_description}

Current job experience:
- Title: {last_job.get("title", "")}
- Company: {last_job.get("company", "")}
- Current highlights: {json.dumps(last_job.get("highlights", []))}
- Current tech: {json.dumps(last_job.get("tech", []))}

Return ONLY a valid JSON object (no markdown, no extra text) with this exact structure:
{{
  "highlights": ["highlight 1", "highlight 2", "highlight 3", "highlight 4", "highlight 5", "highlight 6"],
  "tech": ["tech1", "tech2", "tech3", "tech4", "tech5", "tech6", "tech7", "tech8"]
}}

Guidelines:
- Generate 5-6 new achievement bullets that emphasize skills matching the job description
- Extract 5-8 technologies from the job description that align with the candidate's experience
- Keep bullets concise and measurable when possible
- Ensure tech choices are realistic based on the job description and current experience
- Do not include bullets already similar to existing ones"""

        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text.strip()
        try:
            matched_data = json.loads(response_text)
        except json.JSONDecodeError:
            raise CVError("Failed to parse Claude response as JSON")

        if not isinstance(matched_data, dict):
            raise CVError("Invalid response format from Claude")

        matched_cv = copy.deepcopy(data)
        matched_cv["experiences"][-1]["highlights"] = matched_data.get("highlights", [])
        matched_cv["experiences"][-1]["tech"] = matched_data.get("tech", [])

        out_path = _render_with_custom_data(template, ROOT / "resumes", matched_cv)
        if want_pdf:
            out_path = compile_pdf(out_path)

    except CVError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Internal error: {str(exc)}"}), 500

    return send_file(out_path, as_attachment=True, download_name=out_path.name)


@app.post("/api/cover-letter")
def cover_letter():
    payload = request.get_json(silent=True) or {}
    job_description = (payload.get("job_description") or "").strip()
    want_pdf = bool(payload.get("pdf", False))
    recipient_name = (payload.get("recipient_name") or "").strip()
    recipient_company = (payload.get("recipient_company") or "").strip()

    if not job_description:
        return jsonify({"ok": False, "error": "job_description is required"}), 400

    try:
        from datetime import date

        from scripts.generate import build_environment, slugify

        data = _read_data()
        env_ctx = _read_env()

        client = Anthropic()

        experiences_summary = json.dumps(data.get("experiences", [])[:3], indent=2)
        skills_summary = json.dumps(data.get("skills", []), indent=2)

        prompt = f"""You are a professional cover letter writer. Write a tailored cover letter body for this candidate applying to a specific job.

Job Description:
{job_description}

Candidate Info:
- Name: {env_ctx.get("full_name", "")}
- Headline: {env_ctx.get("headline", "")}
- Summary: {env_ctx.get("summary", "")}

Recent Experience:
{experiences_summary}

Skills:
{skills_summary}

Return ONLY the body paragraphs of the cover letter (no salutation, no closing, no signature). Write 3-4 paragraphs that:
1. Open with enthusiasm for the specific role and company
2. Highlight 2-3 relevant achievements from their experience that directly match the job requirements
3. Connect their skills to the company's needs
4. Close with a forward-looking statement about contributing to the team

Keep the tone professional but personable. Be specific — reference actual achievements and technologies from their experience that match the job. Do not use generic filler. Total length: 250-350 words."""

        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        letter_body = response.content[0].text.strip()

        context = {
            **env_ctx,
            "letter_date": date.today().strftime("%B %d, %Y"),
            "recipient_name": recipient_name,
            "recipient_company": recipient_company,
            "recipient_address": "",
            "salutation": f"Hiring Manager at {recipient_company}" if recipient_company else "Hiring Manager",
            "letter_body": letter_body,
        }

        jenv = build_environment("cover_letter.tex")
        template = jenv.get_template("cover_letter.tex")
        rendered = template.render(**context)

        name_slug = slugify(env_ctx["full_name"])
        today = date.today().strftime("%Y%m%d")
        out_dir = ROOT / "resumes"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{name_slug}_cover_letter_{today}.tex"
        out_path.write_text(rendered, encoding="utf-8")

        if want_pdf:
            out_path = compile_pdf(out_path)

    except CVError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Internal error: {str(exc)}"}), 500

    return send_file(out_path, as_attachment=True, download_name=out_path.name)


def main() -> None:
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
