# cv-manager

[![CI](https://github.com/tlacahuepec/cv-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/tlacahuepec/cv-manager/actions/workflows/ci.yml)

Manage, generate, and store multiple resume/CV versions from templates.

## Project goal

A single source of truth for your CV content, rendered into multiple formats
(LaTeX → PDF, Markdown → HTML/PDF) via reusable templates — with personal
information kept **out of version control**.

## Repository layout

```
cv-manager/
├── data/
│   ├── cv_data.example.json      # Schema reference (committed)
│   └── cv_data.private.json      # Your real structured data (gitignored)
├── templates/
│   ├── classic.tex               # Two-page LaTeX (uses << >> / <% %>)
│   ├── classic.md                # Markdown (uses {{ }} / {% %})
│   ├── modern.tex                # Two-column sidebar LaTeX
│   ├── minimal.md                # ATS-friendly plain Markdown
│   ├── awesome.tex               # Awesome-CV inspired LaTeX
│   ├── cover_letter.tex          # Cover letter LaTeX
│   └── README.md                 # Template authoring guide
├── scripts/
│   ├── generate.py               # CLI CV generator
│   ├── generate_previews.py      # Template thumbnail generator
│   └── history.py                # Generation history utilities
├── web/
│   ├── server.py                 # Flask app (localhost only)
│   ├── static/                   # JS, CSS, preview images
│   └── templates/                # HTML templates
├── tests/
├── resumes/                      # Generated outputs (gitignored)
├── .env.example                  # Identity/contact placeholders (committed)
├── .env                          # Your real identity/contact (gitignored)
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Privacy model

Personal data is split across two gitignored files:

| File                          | Holds                                    | Why                                |
| ----------------------------- | ---------------------------------------- | ---------------------------------- |
| `.env`                        | Single-value fields (name, email, etc.)  | Easy `os.environ` access; standard |
| `data/cv_data.private.json`   | Lists (experience, education, skills…)   | Structured data, easy to edit      |

Both files are blocked by `.gitignore`. The committed `.env.example` and
`data/cv_data.example.json` carry only placeholder values and document the
schema. A defense-in-depth glob (`*.private.*`) is also ignored.

## Setup

```powershell
# 1. Clone
git clone <your-fork-url> cv-manager
cd cv-manager

# 2. Copy the templates and fill in your real data (these stay local)
Copy-Item .env.example .env
Copy-Item data\cv_data.example.json data\cv_data.private.json
# Edit both files in your editor.

# 3. Install Python dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Development

```bash
# Install dev dependencies (includes pytest, ruff, pre-commit)
pip install -r requirements-dev.txt

# Set up pre-commit hooks (secret scanning, linting, formatting)
pre-commit install

# Run hooks manually against all files
pre-commit run --all-files

# Run tests
pytest tests/ -v
```

## Generating a CV

After completing **Setup**, run:

```powershell
# default: templates/classic.tex (writes .tex only)
python scripts/generate.py

# pick a different template
python scripts/generate.py --template modern.tex

# compile to PDF (requires pdflatex for .tex, pandoc for .md)
python scripts/generate.py --template classic.tex --pdf

# export to additional formats (requires pandoc)
python scripts/generate.py --template classic.tex --pdf --format docx,html
```

Output lands at `resumes/{name_slug}_{template}_{YYYYMMDD}.{ext}` — e.g.
`resumes/jane_doe_classic_20260510.tex` (and `.pdf` when `--pdf` is set).
All files in `resumes/` are gitignored (they contain your personal data).

## PDF toolchain (Windows)

PDF compilation (`--pdf`) requires one of these tools on PATH:

- **MiKTeX** (LaTeX → PDF) — provides `pdflatex`.
- **Pandoc** (Markdown → PDF/HTML/DOCX). Pandoc's PDF writer also needs a
  LaTeX engine (MiKTeX covers this).

### Install via a package manager (recommended)

```powershell
# winget (built into Windows 10/11)
winget install --id MiKTeX.MiKTeX
winget install --id JohnMacFarlane.Pandoc

# or Chocolatey
choco install miktex pandoc

# or Scoop
scoop install latex pandoc
```

Open a new terminal after installing so PATH refreshes.

### Manual installers

- MiKTeX: <https://miktex.org/download> (alt: TeX Live, <https://www.tug.org/texlive/>)
- Pandoc: <https://pandoc.org/installing.html>

The script auto-detects each tool and prints an install hint if it's missing.
You can still compile manually if you prefer:

```powershell
pdflatex -output-directory resumes resumes\jane_doe_classic_20260510.tex
pandoc resumes\jane_doe_classic_20260510.md -o resumes\jane_doe_classic_20260510.pdf
```

## Web UI

A local Flask app provides a full-featured browser interface. It binds to
**localhost only** and refuses non-loopback connections.

```powershell
.\.venv\Scripts\python.exe -m web.server
# Open http://127.0.0.1:5000
```

Features:

- Edit identity/contact fields and save to `.env`
- Edit structured JSON with live validation
- Pick a template from a visual grid (with preview thumbnails)
- Generate in PDF, DOCX, or HTML and download instantly
- **AI Job Matching** — paste a job description, get a CV tailored to that role
- **AI Cover Letter** — generate a personalized cover letter from your profile + job description
- **ATS Compatibility Checker** — score your CV 0–100 across structure, keywords, formatting, and content
- **Generation History** — browse and re-download past CVs

## Roadmap

- ~~Phase 1:~~ Structure, privacy model, templates, dependencies.
- ~~Phase 2:~~ CLI generator (`scripts/generate.py`).
- ~~Phase 2.5:~~ PDF compilation (`--pdf`) with auto-detected engines.
- ~~Phase 3:~~ Flask web UI — edit, generate, download.
- ~~Phase 4:~~ Additional templates (modern, minimal, awesome), export formats
  (DOCX, HTML), AI features (job matching, cover letters, ATS checker),
  template previews, generation history, CI pipeline.

## Security notes

- Never commit `.env` or any `*.private.*` file. They are already gitignored.
- If you accidentally stage one: `git restore --staged <file>` before commit.
- Pre-commit hooks with `detect-secrets` are configured to block accidental secret commits.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.
