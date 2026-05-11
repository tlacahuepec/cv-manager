# Templates

Templates render with Jinja2. Data comes from two sources:

| Source                          | Used for                                   | Committed? |
| ------------------------------- | ------------------------------------------ | ---------- |
| `.env` (root)                   | Identity & contact (single-value fields)   | No         |
| `data/cv_data.private.json`     | Structured lists (experiences, etc.)       | No         |

The future generator will merge both into a single render context. Keys exposed to templates:

**From `.env`** (lowercased, `CV_` prefix stripped):
`full_name`, `headline`, `summary`, `email`, `phone`, `location`,
`linkedin`, `github`, `website`.

**From `cv_data.private.json`** (top-level keys):
`experiences[]`, `education[]`, `skills[]`, `projects[]`, `certifications[]`, `languages[]`.

See `data/cv_data.example.json` for each list's object schema.

## Delimiter conventions

LaTeX braces `{}` collide with Jinja's default `{{ }}` / `{% %}`. Templates use:

| File type   | Variable     | Block          | Comment   |
| ----------- | ------------ | -------------- | --------- |
| `*.tex`     | `<< var >>`  | `<% block %>`  | `<# c #>` |
| `*.md`      | `{{ var }}`  | `{% block %}`  | `{# c #}` |

The generator script will configure Jinja's `Environment` with the right delimiters per file extension.

## Adding a new template

1. Copy `classic.tex` or `classic.md` to a new file (e.g. `modern.tex`).
2. Restyle freely; keep the variable names so it stays compatible with the same data.
3. New templates are auto-discovered by filename — no registry edits needed.

## Available templates

- `classic.tex` — traditional single-column LaTeX CV with a colored accent.
- `classic.md` — Markdown counterpart for quick previews / pandoc conversion.
- `modern.tex` — two-column LaTeX with a tinted sidebar (contact, skills,
  languages, certifications). Requires the `paracol` and `fontawesome5`
  packages (bundled with MiKTeX / TeX Live).
- `minimal.md` — plain-text Markdown optimized for ATS resume scanners
  (no tables, no decorations, single column, ALL-CAPS section headings).
