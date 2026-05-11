# cv-manager

Manage, generate, and store multiple resume/CV versions from templates.

## Project goal

A single source of truth for your CV content, rendered into multiple formats
(LaTeX → PDF, Markdown → HTML/PDF) via reusable templates — with personal
information kept **out of version control**.

## Repository layout

```
cv-manager/
├── data/
│   ├── cv_data.example.json   # Schema reference (committed)
│   └── cv_data.private.json   # Your real structured data (gitignored)
├── templates/
│   ├── classic.tex            # LaTeX template (uses << >> / <% %>)
│   ├── classic.md             # Markdown template (uses {{ }} / {% %})
│   └── README.md              # Template authoring guide
├── resumes/                   # Generated outputs (PDFs gitignored)
├── scripts/                   # Generator (Phase 2)
├── .env.example               # Identity/contact placeholders (committed)
├── .env                       # Your real identity/contact (gitignored)
├── .gitignore
├── requirements.txt
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

# 3. (Optional, ready for Phase 2) install Python deps
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Workflow (current)

1. Edit `.env` and `data/cv_data.private.json`.
2. Edit a template under `templates/` if you want a new look.
3. Run the generator to produce a CV under `resumes/`.

## Generating a CV

After completing **Setup**, run:

```powershell
# default: templates/classic.tex (writes .tex only)
python scripts/generate.py

# pick a different template
python scripts/generate.py --template classic.md

# also compile to PDF (requires pdflatex for .tex, pandoc for .md)
python scripts/generate.py --template classic.tex --pdf
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

A small Flask app provides a browser editor for `.env` and the private JSON,
plus a one-click generate/download button. It binds to **localhost only** and
refuses non-loopback connections.

```powershell
.\.venv\Scripts\python.exe -m web.server
# Open http://127.0.0.1:5000
```

Features:

- Edit identity/contact fields, save to `.env`.
- Edit the structured JSON in a textarea (validated before save).
- Pick a template, optionally compile to PDF, download the result.

## Roadmap

- **Phase 1:** structure, privacy, templates, dependencies.
- **Phase 2:** `scripts/generate.py` — render Jinja templates from `.env` +
  private JSON.
- **Phase 2.5:** `--pdf` flag auto-runs `pdflatex` / `pandoc`.
- **Phase 3 (this commit):** Flask web UI (localhost-only) to edit data and
  download generated CVs.
- **Phase 4:** More templates (modern, minimal), version history, CI builds.

## Security notes

- Never commit `.env` or any `*.private.*` file. They are already gitignored.
- If you accidentally stage one: `git restore --staged <file>` before commit.
- For extra safety, consider a `detect-secrets` pre-commit hook (Phase 2+).

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.
