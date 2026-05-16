"""Tests for scripts/generate.py — the core CV rendering engine."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

import scripts.generate as gen

# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------


class TestSlugify:
    def test_basic_name(self):
        assert gen.slugify("Jane Doe") == "jane_doe"

    def test_special_characters(self):
        assert gen.slugify("José García-López") == "jos_garc_a_l_pez"

    def test_extra_whitespace(self):
        assert gen.slugify("  Hello   World  ") == "hello_world"

    def test_empty_string(self):
        assert gen.slugify("") == "cv"

    def test_only_special_chars(self):
        assert gen.slugify("@#$%") == "cv"

    def test_numbers_preserved(self):
        assert gen.slugify("Version 2.0") == "version_2_0"


# ---------------------------------------------------------------------------
# load_env_context
# ---------------------------------------------------------------------------


class TestLoadEnvContext:
    def test_loads_env_vars(self, project_root):
        ctx = gen.load_env_context()
        assert ctx["full_name"] == "Jane Doe"
        assert ctx["email"] == "jane@example.com"
        assert ctx["headline"] == "Senior Software Engineer"

    def test_strips_prefix_and_lowercases(self, project_root):
        ctx = gen.load_env_context()
        assert "CV_FULL_NAME" not in ctx
        assert "full_name" in ctx

    def test_missing_env_file(self, project_root):
        gen.ENV_FILE.unlink()
        with pytest.raises(gen.CVError, match="missing"):
            gen.load_env_context()

    def test_missing_full_name(self, project_root, monkeypatch):
        env_file = gen.ENV_FILE
        env_file.write_text('CV_EMAIL="test@example.com"\n', encoding="utf-8")
        monkeypatch.delenv("CV_FULL_NAME", raising=False)
        with pytest.raises(gen.CVError, match="CV_FULL_NAME"):
            gen.load_env_context()


# ---------------------------------------------------------------------------
# load_json_context
# ---------------------------------------------------------------------------


class TestLoadJsonContext:
    def test_loads_valid_json(self, project_root):
        ctx = gen.load_json_context()
        assert "experiences" in ctx
        assert len(ctx["experiences"]) == 1
        assert ctx["experiences"][0]["company"] == "Acme Corp"

    def test_missing_data_file(self, project_root):
        gen.DATA_FILE.unlink()
        with pytest.raises(gen.CVError, match="missing"):
            gen.load_json_context()

    def test_invalid_json(self, project_root):
        gen.DATA_FILE.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(gen.CVError, match="not valid JSON"):
            gen.load_json_context()


# ---------------------------------------------------------------------------
# build_environment
# ---------------------------------------------------------------------------


class TestBuildEnvironment:
    def test_tex_uses_custom_delimiters(self):
        env = gen.build_environment("classic.tex")
        assert env.variable_start_string == "<<"
        assert env.variable_end_string == ">>"
        assert env.block_start_string == "<%"
        assert env.block_end_string == "%>"

    def test_md_uses_standard_delimiters(self):
        env = gen.build_environment("classic.md")
        assert env.variable_start_string == "{{"
        assert env.variable_end_string == "}}"
        assert env.block_start_string == "{%"
        assert env.block_end_string == "%}"

    def test_unknown_ext_uses_standard_delimiters(self):
        env = gen.build_environment("test.html")
        assert env.variable_start_string == "{{"


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------


class TestRender:
    def test_render_classic_tex(self, project_root, out_dir):
        path = gen.render("classic.tex", out_dir)
        assert path.exists()
        assert path.suffix == ".tex"
        content = path.read_text(encoding="utf-8")
        assert "Jane Doe" in content

    def test_render_minimal_md(self, project_root, out_dir):
        path = gen.render("minimal.md", out_dir)
        assert path.exists()
        assert path.suffix == ".md"
        content = path.read_text(encoding="utf-8")
        assert "Jane Doe" in content

    def test_output_filename_pattern(self, project_root, out_dir):
        path = gen.render("classic.tex", out_dir)
        assert "jane_doe" in path.name
        assert "classic" in path.name
        assert path.name.endswith(".tex")

    def test_creates_output_dir(self, project_root, tmp_path):
        new_dir = tmp_path / "new_output"
        path = gen.render("classic.tex", new_dir)
        assert new_dir.exists()
        assert path.exists()

    def test_template_not_found(self, project_root, out_dir):
        with pytest.raises(gen.CVError, match="not found"):
            gen.render("nonexistent.tex", out_dir)

    def test_all_tex_templates_render(self, project_root, out_dir):
        templates_dir = gen.TEMPLATES_DIR
        for tpl in templates_dir.iterdir():
            if tpl.suffix == ".tex":
                path = gen.render(tpl.name, out_dir)
                assert path.exists()
                content = path.read_text(encoding="utf-8")
                assert "Jane Doe" in content

    def test_all_md_templates_render(self, project_root, out_dir):
        templates_dir = gen.TEMPLATES_DIR
        for tpl in templates_dir.iterdir():
            if tpl.suffix == ".md" and tpl.name.lower() != "readme.md":
                path = gen.render(tpl.name, out_dir)
                assert path.exists()
                content = path.read_text(encoding="utf-8")
                assert "Jane Doe" in content


# ---------------------------------------------------------------------------
# _needs_xelatex
# ---------------------------------------------------------------------------


class TestNeedsXelatex:
    def test_detects_marker(self, tmp_path):
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("% engine: xelatex\n\\documentclass{article}\n", encoding="utf-8")
        assert gen._needs_xelatex(tex_file) is True

    def test_no_marker(self, tmp_path):
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\n\\begin{document}\n", encoding="utf-8")
        assert gen._needs_xelatex(tex_file) is False

    def test_marker_beyond_2000_chars_not_detected(self, tmp_path):
        tex_file = tmp_path / "test.tex"
        content = "x" * 2001 + "\n% engine: xelatex\n"
        tex_file.write_text(content, encoding="utf-8")
        assert gen._needs_xelatex(tex_file) is False


# ---------------------------------------------------------------------------
# compile_pdf
# ---------------------------------------------------------------------------


class TestCompilePdf:
    def test_tex_uses_pdflatex_by_default(self, tmp_path):
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\n\\begin{document}Hi\\end{document}\n", encoding="utf-8")

        with patch("scripts.generate.shutil.which", return_value="/usr/bin/pdflatex"):
            with patch("scripts.generate._run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
                (tmp_path / "test.pdf").write_bytes(b"%PDF-fake")
                gen.compile_pdf(tex_file)

                call_args = mock_run.call_args[0][0]
                assert call_args[0] == "pdflatex"

    def test_tex_uses_xelatex_when_marker_present(self, tmp_path):
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("% engine: xelatex\n\\documentclass{article}\n", encoding="utf-8")

        with patch("scripts.generate.shutil.which", return_value="/usr/bin/xelatex"):
            with patch("scripts.generate._run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
                (tmp_path / "test.pdf").write_bytes(b"%PDF-fake")
                gen.compile_pdf(tex_file)

                call_args = mock_run.call_args[0][0]
                assert call_args[0] == "xelatex"

    def test_tex_missing_pdflatex(self, tmp_path):
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\n", encoding="utf-8")

        with patch("scripts.generate.shutil.which", return_value=None):
            with pytest.raises(gen.CVError, match="pdflatex not found"):
                gen.compile_pdf(tex_file)

    def test_tex_missing_xelatex(self, tmp_path):
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("% engine: xelatex\n\\documentclass{article}\n", encoding="utf-8")

        with patch("scripts.generate.shutil.which", return_value=None):
            with pytest.raises(gen.CVError, match="xelatex not found"):
                gen.compile_pdf(tex_file)

    def test_md_uses_pandoc(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Hello\n", encoding="utf-8")

        with patch("scripts.generate.shutil.which", return_value="/usr/bin/pandoc"):
            with patch("scripts.generate._run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
                gen.compile_pdf(md_file)

                call_args = mock_run.call_args[0][0]
                assert call_args[0] == "pandoc"

    def test_md_missing_pandoc(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Hello\n", encoding="utf-8")

        with patch("scripts.generate.shutil.which", return_value=None):
            with pytest.raises(gen.CVError, match="pandoc not found"):
                gen.compile_pdf(md_file)

    def test_unsupported_suffix(self, tmp_path):
        file = tmp_path / "test.rst"
        file.write_text("Hello\n", encoding="utf-8")
        with pytest.raises(gen.CVError, match="don't know how to compile"):
            gen.compile_pdf(file)

    def test_compilation_failure_raises(self, tmp_path):
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\n", encoding="utf-8")

        with patch("scripts.generate.shutil.which", return_value="/usr/bin/pdflatex"):
            with patch("scripts.generate._run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(
                    args=[], returncode=1, stdout="Error on line 1", stderr=""
                )
                with pytest.raises(gen.CVError, match="failed"):
                    gen.compile_pdf(tex_file)

    def test_aux_files_cleaned(self, tmp_path):
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\n", encoding="utf-8")

        for suf in gen.LATEX_AUX_SUFFIXES:
            (tmp_path / f"test{suf}").write_text("aux", encoding="utf-8")

        with patch("scripts.generate.shutil.which", return_value="/usr/bin/pdflatex"):
            with patch("scripts.generate._run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
                (tmp_path / "test.pdf").write_bytes(b"%PDF-fake")
                gen.compile_pdf(tex_file)

        for suf in gen.LATEX_AUX_SUFFIXES:
            assert not (tmp_path / f"test{suf}").exists()


# ---------------------------------------------------------------------------
# main (CLI integration)
# ---------------------------------------------------------------------------


class TestMain:
    def test_default_args(self, project_root, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["generate.py"])
        gen.main()
        captured = capsys.readouterr()
        assert "wrote" in captured.out
        assert "classic" in captured.out

    def test_custom_template(self, project_root, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["generate.py", "--template", "minimal.md"])
        gen.main()
        captured = capsys.readouterr()
        assert "wrote" in captured.out
        assert "minimal" in captured.out

    def test_invalid_template_exits(self, project_root, monkeypatch):
        monkeypatch.setattr("sys.argv", ["generate.py", "--template", "nope.tex"])
        with pytest.raises(SystemExit):
            gen.main()

    def test_pdf_flag_calls_compile(self, project_root, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["generate.py", "--pdf"])
        pdf_path = project_root / "resumes" / "fake.pdf"
        with patch("scripts.generate.compile_pdf") as mock_compile:
            mock_compile.return_value = pdf_path
            gen.main()
            mock_compile.assert_called_once()
