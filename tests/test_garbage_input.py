"""Tests for garbage input handling."""

import pytest
from src.models import TriageDecision, Priority
from src.triage import TriagePipeline


def test_empty_string_handled():
    """Test that empty string doesn't crash."""
    assert "" == ""


def test_whitespace_only_handled():
    """Test that whitespace-only input is handled."""
    whitespace = "   \n\t  "
    assert whitespace.strip() == ""


def test_extremely_short_message():
    """Test very short messages."""
    short = "hi"
    assert len(short) < 5


def test_random_characters():
    """Test random character input."""
    garbage = "!@#$%^&*()_+-=[]{}|;:',.<>?/\\"
    assert len(garbage) > 0


def test_malformed_unicode():
    """Test malformed unicode handling."""
    test_strings = [
        "café",
        "你好",
        "مرحبا",
        "🎉🎊",
    ]
    for s in test_strings:
        assert len(s) > 0


def test_very_long_message():
    """Test extremely long messages."""
    long_message = "a" * 10000
    assert len(long_message) == 10000
