"""Render a CV template using data from `.env` and `data/cv_data.private.json`.

Usage:
    python scripts/generate.py [--template classic.tex] [--out-dir resumes]

Identity / contact fields come from environment variables (`CV_*` keys in
`.env`). Structured lists (experiences, education, ...) come from
`data/cv_data.private.json`. Both files are gitignored.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
DATA_FILE = ROOT / "data" / "cv_data.private.json"
DATA_EXAMPLE = ROOT / "data" / "cv_data.example.json"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"

ENV_PREFIX = "CV_"


class CVError(Exception):
    """Recoverable error with a user-facing message."""


def _die(msg: str) -> "None":
    raise CVError(msg)


def load_env_context() -> dict:
    """Load CV_* env vars into a dict with the prefix stripped and lowercased."""
    if not ENV_FILE.exists():
        _die(
            f"missing {ENV_FILE.relative_to(ROOT)}. "
            f"Copy {ENV_EXAMPLE.relative_to(ROOT)} to .env and fill in your details."
        )
    load_dotenv(ENV_FILE)
    ctx = {}
    for key, value in os.environ.items():
        if key.startswith(ENV_PREFIX):
            ctx[key[len(ENV_PREFIX) :].lower()] = value
    if not ctx.get("full_name"):
        _die("CV_FULL_NAME is not set in .env")
    return ctx


def load_json_context() -> dict:
    """Load structured CV data from the private JSON file."""
    if not DATA_FILE.exists():
        _die(
            f"missing {DATA_FILE.relative_to(ROOT)}. "
            f"Copy {DATA_EXAMPLE.relative_to(ROOT)} to cv_data.private.json and edit it."
        )
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _die(f"{DATA_FILE.relative_to(ROOT)} is not valid JSON: {exc}")


def build_environment(template_name: str) -> Environment:
    """Return a Jinja2 Environment with delimiters appropriate for the template."""
    suffix = Path(template_name).suffix.lower()
    if suffix == ".tex":
        return Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            variable_start_string="<<",
            variable_end_string=">>",
            block_start_string="<%",
            block_end_string="%>",
            comment_start_string="<#",
            comment_end_string="#>",
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
            autoescape=False,
            undefined=StrictUndefined,
        )
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        autoescape=False,
        undefined=StrictUndefined,
    )


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "cv"


def render(template_name: str, out_dir: Path) -> Path:
    env_ctx = load_env_context()
    json_ctx = load_json_context()
    # Env wins on key conflicts (identity belongs in .env).
    context = {**json_ctx, **env_ctx}

    jenv = build_environment(template_name)
    try:
        template = jenv.get_template(template_name)
    except TemplateNotFound:
        available = sorted(
            p.name
            for p in TEMPLATES_DIR.iterdir()
            if p.is_file() and p.suffix in {".tex", ".md"} and p.name.lower() != "readme.md"
        )
        _die(f"template {template_name!r} not found. Available: {', '.join(available)}")

    rendered = template.render(**context)

    name_slug = slugify(env_ctx["full_name"])
    template_stem = Path(template_name).stem
    ext = Path(template_name).suffix
    today = date.today().strftime("%Y%m%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name_slug}_{template_stem}_{today}{ext}"
    out_path.write_text(rendered, encoding="utf-8")
    return out_path


LATEX_AUX_SUFFIXES = (".aux", ".log", ".out", ".toc", ".synctex.gz", ".fls", ".fdb_latexmk")

# Templates containing this comment line will be compiled with xelatex instead of pdflatex.
_XELATEX_MARKER = "% engine: xelatex"


def _needs_xelatex(source: Path) -> bool:
    """Check if a .tex file requires XeLaTeX (e.g. uses fontspec)."""
    head = source.read_text(encoding="utf-8")[:2000]
    return _XELATEX_MARKER in head


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def _print_failure(tool: str, result: subprocess.CompletedProcess) -> None:
    output = (result.stdout or "") + (result.stderr or "")
    tail = "\n".join(output.splitlines()[-30:])
    raise CVError(f"{tool} failed (exit {result.returncode})\n{tail}")


def compile_pdf(source: Path) -> Path:
    """Compile a rendered .tex or .md file to PDF. Returns the PDF path."""
    out_dir = source.parent
    pdf_path = source.with_suffix(".pdf")
    suffix = source.suffix.lower()

    if suffix == ".tex":
        use_xelatex = _needs_xelatex(source)
        engine = "xelatex" if use_xelatex else "pdflatex"
        if not shutil.which(engine):
            if use_xelatex:
                _die(
                    "xelatex not found on PATH. This template requires XeLaTeX for font support. "
                    "Install MiKTeX (https://miktex.org/download) or TeX Live."
                )
            else:
                _die("pdflatex not found on PATH. Install MiKTeX (https://miktex.org/download) or TeX Live.")
        cmd = [engine, "-interaction=nonstopmode", "-output-directory", str(out_dir), str(source)]
        # Run twice so cross-references / TOC settle.
        for _ in range(2):
            result = _run(cmd, cwd=out_dir)
            if result.returncode != 0:
                _print_failure(engine, result)
        # Clean aux files.
        stem = source.stem
        for suf in LATEX_AUX_SUFFIXES:
            aux = out_dir / f"{stem}{suf}"
            if aux.exists():
                aux.unlink()
    elif suffix == ".md":
        if not shutil.which("pandoc"):
            _die(
                "pandoc not found on PATH. Install from https://pandoc.org/installing.html or `winget install JohnMacFarlane.Pandoc`."
            )
        cmd = ["pandoc", str(source), "-o", str(pdf_path)]
        result = _run(cmd, cwd=out_dir)
        if result.returncode != 0:
            _print_failure("pandoc", result)
    else:
        _die(f"don't know how to compile {suffix} to PDF")

    return pdf_path


def export_format(source: Path, fmt: str) -> Path:
    """Export a rendered source file to an additional format (docx, html). Returns output path."""
    if not shutil.which("pandoc"):
        _die(
            "pandoc not found on PATH. Install from https://pandoc.org/installing.html or `winget install JohnMacFarlane.Pandoc`."
        )

    out_path = source.with_suffix(f".{fmt}")
    cmd = ["pandoc", str(source), "-o", str(out_path), "--standalone"]

    if fmt == "html":
        cmd.append("--embed-resources")

    result = _run(cmd, cwd=source.parent)
    if result.returncode != 0:
        _print_failure("pandoc", result)

    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--template",
        default="classic.tex",
        help="Template filename in templates/ (default: classic.tex)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "resumes",
        help="Output directory (default: resumes/)",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also compile to PDF (requires pdflatex for .tex, pandoc for .md)",
    )
    parser.add_argument(
        "--format",
        dest="formats",
        help="Additional export formats, comma-separated (docx, html). Requires pandoc.",
    )
    args = parser.parse_args()

    try:
        out_path = render(args.template, args.out_dir)
        print(f"wrote {out_path.relative_to(ROOT)}")

        if args.pdf:
            pdf_path = compile_pdf(out_path)
            print(f"wrote {pdf_path.relative_to(ROOT)}")

        if args.formats:
            for fmt in args.formats.split(","):
                fmt = fmt.strip().lower()
                if fmt and fmt != "pdf":
                    export_path = export_format(out_path, fmt)
                    print(f"wrote {export_path.relative_to(ROOT)}")
    except CVError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
