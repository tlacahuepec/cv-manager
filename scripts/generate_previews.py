"""Generate preview thumbnails for all CV templates.

Renders each template with sample data, compiles to PDF, then converts
page 1 to a PNG thumbnail stored in web/static/previews/.

Usage:
    python scripts/generate_previews.py

Requires: pdflatex (or xelatex), pandoc, pymupdf
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.generate import (  # noqa: E402
    TEMPLATES_DIR,
    CVError,
    compile_pdf,
    render,
)

PREVIEWS_DIR = ROOT / "web" / "static" / "previews"
THUMB_WIDTH = 300  # pixels


def generate_preview(template_name: str, out_dir: Path) -> Path | None:
    """Render a template, compile to PDF, extract page 1 as PNG."""
    try:
        rendered_path = render(template_name, out_dir)
        pdf_path = compile_pdf(rendered_path)
    except CVError as exc:
        print(f"  SKIP {template_name}: {exc}")
        return None

    doc = fitz.open(pdf_path)
    page = doc[0]
    zoom = THUMB_WIDTH / page.rect.width
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)

    stem = Path(template_name).stem
    png_path = PREVIEWS_DIR / f"{stem}.png"
    pix.save(str(png_path))
    doc.close()

    return png_path


def main() -> None:
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    tmp_dir = ROOT / "resumes" / "_previews_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    templates = sorted(
        p.name
        for p in TEMPLATES_DIR.iterdir()
        if p.is_file() and p.suffix in {".tex", ".md"} and p.name.lower() != "readme.md"
    )

    print(f"Generating previews for {len(templates)} templates...")
    for tpl in templates:
        png = generate_preview(tpl, tmp_dir)
        if png:
            print(f"  OK: {tpl} -> {png.relative_to(ROOT)}")

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print("Done.")


if __name__ == "__main__":
    main()
