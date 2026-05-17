"""CV generation history tracking.

Logs each generation event to resumes/history.json with metadata.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

HISTORY_FILE = Path(__file__).resolve().parent.parent / "resumes" / "history.json"
MAX_ENTRIES = 50


def _load() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries: list[dict]) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def log_generation(
    *,
    filename: str,
    template: str,
    matched: bool = False,
    job_title: str = "",
    is_cover_letter: bool = False,
) -> dict:
    """Append a generation event to history. Returns the new entry."""
    entries = _load()

    entry = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "template": template,
        "filename": filename,
        "matched": matched,
        "job_title": job_title,
        "is_cover_letter": is_cover_letter,
    }

    entries.insert(0, entry)
    entries = entries[:MAX_ENTRIES]
    _save(entries)
    return entry


def get_history() -> list[dict]:
    """Return all history entries, most recent first."""
    return _load()


def get_entry(entry_id: str) -> dict | None:
    """Find a history entry by ID."""
    for entry in _load():
        if entry["id"] == entry_id:
            return entry
    return None
