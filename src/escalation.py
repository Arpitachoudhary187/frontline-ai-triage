"""
Escalation policy for FRONTLINE triage.

Determines when a message should be routed to human review based on
confidence, risk factors, and message characteristics.
"""

import logging
from typing import Tuple
from src.models import TriageDecision, Priority

logger = logging.getLogger(__name__)


class EscalationPolicy:
    """
    Escalation policy engine.
    Determines whether a message needs human review.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.70,
        escalate_p0_p1: bool = True,
        escalate_unclear: bool = True,
    ):
        """
        Initialize escalation policy.
        
        Args:
            confidence_threshold: If confidence < this, escalate to human
            escalate_p0_p1: Always escalate P0/P1 for review
            escalate_unclear: Escalate "unclear" category messages
        """
        self.confidence_threshold = confidence_threshold
        self.escalate_p0_p1 = escalate_p0_p1
        self.escalate_unclear = escalate_unclear

    def should_escalate(
        self,
        decision: TriageDecision,
        message_text: str = ""
    ) -> Tuple[bool, str]:
        """
        Determine if a message needs human escalation.
        
        Args:
            decision: LLM triage decision
            message_text: Original customer message (for context)
        
        Returns:
            (should_escalate: bool, reason: str)
        """
        reasons = []

        # 1. Low confidence threshold
        if decision.confidence < self.confidence_threshold:
            reasons.append(f"Confidence below threshold ({decision.confidence:.2f} < {self.confidence_threshold})")

        # 2. LLM already marked needs_human=true
        if decision.needs_human:
            reasons.append("LLM marked needs_human=true")

        # 3. Escalate critical priorities
        if self.escalate_p0_p1 and decision.priority in [Priority.P0, Priority.P1]:
            reasons.append(f"Priority {decision.priority} requires human review")

        # 4. Unclear category
        if self.escalate_unclear and decision.category == "unclear":
            reasons.append("Unclear message category")

        # 5. Very high confidence but P0 (double-check critical cases)
        if decision.priority == Priority.P0 and decision.confidence > 0.95:
            # Don't escalate super-obvious critical issues
            pass

        # 6. Empty or garbage-like message
        if not message_text or len(message_text.strip()) < 3:
            reasons.append("Message too short or empty")

        # Determine escalation
        should_escalate = len(reasons) > 0
        reason = "; ".join(reasons) if reasons else "No escalation needed"

        return should_escalate, reason

    def apply_escalation_flag(
        self,
        decision: TriageDecision,
        message_text: str = ""
    ) -> TriageDecision:
        """
        Apply escalation policy to decision, updating needs_human if necessary.
        
        Args:
            decision: Original triage decision
            message_text: Original customer message
        
        Returns:
            Updated TriageDecision with escalation applied
        """
        should_escalate, _ = self.should_escalate(decision, message_text)
        
        if should_escalate and not decision.needs_human:
            # If escalation policy says yes but LLM said no, override to yes
            # Also lower confidence slightly to signal uncertainty
            decision_dict = decision.dict()
            decision_dict["needs_human"] = True
            if decision_dict["confidence"] > 0.5:
                decision_dict["confidence"] = max(0.5, decision_dict["confidence"] - 0.1)
            return TriageDecision(**decision_dict)
        
        return decision
