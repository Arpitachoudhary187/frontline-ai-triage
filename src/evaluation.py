"""
Evaluation module for FRONTLINE triage.

Compares predictions against ground truth and calculates accuracy metrics.
"""

import json
import logging
from typing import List, Optional, Tuple
from src.models import TriageResult, EvaluationMetrics

logger = logging.getLogger(__name__)


class Evaluator:
    """
    Evaluation engine for comparing predictions against ground truth.
    """

    def __init__(self):
        """Initialize evaluator."""
        self.ground_truth = {}

    def load_ground_truth(self, filepath: str) -> Tuple[int, Optional[str]]:
        """
        Load ground truth labels from JSON file.
        
        Expected format:
        [
            {"message_id": "...", "category": "...", "priority": "...", "needs_human": true|false},
            ...
        ]
        
        Args:
            filepath: Path to ground truth JSON file
        
        Returns:
            (count_loaded, error_message)
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                return 0, "Ground truth must be a JSON list"

            self.ground_truth = {}
            for item in data:
                msg_id = item.get("message_id")
                if msg_id:
                    self.ground_truth[msg_id] = {
                        "category": item.get("category"),
                        "priority": item.get("priority"),
                        "needs_human": item.get("needs_human")
                    }

            logger.info(f"Loaded ground truth for {len(self.ground_truth)} messages")
            return len(self.ground_truth), None

        except Exception as e:
            error_msg = f"Failed to load ground truth: {str(e)}"
            logger.error(error_msg)
            return 0, error_msg

    def evaluate(self, results: List[TriageResult]) -> EvaluationMetrics:
        """
        Compare predictions against ground truth.
        
        Args:
            results: List of TriageResult objects
        
        Returns:
            EvaluationMetrics with accuracy statistics
        """
        if not self.ground_truth:
            logger.warning("No ground truth loaded")
            return EvaluationMetrics(
                total_messages=len(results),
                category_agreement=0.0,
                priority_agreement=0.0,
                needs_human_agreement=0.0,
                overall_agreement=0.0,
                failures=[]
            )

        category_correct = 0
        priority_correct = 0
        needs_human_correct = 0
        overall_correct = 0
        failures = []

        for result in results:
            if result.message_id not in self.ground_truth:
                continue

            truth = self.ground_truth[result.message_id]
            pred = result.decision

            # Category match
            cat_match = pred.category == truth["category"]
            if cat_match:
                category_correct += 1

            # Priority match
            pri_match = str(pred.priority.value) == str(truth["priority"])
            if pri_match:
                priority_correct += 1

            # Needs human match
            nh_match = pred.needs_human == truth["needs_human"]
            if nh_match:
                needs_human_correct += 1

            # Overall match
            if cat_match and pri_match and nh_match:
                overall_correct += 1
            else:
                failures.append({
                    "message_id": result.message_id,
                    "predicted": {
                        "category": pred.category,
                        "priority": str(pred.priority.value),
                        "needs_human": pred.needs_human
                    },
                    "expected": truth
                })

        total_evaluated = len([r for r in results if r.message_id in self.ground_truth])
        
        if total_evaluated == 0:
            category_pct = 0.0
            priority_pct = 0.0
            needs_human_pct = 0.0
            overall_pct = 0.0
        else:
            category_pct = (category_correct / total_evaluated) * 100
            priority_pct = (priority_correct / total_evaluated) * 100
            needs_human_pct = (needs_human_correct / total_evaluated) * 100
            overall_pct = (overall_correct / total_evaluated) * 100

        logger.info(
            f"Evaluation: Category={category_pct:.1f}%, Priority={priority_pct:.1f}%, "
            f"NeedsHuman={needs_human_pct:.1f}%, Overall={overall_pct:.1f}%"
        )

        return EvaluationMetrics(
            total_messages=total_evaluated,
            category_agreement=category_pct,
            priority_agreement=priority_pct,
            needs_human_agreement=needs_human_pct,
            overall_agreement=overall_pct,
            failures=failures[:10]  # Keep first 10 failures for analysis
        )

    def save_ground_truth_template(self, results: List[TriageResult], filepath: str) -> Optional[str]:
        """
        Save a ground-truth template that users can fill in.
        Useful for creating ground truth files.
        
        Args:
            results: List of TriageResult objects
            filepath: Where to save template
        
        Returns:
            Error message if any, None on success
        """
        try:
            template = []
            for result in results[:100]:  # Limit to first 100
                template.append({
                    "message_id": result.message_id,
                    "message_text": result.message_text[:100],  # First 100 chars as context
                    "category": "FILL_ME_IN",
                    "priority": "FILL_ME_IN",
                    "needs_human": False
                })

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)

            logger.info(f"Ground truth template saved to {filepath}")
            return None

        except Exception as e:
            error_msg = f"Failed to save template: {str(e)}"
            logger.error(error_msg)
            return error_msg
