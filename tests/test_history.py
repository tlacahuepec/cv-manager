"""Tests for scripts/history.py — CV generation history tracking."""

from __future__ import annotations

from unittest.mock import patch

import scripts.history as hist


class TestHistory:
    def test_log_and_retrieve(self, tmp_path):
        history_file = tmp_path / "history.json"
        with patch.object(hist, "HISTORY_FILE", history_file):
            entry = hist.log_generation(filename="test.tex", template="classic.tex")
            assert entry["filename"] == "test.tex"
            assert entry["template"] == "classic.tex"
            assert entry["matched"] is False
            assert "id" in entry
            assert "timestamp" in entry

            entries = hist.get_history()
            assert len(entries) == 1
            assert entries[0]["id"] == entry["id"]

    def test_log_matched(self, tmp_path):
        history_file = tmp_path / "history.json"
        with patch.object(hist, "HISTORY_FILE", history_file):
            entry = hist.log_generation(
                filename="matched.tex",
                template="modern.tex",
                matched=True,
                job_title="Senior Engineer at Acme",
            )
            assert entry["matched"] is True
            assert entry["job_title"] == "Senior Engineer at Acme"

    def test_log_cover_letter(self, tmp_path):
        history_file = tmp_path / "history.json"
        with patch.object(hist, "HISTORY_FILE", history_file):
            entry = hist.log_generation(
                filename="cover.tex",
                template="cover_letter.tex",
                is_cover_letter=True,
            )
            assert entry["is_cover_letter"] is True

    def test_max_entries_cap(self, tmp_path):
        history_file = tmp_path / "history.json"
        with patch.object(hist, "HISTORY_FILE", history_file):
            for i in range(60):
                hist.log_generation(filename=f"file_{i}.tex", template="classic.tex")
            entries = hist.get_history()
            assert len(entries) == 50

    def test_get_entry_by_id(self, tmp_path):
        history_file = tmp_path / "history.json"
        with patch.object(hist, "HISTORY_FILE", history_file):
            entry = hist.log_generation(filename="find_me.tex", template="classic.tex")
            found = hist.get_entry(entry["id"])
            assert found is not None
            assert found["filename"] == "find_me.tex"

    def test_get_entry_not_found(self, tmp_path):
        history_file = tmp_path / "history.json"
        with patch.object(hist, "HISTORY_FILE", history_file):
            assert hist.get_entry("nonexistent") is None

    def test_empty_history(self, tmp_path):
        history_file = tmp_path / "history.json"
        with patch.object(hist, "HISTORY_FILE", history_file):
            assert hist.get_history() == []

    def test_corrupted_file_returns_empty(self, tmp_path):
        history_file = tmp_path / "history.json"
        history_file.write_text("not json", encoding="utf-8")
        with patch.object(hist, "HISTORY_FILE", history_file):
            assert hist.get_history() == []
