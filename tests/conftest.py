"""Shared fixtures for cv-manager tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

SAMPLE_ENV_CONTENT = """\
CV_FULL_NAME="Jane Doe"
CV_HEADLINE="Senior Software Engineer"
CV_SUMMARY="Experienced engineer with a focus on distributed systems."
CV_EMAIL="jane@example.com"
CV_PHONE="+1 555 000 1234"
CV_LOCATION="San Francisco, CA"
CV_LINKEDIN="https://www.linkedin.com/in/janedoe"
CV_GITHUB="https://github.com/janedoe"
CV_WEBSITE="https://janedoe.dev"
"""

SAMPLE_JSON_DATA = {
    "experiences": [
        {
            "title": "Senior Software Engineer",
            "company": "Acme Corp",
            "location": "Remote",
            "start_date": "2023-01",
            "end_date": "Present",
            "highlights": [
                "Led migration of legacy monolith to microservices.",
                "Mentored 4 engineers.",
            ],
            "tech": ["Python", "Go", "Kubernetes"],
        }
    ],
    "education": [
        {
            "degree": "B.Sc. in Computer Science",
            "institution": "Example University",
            "location": "City, Country",
            "start_date": "2016",
            "end_date": "2020",
            "notes": "",
        }
    ],
    "skills": [
        {"category": "Languages", "items": ["Python", "Go", "TypeScript"]},
        {"category": "Infrastructure", "items": ["Kubernetes", "Docker"]},
    ],
    "projects": [
        {
            "name": "Open Source Tool",
            "url": "https://github.com/janedoe/tool",
            "description": "A CLI tool for automating deploys.",
            "tech": ["Python", "Click"],
        }
    ],
    "certifications": [
        {
            "name": "AWS Solutions Architect",
            "issuer": "Amazon",
            "date": "2024-03",
            "url": "https://example.com/cert",
        }
    ],
    "languages": [
        {"name": "English", "level": "Native"},
        {"name": "Spanish", "level": "Professional"},
    ],
}


@pytest.fixture
def project_root(tmp_path, monkeypatch):
    """Create a mock project root with templates, data, and .env."""
    root = tmp_path / "cv-manager"
    root.mkdir()

    templates_dir = root / "templates"
    templates_dir.mkdir()

    data_dir = root / "data"
    data_dir.mkdir()

    resumes_dir = root / "resumes"
    resumes_dir.mkdir()

    env_file = root / ".env"
    env_file.write_text(SAMPLE_ENV_CONTENT, encoding="utf-8")

    data_file = data_dir / "cv_data.private.json"
    data_file.write_text(json.dumps(SAMPLE_JSON_DATA), encoding="utf-8")

    real_templates = Path(__file__).resolve().parent.parent / "templates"
    for tpl in real_templates.iterdir():
        if tpl.is_file() and tpl.suffix in {".tex", ".md"} and tpl.name.lower() != "readme.md":
            shutil.copy(tpl, templates_dir / tpl.name)

    env_example = root / ".env.example"
    env_example.write_text(SAMPLE_ENV_CONTENT, encoding="utf-8")

    data_example = data_dir / "cv_data.example.json"
    data_example.write_text(json.dumps(SAMPLE_JSON_DATA), encoding="utf-8")

    import scripts.generate as gen

    monkeypatch.setattr(gen, "ROOT", root)
    monkeypatch.setattr(gen, "TEMPLATES_DIR", templates_dir)
    monkeypatch.setattr(gen, "DATA_FILE", data_file)
    monkeypatch.setattr(gen, "DATA_EXAMPLE", data_example)
    monkeypatch.setattr(gen, "ENV_FILE", env_file)
    monkeypatch.setattr(gen, "ENV_EXAMPLE", env_example)

    return root


@pytest.fixture
def out_dir(project_root):
    """Return the resumes output directory."""
    return project_root / "resumes"
