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
3. (Phase 2) Run the generator to produce a CV under `resumes/`.

## Roadmap

- **Phase 1 (this commit):** structure, privacy, templates, dependencies.
- **Phase 2:** `scripts/generate.py` — merge env + JSON, render Jinja, run
  `pdflatex` / `pandoc`, emit timestamped PDFs into `resumes/`.
- **Phase 3:** Flask web UI to edit data, preview, and download.
- **Phase 4:** More templates (modern, minimal), version history, CI builds.

## Security notes

- Never commit `.env` or any `*.private.*` file. They are already gitignored.
- If you accidentally stage one: `git restore --staged <file>` before commit.
- For extra safety, consider a `detect-secrets` pre-commit hook (Phase 2+).
