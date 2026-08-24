"""
Data models for FRONTLINE customer-support triage classifier.

Defines the core schema: structured output validation, escalation decisions,
and batch processing results.
"""

from pydantic import BaseModel, Field, validator
from typing import Literal, Optional, List
from enum import Enum


class Priority(str, Enum):
    """Priority levels for customer-support triage."""
    P0 = "P0"  # Critical / immediate risk
    P1 = "P1"  # High-impact / urgent
    P2 = "P2"  # Normal support issue
    P3 = "P3"  # Low urgency / general info


class TriageDecision(BaseModel):
    """
    Structured triage output for a single customer message.
    
    This is the core output schema that the LLM must produce.
    Never invented fields must be validated strictly.
    """
    category: str = Field(
        ...,
        description="Triage category (e.g., 'payment_issue', 'account_access', 'general_inquiry')"
    )
    priority: Priority = Field(
        ...,
        description="Priority level: P0 (critical), P1 (high), P2 (normal), P3 (low)"
    )
    summary: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Concise summary of the issue (no fabricated details)"
    )
    suggested_action: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Recommended next step for support team"
    )
    needs_human: bool = Field(
        ...,
        description="Whether this message requires immediate human review"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in this classification (0.0 to 1.0)"
    )

    @validator("summary", "suggested_action")
    def no_fabricated_details(cls, v):
        """Ensure summaries don't contain invented facts."""
        if not v or v.isspace():
            raise ValueError("Field cannot be empty or whitespace-only")
        return v.strip()


class TriageResult(BaseModel):
    """
    Complete result for a single message, including metadata.
    """
    message_id: str
    message_text: str
    decision: TriageDecision
    latency_ms: float
    validation_error: Optional[str] = None
    escalation_reason: Optional[str] = None


class BatchResults(BaseModel):
    """
    Summary and results for batch processing.
    """
    total_messages: int
    successful_classifications: int
    failed_classifications: int
    escalated_to_human: int
    average_confidence: float
    average_latency_ms: float
    priority_distribution: dict = Field(default_factory=dict)  # {P0: count, P1: count, ...}
    results: List[TriageResult] = Field(default_factory=list)


class EvaluationMetrics(BaseModel):
    """
    Metrics comparing predictions against ground truth.
    """
    total_messages: int
    category_agreement: float  # Percentage of correct category predictions
    priority_agreement: float   # Percentage of correct priority predictions
    needs_human_agreement: float  # Percentage of correct needs_human predictions
    overall_agreement: float    # Percentage of all fields matching
    failures: List[dict] = Field(default_factory=list)  # Failed cases
