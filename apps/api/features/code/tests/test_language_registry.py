"""Tests for the language registry and runner loading."""

from __future__ import annotations

from judge.registry import LANGUAGE_REGISTRY, get_language, get_supported_languages


class TestLanguageRegistry:
    def test_all_languages_registered(self):
        assert "python" in LANGUAGE_REGISTRY
        assert "javascript" in LANGUAGE_REGISTRY
        assert "typescript" in LANGUAGE_REGISTRY
        assert "java" in LANGUAGE_REGISTRY
        assert "cpp" in LANGUAGE_REGISTRY
        assert "go" in LANGUAGE_REGISTRY
        assert "rust" in LANGUAGE_REGISTRY

    def test_get_language_returns_config(self):
        cfg = get_language("python")
        assert cfg is not None
        assert cfg.id == "python"
        assert cfg.file_extension == ".py"
        assert cfg.run_command is not None

    def test_get_language_returns_none_for_unknown(self):
        assert get_language("brainfuck") is None

    def test_interpreted_languages_have_no_compile(self):
        assert get_language("python").compile_command is None
        assert get_language("javascript").compile_command is None

    def test_compiled_languages_have_compile(self):
        assert get_language("java").compile_command is not None
        assert get_language("cpp").compile_command is not None
        assert get_language("go").compile_command is not None
        assert get_language("rust").compile_command is not None
        assert get_language("typescript").compile_command is not None

    def test_get_supported_languages_returns_list(self):
        langs = get_supported_languages()
        assert len(langs) >= 7
        for lang in langs:
            assert "id" in lang
            assert "name" in lang
            assert "extension" in lang
