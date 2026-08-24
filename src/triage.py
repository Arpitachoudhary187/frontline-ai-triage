"""
Main triage pipeline for FRONTLINE.

Orchestrates LLM classification, validation, escalation, and result collection.
"""

import time
import logging
from typing import List, Optional
from src.models import TriageResult, TriageDecision, BatchResults, Priority
from src.llm_client import LLMClient
from src.escalation import EscalationPolicy

logger = logging.getLogger(__name__)


class TriagePipeline:
    """
    Main triage classification pipeline.
    Handles end-to-end message classification with validation and escalation.
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        escalation_policy: Optional[EscalationPolicy] = None
    ):
        """
        Initialize triage pipeline.
        
        Args:
            llm_client: LLM client instance (creates default if not provided)
            escalation_policy: Escalation policy (creates default if not provided)
        """
        try:
            self.llm_client = llm_client or LLMClient()
        except Exception as e:
            logger.error(f"LLM client initialization failed: {str(e)}")
            self.llm_client = None

        self.escalation_policy = escalation_policy or EscalationPolicy()
        self.results: List[TriageResult] = []

    def classify_message(self, message_id: str, message_text: str) -> TriageResult:
        """
        Classify a single message end-to-end.
        
        Args:
            message_id: Stable message identifier
            message_text: Raw customer message
        
        Returns:
            TriageResult with decision and metadata
        """
        start_time = time.time()
        
        try:
            # Call LLM
            if not self.llm_client:
                decision = None
                error = "LLM client not initialized"
            else:
                decision, error = self.llm_client.classify(message_text)

            latency_ms = (time.time() - start_time) * 1000

            if error or not decision:
                logger.warning(f"Classification failed for {message_id}: {error}")
                return TriageResult(
                    message_id=message_id,
                    message_text=message_text,
                    decision=self._create_fallback_decision(),
                    latency_ms=latency_ms,
                    validation_error=error or "Unknown error"
                )

            # Apply escalation policy
            decision = self.escalation_policy.apply_escalation_flag(decision, message_text)

            # Check if needs escalation
            should_escalate, escalation_reason = self.escalation_policy.should_escalate(
                decision,
                message_text
            )

            result = TriageResult(
                message_id=message_id,
                message_text=message_text,
                decision=decision,
                latency_ms=latency_ms,
                escalation_reason=escalation_reason if should_escalate else None
            )

            return result

        except Exception as e:
            logger.error(f"Unexpected error classifying {message_id}: {str(e)}")
            latency_ms = (time.time() - start_time) * 1000
            return TriageResult(
                message_id=message_id,
                message_text=message_text,
                decision=self._create_fallback_decision(),
                latency_ms=latency_ms,
                validation_error=f"Exception: {str(e)}"
            )

    def process_batch(self, messages: List[dict]) -> BatchResults:
        """
        Process a batch of messages.
        
        Args:
            messages: List of dicts with 'id' and 'text' keys
        
        Returns:
            BatchResults with summary statistics and all results
        """
        self.results = []
        latencies = []
        confidences = []
        priority_counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        escalated_count = 0

        logger.info(f"Processing batch of {len(messages)} messages")

        for msg in messages:
            try:
                message_id = msg.get("id", f"msg_{len(self.results)}")
                message_text = msg.get("text", "")

                result = self.classify_message(message_id, message_text)
                self.results.append(result)

                latencies.append(result.latency_ms)
                confidences.append(result.decision.confidence)
                priority_counts[result.decision.priority] += 1

                if result.escalation_reason:
                    escalated_count += 1

                logger.debug(
                    f"[{message_id}] {result.decision.category} / {result.decision.priority} "
                    f"(conf: {result.decision.confidence:.2f}) "
                    f"{'[ESCALATED]' if result.escalation_reason else ''}"
                )

            except Exception as e:
                logger.error(f"Error processing message {msg.get('id')}: {str(e)}")
                continue

        # Calculate summary
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        successful = len([r for r in self.results if not r.validation_error])
        failed = len([r for r in self.results if r.validation_error])

        batch_results = BatchResults(
            total_messages=len(messages),
            successful_classifications=successful,
            failed_classifications=failed,
            escalated_to_human=escalated_count,
            average_confidence=avg_confidence,
            average_latency_ms=avg_latency,
            priority_distribution=priority_counts,
            results=self.results
        )

        logger.info(
            f"Batch complete: {successful} successful, {failed} failed, "
            f"{escalated_count} escalated. Avg confidence: {avg_confidence:.2f}, "
            f"Avg latency: {avg_latency:.1f}ms"
        )

        return batch_results

    def _create_fallback_decision(self) -> TriageDecision:
        """
        Create a safe fallback decision for errors.
        Routes to human review with low confidence.
        """
        return TriageDecision(
            category="unclear",
            priority=Priority.P2,
            summary="Classification failed - requires human review",
            suggested_action="Route to support team for manual triage",
            needs_human=True,
            confidence=0.1
        )
