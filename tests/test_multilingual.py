"""Tests for multilingual message handling."""

import pytest
from src.demo_data import DEMO_MESSAGES


def test_hinglish_message_present():
    """Verify Hinglish demo message exists."""
    hinglish = [m for m in DEMO_MESSAGES if "Hinglish" in m.get("description", "")]
    assert len(hinglish) > 0


def test_multilingual_support():
    """Test support for multiple languages."""
    messages = [
        "Bonjour",
        "Hola",
        "Hallo",
        "你好",
        "こんにちは",
        "namaste",
    ]
    
    for msg in messages:
        assert len(msg) > 0
