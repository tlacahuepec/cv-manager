"""Local-only Flask web UI for cv-manager.

Run with:
    python -m web.server

Binds to 127.0.0.1:5000. Refuses non-loopback connections defensively.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, send_file

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.generate import (  # noqa: E402
    CVError,
    DATA_EXAMPLE,
    DATA_FILE,
    ENV_EXAMPLE,
    ENV_FILE,
    ENV_PREFIX,
    TEMPLATES_DIR,
    compile_pdf,
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
            result[key[len(ENV_PREFIX):].lower()] = value
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
            short = key[len(ENV_PREFIX):].lower()
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
        p.name for p in TEMPLATES_DIR.iterdir()
        if p.is_file()
        and p.suffix in {".tex", ".md"}
        and p.name.lower() != "readme.md"
    )


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/state")
def get_state():
    return jsonify({
        "env": _read_env(),
        "env_keys": ENV_KEYS,
        "data": _read_data(),
        "templates": _list_templates(),
        "env_file_exists": ENV_FILE.exists(),
        "data_file_exists": DATA_FILE.exists(),
    })


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
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", template):
        return jsonify({"ok": False, "error": "invalid template name"}), 400
    try:
        out_path = render(template, ROOT / "resumes")
        if want_pdf:
            out_path = compile_pdf(out_path)
    except CVError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return send_file(out_path, as_attachment=True, download_name=out_path.name)


def main() -> None:
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
