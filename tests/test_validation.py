"""Tests for Pydantic model validation."""

import pytest
from src.models import TriageDecision, Priority


def test_valid_triage_decision():
    """Test creation of valid triage decision."""
    decision = TriageDecision(
        category="payment_issue",
        priority=Priority.P1,
        summary="User payment failed",
        suggested_action="Investigate transaction",
        needs_human=True,
        confidence=0.85
    )
    assert decision.category == "payment_issue"
    assert decision.priority == Priority.P1
    assert decision.confidence == 0.85


def test_invalid_confidence():
    """Test that confidence must be 0.0-1.0."""
    with pytest.raises(ValueError):
        TriageDecision(
            category="test",
            priority=Priority.P2,
            summary="Test",
            suggested_action="Test",
            needs_human=False,
            confidence=1.5  # Invalid
        )


def test_empty_summary_rejected():
    """Test that empty summary is rejected."""
    with pytest.raises(ValueError):
        TriageDecision(
            category="test",
            priority=Priority.P2,
            summary="",  # Invalid
            suggested_action="Test",
            needs_human=False,
            confidence=0.5
        )


def test_all_priorities():
    """Test all priority levels."""
    for priority in [Priority.P0, Priority.P1, Priority.P2, Priority.P3]:
        decision = TriageDecision(
            category="test",
            priority=priority,
            summary="Test",
            suggested_action="Test",
            needs_human=False,
            confidence=0.5
        )
        assert decision.priority == priority
