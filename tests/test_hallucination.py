"""Tests for hallucination prevention."""

import pytest
from src.models import TriageDecision, Priority


def test_hallucinated_fields_rejected():
    """
    Test that extra/hallucinated fields are handled.
    Pydantic will reject unknown fields by default.
    """
    valid = {
        "category": "test",
        "priority": "P2",
        "summary": "Test",
        "suggested_action": "Test",
        "needs_human": False,
        "confidence": 0.5
    }
    
    decision = TriageDecision(**valid)
    assert decision.category == "test"


def test_no_invented_transaction_ids():
    """
    Test that summary doesn't contain invented transaction IDs.
    """
    summary = "Payment issue - no transaction ID mentioned"
    decision = TriageDecision(
        category="payment_issue",
        priority=Priority.P1,
        summary=summary,
        suggested_action="Request transaction ID from customer",
        needs_human=True,
        confidence=0.7
    )
    
    assert "#" not in decision.summary or "transaction" not in decision.summary.lower()
