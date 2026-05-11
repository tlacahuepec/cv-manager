# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-05-10

### Added
- `templates/modern.tex` — two-column LaTeX template with tinted sidebar
  (contact, skills, languages, certifications) and main column (summary,
  experience, education, projects). Requires `paracol` and `fontawesome5`.
- `templates/minimal.md` — ATS-friendly Markdown template (plain text, no
  tables, ALL-CAPS section headings).

## [0.3.0] - 2026-05-10

### Added
- Flask web UI at `web/` (server, HTML, JS, CSS).
- Endpoints: `GET /`, `GET /api/state`, `POST /api/env`, `POST /api/data`,
  `POST /api/generate`.
- Browser editor for `.env` and `data/cv_data.private.json` with template
  picker, PDF checkbox, and one-click download.
- `Flask>=3.0` dependency.

### Changed
- `scripts/generate.py` raises `CVError` instead of calling `sys.exit`, so
  the web layer can return clean 400 responses.
- Template lister now excludes `README.md` from the available list.

### Security
- Web server binds to `127.0.0.1:5000` and rejects non-loopback connections.

## [0.2.1] - 2026-05-10

### Added
- `--pdf` flag on `scripts/generate.py`. Auto-runs `pdflatex` (twice, for
  refs/TOC) for `.tex` and `pandoc` for `.md`.
- LaTeX aux file cleanup (`.aux .log .out .toc .synctex.gz .fls .fdb_latexmk`)
  after successful PDF compilation.
- Pre-flight detection of `pdflatex` / `pandoc` with install hints (winget,
  Chocolatey, Scoop) when missing.
- README section for the Windows PDF toolchain.

## [0.2.0] - 2026-05-10

### Added
- `scripts/generate.py` — render Jinja templates from `.env` (identity) and
  `data/cv_data.private.json` (structured lists).
- File-extension-aware Jinja delimiters: `<< >> / <% %>` for `.tex`,
  defaults for `.md`.
- Output naming pattern: `{name_slug}_{template}_{YYYYMMDD}.{ext}`.
- Friendly errors for missing `.env`, missing private JSON, invalid JSON,
  unknown template.
- `scripts/__init__.py`.

### Changed
- `.gitignore` now excludes everything in `resumes/` except `.gitkeep`
  (rendered `.tex`/`.md` carry personal data).

## [0.1.0] - 2026-05-10

### Added
- Initial repository scaffolding for cv-manager.
- Hybrid privacy model: `.env` (identity/contact) + `data/cv_data.private.json`
  (structured lists), both gitignored. Committed counterparts:
  `.env.example` and `data/cv_data.example.json`.
- `.gitignore` covering `.env`, `*.private.*`, LaTeX build artifacts,
  Python caches, and editor/OS files.
- `templates/classic.tex` (LaTeX) and `templates/classic.md` (Markdown).
- `templates/README.md` documenting placeholder conventions and data sources.
- `requirements.txt` pinning `python-dotenv` and `Jinja2`.
- README with setup, privacy model, and roadmap.

[Unreleased]: https://github.com/SantiestebanE/cv-manager/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/SantiestebanE/cv-manager/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/SantiestebanE/cv-manager/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/SantiestebanE/cv-manager/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/SantiestebanE/cv-manager/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/SantiestebanE/cv-manager/releases/tag/v0.1.0
